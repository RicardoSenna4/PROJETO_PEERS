"""Tarefa 4: verificações do contrato de entrada com casos sintéticos isolados."""
from copy import deepcopy
import pytest

from src.validation import InputValidationError, validate_input


@pytest.fixture
def valid_data():
    return {
        'Clientes': [{'id': 10, 'canal_aquisicao': 'orgânico', 'segmento': 'B2C'}],
        'Produtos': [{'id': 20, 'categoria': 'Livros', 'preco_unitario': 30.0, 'fornecedor': 'Fornecedor X'}],
        'Pedidos': [{'id': 30, 'cliente_id': 10, 'data_pedido': '2023-01-15',
                     'status': 'entregue', 'valor_total': None}],
        'Itens_Pedido': [{'id': 40, 'pedido_id': 30, 'produto_id': 20,
                         'quantidade': 2, 'preco_praticado': 27.0, 'desconto_aplicado': None}],
        'Avaliacoes': [{'id': 50, 'pedido_id': 30, 'produto_id': 20,
                        'cliente_id': 10, 'nota': 5}],
        'Tickets_Suporte': [{'id': 60, 'pedido_id': 30, 'cliente_id': 10,
                             'data_abertura': '2023-01-16', 'status': 'resolvido'}],
    }


def test_preflight_accepts_null_financial_fields_without_imputing(valid_data):
    original = deepcopy(valid_data)
    result = validate_input(valid_data)
    assert result['pedidos'] == 1
    assert result['itens'] == 1
    assert valid_data == original
    assert valid_data['Pedidos'][0]['valor_total'] is None
    assert valid_data['Itens_Pedido'][0]['desconto_aplicado'] is None


@pytest.mark.parametrize('table', ['Clientes', 'Produtos', 'Pedidos', 'Itens_Pedido', 'Avaliacoes', 'Tickets_Suporte'])
def test_preflight_rejects_duplicate_primary_keys(valid_data, table):
    valid_data[table].append(deepcopy(valid_data[table][0]))
    with pytest.raises(InputValidationError, match='duplicad'):
        validate_input(valid_data)


@pytest.mark.parametrize('table,field,value', [
    ('Pedidos', 'cliente_id', 999),
    ('Itens_Pedido', 'pedido_id', 999),
    ('Itens_Pedido', 'produto_id', 999),
    ('Avaliacoes', 'cliente_id', 999),
    ('Tickets_Suporte', 'pedido_id', 999),
])
def test_preflight_rejects_orphan_references(valid_data, table, field, value):
    valid_data[table][0][field] = value
    with pytest.raises(InputValidationError, match='[óo]rf'):
        validate_input(valid_data)


@pytest.mark.parametrize('name,field,value', [
    ('Pedidos', 'status', 'status_novo'),
    ('Pedidos', 'data_pedido', '2025-01-10'),
    ('Pedidos', 'data_pedido', '2024-99-10'),
    ('Itens_Pedido', 'quantidade', 0),
    ('Itens_Pedido', 'preco_praticado', -5),
    ('Itens_Pedido', 'desconto_aplicado', 1.4),
])
def test_preflight_rejects_invalid_domain(valid_data, name, field, value):
    valid_data[name][0][field] = value
    with pytest.raises(InputValidationError):
        validate_input(valid_data)


def test_preflight_rejects_missing_critical_field(valid_data):
    del valid_data['Pedidos'][0]['status']
    with pytest.raises(InputValidationError, match='status'):
        validate_input(valid_data)


def test_preflight_rejects_cross_customer_ticket(valid_data):
    valid_data['Clientes'].append({'id': 11, 'canal_aquisicao': 'orgânico', 'segmento': 'B2B'})
    valid_data['Tickets_Suporte'][0]['cliente_id'] = 11
    with pytest.raises(InputValidationError, match='cliente'):
        validate_input(valid_data)


def test_preflight_rejects_review_of_product_not_in_order(valid_data):
    valid_data['Produtos'].append({'id': 21, 'categoria': 'Livros', 'preco_unitario': 10.0, 'fornecedor': 'Y'})
    valid_data['Avaliacoes'][0]['produto_id'] = 21
    with pytest.raises(InputValidationError, match='produto'):
        validate_input(valid_data)
