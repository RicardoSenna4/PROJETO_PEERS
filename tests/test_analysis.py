"""Testes determinísticos: regras sintéticas + confirmação independente com SQLite."""
from collections import Counter
from decimal import Decimal
from pathlib import Path
import sqlite3
import pytest

from src.workbook import load_xlsx
from src.analysis import (audit, indexed, percent, status_metrics, categories_metrics,
                          acquisition_metrics, monthly_metrics, reconcile, supplier_metrics)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='session')
def db():
    result = load_xlsx(ROOT / 'input/Base_Dados_OrbitShop_v3.xlsx')
    result.pop('Leia-me',None)
    return result


def test_percent_denominator():
    assert percent(1,4) == 25
    assert percent(0,4) == 0
    assert percent(1,0) is None


def test_duplicate_key_rejected():
    with pytest.raises(ValueError): indexed([{'id':1},{'id':1}])


def test_status_year_does_not_use_cancellation_date():
    records=[{'id':1,'status':'cancelado','data_pedido':'2023-01-01'},
             {'id':2,'status':'entregue','data_pedido':'2023-10-01'},
             {'id':3,'status':'cancelado','data_pedido':'2024-06-01'}]
    m=status_metrics(records)
    assert m['anos']['2023']['taxa_cancelamento_pct']==50
    assert m['anos']['2024']['taxa_cancelamento_pct']==100
    assert m['variacao_cancelados_pct']==0


def test_category_uses_items_practiced_price_and_delivered_only():
    data={'Pedidos':[{'id':1,'status':'entregue'},{'id':2,'status':'cancelado'}],
        'Produtos':[{'id':7,'categoria':'Cat','preco_unitario':999999}],
        'Itens_Pedido':[{'pedido_id':1,'produto_id':7,'quantidade':2,'preco_praticado':10.10},
                        {'pedido_id':2,'produto_id':7,'quantidade':100,'preco_praticado':50}]}
    rows=categories_metrics(data)
    assert rows[0]['valor_bruto_itens']=='20.20'
    assert rows[0]['unidades']==2
    assert categories_metrics(data, {'entregue','cancelado'})[0]['unidades']==102


def test_acquisition_not_sales_channel_and_no_join_multiplication():
    data={'Clientes':[{'id':10,'canal_aquisicao':'A','segmento':'B2C'}],
          'Pedidos':[{'id':1,'cliente_id':10,'data_pedido':'2023-01-02','status':'entregue','valor_total':10,'canal_venda':'marketplace'},
                     {'id':2,'cliente_id':10,'data_pedido':'2023-01-02','status':'cancelado','valor_total':None,'canal_venda':'site'}]}
    result=acquisition_metrics(data)['canais'][0]
    assert result['canal_aquisicao']=='A'
    assert result['clientes_com_pedido']==1
    assert result['pedidos']==2
    assert result['taxa_cancelamento_pct']==50
    assert result['ticket_medio_entregue_reportado']=='10.00'


def test_reconciliation_never_imputes_missing_as_true():
    data={'Pedidos':[{'id':1,'status':'entregue','valor_total':20},
                     {'id':2,'status':'entregue','valor_total':None}],
          'Itens_Pedido':[{'pedido_id':1,'quantidade':2,'preco_praticado':10,'desconto_aplicado':0.10},
                          {'pedido_id':2,'quantidade':1,'preco_praticado':20,'desconto_aplicado':None}]}
    summary, rows = reconcile(data)
    assert summary['contagens']['gross_equal_within_cent']==1
    assert summary['contagens']['net_equal_within_cent']==0
    assert summary['contagens']['sem_valor_reportado']==1
    assert summary['contagens']['desconto_desconhecido_pedidos']==1
    assert rows[1]['valor_total_reportado']==''
    assert rows[1]['valor_liquido_desconto_conhecido']==''
    assert rows[0]['valor_liquido_desconto_conhecido']=='18.00'


def test_months_are_consecutive_even_if_empty():
    d={'Pedidos':[{'id':1,'data_pedido':'2023-11-01'}], 'Tickets_Suporte':[]}
    result=monthly_metrics(d)
    assert len(result['meses'])==24
    assert next(r for r in result['meses'] if r['mes']=='2024-04')['pedidos']==0


