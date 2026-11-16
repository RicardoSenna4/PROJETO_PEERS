# Tarefa 10 — Q7: desempenho de fornecedores e suporte

## Observações e definição da métrica
Avaliações têm produto identificado; tickets têm apenas pedido identificado. A comparação de chamados por fornecedor utiliza **somente pedidos monofornecedor**. A incidência é a contagem de **pedidos distintos com chamado**, dividida pelos pedidos monofornecedor; não é o número de tickets por pedido.

| Fornecedor | Avaliações | Média | Nota ≤ 2 | Pedidos mono | Pedidos mono com chamado | Incidência |
|---|---:|---:|---:|---:|---:|---:|
| DeltaFornece ME | 985 | 2.30 | 59.90% | 596 | 147 | 24.66% |
| SulFornece SA | 845 | 3.62 | 22.37% | 558 | 148 | 26.52% |
| NorteImport Ltda | 824 | 3.66 | 22.09% | 517 | 140 | 27.08% |
| TechBrasil Ltda | 1,027 | 3.74 | 20.25% | 660 | 182 | 27.58% |
| AlphaSupply | 684 | 3.80 | 18.13% | 380 | 106 | 27.89% |
| GlobalBR Comércio | 912 | 3.80 | 17.43% | 561 | 153 | 27.27% |
| FornecedorX | 789 | 3.81 | 18.76% | 494 | 142 | 28.74% |
| MegaDistribuidora | 1,241 | 3.82 | 17.73% | 755 | 186 | 24.64% |
| MarcoPolo Distribuição | 693 | 3.84 | 17.75% | 439 | 120 | 27.33% |

## Explicação do pico de suporte
Foram 156 tickets em outubro de 2023, 375 em novembro e 391 em dezembro. Os dois últimos meses somam 766 tickets, dos quais 603 estão associados a pedidos comprados em novembro.

10,040 pedidos contêm múltiplos fornecedores; 2,676 de 4,000 tickets (66.90%) não podem ser atribuídos individualmente a um fornecedor.

**DeltaFornece ME** apresenta média 2.30/5 em 985 avaliações, com 59.90% de notas ≤2. Sua incidência de chamados nos 596 pedidos monofornecedor é 24.66%. A nota pior não prova que o fornecedor causou o pico de chamados.

## Limitações e leitura para o conselho
- Avaliação negativa é associação ao produto, não prova defeito ou culpa do fornecedor.
- Tickets em pedidos com múltiplos fornecedores permanecem sem atribuição; não replicar o ticket a todos os fornecedores.
- Não existem causas-raiz por item nem séries de incidentes por fornecedor suficientes para identificar a origem do aumento.
- O volume da coorte de novembro pode explicar parte do número absoluto de tickets, sem comprovar deterioração operacional.

Arquivos reproduzíveis: `outputs/q7_fornecedores.csv`, `outputs/q7_causas_mensais.csv`, `outputs/q7_fornecedores.png`.
