# 03 — Contrato de métricas e premissas verificadas (Tarefa 3)

**Prioridade:** enunciado oficial do Case OrbitShop → aba `Leia-me` do Excel → fatos verificados na auditoria → decisões metodológicas explícitas. Esta especificação não atesta reconhecimento contábil de receita nem transforma correlação em causalidade.

**Origem auditada:** `input/Base_Dados_OrbitShop_v3.xlsx` (seis tabelas, 2023–2024). **Reprodução:** `python -m scripts.run_data_audit`; evidências em `docs/02_AUDITORIA_DADOS.md`, `outputs/auditoria_qualidade.json` e `outputs/dicionario_dados.csv`.

## 1. Regras transversais

1. **Grão, sempre explícito:** `Pedidos.id` (pedido), `Itens_Pedido.id` (linha/item), `Avaliacoes.id` (avaliação), `Tickets_Suporte.id` (ticket), `Clientes.id` (cliente) e `Produtos.id` (produto). Não somar atributos de pedido depois de join com itens sem deduplicar por `pedido_id`.
2. **Datas:** agrupamento de pedidos por `Pedidos.data_pedido`; de chamados por `Tickets_Suporte.data_abertura`. Datas armazenadas em formato ISO. Status são **fotografia**, sem `data_cancelamento` ou trilha de mudanças. Dados de abertura/avaliação são 2023–2024; 51 chamados foram resolvidos em 2025, o que é temporalmente compatível com abertura em 2024.
3. **Denominador:** pedidos distintos da população declarada. Ao comparar canal ou período, manter filtro e status consistentes. Reportar contagens e tamanho da amostra junto aos percentuais.
4. **Nulos:** não substituir silenciosamente `valor_total` (79 pedidos), `desconto_aplicado` (301 itens), `data_resolucao` (1.653 tickets) nem `comentario` (1.679 avaliações). Os dois últimos podem ser ausências legítimas. Registrar **n** válido usado em cada média.
5. **Precisão:** cálculos monetários em `Decimal`, acumular antes de arredondar a centavos; apresentar como `R$`, taxas com `%`, diferença absoluta de taxa em pontos percentuais (`p.p.`). Tolerância de comparação monetária **± R$ 0,01 por pedido**, que não torna diferenças sistemáticas aceitáveis.
6. **Recorte:** análise padrão de 01/01/2023 a 31/12/2024; não concluir comportamentos fora da janela. Não tratar registros com status `em_transito` como entrega finalizada nem `devolvido` como receita preservada.
7. **Rastreabilidade:** exportar cada tabela de suporte em CSV; todas as cifras do memo devem vir de resultados reproduzíveis no código. Separar `observado`, `hipótese`, `limitação` e `recomendação`.

## 2. Descoberta obrigatória: `preco_praticado` **já tem o desconto**

Para os **36.439 itens** cujo `desconto_aplicado` está preenchido:

```text
preco_praticado ≈ ROUND(preco_unitario × (1 − desconto_aplicado), 2)
```

A auditoria encontrou **35.943 coincidências exatas após arredondamento decimal HALF_UP** e **36.439/36.439 coincidências com diferença ≤ R$ 0,01**. Isso é forte evidência estrutural de que `preco_praticado` **já inclui o desconto**. Portanto:

- **Valor comercial principal da linha:** `quantidade × preco_praticado`.
- **Proibido:** `quantidade × preco_praticado × (1−desconto_aplicado)` como receita/valor líquido; representa **dupla dedução**. Se exibido em auditorias antigas, rotular como cenário metodologicamente inadequado e não usar em decisões.
- **Desconto teórico de catálogo, apenas quando necessário:** `quantidade × (preco_unitario − preco_praticado)`; não implica desconto recuperável ou valor capturado.
- Nos **301 itens com desconto ausente**, usar `preco_praticado` observado para valor comercial e manter `desconto_aplicado` como **desconhecido**; é possível estimar um desconto *implícito* a partir do catálogo, mas essa estimativa não substitui o campo real.
- `cupom_desconto` informa somente `sim/não`, sem montante; não subtrair valor de cupom inexistente no arquivo e não assumir que o cupom já está ou não embutido no preço.

**Nível de evidência:** relação numérica verificada para a base; sua interpretação comercial e regras de integração ainda precisam de confirmação do time de dados.

## 3. Dicionário operacional de métricas Q2–Q9