def test_real_workbook_referential_integrity(db):
    m=audit(db)
    assert m['tabelas']['Pedidos']['registros']==15000
    assert m['tabelas']['Itens_Pedido']['registros']==36740
    assert all(v==0 for v in m['chaves_estrangeiras_orfas'].values())
    assert all(v==0 for v in m['anomalias_relacionais'].values())


def test_status_count_independently_by_sqlite(db):
    conn=sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE orders (id INTEGER PRIMARY KEY, status TEXT, year TEXT)')
    conn.executemany('INSERT INTO orders VALUES (?,?,?)',[(r['id'],r['status'],r['data_pedido'][:4]) for r in db['Pedidos']])
    counts=dict(conn.execute('SELECT status,COUNT(*) FROM orders GROUP BY status'))
    actual={r['status']:r['pedidos'] for r in status_metrics(db['Pedidos'])['tabela_status']}
    assert counts==actual
    assert conn.execute("SELECT COUNT(*) FROM orders WHERE status='cancelado'").fetchone()[0]==2537


def test_cancelled_paid_search_independently_by_sqlite(db):
    conn=sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE orders (id INTEGER, customer INTEGER, status TEXT)')
    conn.execute('CREATE TABLE customers (id INTEGER, channel TEXT)')
    conn.executemany('INSERT INTO orders VALUES (?,?,?)',[(r['id'],r['cliente_id'],r['status']) for r in db['Pedidos']])
    conn.executemany('INSERT INTO customers VALUES (?,?)',[(r['id'],r['canal_aquisicao']) for r in db['Clientes']])
    group=dict((canal,(total,cancelled)) for canal,total,cancelled in conn.execute('''
      SELECT channel,COUNT(*),SUM(status='cancelado') FROM orders JOIN customers ON customer=customers.id GROUP BY channel'''))
    actual={r['canal_aquisicao']:(r['pedidos'],r['cancelados']) for r in acquisition_metrics(db)['canais']}
    assert actual==group
    assert group['paid_search']==(3965,1219)


def test_no_line_duplication_and_category_total(db):
    orders=indexed(db['Pedidos'])
    c=categories_metrics(db)
    relevant=[i for i in db['Itens_Pedido'] if orders[i['pedido_id']]['status']=='entregue']
    assert sum(r['linhas'] for r in c)==len(relevant)
    assert sum(r['unidades'] for r in c)==sum(i['quantidade'] for i in relevant)
    assert sum(Decimal(r['valor_bruto_itens']) for r in c)==Decimal('118084610.50')


def test_reconciliation_real_14921_zero_match(db):
    summary,rows=reconcile(db)
    counts=summary['contagens']
    assert len(rows)==15000
    assert counts['com_valor_reportado']==14921
    assert counts['sem_valor_reportado']==79
    assert counts['desconto_desconhecido_pedidos']==301
    assert counts['gross_equal_within_cent']==0
    assert counts['net_equal_within_cent']==0
    assert Decimal(summary['totais_brl']['gross_all'])==Decimal('176730490.88')


def test_supplier_review_rates_no_ticket_doublecount(db):
    m=supplier_metrics(db)
    assert sum(x['n_avaliacoes'] for x in m['fornecedores'])==8000
    assert sum(x['pedidos_com_apenas_este_fornecedor'] for x in m['fornecedores'])==4960
    assert sum(x['tickets_nesses_pedidos'] for x in m['fornecedores'])==1324
    assert m['chamados_multifornecedor_sem_atribuicao']==2676
    delta=m['fornecedores'][0]
    assert delta['fornecedor']=='DeltaFornece ME'
    assert delta['n_avaliacoes']==985


def test_nov_2023_support_from_nov_cohort(db):
    m=monthly_metrics(db)
    assert next(r for r in m['meses'] if r['mes']=='2023-11')['pedidos']==2317
    assert m['chamados_nov_dez_2023']==766
    assert m['chamados_nov_dez_ligados_pedidos_nov']==603
