# Decisões de engenharia e riscos

1. **Escopo:** análise de dados reproduzível, sem dashboard ou aplicação web. Justificativa: o case exige um memo e código explicativo, não software de produção.
2. **Fonte:** arquivos originais preservados em `input/`. A Q1 foi copiada para `Q1_CONGELADA_PRE_ANALISE.md` antes de abrir o Excel. Não foi reescrita posteriormente.
3. **Formato de ingestão:** leitor OOXML mínimo, testado na planilha específica. Risco: outros XLSX com datas numéricas, fórmulas complexas ou recursos não suportados podem demandar biblioteca geral. Não anunciar suporte a formatos externos.
4. **Grão de joins:** `Pedidos.id` é único; itens são 1:N; suporte e avaliação têm grão próprio. Somar `valor_total` após merge com itens causaria replicação indevida. Rankings agregam itens e status consulta pedido por dicionário 1:1.
5. **Valores monetários:** conversão para `Decimal` a partir da representação numérica, soma antes de arredondamento final. Tolerância documentada de R$ 0,01, não uma correção automática.
6. **Receita:** não alegar reconhecimento contábil. Usar "valor bruto dos itens em pedidos entregues" apenas como proxy. Nem ele nem `valor_total` são suficientemente comprovados para demonstrar margem.
7. **Cancelamento:** coorte por data de compra e status atual. Impossível reproduzir métricas baseadas em data do evento de cancelamento sem histórico.
8. **Fornecedores:** avaliações atribuíveis por `produto_id`; tickets apenas por `pedido_id`, portanto atribuição causal individual não é confiável nos casos multiforncedor.
9. **Q8:** uma única ação de contenção: congelar **a expansão** do investimento em `paid_search`, e medir sua taxa de cancelamento enquanto se obtém granularidade causal. Adia ação imediata de qualidade do fornecedor Delta. Não há estimativa monetária de margem por falta de reconciliação.
10. **Proibição de publicação automática:** nenhuma requisição externa, push para GitHub ou envio de e-mail é feito pelo projeto.

11. **Tarefa 2 — Desconto embutido no preço:** 36.439 de 36.439 linhas com desconto conhecido obedecem à relação `preco_praticado ≈ preco_unitario × (1−desconto_aplicado)` até R$ 0,01. O cenário de “valor líquido” que subtrai novamente `desconto_aplicado` não deve ser usado para tomada de decisão. Não houve alteração silenciosa do XLSX; os arquivos anteriores de simulação continuam rastreáveis.
12. **Tarefa 3 — Contrato formal:** `docs/03_METRICAS_E_ASSUNCOES.md` é a referência atualizada para fórmulas, grão, populações, lacunas e testes de aceitação de Q2–Q9.
