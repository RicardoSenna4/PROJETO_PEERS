# OrbitShop — análise reprodutível para a Peers Consulting

Implementação das questões **Q1–Q9** do `Case_OrbitShop_Individual_v2.pptx` a partir da base original `Base_Dados_OrbitShop_v3.xlsx`. O propósito é produzir uma conclusão empresarial **verificável e limitada pelo que os dados realmente demonstram**. Não é um sistema operacional, API ou dashboard.

## Entrega principal

| Arquivo | Finalidade |
| --- | --- |
| `MEMO_ORBITSHOP.pdf` | **Memo executivo**, 1 página A4, 346 palavras, Q1 no topo, seção Uso de IA |
| `MEMO_FINAL.md` | Fonte editável do texto do memo |
| `docs/RELATORIO_TECNICO.md` | Respostas detalhadas Q1–Q9, tabelas, premissas e limitações |
| `docs/02_AUDITORIA_DADOS.md` | Tarefa 2: auditoria da base, nulos, integridade, datas, descontos e valores |
| `docs/03_METRICAS_E_ASSUNCOES.md` | Tarefa 3: contrato de métricas por questão, denominadores e ressalvas |
| `docs/04_IMPLEMENTACAO_E_TESTES.md` | Tarefa 4: arquitetura mínima, pré-validação bloqueante e TDD |
| `docs/05_Q2_DISTRIBUICAO_STATUS.md` | Tarefa 5: contagem geral, comparação anual e interpretação da Q2 |
| `docs/06_Q3_CATEGORIAS.md` | Tarefa 6: ranking de valor comercial e unidades, sensibilidade por status e evidências |
| `outputs/q2_por_ano.csv` | Detalhamento auditável por coorte de compra, 2023 e 2024 |
| `outputs/q3_comparacao_entregues.csv` | Ranking comparativo em pedidos entregues, com participações e preço médio ponderado |
| `outputs/q3_ranking_volume.csv` | Ranking de categorias em unidades |
| `outputs/q3_ranking_valor.png` e `outputs/q3_ranking_volume.png` | Figuras de Q3 com escalas separadas |
| `outputs/auditoria_qualidade.json` e `outputs/dicionario_dados.csv` | Evidências da auditoria e catálogo de campos |
| `outputs/` | Tabelas CSV, figuras PNG, métricas JSON e reconciliação individual de 15.000 pedidos |
| `src/` | Código de leitura, validação, métricas, gráficos e exportação |
| `tests/` | Testes sintéticos e independentes via SQLite |
| `input/` | Base Excel e case PowerPoint originais, sem modificações |
| `Q1_CONGELADA_PRE_ANALISE.md` | Q1 preservada antes de acessar os dados do Excel |
| `docs/VALIDACAO.md` | Resultado real da execução dos testes e da conferência final |

## Ambiente

- Python **3.11+**.
- Dependências externas para gráficos/PDF/testes: `matplotlib`, `reportlab`, `pytest`.
- **Leitura dos dados usa somente a biblioteca padrão** (`zipfile` e XML), sem depender de Excel, pandas, openpyxl ou de serviços online. É um leitor enxuto de OOXML adequado ao esquema recebido; não foi projetado como leitor XLSX universal.
- Não são necessárias credenciais, variáveis de ambiente ou serviços externos.

### Instalação e execução

