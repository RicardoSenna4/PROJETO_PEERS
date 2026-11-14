# Uso de IA — registro factual

**Ferramenta utilizada:** ChatGPT. O projeto foi implementado nesta conversa, com execução de Python no ambiente de trabalho. Não houve participação do Manus nesta execução nem ação automática no GitHub.

## O que a IA executou

- Leu o enunciado e o material metodológico disponibilizados.
- Preservou a Q1 original antes de acessar os dados de Excel.
- Desenvolveu um leitor de XLSX via biblioteca padrão, funções de auditoria e métricas, figuras, gerador de relatórios e testes automatizados.
- Conferiu contagens de status e aquisição em SQLite independente do código de agregações.
- Gerou tabelas e gráficos a partir de dados reais; redigiu o memo e o relatório de suporte, explicitando hipóteses e limitações.

## Erros/simplificações identificados e correções

1. **Descontos ausentes:** a exploração inicial usava uma simulação de `desconto_aplicado` ausente como zero sem separar completamente o universo conhecido. A implementação final mantém `valor_liquido_desconto_conhecido` em branco para qualquer pedido com desconto ausente e preserva um segundo campo rotulado `valor_liquido_assumindo_nulo_zero` para sensibilidade. São **301 pedidos** com ao menos um item de desconto desconhecido; 299 deles têm total reportado.
2. **Fixture sintética:** a função de aquisição inicialmente pressupunha a presença do canal `paid_search` ao calcular sua participação em cancelamentos. O teste com um canal fictício mostrou a fragilidade; foi corrigida com valor padrão zero.
3. **Teste lento:** um teste de volume reconstruía o índice de pedidos dentro de um laço. O teste foi corrigido para construir o índice uma única vez e executar em tempo adequado, sem alterar o resultado.
4. **Atribuição de tickets:** foi deliberadamente impedida a atribuição de tickets de pedidos multifornecedor a um fornecedor específico. A análise de taxas restringe a atribuição observacional a pedidos monofornecedor, e documenta exclusões.

## Limite da validação

Os **14 testes automatizados** foram executados e aprovados, mas **não substituem a revisão humana do avaliador**. A base não contém histórico de status, eventos de pagamento, conciliação contábil, campanhas, nem identificação de fornecedor causador do ticket. As recomendações estão sujeitas a esses limites.

## Revisão crítica de método — execução das tarefas 2 e 3

Foi feito um teste explícito da relação entre preço de catálogo, desconto e preço praticado. O resultado confirmou, em 36.439 linhas com desconto conhecido e tolerância de R$ 0,01, que o preço praticado já está descontado. Essa verificação revelou que a simulação inicial que aplicava novamente `desconto_aplicado` duplicava o desconto. A metodologia foi corrigida em `docs/03_METRICAS_E_ASSUNCOES.md` e nos avisos do README; os cenários antigos permanecem apenas como evidência histórica e não devem ser apresentados como receita. Os 21 testes foram executados de fato.

### 14/11/2026 — Evolução das tarefas 4 e 5

- Assistência com IA utilizada para elaborar a pré-validação, escrever casos sintéticos e gerar o relatório Q2 a partir de resultados reproduzíveis.
- Um teste de ID duplicado inicialmente falhou por exigir a expressão `duplicad` na mensagem, enquanto a exceção real empregava `duplicatas`; o teste foi corrigido para verificar o mesmo comportamento por `duplica` sem reduzir a exigência de rejeição da duplicação.
- Executados 46 testes, incluindo validação independente de totais por coorte com SQLite e integração da CLI com CSV e PNG. A verificação de consistência foi técnica, não prova de causalidade ou de receita auditada.
