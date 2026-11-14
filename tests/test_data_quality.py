"""Regression tests for tasks 2/3: schema, consistency and the discount contract."""
from __future__ import annotations
from pathlib import Path
from decimal import Decimal
import pytest

from src.workbook import load_xlsx
from src.data_quality import build_quality_report

ROOT = Path(__file__).parents[1]
ORIGINAL = ROOT / 'input' / 'Base_Dados_OrbitShop_v3.xlsx'


@pytest.fixture(scope='module')
def data():
    workbook = load_xlsx(ORIGINAL)
    workbook.pop('Leia-me', None)
    return workbook


@pytest.fixture(scope='module')
def quality(data):
    return build_quality_report(data, ORIGINAL)


def test_record_counts_and_missing_fields(quality):
    expected = {'Clientes':3000,'Produtos':200,'Pedidos':15000,'Itens_Pedido':36740,
                'Tickets_Suporte':4000,'Avaliacoes':8000}
    assert {name:x['rows'] for name,x in quality['tables'].items()} == expected
    assert quality['tables']['Pedidos']['fields']['valor_total']['missing'] == 79
    assert quality['tables']['Itens_Pedido']['fields']['desconto_aplicado']['missing'] == 301
    assert quality['tables']['Tickets_Suporte']['fields']['data_resolucao']['missing'] == 1653
    assert quality['tables']['Avaliacoes']['fields']['comentario']['missing'] == 1679


def test_fk_and_primary_key_constraints(quality):
    assert all(v['orphans'] == 0 for v in quality['foreign_keys'].values())
    assert all(v['pk_duplicates'] == 0 for v in quality['tables'].values())
    assert quality['logical']['pedidos_sem_itens'] == 0
    assert quality['logical']['avaliacoes_produto_nao_consta_do_pedido'] == 0


def test_dates_are_consistent_without_misclassifying_2025_resolution(quality):
    assert all(v['invalid_count']==0 for v in quality['dates'].values())
    assert quality['logical']['resolucoes_anteriores_a_abertura']==0
    assert quality['logical']['resolvidos_sem_data_resolucao']==0
    assert quality['logical']['nao_resolvidos_com_data_resolucao']==0
    assert quality['logical']['resolucoes_em_2025']==51


def test_price_already_contains_discount(quality):
    d=quality['discounts_and_price']
    assert d['known']==36439
    assert d['price_matches_catalog_minus_discount_within_1_cent']==d['known']
    assert Decimal(d['maximum_absolute_difference'])<=Decimal('0.01')


def test_reported_totals_are_not_reconciled(quality):
    f=quality['financial']
    assert f['orders_missing_reported_total']==79
    assert f['orders_reported_total_available']==14921
    assert f['orders_gross_items_match_within_1_cent']==0
    assert Decimal(f['signed_difference_reported_minus_gross'])==Decimal('-137443424.82')


def test_detects_invalid_price_without_changing_original(data):
    patched = {name:list(rows) for name,rows in data.items()}
    original=patched['Itens_Pedido'][0]
    patched['Itens_Pedido'][0]={**original,'preco_praticado':original['preco_praticado']+100}
    reported=build_quality_report(patched, ORIGINAL)
    assert original['id'] in reported['discounts_and_price']['not_matching_sample_ids']
    assert reported['discounts_and_price']['price_matches_catalog_minus_discount_within_1_cent']==36438
    assert data['Itens_Pedido'][0]['preco_praticado']==original['preco_praticado']


def test_orphan_detection_is_nonfatal(data):
    patched={name:list(rows) for name,rows in data.items()}
    original=patched['Itens_Pedido'][0]
    patched['Itens_Pedido'][0]={**original,'produto_id':9999999}
    result=build_quality_report(patched, ORIGINAL)
    assert result['foreign_keys']['Itens_Pedido.produto_id → Produtos.id']['orphans']==1
