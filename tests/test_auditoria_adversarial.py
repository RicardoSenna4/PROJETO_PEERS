"""Testes da independência e da detecção de alterações indevidas nas métricas."""
from copy import deepcopy
from pathlib import Path
import pytest
from src.workbook import load_xlsx
from src.analysis import analyze
from src.q8_q9 import build_q8_q9
from src.audit_review import audit_independent

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def basis():
    data=load_xlsx(ROOT/'input/Base_Dados_OrbitShop_v3.xlsx');data.pop('Leia-me',None)
    metrics,_=analyze(data);metrics['Q8_Q9']=build_q8_q9(metrics)
    return data,metrics


def test_audit_independent_matches_source(basis):
    report=audit_independent(*basis)
    assert report['total']>=12
    assert report['aprovadas']==report['total'], report['falhas']
    assert not report['falhas']
    assert any(r['prioridade']=='P0' for r in report['riscos_abertos'])


def test_audit_detects_wrong_q4_denominator(basis):
    data, metrics=basis
    broken=deepcopy(metrics)
    broken['Q4']['canais'][0]['pedidos']+=1
    assert 'Q4_AQUISICAO' in [x['id'] for x in audit_independent(data,broken)['falhas']]


def test_audit_detects_wrong_money_population(basis):
    data, metrics=basis
    broken=deepcopy(metrics)
    broken['Q6']['totais_brl']['gross_on_reported']='1.00'
    assert 'Q6_VALORES_CENTAVOS' in [x['id'] for x in audit_independent(data,broken)['falhas']]


def test_audit_detects_supplier_ticket_attribution_inflation(basis):
    data, metrics=basis
    broken=deepcopy(metrics)
    broken['Q7']['tickets_multifornecedor_sem_atribuicao']+=100
    assert 'Q7_TICKETS_MONO_MULTI' in [x['id'] for x in audit_independent(data,broken)['falhas']]


def test_audit_detects_two_recommendations(basis):
    data, metrics=basis
    broken=deepcopy(metrics)
    broken['Q8_Q9']['Q8']['recomendacoes_imediatas'].append({'acao':'Outra'})
    assert 'Q8_ACAO_UNICA' in [x['id'] for x in audit_independent(data,broken)['falhas']]
