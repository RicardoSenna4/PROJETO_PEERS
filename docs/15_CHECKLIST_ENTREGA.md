# Tarefa 15 — Checklist de entrega final

## Requisitos oficiais

| Exigência | Evidência | Estado |
|---|---|---|
| Q1 no topo, exatamente três perguntas anteriores à base | `Q1_CONGELADA_PRE_ANALISE.md`, `MEMO_FINAL.md` | OK |
| Q2: distribuição por status, tabela e gráfico | `outputs/q2_status.csv`, `outputs/q2_status.png` | OK |
| Q3: valor comercial dos itens e volume por categoria | `outputs/q3_comparacao_entregues.csv`, `outputs/q3_ranking_volume.csv` | OK |
| Q4: aquisição, cancelamentos, ticket médio | `outputs/q4_canais.csv`, `docs/07_Q4_AQUISICAO.md` | OK |
| Q5: evolução mensal de 2023/2024 e hipóteses | `outputs/q5_mensal.csv`, `docs/08_Q5_SERIE_MENSAL.md` | OK |
| Q6: totais do pedido × itens | `outputs/q6_reconciliacao_pedido.csv`, `docs/09_Q6_RECONCILIACAO.md` | OK; não conciliados |
| Q7: fornecedor, avaliações e suporte | `outputs/q7_fornecedores.csv`, `docs/10_Q7_FORNECEDORES.md` | OK com atribuição limitada |
| Q8: uma decisão e trade-off | `docs/11_Q8_Q9_DECISAO.md` | OK |
| Q9: lacuna de dados e informação adicional necessária | `docs/11_Q8_Q9_DECISAO.md` | OK |
| Memo em uma página, até 400 palavras, seção Uso de IA | `MEMO_ORBITSHOP.pdf`, `MEMO_FINAL.md` | OK |
| Código/README para reprodução | `src/`, `scripts/`, `tests/`, `README.md` | OK |
| Fontes originais intactas | `input/`, hashes SHA-256 e teste automatizado | OK |
| Testes e auditoria independentes | `pytest`, `src/audit_review.py`, `scripts/verify_reproducibility.py` | OK |
| ZIP com manifesto SHA-256 | `scripts/package_release.py` | OK |
| Autoria e versionamento | Histórico de commits em `develop` | Verificar no remoto |

## Interpretação financeira

O case contém inconsistências sistêmicas entre `Pedidos.valor_total` e a soma de `Itens_Pedido` com `preco_praticado`. Nenhum dos 14.921 pedidos com total informado reconciliou a ±R$ 0,01. **Não apresentar os agregados como receita auditada.** O valor dos itens é proxy comercial do pedido, não faturamento reconhecido.

## Execução mínima de um avaliador

```bash
python -m pip install -r requirements.txt
python -m src.run
python -m pytest -q
python scripts/build_deliverables.py
python -m scripts.verify_reproducibility
```

Para produzir o ZIP de submissão:

```bash
python -m scripts.package_release --output ../OrbitShop_Case_Peers_Entrega_Final.zip
```

## Submissão

O enunciado pede envio a **recrutamento@peers.com.br**, com assunto contendo `[CASE-ORBITSHOP]` e nome do candidato, em ZIP ou link GitHub/Drive. **Nenhum e-mail é enviado pelo código.** Confirme destinatário, permissões do link e se o recrutador ainda aceita envio: o prazo original informado era **16/11/2026 às 10h**, já ultrapassado na data desta conclusão.

## Riscos que não foram eliminados

- Não há motivo, timestamp e trilha de eventos de cancelamentos por pedido.
- Não há ledger/contabilidade ou explicações de divergências de valores para receita.
- Tickets de pedidos multifornecedor não identificam o fornecedor responsável.
- Hipóteses sobre promoções e picos de pedidos não estão comprovadas por calendário comercial.
- A revisão final do candidato continua necessária antes da submissão.
