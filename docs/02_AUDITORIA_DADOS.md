# 02 — Auditoria exploratória e qualidade dos dados (Tarefa 2)

## Fonte, objetivo e escopo

Origem: `Base_Dados_OrbitShop_v3.xlsx`; SHA-256: `f400a18e7cc838a201981c8a3ae2234e1a32a385ba1a3b91348f4f7770ca6f4b`. 
Inspeção **somente leitura**; os seis conjuntos de dados não foram modificados. A aba `Leia-me` esclarece que lacunas e discrepâncias financeiras são propositalmente mantidas no case.

## 1. Visão geral e valores ausentes

| Tabela | Registros | Campos | Chave primária duplicada | Campos incompletos |
|---|---:|---:|---:|---|
| Clientes | 3.000 | 8 | 0 | Nenhum |
| Produtos | 200 | 7 | 0 | Nenhum |
| Pedidos | 15.000 | 7 | 0 | `valor_total`: 79 (0.53%) |
| Itens_Pedido | 36.740 | 6 | 0 | `desconto_aplicado`: 301 (0.82%) |
| Tickets_Suporte | 4.000 | 7 | 0 | `data_resolucao`: 1653 (41.33%) |
| Avaliacoes | 8.000 | 7 | 0 | `comentario`: 1679 (20.99%) |

**Notas sobre os vazios:** `Pedidos.valor_total` e `Itens_Pedido.desconto_aplicado` impactam decisões financeiras; `Tickets_Suporte.data_resolucao` está ausente em abertos/escalados, e `Avaliacoes.comentario` é facultativo. Não substituir nulos automaticamente por zero.

## 2. Dicionário de dados observado

Campos e tipos foram inferidos a partir das células, não confirmados por um esquema formal do banco. Os tipos `int` e `float` aparecem juntos em alguns campos numéricos sem indicar erro.

**Clientes:** `id`, `nome`, `email`, `cidade`, `estado`, `data_cadastro`, `segmento`, `canal_aquisicao`.
**Produtos:** `id`, `nome`, `categoria`, `subcategoria`, `preco_unitario`, `custo_unitario`, `fornecedor`.
**Pedidos:** `id`, `cliente_id`, `data_pedido`, `status`, `valor_total`, `canal_venda`, `cupom_desconto`.
**Itens_Pedido:** `id`, `pedido_id`, `produto_id`, `quantidade`, `preco_praticado`, `desconto_aplicado`.
**Tickets_Suporte:** `id`, `pedido_id`, `cliente_id`, `categoria_problema`, `data_abertura`, `data_resolucao`, `status`.
**Avaliacoes:** `id`, `pedido_id`, `produto_id`, `cliente_id`, `nota`, `comentario`, `data_avaliacao`.

O dicionário por campo, com cardinalidades, tipos e ausentes, está em `outputs/dicionario_dados.csv`. Algumas colunas são strings ISO de data, não datas serializadas pelo Excel.

## 3. Integridade referencial e duplicidades

| Relação | Chaves órfãs |
|---|---:|
| `Pedidos.cliente_id → Clientes.id` | 0 |
| `Itens_Pedido.pedido_id → Pedidos.id` | 0 |
| `Itens_Pedido.produto_id → Produtos.id` | 0 |
| `Tickets_Suporte.pedido_id → Pedidos.id` | 0 |
| `Tickets_Suporte.cliente_id → Clientes.id` | 0 |
| `Avaliacoes.pedido_id → Pedidos.id` | 0 |
| `Avaliacoes.produto_id → Produtos.id` | 0 |
| `Avaliacoes.cliente_id → Clientes.id` | 0 |

Todas as seis chaves primárias são únicas; emails normalizados e pares (`pedido_id`, `produto_id`) de itens também não apresentaram duplicidades.

### Coerência relacional e temporal

| Verificação | Ocorrências |
|---|---:|
| `pedidos_sem_itens` | 0 |
| `clientes_com_cadastro_posterior_ao_pedido` | 0 |
| `tickets_cliente_diverge_do_pedido` | 0 |
| `avaliacoes_cliente_diverge_do_pedido` | 0 |
| `avaliacoes_produto_nao_consta_do_pedido` | 0 |
| `tickets_anteriores_ao_pedido` | 0 |
| `avaliacoes_anteriores_ao_pedido` | 0 |
| `resolucoes_anteriores_a_abertura` | 0 |
| `resolvidos_sem_data_resolucao` | 0 |
| `nao_resolvidos_com_data_resolucao` | 0 |
| `resolucoes_em_2025` | 51 |
| `pedidos_fora_2023_2024` | 0 |
| `tickets_abertos_fora_2023_2024` | 0 |
| `avaliacoes_fora_2023_2024` | 0 |
| `preco_catalogo_menor_que_custo` | 0 |
| `email_repetido_apos_normalizar` | 0 |
| `itens_mesmo_produto_repetido_no_pedido` | 0 |
| `mais_de_um_ticket_por_pedido` | 0 |
| `mais_de_uma_avaliacao_por_pedido` | 0 |

**Interpretação:** as 51 resoluções datadas de 2025 são eventos posteriores ao período de criação dos pedidos, **não datas inválidas**. Cadastros de clientes começam em 2022, antes do período de vendas, o que também não é defeito. Chamados resolvidos têm data de resolução, enquanto os chamados abertos/escalados não têm.

