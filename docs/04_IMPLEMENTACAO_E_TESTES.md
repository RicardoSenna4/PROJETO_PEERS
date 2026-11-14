# Tarefa 4 — Estrutura técnica e testes fundamentais

## Objetivo, escopo e arquitetura

Manter uma análise Python executável por CLI, sem sistemas externos e sem alterar a planilha original. A solução existente foi preservada e ganhou **pré-validação bloqueante**, pois uma auditoria que só relata problemas não deve permitir a execução silenciosa de cálculos sobre chaves inválidas.

| Componente | Responsabilidade |
|---|---|
| `src/workbook.py` | leitura de XLSX/OOXML em memória, sem alterar o arquivo |
| `src/validation.py` | contrato de entrada: abas, campos, IDs únicos, relações, datas, status, números, vínculo cliente/pedido e avaliação/produto |
| `src/data_quality.py` | auditoria explicativa da Tarefa 2 (não bloqueante) |
| `src/analysis.py` | fórmulas operacionais puras, em granularidades definidas |
| `src/run.py` | pipeline CLI, relatórios, CSV e gráficos |
| `tests/` | testes sintéticos, checagens da base real e comparação com SQLite |

A validação bloqueante é chamada por `python -m src.run`, antes de `analyze(data)`. Ela não faz imputação de `valor_total` ou `desconto_aplicado` nulos, não descarta linhas, e não salva modificações no Excel. O domínio de status e a janela 2023–2024 são **contratos específicos deste case**, não uma API genérica para qualquer arquivo.

## Fluxo TDD demonstrado

1. Testes da nova validação foram escritos primeiro.
2. Primeira execução: falha de importação de `src.validation` (módulo ausente) — **RED**.
3. Implementação mínima em `src/validation.py` e ativação em `src/run.py` — **GREEN**.
4. Revisão de mensagens de erro, preservação dos nulos e ausência de dependências extras — **REFACTOR/REVIEW**.

Evidência dos testes adicionados: rejeição de chave primária repetida em cada uma das seis tabelas, referência órfã, status desconhecido, data inválida ou fora do período, quantidade não positiva, preço negativo, desconto fora de `[0, 1]`, campo crítico ausente, cliente inconsistente e produto avaliado que não consta do pedido. Com dados válidos, o relatório de validação deve ser emitido sem modificar a entrada.

## Como reproduzir

```bash
python -m pytest -q tests/test_validation.py
python -m src.run --input input/Base_Dados_OrbitShop_v3.xlsx --output outputs
python -m pytest -q
```

**Limites da etapa:** a pré-validação detecta inconsistências estruturais; não pode comprovar reconhecimento contábil, motivo causal de cancelamento nem responsabilidade de fornecedores. Os campos financeiros seguem as ressalvas em `docs/03_METRICAS_E_ASSUNCOES.md`.
