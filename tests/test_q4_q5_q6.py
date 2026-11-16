"""Testes independentes das Q4, Q5 e Q6."""
from pathlib import Path
from decimal import Decimal
import pytest
from src.workbook import load_xlsx
from src.q4 import build_q4, render_q4_report
from src.q5 import build_q5, render_q5_report
from src.q6 import build_q6, render_q6_report

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope="module")
def db():
    return load_xlsx(ROOT/"input"/"Base_Dados_OrbitShop_v3.xlsx")

def sample():
    return dict(Clientes=[
            dict(id=1,canal_aquisicao="paid_search",segmento="B2C"),
            dict(id=2,canal_aquisicao="orgânico",segmento="B2B")],
        Pedidos=[
            dict(id=10,cliente_id=1,canal_venda="site",status="entregue",data_pedido="2023-11-01",valor_total=90),
            dict(id=11,cliente_id=1,canal_venda="marketplace",status="cancelado",data_pedido="2023-11-02",valor_total=None),
            dict(id=12,cliente_id=2,canal_venda="site",status="entregue",data_pedido="2024-02-03",valor_total=20)],
        Itens_Pedido=[
            dict(id=101,pedido_id=10,quantidade=2,preco_praticado=40,desconto_aplicado=.2),
            dict(id=102,pedido_id=11,quantidade=1,preco_praticado=30,desconto_aplicado=0),
            dict(id=103,pedido_id=12,quantidade=1,preco_praticado=20,desconto_aplicado=0)],
        Tickets_Suporte=[
            dict(id=201,pedido_id=10,data_abertura="2023-11-04"),
            dict(id=202,pedido_id=10,data_abertura="2023-12-01"),
            dict(id=203,pedido_id=12,data_abertura="2024-02-04")])

def test_q4_acquisition_vs_sales_and_ticket():
    q=build_q4(sample());r=q["canais"][0]
    assert r["canal_aquisicao"]=="paid_search"
    assert (r["pedidos"],r["cancelados"])==(2,1)
    assert r["ticket_medio_entregue_reportado"]=="90.00"
    assert r["ticket_medio_proxy_itens_entregues"]=="80.00"

def test_q4_join_rejects_missing_customer():
    d=sample();d["Pedidos"][0]["cliente_id"]=999
    with pytest.raises(ValueError,match="cliente inexistente"):build_q4(d)

def test_q5_incidence_deduplicates_tickets():
    q=build_q5(sample());r=next(x for x in q["coortes_suporte"] if x["mes_compra"]=="2023-11")
    assert (r["pedidos"],r["tickets_vinculados"],r["pedidos_com_ticket"])==(2,2,1)
    assert r["incidencia_pedidos_com_ticket_pct"]==50
    assert len(q["meses"])==24

def test_q5_invalid_ticket_rejected():
    d=sample();d["Tickets_Suporte"][0]["pedido_id"]=999
    with pytest.raises(ValueError,match="pedido inexistente"):build_q5(d)

def test_q6_no_double_discount():
    q,rows=build_q6(sample())
    assert len(rows)==3
    assert q["contagens"]["sem_valor_reportado"]==1
    assert q["contagens"]["conciliados_ate_um_centavo"]==1
    assert next(r for r in rows if r["pedido_id"]==10)["valor_comercial_itens"]=="80.00"
    assert all("valor_liquido_desconto_conhecido" not in r for r in rows)

def test_q6_missing_order_item_rejected():
    d=sample();d["Itens_Pedido"].pop()
    with pytest.raises(ValueError,match="sem itens"):build_q6(d)

def test_real_workbook_consistency(db):
    q4=build_q4(db);q5=build_q5(db);q6,rows=build_q6(db)
    assert sum(x["pedidos"] for x in q4["canais"])==15000
    assert sum(x["cancelados"] for x in q4["canais"])==2537
    assert q4["canais"][0]["cancelados"]==1219
    assert sum(x["pedidos"] for x in q5["meses"])==15000
    assert next(x for x in q5["meses"] if x["mes"]=="2023-11")["pedidos"]==2317
    assert len(rows)==15000
    assert q6["contagens"]["com_valor_reportado"]==14921
    assert q6["contagens"]["sem_valor_reportado"]==79
    assert q6["contagens"]["conciliados_ate_um_centavo"]==0
