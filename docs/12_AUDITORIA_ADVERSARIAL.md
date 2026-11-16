# Tarefa 12 — Auditoria adversarial independente (Q2–Q9)

## Método
Comparação independente em SQLite, reconstruindo tabelas diretamente do Excel, com valores financeiros em centavos inteiros. Não reutiliza as funções de agregação auditadas.

**Verificações:** 15/15 aprovadas.

| Check | Resultado | Critério |
|---|---|---|
| `Q2_STATUS` | PASS | Distribuição por status de pedido distinto |
| `Q2_ANO` | PASS | Coorte definida por data_pedido |
| `Q3_CATEGORIA` | PASS | Valor de itens entregues = quantidade × preço praticado |
| `Q4_AQUISICAO` | PASS | Canal de aquisição cadastrado no cliente |
| `Q5_SERIE` | PASS | 24 coortes mensais por data_pedido |
| `Q5_CONTAGEM_MESES` | PASS | Meses consecutivos de 2023-01 a 2024-12 |
| `Q5_TICKETS` | PASS | Relógio de abertura, não data de compra |
| `Q6_POPULACAO` | PASS | Um pedido por linha, sem imputar 79 nulos |
| `Q6_VALORES_CENTAVOS` | PASS | Centavos inteiros com universo comparável, sem duplo desconto |
| `Q7_NOTAS` | PASS | Avaliações: grão produto-avaliação |
| `Q7_PEDIDOS_MONO_MULTI` | PASS | Fornecedor único por pedido, não por linha |
| `Q7_TICKETS_MONO_MULTI` | PASS | Não replicar tickets multiforncedor pelos fornecedores |
| `Q8_ACAO_UNICA` | PASS | Conselho aceita apenas uma ação imediata |
| `Q8_NUMERADOR` | PASS | Taxa de cancelamento sem extrapolação causal |
| `Q9_LACUNA` | PASS | Uma pergunta material não respondida |

## Divergências reproduzidas
Nenhuma divergência entre as métricas auditadas e as consultas independentes **dentro dos invariantes testados**. Isso não comprova causalidade nem qualidade completa da fonte.

## Riscos e bloqueios que permanecem
- **P0 — Conciliação financeira:** Valor total do pedido e itens divergentes; faltam componentes e razão contábil.
- **P1 — Causalidade de cancelamentos:** Sem motivo, timestamp do cancelamento e campanha por pedido.
- **P1 — Atribuição de suporte:** Tickets de pedidos com mais de um fornecedor não têm produto responsável.
- **P2 — Viés de seleção das avaliações:** Não há evidência de representatividade de quem avaliou.

## Testes hostis
- Um ticket repetido no mesmo pedido não deve duplicar pedidos com chamados.
- Um pedido com mais de um fornecedor não atribui seu ticket a fornecedor individual.
- Alterações artificiais em métricas precisam produzir `FAIL` na auditoria.
- Comparação financeira inclui somente os pedidos com valores preenchidos e mantém a mesma população de itens.

## Limites
O resultado da auditoria atesta consistência interna mensurável; não valida a classificação de status, o reconhecimento contábil, o conteúdo dos motivos de cancelamento nem vínculos causais. Corrigir o dado de origem exige investigação e nova evidência.
