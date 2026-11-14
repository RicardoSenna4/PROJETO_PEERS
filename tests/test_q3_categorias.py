"""Tarefa 6: categorias (Q3), testes sintéticos e SQLite independente."""
from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from src.q3 import build_q3, render_q3_report
from src.workbook import load_xlsx

ROOT = Path(__file__).resolve().parents[1]


def fixture_base() -> dict:
    return {
        'Pedidos': [
            {'id': 1, 'status': 'entregue'},
            {'id': 2, 'status': 'entregue'},
            {'id': 3, 'status': 'cancelado'},
        ],
        'Produtos': [
            {'id': 10, 'categoria': 'Valor', 'preco_unitario': 150},
            {'id': 20, 'categoria': 'Quantidade', 'preco_unitario': 25},
        ],
        'Itens_Pedido': [
            {'id': 101, 'pedido_id': 1, 'produto_id': 10, 'quantidade': 1,
             'preco_praticado': 120, 'desconto_aplicado': 0.20},
            {'id': 102, 'pedido_id': 1, 'produto_id': 20, 'quantidade': 3,
             'preco_praticado': 20, 'desconto_aplicado': 0.20},
            {'id': 103, 'pedido_id': 2, 'produto_id': 20, 'quantidade': 2,
             'preco_praticado': 20, 'desconto_aplicado': 0.20},
            {'id': 104, 'pedido_id': 3, 'produto_id': 10, 'quantidade': 200,
             'preco_praticado': 120, 'desconto_aplicado': 0.20},
        ],
    }


def test_q3_uses_practiced_prices_without_reapplying_discount():
    result = build_q3(fixture_base())
    main = result['cenarios']['entregues']
    assert main['n_pedidos_elegiveis'] == 2
    assert main['n_linhas_itens'] == 3
    assert main['unidades'] == 6
    assert Decimal(main['valor_comercial_itens']) == Decimal('220.00')
    assert result['comparacao'][0]['categoria'] == 'Valor'
    assert result['ranking_volume'][0]['categoria'] == 'Quantidade'
    assert result['rankings_coincidem'] is False
    assert result['cenarios']['todos']['unidades'] == 206
    assert Decimal(result['cenarios']['todos']['valor_comercial_itens']) == Decimal('24220.00')


def test_q3_rejects_duplicated_item_ids():
    data = fixture_base()
    data['Itens_Pedido'][1]['id'] = 101
    with pytest.raises(ValueError, match='duplicatas'):
        build_q3(data)


def test_q3_rejects_orphan_product():
    data = fixture_base()
    data['Itens_Pedido'][0]['produto_id'] = 999
    with pytest.raises(ValueError, match='produto inexistente'):
        build_q3(data)


def test_q3_rejects_zero_quantity():
    data = fixture_base()
    data['Itens_Pedido'][0]['quantidade'] = 0
    with pytest.raises(ValueError, match='quantidade inválida'):
        build_q3(data)


def test_q3_renders_brazilian_values_and_explicit_limits():
    report = render_q3_report(build_q3(fixture_base()))
    assert 'R$ 220,00' in report
    assert 'receita reconhecida' in report
    assert 'não reaplicar' in report


def test_q3_real_data_independent_sqlite_integer_cents():
    data = load_xlsx(ROOT / 'input' / 'Base_Dados_OrbitShop_v3.xlsx')
    result = build_q3(data)
    conn = sqlite3.connect(':memory:')
    conn.executescript('''
        CREATE TABLE pedidos(id INTEGER PRIMARY KEY, status TEXT);
        CREATE TABLE produtos(id INTEGER PRIMARY KEY, categoria TEXT);
        CREATE TABLE itens(id INTEGER PRIMARY KEY, pedido_id INTEGER, produto_id INTEGER,
                           quantidade INTEGER, preco_centavos INTEGER);
    ''')
    conn.executemany('INSERT INTO pedidos VALUES (?,?)',
                     ((r['id'], r['status']) for r in data['Pedidos']))
    conn.executemany('INSERT INTO produtos VALUES (?,?)',
                     ((r['id'], r['categoria']) for r in data['Produtos']))
    conn.executemany('INSERT INTO itens VALUES (?,?,?,?,?)',
                     ((r['id'], r['pedido_id'], r['produto_id'], r['quantidade'],
                       int(Decimal(str(r['preco_praticado'])) * 100))
                      for r in data['Itens_Pedido']))
    sql = list(conn.execute('''
        SELECT p.categoria, SUM(i.quantidade), SUM(i.quantidade*i.preco_centavos),
               COUNT(DISTINCT i.id)
        FROM itens i JOIN pedidos o ON i.pedido_id=o.id
        JOIN produtos p ON i.produto_id=p.id
        WHERE o.status='entregue'
        GROUP BY p.categoria ORDER BY p.categoria
    '''))
    rows = {r['categoria']: r for r in result['comparacao']}
    assert len(sql) == len(rows) == 8
    for category, quantity, cents, n_items in sql:
        assert quantity == rows[category]['unidades']
        assert cents == int(Decimal(rows[category]['valor_comercial_itens_brl']) * 100)
        assert n_items == rows[category]['linhas_itens']
    assert sum(s[1] for s in sql) == 73212
    assert sum(s[2] for s in sql) == 11808461050
    assert result['rankings_coincidem'] is False
    assert rows['Moda']['posicao_volume'] == 3
    assert rows['Moda']['posicao_valor'] == 5
    assert rows['Beleza & Saúde']['posicao_volume'] == 4
    assert rows['Beleza & Saúde']['posicao_valor'] == 3


def test_q3_cli_generates_csv_charts_report(tmp_path):
    output_dir = tmp_path / 'out'
    report = tmp_path / 'docs' / 'q3.md'
    run = subprocess.run(
        [sys.executable, '-m', 'src.run',
         '--input', str(ROOT / 'input' / 'Base_Dados_OrbitShop_v3.xlsx'),
         '--output', str(output_dir), '--q3-report', str(report),
         '--q2-report', str(tmp_path / 'docs' / 'q2.md')],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert run.returncode == 0, run.stderr
    with (output_dir / 'q3_comparacao_entregues.csv').open(encoding='utf-8-sig', newline='') as handle:
        csv_rows = list(csv.DictReader(handle))
    assert len(csv_rows) == 8
    assert sum(int(r['unidades']) for r in csv_rows) == 73212
    assert sum((Decimal(r['valor_comercial_itens_brl']) for r in csv_rows), Decimal(0)) == Decimal('118084610.50')
    for path in ('q3_ranking_valor.png', 'q3_ranking_volume.png'):
        assert (output_dir / path).read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    assert 'Os rankings não coincidem' in report.read_text(encoding='utf-8')
