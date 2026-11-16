# Tarefas 2 e 3 — Pacote executado

**Tarefa 2:** auditoria exploratória completa da base, sem modificá-la. 6 tabelas, integridade referencial, campos faltantes, domínios, datas, preço praticado/desconto, reconciliação preliminar e grão de joins.

**Tarefa 3:** contrato de métricas para Q2–Q9, com fórmulas, denominadores, recortes, exceções, nulos, precisão, limitação de causalidade e critérios de aceitação.

## Arquivos principais

- `docs/02_AUDITORIA_DADOS.md` — resultados da auditoria e riscos.
- `docs/03_METRICAS_E_ASSUNCOES.md` — contrato de métricas atualizado.
- `outputs/auditoria_qualidade.json` — inventário completo e evidências verificadas.
- `outputs/dicionario_dados.csv` — dicionário observado por campo, tipos, ausentes e cardinalidades.
- `src/data_quality.py` — funções puras da auditoria.
- `scripts/run_data_audit.py` — comando de execução para reproduzir relatórios.
- `tests/test_data_quality.py` — sete novos testes de qualidade e regressão.

## Executar no projeto completo

```bash
python -m scripts.run_data_audit
python -m pytest -q
```

A origem deve estar em `input/Base_Dados_OrbitShop_v3.xlsx`. O script lê o arquivo e escreve apenas sob `outputs/` e `docs/`.

## Limite técnico importante

Descobriu-se que `preco_praticado` já reflete `desconto_aplicado` nos 36.439 itens com desconto informado (tolerância de R$ 0,01). **Não aplique o desconto novamente.** A antiga implementação de Q6 inclui colunas de simulação de desconto adicional; essas colunas não devem ser interpretadas como receita ou valor líquido. Para métricas novas, use `quantidade × preco_praticado` como **valor comercial de linhas**, não faturamento contábil.

O XLSX original, a Q1 congelada e os demais entregáveis anteriores não foram sobrescritos.
