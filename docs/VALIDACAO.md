# Verificação de entrega — evidência de execução

## Status

| Controle | Resultado |
|---|---|
| Planilha original e enunciado preservados | Sim; hashes SHA-256 registrados abaixo |
| Q1 mantida anterior à análise | Sim, `Q1_CONGELADA_PRE_ANALISE.md` |
| 6 tabelas analisadas | Sim: Clientes (3.000), Produtos (200), Pedidos (15.000), Itens_Pedido (36.740), Tickets_Suporte (4.000), Avaliacoes (8.000) |
| Orfandade e relações | Zero chaves órfãs; zero avaliações fora do pedido; zero divergências cliente-pedido |
| Saídas Q2–Q9 | `outputs/` e `docs/RELATORIO_TECNICO.md` |
| Reconciliação por pedido | 15.000 linhas com 0 conciliações brutas nos 14.921 com `valor_total` não nulo |
| Gráficos exportados | Q2, Q4, Q5, Q7 (4 PNGs) |
| Testes automatizados | **14 passed in 1.84s** (`python -m pytest -q`, execução real) |
| Auditoria independente SQLite | Sim, testes validam totais por status e taxa/canal de aquisição |
| Reprocessamento independente | `metricas.json` e `q6_reconciliacao_pedido.csv` produziram bytes idênticos em duas execuções |
| Memo executivo | 1 página A4 (verificação `pdfinfo`) e 346 palavras (contagem automática do texto-fonte) |
| Envio de e-mail ou push para GitHub | Não executado |

## SHA-256 da origem

```
f400a18e7cc838a201981c8a3ae2234e1a32a385ba1a3b91348f4f7770ca6f4b  input/Base_Dados_OrbitShop_v3.xlsx
ed902d4c507dd767c52143c4a528720f24da0b779833fcf78c1a1ca78af8f1f5  input/Case_OrbitShop_Individual_v2.pptx
6eb8e615d55e6dfad8c007093f21a0786ee7c5e8be2239ffa913b15f22c53ae8  Q1_CONGELADA_PRE_ANALISE.md
```

## SHA-256 de saídas reproduzidas

```
c5faf76f5c4e01c5b9ad0a701e7e941027c6da55c3f1ac93ffba6c0a53e742cd  outputs/metricas.json
bce189ab9506c94f515fdc25aa9f470821fa851db2da6bcbfa45b804c2c2d2cd  outputs/q6_reconciliacao_pedido.csv
```

## Reproduzir

```bash
python -m src.run --input input/Base_Dados_OrbitShop_v3.xlsx --output outputs
python -m pytest -q
python scripts/build_deliverables.py
```

A validade das recomendações é **condicionada ao sentido das métricas**: teste verde não prova reconhecimento de receita, causalidade entre canal e cancelamento nem responsabilidade do fornecedor por ticket.

## Verificação adicional — Tarefas 2 e 3

- Auditoria reproduzida com `python -m scripts.run_data_audit`: gerou `docs/02_AUDITORIA_DADOS.md`, `outputs/auditoria_qualidade.json` e `outputs/dicionario_dados.csv`.
- Confirmação não presumida: `preco_praticado` já reflete desconto informado em 36.439/36.439 itens a ± R$ 0,01. Ajustado contrato metodológico; antigas simulações de desconto adicional ficam marcadas como inadequadas para receita.
- **21 testes aprovados** (`python -m pytest -q`, execução posterior à inclusão de `tests/test_data_quality.py`, incluindo detecção de dados adulterados e chave órfã). A referência anterior de 14 testes documenta a execução precedente, não a mais recente.
- Planilha original não foi alterada; mesmo SHA-256 indicado no topo deste documento.

## Verificação adicional — Tarefas 4 e 5 (14/11/2026)

- Tarefa 4: `src/validation.py` bloqueia erros críticos de grão, chaves, domínio, data e quantidade, preservando dados originais e valores financeiros nulos.
- Tarefa 5: `src/analysis.py` exige um ID por pedido, calcula percentuais e diferenças sobre o ano de compra. `src/q2.py` gera relatório consistente com `q2_status.csv`, `q2_por_ano.csv` e `q2_status.png`.
- Testes escritos antes dos módulos e executados inicialmente com falha por ausência de implementação (RED); depois aprovados com as mudanças (GREEN).
- Teste independente SQLite confirma coortes de 2023 e 2024; integração real testa a CLI e a geração do CSV, relatório e PNG.
- Valor-base Q2: 15.000 pedidos, 2.537 cancelados (16,9133%). Por coorte: 2023 = 8.386/1.407 (16,7780%); 2024 = 6.614/1.130 (17,0850%). ∆ da quantidade = -19,6873%; ∆ taxa = +0,3070 p.p.
- Originais preservados: `input/Base_Dados_OrbitShop_v3.xlsx` SHA-256 `f400a18e7cc838a201981c8a3ae2234e1a32a385ba1a3b91348f4f7770ca6f4b`; Q1 congelada SHA-256 `6eb8e615d55e6dfad8c007093f21a0786ee7c5e8be2239ffa913b15f22c53ae8`.
- Verificação final: executar `python -m pytest -q`; o resultado recente está registrado no relatório de entrega das tarefas 4 e 5.

