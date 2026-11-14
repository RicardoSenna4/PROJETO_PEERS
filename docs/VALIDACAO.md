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
