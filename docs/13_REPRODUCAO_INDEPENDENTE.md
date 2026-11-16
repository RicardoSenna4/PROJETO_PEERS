# Tarefa 13 — Refatoração, consistência e reprodução independente

## Intervenção justificada

A comparação de duas execuções isoladas revelou divergências nos bytes de `outputs/metricas.json` e `docs/RELATORIO_TECNICO.md`, apesar de todos os valores numéricos permanecerem corretos. A origem foi a iteração sobre um `set` de causas de chamados em `src/q7.py`, cujo ordenamento variava com o hash de cada processo Python.

**Correção:** construir o `Counter` do trimestre e serializar as categorias em ordem lexical. A agregação financeira, a atribuição de tickets e os indicadores de negócio não foram alterados. Um teste sintético garante ordem determinística.

## Procedimento de verificação

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python -m scripts.verify_reproducibility
```

O verificador cria **duas cópias limpas temporárias**, cada uma contendo entradas originais, código, testes e dependências declaradas, mas sem `outputs/` preexistentes; em ambas executa análise e gerador de memo. A suíte automatizada é executada separadamente com `python -m pytest -q`; a opção `--with-tests` permite solicitá-la também no primeiro workspace quando o ambiente suporta essa combinação. Em seguida compara os hashes SHA-256 de CSVs, JSONs, relatórios e memo Markdown, verifica Q1 integral, total de pedidos, limite de palavras, PDF com uma página e imutabilidade das fontes. Não compara bytes do PDF porque metadados internos podem variar entre execuções.

A reprodução local usa as bibliotecas Python instaladas no ambiente, **não cria um sistema operacional ou interpretador totalmente isolado**. O GitHub Actions valida uma instalação limpa de dependências no runner.

## Escopo dos riscos remanescentes

- Reconciliação Q6 não comprova receita reconhecida.
- Correlação de cancelamento em `paid_search` não é causalidade.
- A maior parte dos chamados é de pedidos multifornecedor, sem atribuição de culpa a um fornecedor.
- O relatório é análise de base histórica, não uma validação de sistemas de produção.