| Q | Métrica | Fórmula e unidade | Grão, população e filtros | Tratamento de nulos e ressalva |
|---|---|---|---|---|
| Q2 | Pedidos por status | `COUNT(DISTINCT pedido_id)`; unidades, participação `n_status / N × 100` | `Pedidos`, **todos** os status, 2023–2024 | Nenhum status faltante; soma das contagens = 15.000 |
| Q2 | Taxa de cancelamento | `COUNT(DISTINCT pedidos status='cancelado') / COUNT(DISTINCT pedidos) × 100` | Coorte de `data_pedido` e, quando aplicável, segmento/canal; incluir todos os status no denominador | Status atual não informa **quando** foi cancelado |
| Q2 | Evolução em n e em taxa | `Δn = (n_2024/n_2023 − 1)×100` ; `Δtaxa_pp = taxa_2024−taxa_2023`; `Δtaxa_rel = (taxa_2024/taxa_2023−1)×100` | Comparar mesmas regras nas coortes anuais | Não confundir 40% de aumento de **volume** com 40 p.p. ou 40% relativos na **taxa** |
| Q3 | Volume por categoria | `SUM(Itens_Pedido.quantidade)`; unidades físicas | `Itens_Pedido → Produtos`, filtrando pedidos com status **`entregue`** como universo principal | Não contar linhas ou número de pedidos como unidades |
| Q3 | Valor comercial por categoria | `SUM(quantidade × preco_praticado)`; R$ | Mesmo universo de Q3, agrupamento por `Produtos.categoria` | **Proxy comercial**, não `receita líquida reconhecida`; sem segunda aplicação de desconto |
| Q3 | Comparação de ranking | Ordenar separadamente valor comercial e unidades; `preço médio ponderado = valor/unidades` | Mesmos itens e status dos dois rankings | Categorias com preços médios distintos podem inverter ranking |
| Q4 | Taxa de cancelamento por aquisição | `n_cancelados_do_canal / n_pedidos_do_canal ×100` | Join `Pedidos.cliente_id → Clientes.id`; agrupar por **`Clientes.canal_aquisicao`** | `Pedidos.canal_venda` é **outra dimensão**, não substituir |
| Q4 | Participação do canal | `pedidos_do_canal / todos_pedidos ×100`; `% dos cancelamentos = cancelados_canal/cancelados_total ×100` | Mesmo join, todos os pedidos | Reportar também `n` clientes e pedidos |
| Q4 | Ticket médio **registrado** | `Σ(Pedidos.valor_total não nulo) / COUNT(Pedidos com valor_total não nulo)`; R$/pedido | Apenas pedidos status **`entregue`** com valor total não nulo, por canal de aquisição | 58 pedidos entregues sem `valor_total`; **valor registrado não reconcilia com itens, logo não comprova ticket financeiro real** |
| Q4 | Sensibilidade de ticket | `Σ(valor comercial dos itens de pedidos entregues) / COUNT(pedidos entregues)` | Mesmo status, por canal, com linhas item agregadas no grão pedido antes do join | Alternativa **proxy**, não substituir por receita contábil; segmentar B2B/B2C e ano para contextualizar mix |
| Q5 | Volume mensal de pedidos | `COUNT(DISTINCT pedido_id)` por `YYYY-MM(data_pedido)` | Criar calendário mensal fixo 2023-01 a 2024-12 (24 linhas) | Mês sem eventos = 0; não inventar data inexistente |
| Q5 | Pico mensal | Maior contagem de pedido por ano; comparar também mês anterior e baseline | Mesmo recorte dos 24 meses | Causa de pico é **hipótese**, precisa calendário promocional/campanhas |
| Q5 | Suporte por abertura | `COUNT(DISTINCT ticket_id)` por `YYYY-MM(data_abertura)` | `Tickets_Suporte`, 2023–2024 | A abertura pode ocorrer após mês do pedido: não correlacionar sem defasagem |
| Q5 | Incidência de chamados por coorte | `COUNT(DISTINCT pedido_id com ticket) / COUNT(DISTINCT pedidos na coorte) ×100` | Atribuir ticket à coorte `YYYY-MM(data_pedido)` | Usar incidência, não simplesmente nº tickets / pedidos caso existam vários tickets por pedido |
| Q6 | Total reportado | `Pedidos.valor_total`; R$ | Um valor por pedido, somente não nulos | 79 sem total; não preencher sem evidência |
| Q6 | Total comercial reconstruído | `Σ_itens(qtd × preco_praticado)`; R$ | Agregar itens **antes** de comparar com pedido; todos os status na reconciliação estrutural | Não aplicar desconto de novo; status cancelado/devolvido não equivale a venda realizada |
| Q6 | Diferença por pedido | `residual = valor_total − total_comercial_reconstruído` | Somente pedidos com total reportado válido; igualdade quando `abs(residual) ≤ R$0,01` | Exibir nº nulos, divergentes, média/mediana/maiores diferenças, soma sinalizada e soma absoluta |
| Q6 | Lacuna de reconciliação | `SUM(residual)`, `SUM(abs(residual))` e `% pedidos divergentes` | Mesma amostra de pedidos comparáveis | **Não** somar totais de universos distintos (ex.: incluir itens de 79 pedidos nulos no confronto) |
| Q7 | Nota média por fornecedor | `AVG(Avaliacoes.nota)` e mediana; proporção `nota ≤2` | `Avaliacoes.produto_id → Produtos.id → fornecedor`; todas as avaliações válidas | Avaliação é relativa a produto/fornecedor, não prova autoria do motivo de suporte |
| Q7 | Incidência de chamado atribuível apenas ao pedido monofornecedor | `pedidos monofornecedor com ticket / pedidos monofornecedor ×100` | Fornecedor único determinado pelos **itens distintos por pedido** | Indica associação no pedido, **não responsabilidade causal** |
| Q7 | Exposição e amostra | `COUNT(DISTINCT pedidos com fornecedor)`, nº avaliações, unidades entregues | Manter separadas exposição a pedido e incidência monofornecedor | Pedidos multiforncedor não podem ter ticket distribuído automaticamente por todos; n das avaliações explícito |
| Q7 | Pico de chamados por tipo | `COUNT(ticket_id)` por mês de abertura e categoria_problema | `Tickets_Suporte` | Explicação causal não é identificável sem motivo ao nível produto/fornecedor |
| Q8 | Priorização da ação | Selecionar **uma** ação sustentada por magnitude, exposição e viabilidade | Usar evidências verificadas Q2–Q7 | Benefício monetário **não quantificável** sem reconciliação financeira; declarar custo de oportunidade |
| Q9 | Pergunta não respondida | Uma pergunta material, seguida dos campos necessários para respondê-la | Solicitar, por exemplo, motivos de cancelamento, históricos de status, autorizações/estornos e dados de campanha | Diferenciar informação ausente de informação contraditória |

