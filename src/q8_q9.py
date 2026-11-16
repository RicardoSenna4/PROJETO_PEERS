"""Q8 e Q9: recomendação única, quantificável e explicitamente não causal."""
from __future__ import annotations

from .analysis import percent


def build_q8_q9(metrics: dict) -> dict:
    q4 = metrics['Q4']
    channels = q4['canais']
    paid = next((c for c in channels if c['canal_aquisicao'] == 'paid_search'), None)
    if paid is None:
        raise ValueError('O canal paid_search não consta da base; revisar hipótese de recomendação.')
    other_orders = sum(c['pedidos'] for c in channels if c is not paid)
    other_cancelled = sum(c['cancelados'] for c in channels if c is not paid)
    if not other_orders or not paid['pedidos']:
        raise ValueError('Não há amostra comparável de cancelamentos.')
    other_rate = 100 * other_cancelled / other_orders
    paid_rate = 100 * paid['cancelados'] / paid['pedidos']
    gap_pp = paid_rate - other_rate
    if gap_pp <= 0:
        raise ValueError('O canal paid_search não é o pior; não reutilizar recomendação antiga.')
    q6 = metrics['Q6']; q7 = metrics['Q7']
    cancelled = sum(c['cancelados'] for c in channels)
    total_orders = sum(c['pedidos'] for c in channels)
    if total_orders != metrics['Q2']['n']:
        raise ValueError('Populações de Q2 e Q4 incompatíveis.')
    # Critério de priorização: desvio relevante, muitos pedidos e ação reversível.
    # Não simular redução de cancelamentos como economia ou efeito causal.
    rec = {
        'acao': 'Congelar apenas a EXPANSÃO do investimento em paid_search enquanto se investiga a causa da taxa anormal de cancelamento.',
        'tipo': 'Contenção reversível, sem interromper campanhas existentes automaticamente',
        'canal': 'paid_search',
        'pedidos_expostos': paid['pedidos'],
        'participacao_pedidos_pct': percent(paid['pedidos'], total_orders),
        'cancelados': paid['cancelados'],
        'participacao_cancelamentos_pct': percent(paid['cancelados'], cancelled),
        'taxa_canal_pct': round(paid_rate, 4),
        'taxa_demais_pct': round(other_rate, 4),
        'diferenca_pontos_percentuais': round(gap_pp, 4),
        'razao_taxas_observadas': round(paid_rate / other_rate, 4),
        'indicador_reavaliacao': 'Taxa de cancelamento por coorte de compra, segmento, campanha e motivo, mais qualidade da conciliação financeira.',
        'condicao_para_revisar': 'Após obter histórico de status, motivo e data do cancelamento e resultados por campanha; definir decisão de orçamento em revisão executiva.',
        'tradeoff': 'Adia a expansão comercial de paid_search e desloca atenção de ação imediata de melhoria do fornecedor DeltaFornece ME; pode perder oportunidades de aquisição enquanto se esclarece a causa.',
        'ressalva': 'A diferença observada é associativa. Não representa estimativa causal de cancelamentos evitados, economia, margem, CAC ou ROI.',
    }
    question = 'Por que os pedidos de clientes adquiridos por paid_search são cancelados com maior frequência, e em qual evento da jornada isso ocorre?'
    required = [
        'Histórico por pedido: mudanças de status com data/hora e motivo codificado de cancelamento.',
        'Campanha, anúncio, clique e custo de aquisição ligados ao cliente e ao pedido.',
        'Fluxo de pagamento: autorização, negação, captura, reembolso ou estorno com timestamps.',
        'Disponibilidade de estoque, promessa de entrega e eventos logísticos por pedido.',
        'Composição financeira do pedido: frete, tributos, desconto do cupom em R$, ajustes e repasses, para validar receita antes de estimar impacto.',
    ]
    return {
        'Q8': {
            'recomendacoes_imediatas': [rec],
            'alternativas_nao_escolhidas': [
                'Intervenção imediata no fornecedor DeltaFornece ME: avaliações inferiores, mas vínculo causal com o pico de suporte não demonstrado.',
                'Revisão da engenharia financeira como ação exclusiva: necessária para a rodada, mas não substitui o controle de exposição operacional ao cancelamento.',
            ],
            'restricao_financeira': (f"{q6['contagens']['divergentes']} de {q6['contagens']['com_valor_reportado']} "
                                     'pedidos com total informado divergem dos itens; não calcular benefício financeiro sem conciliação.'),
            'evidencia_fornecedores': f"{q7['tickets_multifornecedor_sem_atribuicao']} tickets em pedidos multiforncedor sem identificação de responsável.",
        },
        'Q9': {
            'pergunta_nao_respondida': question,
            'dados_a_solicitar': required,
            'impacto_na_recomendacao': 'Pode diferenciar tráfego de baixa qualidade de falhas de pagamento, estoque ou logística; a ação deve ser revista após resposta. Sem reconciliação financeira não se deve quantificar benefício em R$.',
        },
    }


def render_decision_report(q89: dict) -> str:
    d = q89['Q8']['recomendacoes_imediatas'][0]
    q9 = q89['Q9']
    return f"""# Tarefa 11 — Q8 e Q9: decisão executiva

## Q8 — Uma única ação imediata

**Ação proposta:** {d['acao']}

**Por quê:** `paid_search` reúne {d['pedidos_expostos']} pedidos ({d['participacao_pedidos_pct']:.2f}% do total) e {d['cancelados']} cancelamentos ({d['participacao_cancelamentos_pct']:.2f}% dos cancelamentos). A taxa observada é {d['taxa_canal_pct']:.2f}%, frente a {d['taxa_demais_pct']:.2f}% dos demais canais — diferença de {d['diferenca_pontos_percentuais']:.2f} p.p. A distância não estabelece efeito causal.

**O que medir:** {d['indicador_reavaliacao']}

**Quando reconsiderar:** {d['condicao_para_revisar']}

**Trade-off explícito:** {d['tradeoff']}

**Financeiro:** {q89['Q8']['restricao_financeira']} Não calcular economia ou margem projetada.

**Alternativas consideradas, mas não escolhidas:**
""" + '\n'.join(f'- {a}' for a in q89['Q8']['alternativas_nao_escolhidas']) + f"""

## Q9 — Pergunta que os dados não respondem

**{q9['pergunta_nao_respondida']}**

Solicitar ao time de dados:
""" + '\n'.join(f'- {x}' for x in q9['dados_a_solicitar']) + f"""

**Consequência:** {q9['impacto_na_recomendacao']}

## Limitação formal

Escolha executiva condicionada a observações, não causalidade demonstrada. Os status são fotografias sem linha do tempo; as somas financeiras não reconciliam com os itens. Uma única ação prioritária não significa que as demais correções deixaram de ser necessárias.
"""
