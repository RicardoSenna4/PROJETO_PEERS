# Tarefa 5 — Q2: pedidos por status

## Definição

Unidade: **pedido distinto**, com `Pedidos.id` único. Universo: todos os pedidos com `data_pedido` entre 2023-01-01 e 2024-12-31. O status é a **fotografia atual** da base e o ano é o **ano da compra**, não o ano em que ocorreu um cancelamento.

## Distribuição geral

| Status | Pedidos | Participação |
|---|---:|---:|
| `entregue` | 9.959 | 66,39% |
| `cancelado` | 2.537 | 16,91% |
| `em_transito` | 1.371 | 9,14% |
| `devolvido` | 1.133 | 7,55% |
| **Total** | **15.000** | **100,00%** |

Visualização: [`outputs/q2_status.png`](../outputs/q2_status.png). Exportação: [`outputs/q2_status.csv`](../outputs/q2_status.csv).

## Cancelamentos por coorte anual

| Ano do pedido | Total | Cancelados | Taxa |
|---|---:|---:|---:|
| 2023 | 8.386 | 1.407 | 16,78% |
| 2024 | 6.614 | 1.130 | 17,09% |

- Total cancelado: **2.537** de **15.000** (**16,91%**).
- Variação da quantidade cancelada, 2024 versus 2023: **-19,69%**.
- Variação absoluta da taxa: **+0,31 ponto percentual**.
- Variação relativa da taxa: **1,83%**.

## Interpretação e confronto das falas

A quantidade de cancelamentos **diminuiu**, enquanto a taxa aumentou ligeiramente, porque o total de pedidos caiu ainda mais. Usando esta mesma população, período e definição, as falas de crescimento de 40% e queda da taxa de 18% para 16% **não são confirmadas**. As alegações podem ter usado janelas, status, eventos de cancelamento ou denominadores diferentes; isso não é verificável sem os critérios e o histórico dos relatórios originais.

## Controles de qualidade

- Soma dos status: **15.000**; total de pedidos: **15.000**.
- Soma das duas coortes: **15.000**.
- Teste independente: agrupamento por `id`, `status` e `ano` com SQLite.
- Limitação: falta a data/histórico do evento de cancelamento, portanto não é possível afirmar a tendência de cancelamentos ocorridos em cada ano.