## Tarefa 6 — Q3

- `python -m src.run`: executado, tabelas CSV, relatório Markdown e gráficos PNG da Q3 produzidos.
- `python -m pytest -q`: **53 passed**.
- Teste independente `tests/test_q3_categorias.py`: joins com três tabelas, somas por categoria em centavos inteiros via SQLite, cenários de filtro de status, unidades e integridade.
- A base e o PPT originais não foram alterados.

## Tarefas 7, 8 e 9 — 16/11/2026

- TDD: novos testes RED (ausência dos módulos), GREEN após implementação; **60 testes aprovados** no conjunto completo.
- Q4: canais, tickets comparativos e estratos por segmento/ano; confirmação SQL independente de 15.000 pedidos e 2.537 cancelamentos.
- Q5: 24 meses, 4.000 tickets, conferência SQL independente de incidência sobre pedidos distintos (não tickets/pedidos).
- Q6: 15.000 pedidos, 14.921 comparáveis, 79 ausentes, nenhum reconciliado ±R$ 0,01; SQLite em centavos inteiros. Nenhuma dupla dedução.
- Arquivos de entrada possuem SHA-256 iguais ao registrado no topo.

## Tarefas 10, 11 e 12 — 16/11/2026

- Q7: pedidos monofornecedor versus multiforncedor, preservação dos 4.000 tickets; incidência definida por **pedidos com ticket**, não quantidade de tickets.
- Q8–Q9: somente uma ação imediata, com denominadores de Q4, custo de oportunidade, pergunta não respondida e campos necessários para teste causal.
- Auditoria Q2–Q9: `src/audit_review.py` gera 15 comparações independentes em SQLite, inclusive Q3 em centavos, Q6 na amostra comparável e Q7 sem replicar chamados.
- Cenários hostis: ticket duplicado no mesmo pedido, pedido multiforncedor, manipulação de contagem do canal, divergência financeira injetada e recomendação dupla.
- **74 testes aprovados**; **15/15 verificações de auditoria aprovadas** (execução `python -m pytest -q` e `python -m src.run`).
- Nenhum dado original alterado; consultar `docs/INTEGRIDADE_DADOS.md`.

### Correção pós-CI — compatibilidade de Q7 com gerador do memo

- A execução remota de 16/11/2026 aprovou 74 testes e reproduziu as métricas, mas identificou `KeyError` no gerador de memo devido a campos legados de Q7.
- Ajustado `scripts/build_deliverables.py` para ler `incidencia_chamado_mono_pct` e `pedidos_monofornecedor` e mantida a agregação explícita por causa no trimestre final de 2023 em `src/q7.py`.
- Reexecutados localmente `python -m src.run`, `python scripts/build_deliverables.py` e `python -m pytest -q`: 74 testes e auditoria 15/15 aprovados; memo PDF A4 de 1 página, 346 palavras.

## Fechamento das tarefas 13–15 — 16/11/2026

- **83/83 testes passaram** em `python -m pytest -q` na árvore atual, incluindo integridade da fonte, memo PDF, Q1 literal, empacotamento e caso sintético de ordenação de causas.
- **83/83 passaram em uma cópia independente**, criada sem saídas anteriores e regenerada por `python -m src.run` e `python scripts/build_deliverables.py` (diretório temporário de diagnóstico).
- `python -m scripts.verify_reproducibility` criou dois workspaces descartáveis e confirmou **29 artefatos textuais idênticos** por SHA-256; conferiu Q1, 1 página A4 e 356 palavras no memo.
- `python -m scripts.package_release` criou ZIP com **99 arquivos de projeto** e `MANIFEST_SHA256.txt` (100 entradas internas), validado por teste de integridade do ZIP e comparação de SHA-256 de cada arquivo.
- Hashes dos dados originais não mudaram: Excel `f400a18e7cc838a201981c8a3ae2234e1a32a385ba1a3b91348f4f7770ca6f4b`; PowerPoint `ed902d4c507dd767c52143c4a528720f24da0b779833fcf78c1a1ca78af8f1f5`.
- A auditoria independente interna da CLI continua com **15/15 checagens**.
- O envio ao recrutamento **não foi realizado**; o prazo oficial às 10h de 16/11/2026 já havia terminado.
- O estado de publicação em GitHub deve ser conferido pelas referências remotas após os commits; a validação local não implica push remoto.