## 4. Validação de domínio e valores numéricos

| Campo | Domínio observado / faixa | Inconsistências verificáveis |
|---|---|---:|
| `Produtos.preco_unitario` | 36.28 a 3495.8 | 0 |
| `Produtos.custo_unitario` | 16.67 a 2319.44 | 0 |
| `Pedidos.valor_total` | 30.42 a 14999.84 | 0 |
| `Itens_Pedido.quantidade` | 1 a 5 | 0 |
| `Itens_Pedido.preco_praticado` | 25.4 a 3495.8 | 0 |
| `Itens_Pedido.desconto_aplicado` | 0 a 0.3 | 0 |
| `Avaliacoes.nota` | 1 a 5 | 0 |
| `Clientes.segmento` | B2B, B2C | 0 |
| `Clientes.canal_aquisicao` | indicação, orgânico, paid_search, redes_sociais | 0 |
| `Pedidos.status` | cancelado, devolvido, em_transito, entregue | 0 |
| `Pedidos.canal_venda` | app, marketplace, site | 0 |
| `Pedidos.cupom_desconto` | não, sim | 0 |
| `Tickets_Suporte.status` | aberto, escalado, resolvido | 0 |
| `Tickets_Suporte.categoria_problema` | atraso, cobrança, defeito, dúvida, troca | 0 |

As listas categóricas acima representam valores encontrados ou validação operacional presumida — **não** são necessariamente enumerações completas do sistema de produção.

## 5. Descontos: descoberta crítica

Há **36.439 itens** com `desconto_aplicado` informado. Em **35.943** deles, o preço praticado coincide exatamente com `preco_unitario × (1 − desconto_aplicado)` arredondado a centavos; em **36.439 de 36.439**, a diferença é no máximo **R$ 0,01**.

**Implicação:** há evidência forte de que `preco_praticado` já incorpora o desconto. Multiplicá-lo novamente por `(1−desconto_aplicado)` causaria **dupla aplicação de descontos**. O significado técnico-contábil de `preco_praticado` permanece sujeito à confirmação do time de dados. Para os 301 descontos ausentes, preservar a lacuna; não preencher `0` sem premissa explicitada.

## 6. Divergência financeira em nível de pedido

- Pedidos: **15.000**; com `valor_total` informado: **14.921**; nulo: **79**.
- Pedidos com igualdade até R$ 0,01 entre `valor_total` e `Σ(quantidade × preco_praticado)`: **0**; com divergência: **14.921**.
- Soma dos valores reportados nos pedidos comparáveis: **R$ 38.418.252,65**.
- Soma das linhas desses mesmos pedidos: **R$ 175.861.677,47**.
- Resíduo agregado (reportado − itens): **R$ -137.443.424,82**; soma das diferenças absolutas: **R$ 150.370.865,92**.

Essas diferenças **não autorizam** substituir uma fonte pela outra como receita ou margem: faltam fatos financeiros sobre frete, impostos, reembolsos, capturas, cupom e reconhecimento de receita. Nesta auditoria, `Σ(qtd × preco_praticado)` é apenas **valor comercial das linhas**, sujeito à política de status.

### Exemplos de reconciliação por ID

| pedido_id | Valor reportado | Itens | Diferença |
|---:|---:|---:|---:|
| 5915 | 1.090,13 | 63.816,49 | -62.726,36 |
| 14854 | 306,43 | 60.909,60 | -60.603,17 |
| 4192 | 1.769,63 | 58.537,32 | -56.767,69 |
| 5212 | 2.287,67 | 58.971,88 | -56.684,21 |
| 6280 | 887,77 | 57.043,33 | -56.155,56 |

## 7. Cardinalidade e riscos nos cruzamentos

- `Pedidos`: 15.000 IDs; `Itens_Pedido`: 36.740 linhas (**2.45 itens/ pedido, em média**). Um join altera o grão para item e multiplicará valores de pedido se agregados sem cuidado.
- **10.040 pedidos** incluem mais de um fornecedor; **2.676 tickets** se relacionam com esses pedidos. Não atribuir automaticamente esses tickets a cada fornecedor.
- O arquivo possui no máximo um ticket e uma avaliação por pedido nesta fotografia, mas isso não prova uma regra permanente do sistema de origem.

## 8. Prioridades e encaminhamento para a Tarefa 3

1. **Crítico:** interromper qualquer afirmação de receita ou margem conciliada; documentar fontes, amostras e campos necessários para reconciliação.
2. **Alto:** usar `preco_praticado` sem descontar novamente; testar cenários sobre valores ausentes, sem imputação disfarçada.
3. **Alto:** fixar grão e denominadores antes de comparar cancelamentos, ticket médio e fornecedores.
4. **Médio:** documentar ausência de histórico de status, data efetiva do cancelamento, canal de campanha detalhado, valor de cupom e prova de pagamentos.
5. **Médio:** distinguir chamados abertos por mês de chamados por coorte de compra; datas de resolução em 2025 não são automaticamente problema.

**Limite da auditoria:** não há validação independente contra ERP, gateway de pagamentos, estoque ou base operacional, apenas verificações internas da planilha original.
