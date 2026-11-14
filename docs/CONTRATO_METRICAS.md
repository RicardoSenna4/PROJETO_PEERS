# Contrato de métricas

| Métrica | Grão | Definição | Dados e filtros | Tratamento de ausentes / ressalva |
|---|---|---|---|---|
| Taxa de cancelamento | Pedido | Pedidos com status `cancelado` / pedidos distintos no grupo | `Pedidos.id`, `Pedidos.status`, `Pedidos.data_pedido` | Status é fotografia atual; não há data de cancelamento |
| Variação da taxa | Ano de pedido | Taxa ano 2024 − taxa ano 2023 em **p.p.** | Ano em `data_pedido` | Variação relativa da taxa difere da variação absoluta em pontos |
| Distribuição por status | Pedido | Contagem e fração por status | Todos os 15.000 pedidos | Percentuais somam 100% salvo arredondamento |
| Valor bruto por categoria | Item de pedido | `SUM(quantidade × preco_praticado)` | Só pedidos `entregue`; grupo por categoria do produto | Proxy bruta, sem descontos comprovados nem reconhecimento contábil |
| Volume por categoria | Item de pedido | `SUM(quantidade)` | Mesmo universo da linha anterior | Não confundir unidades com linhas ou pedidos |
| Cancelamento por aquisição | Pedido | Cancelados do canal / pedidos do canal | `Pedidos.cliente_id -> Clientes.id`, usar `Clientes.canal_aquisicao` | Não confundir com canal de venda |
| Ticket médio registrado | Pedido entregue com total válido | `SUM(valor_total válido) / COUNT(valor_total válido)` | Pedidos `entregue` e `valor_total` não nulo | 58 pedidos entregues sem total; **valor_total não reconciliado**; indicador apenas comparativo |
| Pedidos por mês | Pedido | Contagem do `data_pedido` por ano/mês | Janeiro/2023–dezembro/2024 | Gerar meses vazios como zero; sem imputar datas |
| Chamados por mês | Ticket | Contagem de `data_abertura` | Janeiro/2023–dezembro/2024 | Data do ticket pode ser posterior à compra |
| Reconciliação bruta | Pedido | `valor_total − SUM(qtd × preco_praticado)` | Somente quando `valor_total` existe | Tolerância absoluta de R$ 0,01 sobre valores agregados, sem arredondar linhas |
| **Simulação descartada: desconto duplicado** | Pedido | `valor_total − SUM(qtd × preco_praticado × (1−desconto_aplicado))` | **Não usar para decisão**, mesmo quando desconto está preenchido | Auditoria confirma que `preco_praticado` já inclui o desconto em 36.439/36.439 itens até R$ 0,01; fórmula aplica desconto uma segunda vez |
| **Simulação histórica nulos=0 (descartada)** | Pedido | Fórmula da simulação anterior com desconto ausente preenchido hipoteticamente | **Não usar para receita ou margem** | Além de imputar desconto, essa fórmula **desconta duas vezes** nos itens conhecidos |
| Nota média de fornecedor | Avaliação | Média de `nota` por fornecedor do `produto_id` da avaliação | Avaliações ligadas a produtos do pedido | Produto é associado ao fornecedor, não ao responsável pelo ticket |
| Taxa de chamados monofornecedor | Pedido | Tickets associados / pedidos do fornecedor único | Pedidos cujo conjunto de fornecedores tem cardinalidade 1 | Em multifornecedor a atribuição causal é impossível |

**Fonte:** enunciado + estrutura dos seis conjuntos no arquivo Excel; definições são decisões metodológicas justificadas, não regras contábeis atestadas pela empresa.

**Atualização após a Tarefa 2 (13/11/2026):** a relação `preco_praticado ≈ preco_unitario × (1−desconto_aplicado)` foi confirmada em todos os 36.439 itens com desconto conhecido, até R$ 0,01. **Fonte normativa para novas análises:** `docs/03_METRICAS_E_ASSUNCOES.md`. Colunas ou métricas antigas que calculam “líquido” aplicando novamente o desconto são **cenários metodologicamente inadequados**, mantidos só por rastreabilidade, não indicadores financeiros.
