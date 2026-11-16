# Tarefa 11 — Q8 e Q9: decisão executiva

## Q8 — Uma única ação imediata

**Ação proposta:** Congelar apenas a EXPANSÃO do investimento em paid_search enquanto se investiga a causa da taxa anormal de cancelamento.

**Por quê:** `paid_search` reúne 3965 pedidos (26.43% do total) e 1219 cancelamentos (48.05% dos cancelamentos). A taxa observada é 30.74%, frente a 11.94% dos demais canais — diferença de 18.80 p.p. A distância não estabelece efeito causal.

**O que medir:** Taxa de cancelamento por coorte de compra, segmento, campanha e motivo, mais qualidade da conciliação financeira.

**Quando reconsiderar:** Após obter histórico de status, motivo e data do cancelamento e resultados por campanha; definir decisão de orçamento em revisão executiva.

**Trade-off explícito:** Adia a expansão comercial de paid_search e desloca atenção de ação imediata de melhoria do fornecedor DeltaFornece ME; pode perder oportunidades de aquisição enquanto se esclarece a causa.

**Financeiro:** 14921 de 14921 pedidos com total informado divergem dos itens; não calcular benefício financeiro sem conciliação. Não calcular economia ou margem projetada.

**Alternativas consideradas, mas não escolhidas:**
- Intervenção imediata no fornecedor DeltaFornece ME: avaliações inferiores, mas vínculo causal com o pico de suporte não demonstrado.
- Revisão da engenharia financeira como ação exclusiva: necessária para a rodada, mas não substitui o controle de exposição operacional ao cancelamento.

## Q9 — Pergunta que os dados não respondem

**Por que os pedidos de clientes adquiridos por paid_search são cancelados com maior frequência, e em qual evento da jornada isso ocorre?**

Solicitar ao time de dados:
- Histórico por pedido: mudanças de status com data/hora e motivo codificado de cancelamento.
- Campanha, anúncio, clique e custo de aquisição ligados ao cliente e ao pedido.
- Fluxo de pagamento: autorização, negação, captura, reembolso ou estorno com timestamps.
- Disponibilidade de estoque, promessa de entrega e eventos logísticos por pedido.
- Composição financeira do pedido: frete, tributos, desconto do cupom em R$, ajustes e repasses, para validar receita antes de estimar impacto.

**Consequência:** Pode diferenciar tráfego de baixa qualidade de falhas de pagamento, estoque ou logística; a ação deve ser revista após resposta. Sem reconciliação financeira não se deve quantificar benefício em R$.

## Limitação formal

Escolha executiva condicionada a observações, não causalidade demonstrada. Os status são fotografias sem linha do tempo; as somas financeiras não reconciliam com os itens. Uma única ação prioritária não significa que as demais correções deixaram de ser necessárias.