## 4. Regras particulares e testes de aceitação

### Q2 — Taxa de cancelamento e falas contraditórias

- Comparar **ano do pedido**, não ano do evento de cancelamento (ausente). Exibir `N`, `n_cancelados`, `%` por coorte e ∆ em n, p.p. e % relativo.
- **Teste:** soma de status = 15.000; cada taxa `0–100%`; conferência independente por agrupamento.
- As falas de Growth (alta de 40%) e CFO (18%→16%) são alegações a verificar; não adaptar filtros para prová-las sem evidência.

### Q3 — Receita x volume

- Usar `entregue` para proxy principal; mostrar sensibilidade `todos` e `não cancelados`, com **rótulos distintos**. `devolvido` e `em_transito` não contam para proxy entregue.
- **Teste:** nenhuma duplicação de linha `Itens_Pedido.id`, `Produtos.id` join 1:1; totais por categoria batem com subtotal dos itens elegíveis.
- Não usar `Produtos.preco_unitario` para calcular valor comercial transacionado.

### Q4 — Aquisição, cancelamentos e ticket

- Agrupar por `Clientes.canal_aquisicao`; cruzamento esperado é **muitos pedidos para um cliente**.
- Métrica principal de ticket é **apenas descritiva sobre valores reportados**, com aviso de Q6; incluir valores ausentes por canal e sensibilidade por segmento B2B/B2C e ano.
- **Teste:** soma de pedidos dos 4 canais = 15.000; soma de cancelados = total Q2; nº de pedidos distintos inalterado após junção.

### Q5 — Séries temporais e hipótese

- 24 linhas consecutivas. Picos definidos ex ante como o **maior mês de cada ano**, não escolher só picos narrativamente convenientes.
- Usar abertura dos chamados para série de suporte e coorte de compra para incidência, rotulando séries com os respectivos relógios.
- **Teste:** soma de meses = 15.000; tickets abertos no período somam 4.000; nenhum ticket anterior ao pedido.
- Hipóteses sobre campanhas, promoções, logística ou sazonalidade precisam de dados externos para validação.

