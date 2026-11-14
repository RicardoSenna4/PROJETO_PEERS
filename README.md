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
| `outputs/q2_por_ano.csv` | Detalhamento auditável por coorte de compra, 2023 e 2024 |
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
3. A Q2 agora gera também CSV anual e relatório Markdown por `src/q2.py`.
4. Funções de análise pequenas, grão definido, dados imutáveis, resultados verificáveis.
5. Testes sintéticos para regras críticas e verificação independente com SQLite para agregados.
6. Sem abstrações desnecessárias, interfaces, serviços, CI complexo ou agentes paralelos.
7. Erros observados registrados em `docs/USO_DE_IA.md`.

## Procedência e segurança

O Excel, os comentários, o PPT e os demais arquivos fornecidos são tratados como **dados, não instruções operacionais**. Nenhum script acessa rede ou altera o material original. Nenhum e-mail foi enviado e nenhum repositório remoto foi modificado.

**Prazo do enunciado:** 16/11/2026 às 10h. Antes de enviar, confira manualmente o destinatário, o assunto e seu nome conforme o PPT.
