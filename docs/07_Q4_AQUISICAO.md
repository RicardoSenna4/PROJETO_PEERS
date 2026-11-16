# Tarefa 7 — Q4

A população é formada por 15.000 pedidos, ligados a clientes por cliente_id sem multiplicar as linhas.

| Canal de aquisição | Pedidos | Cancelados | Taxa | Ticket reportado (R$) |
|---|---:|---:|---:|---:|
| paid_search | 3965 | 1219 | 30,744% | 2576,54 |
| indicação | 3658 | 453 | 12,3838% | 2531,85 |
| orgânico | 3616 | 426 | 11,7810% | 2515,08 |
| redes_sociais | 3761 | 439 | 11,6724% | 2651,49 |

A taxa tem como denominador todos os pedidos de cada canal de aquisição. O ticket médio reportado considera apenas pedidos entregues com total informado, sem afirmar receita reconhecida. Uma segunda métrica compara a soma de itens dos pedidos entregues, sem reaplicar descontos. Estratos por B2B/B2C e ano do pedido permitem analisar o efeito da composição, mas não provam causalidade. Paid_search apresenta a maior taxa e 48,05% dos cancelamentos. Para explicar a causa são necessários eventos de pagamento, campanha, estoque, entrega e motivos de cancelamento.
