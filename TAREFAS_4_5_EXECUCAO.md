# Tarefas 4 e 5 — Registro de execução

**Projeto:** Case OrbitShop / Peers Consulting

## Tarefa 4 — Estrutura técnica e testes fundamentais

- Preservada a implementação existente em Python com leitor OOXML, CLI, métricas e testes.
- Novo módulo `src/validation.py` aplicado antes dos cálculos, sem modificar dados brutos.
- Valida abas e campos essenciais, IDs sem duplicatas, chaves estrangeiras, relacionamentos cliente/pedido, avaliações pertencentes a produtos comprados, quantidade/preço/desconto, status e datas de pedidos.
- Mantém nulos em `Pedidos.valor_total` e `Itens_Pedido.desconto_aplicado` sem imputação.
- Adicionados testes unitários sintéticos para entradas válidas e negativas (`tests/test_validation.py`).
- Red→Green: o módulo faltava durante a primeira execução dos novos testes; os testes foram reexecutados após a implementação e passaram.
- Documentação: `docs/04_IMPLEMENTACAO_E_TESTES.md`.

## Tarefa 5 — Q2: status dos pedidos

| Status | Pedidos | Proporção |
|---|---:|---:|
| Entregue | 9.959 | 66,39% |
| Cancelado | 2.537 | 16,91% |
| Em trânsito | 1.371 | 9,14% |
| Devolvido | 1.133 | 7,55% |
| **Total** | **15.000** | **100% (arred.)** |

| Coorte de compra | Pedidos | Cancelados | Taxa |
|---|---:|---:|---:|
| 2023 | 8.386 | 1.407 | 16,78% |
| 2024 | 6.614 | 1.130 | 17,09% |

- O **número** de cancelamentos caiu **19,69%**, mas a **taxa** subiu **0,31 ponto percentual**. Não confirma as falas atribuídas a Growth e CFO para esse mesmo universo/critério.
- Como não há histórico de status, comparações anuais representam **coortes de data do pedido**, não eventos de cancelamento ocorridos em cada ano.
- A função `status_metrics` agora verifica IDs únicos, status aceitos e a janela temporal do case.
- Gerados `outputs/q2_status.csv`, `outputs/q2_por_ano.csv`, `outputs/q2_status.png` e `docs/05_Q2_DISTRIBUICAO_STATUS.md`.
- Testes incluem comparação com SQLite (contagem independente) e execução real da CLI em pasta temporária, verificando CSVs e assinatura do PNG.

## Verificação

```bash
python -m src.run --input input/Base_Dados_OrbitShop_v3.xlsx --output outputs
python -m pytest -q
```

**Resultado real:** 46 testes aprovados. Planilha e Q1 preservadas:

```text
SHA-256 Base_Dados_OrbitShop_v3.xlsx:
f400a18e7cc838a201981c8a3ae2234e1a32a385ba1a3b91348f4f7770ca6f4b
SHA-256 Q1_CONGELADA_PRE_ANALISE.md:
6eb8e615d55e6dfad8c007093f21a0786ee7c5e8be2239ffa913b15f22c53ae8
```

## Publicação / Git

Foram preparados commits locais com autoria `Ricardo Sena` conforme solicitado. O repositório remoto `RicardoSenna4/PROJETO_PEERS` não foi modificado nesta execução: o conector do GitHub não permite fixar explicitamente a autoria do commit; seria incorreto afirmar que conseguirá registrar exatamente o nome solicitado. A base de clientes foi excluída do histórico versionado público por segurança. Um `git bundle` separado carrega as revisões locais e pode ser enviado com o Git autenticado do usuário.


## Atualização de preservação integral

Por solicitação expressa do proprietário, o repositório agora preserva o Excel, o PPT e **todos os resultados derivados**, sem exclusões de origem. Ver `docs/INTEGRIDADE_DADOS.md`. O texto acima descreve a política anterior; esta seção registra a substituição dessa política.
