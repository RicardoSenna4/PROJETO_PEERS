"""Garantir uma recomendação apenas, métricas derivadas e lacunas honestas."""
from pathlib import Path
import pytest
from src.workbook import load_xlsx
from src.analysis import analyze
from src.q8_q9 import build_q8_q9

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def decision():
    d=load_xlsx(ROOT/'input/Base_Dados_OrbitShop_v3.xlsx');d.pop('Leia-me',None)
    metrics,_=analyze(d)
    return build_q8_q9(metrics)


def test_single_action_and_explicit_opportunity_cost(decision):
    q8=decision['Q8']
    assert len(q8['recomendacoes_imediatas'])==1
    r=q8['recomendacoes_imediatas'][0]
    assert r['canal']=='paid_search'
    assert 'expans' in r['acao'].lower()
    assert r['tradeoff']
    assert r['ressalva']


def test_correct_denominators_not_fictional_savings(decision):
    r=decision['Q8']['recomendacoes_imediatas'][0]
    assert r['pedidos_expostos']==3965
    assert r['cancelados']==1219
    assert r['taxa_canal_pct']==pytest.approx(30.7440,abs=.002)
    assert r['taxa_canal_pct'] > r['taxa_demais_pct']
    assert 15 < r['diferenca_pontos_percentuais'] < 20
    assert 'não calcular' in decision['Q8']['restricao_financeira'].lower()


def test_q9_is_one_explicit_unanswered_business_question(decision):
    q9=decision['Q9']
    assert q9['pergunta_nao_respondida'].count('?')==1
    assert len(q9['dados_a_solicitar'])>=4
    assert any('cancelamento' in x for x in q9['dados_a_solicitar'])
    assert 'Pode diferenciar' in q9['impacto_na_recomendacao']


def test_recommendation_aborts_if_channel_no_longer_problematic():
    fake={'Q2':{'n':2},'Q4':{'canais':[{'canal_aquisicao':'paid_search','pedidos':1,'cancelados':0},
                                    {'canal_aquisicao':'organico','pedidos':1,'cancelados':1}]}}
    with pytest.raises(ValueError,match='não é o pior'):
        build_q8_q9(fake)
