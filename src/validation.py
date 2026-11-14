"""Pré-validação bloqueante da base OrbitShop antes de calcular indicadores.

Diferentemente da auditoria exploratória (que reporta problemas), este módulo
impede que dados estruturalmente inválidos gerem métricas plausíveis e falsas.
Não modifica registros e não preenche lacunas financeiras permitidas.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any


class InputValidationError(ValueError):
    """Entrada incompatível com o contrato do case."""


REQUIRED_FIELDS = {
    'Clientes': {'id', 'segmento', 'canal_aquisicao'},
    'Produtos': {'id', 'categoria', 'preco_unitario', 'fornecedor'},
    'Pedidos': {'id', 'cliente_id', 'data_pedido', 'status', 'valor_total'},
    'Itens_Pedido': {'id', 'pedido_id', 'produto_id', 'quantidade',
                    'preco_praticado', 'desconto_aplicado'},
    'Avaliacoes': {'id', 'pedido_id', 'produto_id', 'cliente_id', 'nota'},
    'Tickets_Suporte': {'id', 'pedido_id', 'cliente_id', 'data_abertura', 'status'},
}

RELATIONS = {
    'Pedidos': {'cliente_id': 'Clientes'},
    'Itens_Pedido': {'pedido_id': 'Pedidos', 'produto_id': 'Produtos'},
    'Avaliacoes': {'pedido_id': 'Pedidos', 'produto_id': 'Produtos',
                  'cliente_id': 'Clientes'},
    'Tickets_Suporte': {'pedido_id': 'Pedidos', 'cliente_id': 'Clientes'},
}

VALID_ORDER_STATUSES = frozenset({'entregue', 'cancelado', 'em_transito', 'devolvido'})


def _decimal(value: Any, field: str) -> Decimal:
    try:
        value = Decimal(str(value))
    except (TypeError, InvalidOperation) as exc:
        raise InputValidationError(f'{field}: valor numérico inválido') from exc
    if not value.is_finite():
        raise InputValidationError(f'{field}: valor não finito')
    return value


def validate_input(data: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Falha rapidamente em chaves, grãos, domínio e valores críticos inválidos.

    Nulos em Pedidos.valor_total e Itens_Pedido.desconto_aplicado são
    intencionalmente preservados. A função devolve somente metadados.
    """
    indices: dict[str, dict[Any, dict]] = {}
    for table, fields in REQUIRED_FIELDS.items():
        if table not in data:
            raise InputValidationError(f'Tabela ausente: {table}')
        rows = data[table]
        if not isinstance(rows, list) or not rows:
            raise InputValidationError(f'Tabela vazia ou inválida: {table}')
        for row in rows:
            missing = fields - row.keys()
            if missing:
                raise InputValidationError(f'{table}: campo obrigatório ausente: {sorted(missing)[0]}')
        identifiers = [row['id'] for row in rows]
        if any(identifier is None for identifier in identifiers):
            raise InputValidationError(f'{table}: id nulo')
        if len(set(identifiers)) != len(identifiers):
            repeated = next(k for k, n in Counter(identifiers).items() if n > 1)
            raise InputValidationError(f'{table}: id duplicado ({repeated})')
        indices[table] = {row['id']: row for row in rows}

    for table, links in RELATIONS.items():
        for field, reference in links.items():
            keys = indices[reference]
            for row in data[table]:
                if row[field] not in keys:
                    raise InputValidationError(
                        f'{table}.{field}: referência órfã para {reference} em id={row["id"]}'
                    )

    orders = indices['Pedidos']
    for row in data['Pedidos']:
        if row['status'] not in VALID_ORDER_STATUSES:
            raise InputValidationError(f'Pedidos.status: valor fora do domínio em id={row["id"]}')
        try:
            dt = date.fromisoformat(str(row['data_pedido']))
        except (TypeError, ValueError) as exc:
            raise InputValidationError(f'Pedidos.data_pedido: data inválida em id={row["id"]}') from exc
        if dt.year not in (2023, 2024):
            raise InputValidationError(f'Pedidos.data_pedido: fora da janela 2023–2024 em id={row["id"]}')
        if row['valor_total'] is not None:
            if _decimal(row['valor_total'], 'Pedidos.valor_total') < 0:
                raise InputValidationError(f'Pedidos.valor_total: negativo em id={row["id"]}')

    products_by_order: dict[Any, set[Any]] = defaultdict(set)
    for row in data['Itens_Pedido']:
        quantity = _decimal(row['quantidade'], 'Itens_Pedido.quantidade')
        if quantity <= 0 or quantity != quantity.to_integral_value():
            raise InputValidationError(f'Itens_Pedido.quantidade: inválida em id={row["id"]}')
        if _decimal(row['preco_praticado'], 'Itens_Pedido.preco_praticado') <= 0:
            raise InputValidationError(f'Itens_Pedido.preco_praticado: inválido em id={row["id"]}')
        discount = row['desconto_aplicado']
        if discount is not None and not 0 <= _decimal(discount, 'Itens_Pedido.desconto_aplicado') <= 1:
            raise InputValidationError(f'Itens_Pedido.desconto_aplicado: fora de [0, 1] em id={row["id"]}')
        products_by_order[row['pedido_id']].add(row['produto_id'])

    if len(products_by_order) != len(orders):
        raise InputValidationError('Pedidos: existe pedido sem itens')

    for table in ('Avaliacoes', 'Tickets_Suporte'):
        for row in data[table]:
            if row['cliente_id'] != orders[row['pedido_id']]['cliente_id']:
                raise InputValidationError(f'{table}: cliente diferente do pedido em id={row["id"]}')
            if table == 'Avaliacoes' and row['produto_id'] not in products_by_order[row['pedido_id']]:
                raise InputValidationError(f'Avaliacoes: produto ausente do pedido em id={row["id"]}')

    return {
        'pedidos': len(data['Pedidos']),
        'itens': len(data['Itens_Pedido']),
        'tabelas': {table: len(rows) for table, rows in data.items() if table in REQUIRED_FIELDS},
        'preenchimento_automatico': False,
    }
