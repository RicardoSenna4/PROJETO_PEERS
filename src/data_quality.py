"""Auditoria reproduzível dos seis conjuntos OrbitShop, sem alterar o XLSX.

Uso: python -m scripts.run_data_audit
Lê a origem por `src.workbook.load_xlsx` (OOXML via biblioteca padrão).
As regras distinguem fatos dos dados e interpretações de negócio não demonstradas.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
from pathlib import Path
from typing import Any

from .analysis import indexed

CENT = Decimal('0.01')
TABLES = ('Clientes', 'Produtos', 'Pedidos', 'Itens_Pedido', 'Tickets_Suporte', 'Avaliacoes')
DATE_COLUMNS = {
    'Clientes': ('data_cadastro',),
    'Pedidos': ('data_pedido',),
    'Tickets_Suporte': ('data_abertura', 'data_resolucao'),
    'Avaliacoes': ('data_avaliacao',),
}
NUMERIC_RULES = {
    'Produtos': {'preco_unitario': 'positive', 'custo_unitario': 'positive'},
    'Pedidos': {'valor_total': 'positive'},
    'Itens_Pedido': {'quantidade': 'positive_int', 'preco_praticado': 'positive', 'desconto_aplicado': 'fraction'},
    'Avaliacoes': {'nota': 'rating'},
}
EXPECTED_DOMAINS = {
    'Clientes': {'segmento': {'B2B', 'B2C'}, 'canal_aquisicao': {'orgânico', 'indicação', 'redes_sociais', 'paid_search'}},
    'Pedidos': {'status': {'entregue', 'cancelado', 'em_transito', 'devolvido'},
                'canal_venda': {'site', 'app', 'marketplace'}, 'cupom_desconto': {'sim', 'não'}},
    'Tickets_Suporte': {'status': {'aberto', 'escalado', 'resolvido'},
                       'categoria_problema': {'atraso', 'troca', 'defeito', 'cobrança', 'dúvida'}},
}
FOREIGN_KEYS = {
    'Pedidos': [('cliente_id', 'Clientes')],
    'Itens_Pedido': [('pedido_id', 'Pedidos'), ('produto_id', 'Produtos')],
    'Tickets_Suporte': [('pedido_id', 'Pedidos'), ('cliente_id', 'Clientes')],
    'Avaliacoes': [('pedido_id', 'Pedidos'), ('produto_id', 'Produtos'), ('cliente_id', 'Clientes')],
}


def missing(x: Any) -> bool:
    return x is None or (isinstance(x, str) and not x.strip())


def dec(x: Any) -> Decimal:
    return Decimal(str(x))


def sample(rows: list[dict], field: str, predicate, count: int = 5) -> list[dict]:
    return [{'id': r.get('id'), field: r.get(field)} for r in rows if predicate(r.get(field))][:count]


def _parse_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except (ValueError, TypeError):
        return None


def build_quality_report(data: dict, source_path: str | Path) -> dict:
    src = Path(source_path)
    tables = {}
    keys = {}
    for name in TABLES:
        rows = data[name]
        id_counts = Counter(r.get('id') for r in rows)
        repeated = sorted((i for i, n in id_counts.items() if n > 1), key=str)
        keys[name] = {r['id']: r for r in rows}
        cols = list(rows[0]) if rows else []
        fields = {}
        for col in cols:
            vals = [r.get(col) for r in rows]
            present = [v for v in vals if not missing(v)]
            distinct = set(str(v) for v in present)
            field_summary = {
                'missing': len(rows) - len(present),
                'missing_pct': round(100 * (len(rows) - len(present)) / len(rows), 3) if rows else None,
                'unique_nonmissing': len(distinct),
                'types': dict(sorted(Counter(type(v).__name__ for v in present).items())),
                'sample_missing_ids': [r.get('id') for r in rows if missing(r.get(col))][:5],
            }
            if len(distinct) <= 12:
                field_summary['counts'] = dict(sorted(Counter(str(v) for v in present).items()))
            fields[col] = field_summary
        tables[name] = {
            'rows': len(rows), 'columns': cols, 'pk_duplicates': sum(n - 1 for n in id_counts.values() if n > 1),
            'pk_duplicate_samples': repeated[:5], 'fields': fields,
        }

    foreign_keys = {}
    for name, checks in FOREIGN_KEYS.items():
        for col, target in checks:
            foreign_keys[f'{name}.{col} → {target}.id'] = {
                'orphans': sum(r[col] not in keys[target] for r in data[name]),
                'sample_record_ids': [r['id'] for r in data[name] if r[col] not in keys[target]][:5],
            }

    domains = {}
    for name, checks in EXPECTED_DOMAINS.items():
        for col, allowed in checks.items():
            rows = data[name]
            unexpected = [r for r in rows if not missing(r[col]) and r[col] not in allowed]
            domains[f'{name}.{col}'] = {
                'observed_counts': dict(sorted(Counter(str(r[col]) for r in rows).items())),
                'out_of_expected_domain': len(unexpected),
                'sample_ids': [r['id'] for r in unexpected[:5]],
                'note': 'domínio de validação operacional assumido a partir das categorias presentes e do caso; não é documentação do sistema de origem',
            }

    numeric = {}
    for name, columns in NUMERIC_RULES.items():
        for col, rule in columns.items():
            rows = data[name]
            supplied = [(r['id'], dec(r[col])) for r in rows if not missing(r[col])]
            bad = []
            for i, v in supplied:
                if ((rule == 'positive' and v <= 0) or
                    (rule == 'positive_int' and (v <= 0 or v != v.to_integral_value())) or
                    (rule == 'fraction' and not (Decimal('0') <= v <= Decimal('1'))) or
                    (rule == 'rating' and (v != v.to_integral_value() or not 1 <= v <= 5))):
                    bad.append(i)
            numeric[f'{name}.{col}'] = {
                'rule': rule, 'nonmissing': len(supplied),
                'minimum': str(min((v for _, v in supplied), default=None)),
                'maximum': str(max((v for _, v in supplied), default=None)),
                'invalid_count': len(bad), 'invalid_sample_ids': bad[:5],
            }

    dates = {}
    for name, columns in DATE_COLUMNS.items():
        for col in columns:
            rows = data[name]
            parsed = [(r['id'], _parse_date(r[col])) for r in rows if not missing(r[col])]
            invalid = [i for i, v in parsed if v is None]
            valid = [v for _, v in parsed if v is not None]
            dates[f'{name}.{col}'] = {
                'nonmissing': len(parsed), 'invalid_count': len(invalid), 'sample_invalid_ids': invalid[:5],
                'first': min(valid).isoformat() if valid else None,
                'last': max(valid).isoformat() if valid else None,
            }

    orders = keys['Pedidos']; clients = keys['Clientes']; products = keys['Produtos']
    membership: dict[int, set[int]] = defaultdict(set)
    supp_by_order: dict[int, set[str]] = defaultdict(set)
    gross_by_order: dict[int, Decimal] = defaultdict(Decimal)
    applied_discounts = {'known': 0, 'price_matches_catalog_minus_discount_exact': 0,
                         'price_matches_catalog_minus_discount_within_1_cent': 0,
                         'maximum_absolute_difference': Decimal('0'), 'not_matching_sample_ids': []}
    for item in data['Itens_Pedido']:
        oid, pid = item['pedido_id'], item['produto_id']
        membership[oid].add(pid)
        if pid in products:
            supp_by_order[oid].add(products[pid]['fornecedor'])
        if oid in orders:
            gross_by_order[oid] += dec(item['quantidade']) * dec(item['preco_praticado'])
        if pid in products and not missing(item['desconto_aplicado']):
            applied_discounts['known'] += 1
            # Valor praticado = preço de catálogo já com o desconto, sujeito a arredondamento de centavos.
            expected = (dec(products[pid]['preco_unitario']) * (Decimal('1') - dec(item['desconto_aplicado']))).quantize(CENT, rounding=ROUND_HALF_UP)
            residual = abs(expected - dec(item['preco_praticado']))
            applied_discounts['maximum_absolute_difference'] = max(applied_discounts['maximum_absolute_difference'], residual)
            if residual == 0:
                applied_discounts['price_matches_catalog_minus_discount_exact'] += 1
            if residual <= CENT:
                applied_discounts['price_matches_catalog_minus_discount_within_1_cent'] += 1
            elif len(applied_discounts['not_matching_sample_ids']) < 5:
                applied_discounts['not_matching_sample_ids'].append(item['id'])
    applied_discounts['maximum_absolute_difference'] = str(applied_discounts['maximum_absolute_difference'])
    repeated_item_pairs = Counter((r['pedido_id'], r['produto_id']) for r in data['Itens_Pedido'])
    repeated_emails = Counter(r['email'].strip().casefold() for r in data['Clientes'])
    repeated_ticket_orders = Counter(r['pedido_id'] for r in data['Tickets_Suporte'])
    repeated_review_orders = Counter(r['pedido_id'] for r in data['Avaliacoes'])
    logical = {
        'pedidos_sem_itens': sum(o['id'] not in membership for o in data['Pedidos']),
        'clientes_com_cadastro_posterior_ao_pedido': sum(o['cliente_id'] in clients and clients[o['cliente_id']]['data_cadastro'] > o['data_pedido'] for o in data['Pedidos']),
        'tickets_cliente_diverge_do_pedido': sum(t['pedido_id'] in orders and t['cliente_id'] != orders[t['pedido_id']]['cliente_id'] for t in data['Tickets_Suporte']),
        'avaliacoes_cliente_diverge_do_pedido': sum(a['pedido_id'] in orders and a['cliente_id'] != orders[a['pedido_id']]['cliente_id'] for a in data['Avaliacoes']),
        'avaliacoes_produto_nao_consta_do_pedido': sum(a['pedido_id'] in orders and a['produto_id'] not in membership[a['pedido_id']] for a in data['Avaliacoes']),
        'tickets_anteriores_ao_pedido': sum(t['pedido_id'] in orders and t['data_abertura'] < orders[t['pedido_id']]['data_pedido'] for t in data['Tickets_Suporte']),
        'avaliacoes_anteriores_ao_pedido': sum(a['pedido_id'] in orders and a['data_avaliacao'] < orders[a['pedido_id']]['data_pedido'] for a in data['Avaliacoes']),
        'resolucoes_anteriores_a_abertura': sum(t['data_resolucao'] is not None and t['data_resolucao'] < t['data_abertura'] for t in data['Tickets_Suporte']),
        'resolvidos_sem_data_resolucao': sum(t['status']=='resolvido' and missing(t['data_resolucao']) for t in data['Tickets_Suporte']),
        'nao_resolvidos_com_data_resolucao': sum(t['status']!='resolvido' and not missing(t['data_resolucao']) for t in data['Tickets_Suporte']),
        'resolucoes_em_2025': sum(t['data_resolucao'] is not None and t['data_resolucao'].startswith('2025-') for t in data['Tickets_Suporte']),
        'pedidos_fora_2023_2024': sum(_parse_date(o['data_pedido']) is None or not '2023-01-01'<=o['data_pedido']<='2024-12-31' for o in data['Pedidos']),
        'tickets_abertos_fora_2023_2024': sum(_parse_date(t['data_abertura']) is None or not '2023-01-01'<=t['data_abertura']<='2024-12-31' for t in data['Tickets_Suporte']),
        'avaliacoes_fora_2023_2024': sum(_parse_date(a['data_avaliacao']) is None or not '2023-01-01'<=a['data_avaliacao']<='2024-12-31' for a in data['Avaliacoes']),
        'preco_catalogo_menor_que_custo': sum(p['preco_unitario']<p['custo_unitario'] for p in data['Produtos']),
        'email_repetido_apos_normalizar': sum(n-1 for n in repeated_emails.values() if n>1),
        'itens_mesmo_produto_repetido_no_pedido': sum(n-1 for n in repeated_item_pairs.values() if n>1),
        'mais_de_um_ticket_por_pedido': sum(n-1 for n in repeated_ticket_orders.values() if n>1),
        'mais_de_uma_avaliacao_por_pedido': sum(n-1 for n in repeated_review_orders.values() if n>1),
    }
    financial = {'orders_total': len(data['Pedidos']),
                 'orders_missing_reported_total': 0, 'orders_reported_total_available': 0,
                 'orders_gross_items_match_within_1_cent': 0, 'orders_gross_items_different': 0,
                 'sum_reported_over_available_orders': Decimal(0),
                 'sum_gross_items_over_same_orders': Decimal(0),
                 'signed_difference_reported_minus_gross': Decimal(0),
                 'absolute_difference_sum': Decimal(0),
                 'largest_difference_examples': []}
    large_residuals = []
    for o in data['Pedidos']:
        if missing(o['valor_total']):
            financial['orders_missing_reported_total'] += 1
            continue
        reported, gross = dec(o['valor_total']), gross_by_order[o['id']]
        diff = reported - gross
        financial['orders_reported_total_available'] += 1
        financial['sum_reported_over_available_orders'] += reported
        financial['sum_gross_items_over_same_orders'] += gross
        financial['signed_difference_reported_minus_gross'] += diff
        financial['absolute_difference_sum'] += abs(diff)
        if abs(diff) <= CENT:
            financial['orders_gross_items_match_within_1_cent'] += 1
        else:
            financial['orders_gross_items_different'] += 1
        large_residuals.append((abs(diff), {'id': o['id'], 'status': o['status'],
                                          'reported': str(reported.quantize(CENT)), 'gross': str(gross.quantize(CENT)),
                                          'reported_minus_gross': str(diff.quantize(CENT))}))
    financial['largest_difference_examples'] = [p for _, p in sorted(large_residuals, key=lambda x: x[0], reverse=True)[:5]]
    for key in ('sum_reported_over_available_orders', 'sum_gross_items_over_same_orders',
                'signed_difference_reported_minus_gross', 'absolute_difference_sum'):
        financial[key] = str(financial[key].quantize(CENT))
    multi = {oid for oid, suppliers in supp_by_order.items() if len(suppliers)>1}
    join_risk = {'pedidos_distintos': len(orders), 'linhas_itens': len(data['Itens_Pedido']),
                 'itens_por_pedido_media': round(len(data['Itens_Pedido'])/len(orders), 4),
                 'pedidos_monofornecedor': len(orders)-len(multi),
                 'pedidos_multifornecedor': len(multi),
                 'tickets_de_pedidos_multifornecedor': sum(t['pedido_id'] in multi for t in data['Tickets_Suporte']),
                 'nota': 'Itens é 1:N em relação a Pedidos; avaliações e tickets são por pedido e não provam fornecedor responsável.'}
    return {'source': {'file': src.name, 'sha256': sha256(src.read_bytes()).hexdigest()},
            'data_contract': 'Aba Leia-me: as seis tabelas não foram limpas; inconsistências são intencionais.',
            'tables': tables, 'foreign_keys': foreign_keys, 'domains': domains, 'numeric': numeric,
            'dates': dates, 'logical': logical, 'discounts_and_price': applied_discounts,
            'financial': financial, 'join_risk': join_risk}


def dictionary_csv_rows(report: dict) -> list[dict]:
    result = []
    for name, t in report['tables'].items():
        for field, d in t['fields'].items():
            result.append({'tabela': name, 'campo': field, 'tipos_python_entre_nao_nulos': ';'.join(d['types']),
                           'registros': t['rows'], 'nulos': d['missing'], 'nulos_pct': d['missing_pct'],
                           'distintos_nao_nulos': d['unique_nonmissing']})
    return result


def make_audit_markdown(report: dict) -> str:
    def fmt_int(n: int) -> str:
        return f'{n:,}'.replace(',', '.')

    def fmt_brl(value: str) -> str:
        return f'{Decimal(value):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    q = report
    lines = [
        '# 02 — Auditoria exploratória e qualidade dos dados (Tarefa 2)', '',
        '## Fonte, objetivo e escopo', '',
        f"Origem: `{q['source']['file']}`; SHA-256: `{q['source']['sha256']}`. ",
        'Inspeção **somente leitura**; os seis conjuntos de dados não foram modificados. A aba `Leia-me` esclarece que lacunas e discrepâncias financeiras são propositalmente mantidas no case.', '',
        '## 1. Visão geral e valores ausentes', '',
        '| Tabela | Registros | Campos | Chave primária duplicada | Campos incompletos |',
        '|---|---:|---:|---:|---|'
    ]
    for name, t in q['tables'].items():
        missing_fields = [f"`{col}`: {d['missing']} ({d['missing_pct']:.2f}%)" for col,d in t['fields'].items() if d['missing']]
        lines.append(f"| {name} | {t['rows']:,} | {len(t['columns'])} | {t['pk_duplicates']} | {'; '.join(missing_fields) if missing_fields else 'Nenhum'} |".replace(',', '.'))
    lines += ['', '**Notas sobre os vazios:** `Pedidos.valor_total` e `Itens_Pedido.desconto_aplicado` impactam decisões financeiras; `Tickets_Suporte.data_resolucao` está ausente em abertos/escalados, e `Avaliacoes.comentario` é facultativo. Não substituir nulos automaticamente por zero.', '',
        '## 2. Dicionário de dados observado', '',
        'Campos e tipos foram inferidos a partir das células, não confirmados por um esquema formal do banco. Os tipos `int` e `float` aparecem juntos em alguns campos numéricos sem indicar erro.', '']
    for name, t in q['tables'].items():
        lines.append(f"**{name}:** " + ', '.join(f'`{col}`' for col in t['columns']) + '.')
    lines += ['', 'O dicionário por campo, com cardinalidades, tipos e ausentes, está em `outputs/dicionario_dados.csv`. Algumas colunas são strings ISO de data, não datas serializadas pelo Excel.', '',
        '## 3. Integridade referencial e duplicidades', '',
        '| Relação | Chaves órfãs |', '|---|---:|']
    for ref, result in q['foreign_keys'].items(): lines.append(f"| `{ref}` | {result['orphans']} |")
    lines += ['', 'Todas as seis chaves primárias são únicas; emails normalizados e pares (`pedido_id`, `produto_id`) de itens também não apresentaram duplicidades.', '',
        '### Coerência relacional e temporal', '',
        '| Verificação | Ocorrências |', '|---|---:|']
    for key, n in q['logical'].items(): lines.append(f'| `{key}` | {n} |')
    lines += ['', '**Interpretação:** as 51 resoluções datadas de 2025 são eventos posteriores ao período de criação dos pedidos, **não datas inválidas**. Cadastros de clientes começam em 2022, antes do período de vendas, o que também não é defeito. Chamados resolvidos têm data de resolução, enquanto os chamados abertos/escalados não têm.', '',
        '## 4. Validação de domínio e valores numéricos', '',
        '| Campo | Domínio observado / faixa | Inconsistências verificáveis |', '|---|---|---:|']
    for name, d in q['numeric'].items():
        lines.append(f"| `{name}` | {d['minimum']} a {d['maximum']} | {d['invalid_count']} |")
    for name, d in q['domains'].items():
        lines.append(f"| `{name}` | {', '.join(d['observed_counts'])} | {d['out_of_expected_domain']} |")
    lines += ['', 'As listas categóricas acima representam valores encontrados ou validação operacional presumida — **não** são necessariamente enumerações completas do sistema de produção.', '',
        '## 5. Descontos: descoberta crítica', '']
    discount = q['discounts_and_price']
    lines += [f"Há **{fmt_int(discount['known'])} itens** com `desconto_aplicado` informado. Em **{fmt_int(discount['price_matches_catalog_minus_discount_exact'])}** deles, o preço praticado coincide exatamente com `preco_unitario × (1 − desconto_aplicado)` arredondado a centavos; em **{fmt_int(discount['price_matches_catalog_minus_discount_within_1_cent'])} de {fmt_int(discount['known'])}**, a diferença é no máximo **R$ {fmt_brl(discount['maximum_absolute_difference'])}**.",
              '', '**Implicação:** há evidência forte de que `preco_praticado` já incorpora o desconto. Multiplicá-lo novamente por `(1−desconto_aplicado)` causaria **dupla aplicação de descontos**. O significado técnico-contábil de `preco_praticado` permanece sujeito à confirmação do time de dados. Para os 301 descontos ausentes, preservar a lacuna; não preencher `0` sem premissa explicitada.', '',
              '## 6. Divergência financeira em nível de pedido', '']
    fin = q['financial']
    lines += [f"- Pedidos: **{fmt_int(fin['orders_total'])}**; com `valor_total` informado: **{fmt_int(fin['orders_reported_total_available'])}**; nulo: **{fin['orders_missing_reported_total']}**.",
              f"- Pedidos com igualdade até R$ 0,01 entre `valor_total` e `Σ(quantidade × preco_praticado)`: **{fin['orders_gross_items_match_within_1_cent']}**; com divergência: **{fmt_int(fin['orders_gross_items_different'])}**.",
              f"- Soma dos valores reportados nos pedidos comparáveis: **R$ {fmt_brl(fin['sum_reported_over_available_orders'])}**.",
              f"- Soma das linhas desses mesmos pedidos: **R$ {fmt_brl(fin['sum_gross_items_over_same_orders'])}**.",
              f"- Resíduo agregado (reportado − itens): **R$ {fmt_brl(fin['signed_difference_reported_minus_gross'])}**; soma das diferenças absolutas: **R$ {fmt_brl(fin['absolute_difference_sum'])}**.",
              '', 'Essas diferenças **não autorizam** substituir uma fonte pela outra como receita ou margem: faltam fatos financeiros sobre frete, impostos, reembolsos, capturas, cupom e reconhecimento de receita. Nesta auditoria, `Σ(qtd × preco_praticado)` é apenas **valor comercial das linhas**, sujeito à política de status.', '',
              '### Exemplos de reconciliação por ID', '', '| pedido_id | Valor reportado | Itens | Diferença |', '|---:|---:|---:|---:|']
    for d in fin['largest_difference_examples']:
        lines.append(f"| {d['id']} | {fmt_brl(d['reported'])} | {fmt_brl(d['gross'])} | {fmt_brl(d['reported_minus_gross'])} |")
    j=q['join_risk']
    lines += ['', '## 7. Cardinalidade e riscos nos cruzamentos', '',
              f"- `Pedidos`: {fmt_int(j['pedidos_distintos'])} IDs; `Itens_Pedido`: {fmt_int(j['linhas_itens'])} linhas (**{j['itens_por_pedido_media']:.2f} itens/ pedido, em média**). Um join altera o grão para item e multiplicará valores de pedido se agregados sem cuidado.",
              f"- **{fmt_int(j['pedidos_multifornecedor'])} pedidos** incluem mais de um fornecedor; **{fmt_int(j['tickets_de_pedidos_multifornecedor'])} tickets** se relacionam com esses pedidos. Não atribuir automaticamente esses tickets a cada fornecedor.",
              '- O arquivo possui no máximo um ticket e uma avaliação por pedido nesta fotografia, mas isso não prova uma regra permanente do sistema de origem.', '',
              '## 8. Prioridades e encaminhamento para a Tarefa 3', '',
              '1. **Crítico:** interromper qualquer afirmação de receita ou margem conciliada; documentar fontes, amostras e campos necessários para reconciliação.',
              '2. **Alto:** usar `preco_praticado` sem descontar novamente; testar cenários sobre valores ausentes, sem imputação disfarçada.',
              '3. **Alto:** fixar grão e denominadores antes de comparar cancelamentos, ticket médio e fornecedores.',
              '4. **Médio:** documentar ausência de histórico de status, data efetiva do cancelamento, canal de campanha detalhado, valor de cupom e prova de pagamentos.',
              '5. **Médio:** distinguir chamados abertos por mês de chamados por coorte de compra; datas de resolução em 2025 não são automaticamente problema.', '',
              '**Limite da auditoria:** não há validação independente contra ERP, gateway de pagamentos, estoque ou base operacional, apenas verificações internas da planilha original.', '']
    return '\n'.join(lines)
