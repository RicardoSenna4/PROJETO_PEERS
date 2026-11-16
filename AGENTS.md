# AGENTS.md — Regras do agente para OrbitShop

## Missão e limites

Resolver Q1–Q9 do case Peers/OrbitShop, com código reprodutível e memo de 1 página/400 palavras. Aplicar o espírito de Akita (pequenas entregas, critérios verificáveis, testes críticos, revisão contínua) **sem transferir para o case a complexidade de projetos de produção**.

## Instruções na abertura da sessão

1. Ler `README.md`, `MANUS_PROJECT_INSTRUCTIONS.md`, `docs/00_ESCOPOS_E_FONTE_DA_VERDADE.md` e o documento da fase atual.
2. Preservar Q1 já redigida em `docs/01_Q1_CONGELADA.md`; ela deve estar no topo do memo.
3. Confirmar existência, tamanho e nomes das abas dos arquivos em `input/`. Se houver arquivo inacessível, reportar; **não simular leitura**.
4. Antes de cada fase: declarar objetivo, entrada, saída, teste de aceitação e o que não será feito.

## Não negociáveis

- Enunciado PPT > dados originais > decisões metodológicas documentadas > hipóteses do agente.
- Números de relatório devem ter origem em código executado. Nenhum número na versão final sem fórmula, denominador, filtros e fonte de entrada.
- `data/` é imutável; nenhum preenchimento silencioso de nulos e nenhum `dropna` genérico.
- Chaves: `Pedidos.cliente_id → Clientes.id`; `Itens_Pedido.pedido_id → Pedidos.id`; `Itens_Pedido.produto_id → Produtos.id`; `Avaliacoes` liga pedido, produto e cliente; `Tickets_Suporte` liga pedido e cliente.
- Ao adicionar dimensão/lookup, provar que o número de linhas no grão original não aumentou indevidamente.
- Separar **receita/GMV estimado**, **valor registrado em Pedidos** e **receita reconhecida**. A base pode não comprovar esta última.
- Distinguir número absoluto, taxa, variação absoluta em pontos percentuais e variação relativa.
- Fornecedor associado a pedido não implica ser causa do chamado. Não atribuir ticket multifornnecedor automaticamente.
- Todas as hipóteses explicativas precisam estar rotuladas **hipótese não comprovada** quando não existe dado causal.
- Status atual por pedido não equivale a histórico de alterações de status; não inferir a data do cancelamento a partir de `data_pedido`.
- Não inventar “erros da IA” para preencher a seção obrigatória. Registrar problemas observados e correções concretas; se não ocorrerem, dizer isso.
- Não alterar testes para fazê-los passar. Não afirmar que testes passaram sem execução.

## Implementação sugerida

- Python, pandas, pytest, matplotlib; leitura Excel por biblioteca adequada.
- Script CLI reproduzível (`python -m src.orbitshop...` ou equivalente) **e README com comando testado**.
- Funções com responsabilidades pequenas: carregar, validar, derivar, agregar, plotar.
- Decimais monetários: não arredondar durante agregações; comparar tolerância documentada (por exemplo, R$ 0,01 após regra explícita de arredondamento).
- Uma fonte de verdade para definição de cada métrica, testes independentes com dados sintéticos e amostras reais documentadas.
- Não usar infra, microsserviços, CI complexo nem agentes paralelos para um case individual, salvo justificativa mensurável.

## Checkpoint de cada fase

Relatar:

```text
FASE / OBJETIVO:
ARQUIVOS CRIADOS OU MODIFICADOS:
EVIDÊNCIAS E RESULTADOS:
TESTES EXECUTADOS (com resultado):
RESSALVAS / HIPÓTESES:
PRÓXIMO PASSO:
```

## Parada segura

Se houver divergência financeira, semântica de desconto não comprovada, contradição do enunciado, arquivos indisponíveis ou fragilidade de joins, **não mascarar o problema**. Produzir análise de sensibilidade e documentação de limites; pedir uma decisão humana apenas quando a escolha for material e não puder ser determinada pelo enunciado.

## Política de preservação e versionamento

- **Não excluir, anonimizar, resumir, filtrar ou reescrever o Excel/PPT originais.** O usuário confirmou que os dados são fictícios e autorizou o versionamento integral.
- Manter `input/Base_Dados_OrbitShop_v3.xlsx` e `input/Case_OrbitShop_Individual_v2.pptx` em todos os pacotes e no histórico Git.
- A cada nova tarefa: executar testes pertinentes, registrar diff, gerar um commit específico em `develop` e verificar push remoto. Não declarar publicado sem consultar o commit no GitHub.
- Autor dos commits locais: `Ricardo Sena`, com e-mail associado à conta GitHub. Atribuição da autoria pela integração remota só pode ser declarada após verificação do metadado retornado pelo GitHub.
- Não alterar `main` sem revisão do proprietário.
