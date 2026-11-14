# Tarefa 6 — Q3: categorias por valor comercial e por volume

## Regra de cálculo

- Fonte: abas `Pedidos`, `Itens_Pedido` e `Produtos` da planilha original.
- Grão primário: **linha de item**, unida 1:1 a pedido e produto; não juntar avaliações ou tickets.
- Filtro principal: **`Pedidos.status == 'entregue'`** (9.959 pedidos).
- Valor: `Σ(Itens_Pedido.quantidade × Itens_Pedido.preco_praticado)`. O preço praticado já contém o desconto conhecido: **não reaplicar `desconto_aplicado`**.
- Volume: `Σ(Itens_Pedido.quantidade)` (**unidades**, não pedidos ou linhas).
- O valor é um **proxy comercial de itens entregues**; não equivale a receita reconhecida, faturamento contábil ou margem. Os totais de `Pedidos.valor_total` não conciliam com os itens na Q6.

## Ranking por valor comercial (principal)

| Pos. valor | Categoria | Valor comercial | Participação valor | Pos. volume | Unidades | Participação unidades | Valor médio/unidade |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | Eletrônicos | R$ 21.999.024,44 | 18,63% | 1 | 12.436 | 16,99% | R$ 1.768,98 |
| 2 | Casa & Decoração | R$ 17.568.904,23 | 14,88% | 2 | 11.925 | 16,29% | R$ 1.473,28 |
| 3 | Beleza & Saúde | R$ 16.962.519,83 | 14,36% | 4 | 9.346 | 12,77% | R$ 1.814,95 |
| 4 | Esporte & Lazer | R$ 14.293.636,88 | 12,10% | 5 | 8.058 | 11,01% | R$ 1.773,84 |
| 5 | Moda | R$ 13.902.592,20 | 11,77% | 3 | 10.321 | 14,10% | R$ 1.347,02 |
| 6 | Livros & Papelaria | R$ 12.951.931,61 | 10,97% | 6 | 7.185 | 9,81% | R$ 1.802,63 |
| 7 | Bebês & Crianças | R$ 10.935.414,92 | 9,26% | 8 | 6.960 | 9,51% | R$ 1.571,18 |
| 8 | Alimentos & Bebidas | R$ 9.470.586,39 | 8,02% | 7 | 6.981 | 9,54% | R$ 1.356,62 |
| **Total** | **8 categorias** | **R$ 118.084.610,50** | **100%** | — | **73.212** | **100%** | — |

## Ranking por volume

| Pos. volume | Categoria | Unidades | Pos. valor | Valor comercial |
|---:|---|---:|---:|---:|
| 1 | Eletrônicos | 12.436 | 1 | R$ 21.999.024,44 |
| 2 | Casa & Decoração | 11.925 | 2 | R$ 17.568.904,23 |
| 3 | Moda | 10.321 | 5 | R$ 13.902.592,20 |
| 4 | Beleza & Saúde | 9.346 | 3 | R$ 16.962.519,83 |
| 5 | Esporte & Lazer | 8.058 | 4 | R$ 14.293.636,88 |
| 6 | Livros & Papelaria | 7.185 | 6 | R$ 12.951.931,61 |
| 7 | Alimentos & Bebidas | 6.981 | 8 | R$ 9.470.586,39 |
| 8 | Bebês & Crianças | 6.960 | 7 | R$ 10.935.414,92 |

## Interpretação

**Os rankings não coincidem.**  Exemplos: Moda 3º por unidades e 5º por valor, com valor médio de R$ 1.347,02 por unidade; Beleza & Saúde 4º por unidades e 3º por valor, com valor médio de R$ 1.814,95 por unidade. A diferença de classificação é compatível com variações de valor médio ponderado por unidade; não demonstra causas comerciais ou de preferência.

## Sensibilidade ao filtro de status (não misturar universos)

| Cenário | Pedidos elegíveis | Linhas de itens | Unidades | Valor de itens |
|---|---:|---:|---:|---:|
| entregues | 9.959 | 24.385 | 73.212 | R$ 118.084.610,50 |
| nao cancelados | 12.463 | 30.442 | 91.491 | R$ 146.962.980,22 |
| todos | 15.000 | 36.740 | 110.164 | R$ 176.730.490,88 |

- Cenário **entregues**: principal e mais conservador como proxy de vendas efetivadas; ainda sujeito a reconciliação financeira.
- Cenário **não cancelados**: inclui devolvidos e em trânsito; não constitui receita realizada.
- Cenário **todos**: inclui cancelados e, portanto, é apenas volume/valor registrado nos itens criados.

## Verificações e arquivos

- Cada `Itens_Pedido.id` é único; `Produtos.id` e `Pedidos.id` são únicos. Não há expansão indevida no join.
- Soma das linhas elegíveis por categoria = linhas de itens elegíveis; idem para unidades e valor até R$ 0,01.
- Conferência independente via SQLite com totais em centavos inteiros, incluindo ranking.
- CSV: `outputs/q3_comparacao_entregues.csv` e `outputs/q3_ranking_volume.csv`; cenários existentes `outputs/q3_categorias_*.csv`.
- Gráficos: `outputs/q3_ranking_valor.png` e `outputs/q3_ranking_volume.png`.

**Limitações:** sem conciliação `valor_total`, sem confirmação de receita reconhecida e sem informação sobre os custos logísticos/impostos por pedido.
