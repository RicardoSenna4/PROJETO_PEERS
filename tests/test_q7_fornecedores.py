"""Q7: cenários adversariais de join, tickets repetidos e base real."""
from pathlib import Path
import pytest
from src.q7 import build_q7
from src.workbook import load_xlsx

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def db():
    d=load_xlsx(ROOT/'input/Base_Dados_OrbitShop_v3.xlsx');d.pop('Leia-me',None)
    return d


def test_q7_real_conserves_tickets_and_exposure(db):
    q=build_q7(db)
    assert len(q['fornecedores'])==9
    assert q['pedidos_multifornecedor']==10040
    assert q['pedidos_monofornecedor']==4960
    assert q['tickets_multifornecedor_sem_atribuicao']==2676
    assert q['tickets_monofornecedor']==1324
    assert q['tickets_total']==4000
    assert sum(r['pedidos_monofornecedor'] for r in q['fornecedores'])==4960
    assert sum(r['pedidos_mono_com_chamado'] for r in q['fornecedores'])==1324
    assert sum(r['n_avaliacoes'] for r in q['fornecedores'])==8000


def test_q7_delta_has_lowest_rating_but_not_highest_incidence(db):
    rows=build_q7(db)['fornecedores']
    delta=rows[0]
    assert delta['fornecedor']=='DeltaFornece ME'
    assert delta['nota_media']==pytest.approx(2.3046)
    assert delta['avaliacoes_negativas_pct']==pytest.approx(59.8985)
    assert delta['incidencia_chamado_mono_pct']<max(r['incidencia_chamado_mono_pct'] for r in rows)


def test_q7_peak_timing_and_ticket_categories(db):
    q=build_q7(db)
    assert [q['tickets_out_2023'],q['tickets_nov_2023'],q['tickets_dez_2023']]==[156,375,391]
    assert q['tickets_nov_dez_2023']==766
    assert q['tickets_nov_dez_2023_coorte_nov']==603
    assert sum(x['tickets'] for x in q['pico_causa_por_mes'])==4000


def test_q7_multiple_tickets_do_not_multiply_orders_or_supplier_attribution():
    d={
      'Produtos':[{'id':11,'fornecedor':'A'},{'id':12,'fornecedor':'B'}],
      'Pedidos':[{'id':1,'status':'entregue','data_pedido':'2023-10-01'},{'id':2,'status':'entregue','data_pedido':'2023-10-01'}],
      'Itens_Pedido':[{'id':1,'pedido_id':1,'produto_id':11,'quantidade':2},
                      {'id':2,'pedido_id':2,'produto_id':11,'quantidade':1},
                      {'id':3,'pedido_id':2,'produto_id':12,'quantidade':1}],
      'Avaliacoes':[{'id':1,'produto_id':11,'nota':1},{'id':2,'produto_id':12,'nota':5}],
      'Tickets_Suporte':[{'id':1,'pedido_id':1,'data_abertura':'2023-11-01','categoria_problema':'defeito'},
                         {'id':2,'pedido_id':1,'data_abertura':'2023-11-03','categoria_problema':'troca'},
                         {'id':3,'pedido_id':2,'data_abertura':'2023-12-01','categoria_problema':'troca'}],
    }
    q=build_q7(d)
    a=next(x for x in q['fornecedores'] if x['fornecedor']=='A')
    b=next(x for x in q['fornecedores'] if x['fornecedor']=='B')
    assert a['pedidos_monofornecedor']==1
    assert a['pedidos_mono_com_chamado']==1
    assert a['tickets_em_pedidos_mono']==2
    assert a['incidencia_chamado_mono_pct']==100
    assert b['pedidos_mono_com_chamado']==0
    assert q['tickets_multifornecedor_sem_atribuicao']==1
    assert q['tickets_monofornecedor']==2


def test_q7_customer_journey_not_confused_with_supplier(db):
    q=build_q7(db)
    assert q['proporcao_tickets_sem_atribuicao_pct']==66.9
    assert all(0 <= row['incidencia_chamado_mono_pct'] <= 100 for row in q['fornecedores'])