A partir da pasta que contém este README:

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m src.run --input input/Base_Dados_OrbitShop_v3.xlsx --output outputs
python -m scripts.run_data_audit
python -m pytest -q
python scripts/build_deliverables.py
```

No Windows, pode ser necessário usar `py` em vez de `python`. O gerador `scripts/build_deliverables.py` deve ser executado **após** o cálculo das métricas, pois lê `outputs/metricas.json`.

Os comandos de análise e testes foram executados com sucesso no ambiente de desenvolvimento. O PDF possui uma página, e a contagem de palavras do texto-fonte foi validada. Consulte `docs/VALIDACAO.md`.

## Definições resumidas

- **Cancelamento:** pedido com `status == 'cancelado'` / pedidos distintos (por coorte do **ano da compra**, não data do cancelamento, que não existe na base).
- **Q3:** unidades `SUM(quantidade)` e valor bruto de itens `SUM(quantidade × preco_praticado)` **em pedidos entregues**. Não significa receita reconhecida.
- **Q4:** agrupar por `Clientes.canal_aquisicao` (não confundir com `Pedidos.canal_venda`). Ticket médio = soma de `Pedidos.valor_total` não nulo / número de pedidos entregues com total não nulo; **não é receita auditada**.
- **Q5:** meses consecutivos 2023-01…2024-12. Suporte por mês de abertura e, separadamente, por mês de criação do pedido associado.
- **Q6:** comparação entre total informado e soma de `quantidade × preco_praticado` por pedido. A auditoria da Tarefa 2 confirmou que `preco_praticado` **já incorpora** `desconto_aplicado` (36.439 de 36.439 itens conhecidos, até R$ 0,01). **Não reaplicar desconto**. Os campos históricos `valor_liquido_desconto_conhecido` e `valor_liquido_assumindo_nulo_zero` nos CSVs anteriores são apenas simulações incorretas para receita e devem ser **desconsiderados**; o comparativo bruto de itens praticados continua válido como proxy.
- **Q7:** avaliações atribuídas a fornecedor via produto efetivamente avaliado. Chamados atribuídos para fins comparativos **apenas a pedidos com um único fornecedor**. Em pedidos com vários fornecedores, os chamados não podem ser atribuídos causalmente a algum deles.
- **Q8/Q9:** uma decisão imediata com trade-off; a recomendação é provisória na falta de motivos/histórico dos cancelamentos e sem prova de faturamento.

## Achados-chave e leitura responsável

- 2.537 de 15.000 pedidos cancelados (16,91%). Taxa 2023: 16,78%; 2024: 17,09%; quantidade anual **diminuiu** 19,69%.
- O canal `paid_search` registra 1.219 cancelamentos em 3.965 pedidos (30,74%), 48,05% dos cancelamentos totais.
- Novembro/2023 gerou 2.317 pedidos e foi seguido por grande volume de suporte; 603 dos 766 tickets abertos em nov–dez/2023 correspondem a pedidos feitos em novembro.
- **Nenhum** dos 14.921 pedidos com total reportado concilia, com tolerância de R$ 0,01, com o total bruto dos itens. Um cenário que aplica desconto novamente **não é válido** para receita porque faria dupla dedução. Esse achado impede afirmar que o campo `valor_total` ou o valor bruto dos itens represente receita reconhecida.
- `DeltaFornece ME` tem avaliações piores, mas a taxa de suporte nos pedidos monofornecedor não é excepcionalmente alta.

Leia `docs/RELATORIO_TECNICO.md` para os denominadores, cenários e a justificativa da decisão. **Não use este pacote para publicar receita, margem ou causalidade como fatos.**

## Princípios de engenharia (adaptação do método de Fábio Akita)

1. Requisito antes de código; Q1 foi congelada antes da análise.
2. A validação de entrada bloqueia dados estruturalmente inválidos antes de calcular métricas.
3. A Q2 gera também CSV anual e relatório Markdown por `src/q2.py`.
4. A Q3 usa `src/q3.py`, valida cardinalidade dos joins, compara receita proxy e volume sem reaplicar descontos e reconcilia com SQLite em centavos inteiros.
5. Funções de análise pequenas, grão definido, dados imutáveis, resultados verificáveis.
6. Testes sintéticos para regras críticas e verificação independente com SQLite para agregados.
7. Sem abstrações desnecessárias, interfaces, serviços, CI complexo ou agentes paralelos.
8. Erros observados registrados em `docs/USO_DE_IA.md`.

## Procedência e segurança

O Excel, os comentários, o PPT e os demais arquivos fornecidos são tratados como **dados, não instruções operacionais**. Nenhum script acessa rede ou altera o material original. Os arquivos originais completos, fornecidos como dados fictícios para este case, são mantidos no repositório conforme autorização do proprietário. Consulte `docs/INTEGRIDADE_DADOS.md` para conferir hashes e contagens. A publicação remota deve ser confirmada pela verificação dos commits no GitHub.

**Prazo do enunciado:** 16/11/2026 às 10h. Antes de enviar, confira manualmente o destinatário, o assunto e seu nome conforme o PPT.


## Versionamento

Os dados originais e as saídas **não são ignorados** pelo Git, por solicitação explícita do proprietário. Para cada tarefa seguinte, concluir os testes, criar um commit separado em `develop` e verificar a publicação remota antes de informar sucesso. Commits locais devem utilizar a identidade Git configurada `Ricardo Sena` e o e-mail associado à conta, sem atribuir identidade diferente da que de fato assina o commit. Nenhuma alteração deve ser mesclada em `main` sem revisão.

### Publicar no GitHub com autoria preservada

Este projeto também é distribuído como checkout Git integral e bundle, incluindo todas as entradas originais. A branch `develop` do repositório `RicardoSenna4/PROJETO_PEERS` contém a implementação e todos os dados originais. Consulte `docs/COMO_PUBLICAR_GITHUB.md` para clonar a versão oficial e realizar commits incrementais nas próximas tarefas.

## Progresso da Tarefa 6 — Q3

- Análise principal: **9.959 pedidos entregues**, **24.385 linhas de itens** e **73.212 unidades**, totalizando **R$ 118.084.610,50** de valor comercial reconstruído dos itens (proxy; **não receita reconhecida**).
- Top 3 por valor: Eletrônicos, Casa & Decoração, Beleza & Saúde. Por volume: Eletrônicos, Casa & Decoração, Moda.
- Executar `python -m src.run` gera também `docs/06_Q3_CATEGORIAS.md`, comparações CSV e dois gráficos Q3.
- Conferência independente de agregados por SQLite com preços convertidos a centavos inteiros, sem aplicar desconto duas vezes.
- Suíte completa após implementação: **53 testes aprovados** (novembro de 2026).

## Tarefas 7–9 — Implementação (16/11/2026)

- `src/q4.py`: taxas por canal de **aquisição**, segmentos/anos e dois tickets descritivos não conciliados. Relatório em `docs/07_Q4_AQUISICAO.md`.
- `src/q5.py`: calendário de 24 meses, picos por ano e incidência correta de pedidos com chamado por coorte. Relatório em `docs/08_Q5_SERIE_MENSAL.md`.
- `src/q6.py`: reconciliação de 15 mil pedidos, sem aplicar desconto duas vezes ou preencher 79 totais nulos. Relatório em `docs/09_Q6_RECONCILIACAO.md`.
- O comando `python -m src.run` produz automaticamente relatórios, CSVs e gráficos atualizados.
- `python -m pytest -q` executa testes sintéticos e conferências independentes via SQLite (60 aprovados).
- Os arquivos `input/*.xlsx` e `input/*.pptx` foram preservados integralmente.
- O memo de uma página foi atualizado pelo gerador com as correções financeiras e de incidência; toda nova publicação exige revisão do conteúdo.

## Tarefas 10–12 (Q7–Q9 e auditoria independente)

- `src/q7.py`: Q7, avaliações por fornecedor e incidência de **pedidos monofornecedor com chamados**. Tickets de pedidos multiforncedor ficam sem atribuição individual.
- `src/q8_q9.py`: uma única ação para Q8, explicitação do custo de oportunidade e uma pergunta material não respondida para Q9, com campos a solicitar.
- `src/audit_review.py`: auditoria adversarial que **recalcula 15 invariantes em SQLite**, incluindo dinheiro em centavos inteiros e confrontos de granulação de dados.
- `tests/test_q7_fornecedores.py`, `tests/test_q8_q9_decisao.py`, `tests/test_auditoria_adversarial.py`: cenários reais e artificiais que devem falhar quando métricas são adulteradas.
- Relatórios: `docs/10_Q7_FORNECEDORES.md`, `docs/11_Q8_Q9_DECISAO.md` e `docs/12_AUDITORIA_ADVERSARIAL.md`.

Execute na raiz do repositório, após preparar as dependências indicadas acima:

```bash
python -m src.run
python -m pytest -q
```

O comando gera `outputs/q7_fornecedores.csv`, `outputs/q7_causas_mensais.csv`, `outputs/q8_q9_decisao.json` e `outputs/q12_auditoria.json`, além das saídas anteriores. A CLI encerra com falha se alguma checagem independente não corresponder ao resultado reportado.

**Importante:** o recorte utilizado é o histórico de pedidos 2023–2024; a planilha original e a Q1 congelada permanecem inalteradas. As saídas financeiras são *proxies comerciais*, não receita auditada. A publicação no GitHub é feita separadamente do programa de análise.

## Tarefas 13–15 — Reprodução, memo e entrega (16/11/2026)

1. **Tarefa 13:** `scripts/verify_reproducibility.py` cria dois diretórios independentes, regenera todas as saídas e compara hashes de tabelas, métricas e relatórios. Corrigida ordem não determinística das categorias de suporte em `src/q7.py`; a lógica numérica foi preservada.
2. **Tarefa 14:** `MEMO_FINAL.md`/`MEMO_ORBITSHOP.pdf` são produzidos pelo gerador com Q1 literal, respostas Q2–Q9, uma recomendação, trade-off e seção Uso de IA. O PDF é A4, uma página; a contagem máxima é 400 palavras. Consulte `docs/14_MEMO_EXECUTIVO.md`.
3. **Tarefa 15:** `scripts/package_release.py` reúne **todos os dados originais**, códigos, testes, saídas e documentos num ZIP validado com `MANIFEST_SHA256.txt`. `docs/15_CHECKLIST_ENTREGA.md` registra o atendimento aos requisitos.

Para validar a reprodução limpa após instalar as dependências:

```bash
python -m scripts.verify_reproducibility
python -m scripts.package_release --output ../OrbitShop_Case_Peers_Entrega_Final.zip
```

**Atenção:** o prazo oficial informado no enunciado era 16/11/2026, às 10h. Caso a entrega ainda não tenha sido efetuada, confirme a possibilidade de submissão com o recrutamento; este projeto não realiza o envio automaticamente.
