"""Testes da infraestrutura de reprodução e integridade de entradas."""
from pathlib import Path
import hashlib
from scripts.verify_reproducibility import sha256, export_inventory, copy_fresh

ROOT = Path(__file__).resolve().parents[1]

def test_original_data_fingerprints():
    assert sha256(ROOT/'input/Base_Dados_OrbitShop_v3.xlsx') == 'f400a18e7cc838a201981c8a3ae2234e1a32a385ba1a3b91348f4f7770ca6f4b'
    assert sha256(ROOT/'input/Case_OrbitShop_Individual_v2.pptx') == 'ed902d4c507dd767c52143c4a528720f24da0b779833fcf78c1a1ca78af8f1f5'
    assert sha256(ROOT/'Q1_CONGELADA_PRE_ANALISE.md') == '6eb8e615d55e6dfad8c007093f21a0786ee7c5e8be2239ffa913b15f22c53ae8'

def test_file_inventory_tracks_changed_content(tmp_path):
    (tmp_path/'outputs').mkdir()
    (tmp_path/'docs').mkdir()
    p=tmp_path/'outputs/example.csv'
    p.write_text('a,b\n1,2\n')
    first=export_inventory(tmp_path)
    assert first['outputs/example.csv'] == hashlib.sha256(p.read_bytes()).hexdigest()
    p.write_text('a,b\n1,3\n')
    assert export_inventory(tmp_path) != first

def test_fresh_copy_leaves_preexisting_outputs_out(tmp_path):
    target=tmp_path/'clean'
    copy_fresh(ROOT,target)
    assert (target/'src/run.py').is_file()
    assert (target/'input/Base_Dados_OrbitShop_v3.xlsx').is_file()
    assert not (target/'outputs').exists()
    assert not (target/'MEMO_FINAL.md').exists()


def test_q7_causes_order_is_stable():
    # Causas precisam produzir a mesma ordem, independentemente da seed de hash.
    from src.q7 import build_q7
    minimal = {
        'Produtos': [{'id': 1, 'fornecedor': 'F'}],
        'Pedidos': [{'id': 1, 'status': 'entregue', 'data_pedido': '2023-11-01'}],
        'Itens_Pedido': [{'id': 1, 'pedido_id': 1, 'produto_id': 1, 'quantidade': 1}],
        'Avaliacoes': [],
        'Tickets_Suporte': [
            {'id': 1, 'pedido_id': 1, 'data_abertura': '2023-11-02', 'categoria_problema': 'zeta'},
            {'id': 2, 'pedido_id': 1, 'data_abertura': '2023-11-03', 'categoria_problema': 'alfa'},
        ],
    }
    # Teste positivo de contrato: a ordem de chaves é lexical.
    q7 = build_q7(minimal)
    assert list(q7['chamados_trimestre_final_2023_por_causa']) == ['alfa', 'zeta']
