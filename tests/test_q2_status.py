"""Tarefa 5: critérios executáveis de Q2, inclusive conferência por SQL independente."""
from pathlib import Path
import sqlite3
import pytest

from src.analysis import status_metrics
from src.q2 import q2_years_rows, render_q2_report
from src.workbook import load_xlsx

ROOT = Path(__file__).resolve().parents[1]


def test_status_requires_one_row_per_order():
    rows=[{'id':1, 'status':'cancelado', 'data_pedido':'2023-01-01'},
          {'id':1, 'status':'entregue', 'data_pedido':'2024-01-01'}]
    with pytest.raises(ValueError, match='duplica'):
        status_metrics(rows)


def test_q2_years_rows_with_growth_vs_rate_counterexample():
    rows=[{'id':1, 'status':'cancelado', 'data_pedido':'2023-01-01'},
          {'id':2, 'status':'entregue', 'data_pedido':'2023-01-01'},
          {'id':3, 'status':'cancelado', 'data_pedido':'2024-02-01'},
          {'id':4, 'status':'entregue', 'data_pedido':'2024-02-01'},
          {'id':5, 'status':'entregue', 'data_pedido':'2024-02-01'}]
    m=status_metrics(rows)
    assert m['variacao_cancelados_pct'] == 0
    assert m['variacao_taxa_pontos_percentuais'] == pytest.approx(-16.6667,abs=0.0001)
    result=q2_years_rows(m)
    assert len(result)==2
    assert result[0]['ano']=='2023'
    assert result[1]['ano']=='2024'
    assert sum(r['cancelados'] for r in result) == 2


def test_real_q2_independent_counts_by_year_and_summary():
    db=load_xlsx(ROOT/'input'/'Base_Dados_OrbitShop_v3.xlsx')
    orders=db['Pedidos']
    conn=sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE pedidos (id INTEGER PRIMARY KEY, ano TEXT, status TEXT)')
    conn.executemany('INSERT INTO pedidos VALUES (?,?,?)',
                     ((o['id'],o['data_pedido'][:4],o['status']) for o in orders))
    raw=list(conn.execute('SELECT ano, COUNT(*), SUM(status="cancelado") FROM pedidos GROUP BY ano ORDER BY ano'))
    m=status_metrics(orders)
    assert raw==[('2023',8386,1407),('2024',6614,1130)]
    assert [(r['ano'],r['pedidos'],r['cancelados']) for r in q2_years_rows(m)]==raw
    assert m['n']==15000
    assert sum(r['pedidos'] for r in m['tabela_status'])==m['n']
    assert abs(sum(r['percentual'] for r in m['tabela_status'])-100)<.0002
    assert round(m['variacao_cancelados_pct'],2)==-19.69
    assert round(m['variacao_taxa_pontos_percentuais'],2)==0.31
    assert round(m['variacao_taxa_relativa_pct'],2)==1.83
    report=render_q2_report(m)
    assert '2.537' in report
    assert '19,69%' in report
    assert '0,31' in report
    assert 'não' in report.lower() # ressalva da comparação


def test_cli_outputs_q2_csv_png_and_report_in_isolated_directory(tmp_path):
    """Integração real: executa a CLI, não apenas funções isoladas/mocks."""
    import csv
    import subprocess
    import sys

    output_dir=tmp_path/'outputs'
    report_path=tmp_path/'docs'/'q2.md'
    process=subprocess.run(
        [sys.executable, '-m', 'src.run',
         '--input', str(ROOT/'input'/'Base_Dados_OrbitShop_v3.xlsx'),
         '--output', str(output_dir), '--q2-report', str(report_path)],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert process.returncode==0, process.stderr
    with (output_dir/'q2_status.csv').open(encoding='utf-8-sig',newline='') as handle:
        rows=list(csv.DictReader(handle))
    assert sum(int(r['pedidos']) for r in rows)==15000
    with (output_dir/'q2_por_ano.csv').open(encoding='utf-8-sig',newline='') as handle:
        years=list(csv.DictReader(handle))
    assert sum(int(r['pedidos']) for r in years)==15000
    assert (output_dir/'q2_status.png').read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    assert '0,31 ponto percentual' in report_path.read_text(encoding='utf-8')