### Q6 — Reconciliação decisiva

- Comparar `valor_total` a `Σ(qtd × preco_praticado)` **dos mesmos pedidos**. Preço praticado já apresenta desconto, não multiplicar por `(1−desconto_aplicado)` mais uma vez.
- **Auditoria encontrada:** 14.921 pedidos possuem total reportado; **nenhum** dos 14.921 é conciliado em ±R$0,01. Reconciliar em sistema externo antes de afirmar receita, GMV ou margem financeira com precisão.
- 79 `valor_total` ausentes; não preencher automaticamente. `cupom_desconto` é booleano descritivo e não prova desconto monetário adicional.
- Para conselho: defender como **dado operacional** número de pedidos, status, unidades e valor comercial de itens entregues **claramente rotulado proxy**; não afirmar receita contabilizada.
- **Teste:** 1 linha na reconciliação por pedido, compare somente na amostra de valor_total informado, não misture com nulos.

### Q7 — Fornecedores e suporte

- Avaliações por `produto_id` permitem comparar fornecedores **de produtos avaliados**. Mostrar notas médias, `% nota≤2`, n e exposição.
- `Tickets_Suporte` não contém `produto_id` ou fornecedor do problema. **10.040 pedidos** têm múltiplos fornecedores e **2.676 chamados** se vinculam a eles; o responsável é indefinido. Usar pedidos **monofornecedor** para comparação conservadora, sem interpretar associação como culpa.
- **Teste:** 1 ticket ≠ 1 item; não replicar ticket para cada fornecedor presente; apresentar exclusões e denominadores.

### Q8 — Uma ação e trade-off

- Avaliar grandeza, risco de execução e reversibilidade; recomendar **somente uma ação imediata** com ao menos uma métrica verificável.
- Informar alternativa postergada e impacto potencial sem quantificar ganho financeiro inventado.
- Decisão é hipótese operacional testável e reversível, não certeza causal.

### Q9 — Pergunta sem dados suficientes

- Exemplo aplicável: **por que clientes originados em `paid_search` cancelam mais?** Precisamos motivo e momento de cancelamento, campanha específica, pagamento/autorização/estorno, eventos de estoque e logística.
- Adicionalmente, para aprovação de números financeiros, solicitar componentes de pedido, capturas, cobranças, cupons monetários e política de conciliação.

## 5. Hipóteses, limites e critérios para revisar este contrato

| Tema | O que está verificado | O que falta confirmar | Efeito na análise |
|---|---|---|---|
| Descontos | Igualdade entre preço de catálogo com desconto e `preco_praticado` em 36.439 linhas até R$ 0,01 | Regra oficial de formação de preço e aplicação do cupom | Evitar dupla dedução; não projetar receita líquida |
| `valor_total` | 79 nulos e 14.921 discrepâncias em relação aos itens | Que componentes/estados compõem o total registrado | Não usar como faturamento auditado |
| Status | `entregue`, `cancelado`, `devolvido`, `em_transito` observados | Histórico, carimbos de mudança e critérios de transição | Ano do cancelamento não identificável |
| Chamados | Data de abertura, tipo, pedido e status disponíveis | Causa raiz, item/fornecedor responsável em pedido multi | Não atribuir culpa sem dados |
| Avaliações | Nota vinculada a produto e pedido | Viés de seleção e representatividade de quem avalia | Comparação observacional, não causal |
| Aquisição | Cliente tem canal de aquisição estático | Campanha, CAC, jornada, exposição e mudança de canal | Diferenças não implicam causalidade |
| Cupons | Apenas indicador `sim`/`não` | Valor, regras, cumulatividade e momento do desconto | Desconto monetário desconhecido |

**Critério de revisão:** se houver dicionário de dados oficial, eventos transacionais ou conciliação externa que contradigam essas escolhas, registrar novo fato e atualizar o contrato e os testes; **não** alterar silenciosamente resultados anteriores.

## 6. Checkpoint para avançar à Tarefa 4

- [x] Conjunto de tabelas e chaves identificado.
- [x] Tipos, nulos, valores inválidos e datas verificados.
- [x] Granularidade e universos documentados.
- [x] Política de descontos justificada por evidência.
- [x] Denominadores, unidades e precisão monetária explicitados.
- [x] Limites e análises de sensibilidade registrados.
- [ ] Regras de receita e `valor_total` **confirmadas pela empresa** — informação indisponível, **bloqueio para afirmações financeiras contábeis**, não para cálculo de proxies.
