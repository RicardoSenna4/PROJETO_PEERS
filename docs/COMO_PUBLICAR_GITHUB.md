# Fluxo de versionamento — GitHub OrbitShop

**Repositório remoto oficial:** https://github.com/RicardoSenna4/PROJETO_PEERS

**Branch de trabalho:** `develop`. A branch `main` fica protegida contra alterações sem revisão.

O projeto completo até a Tarefa 5 foi publicado na branch `develop`, incluindo os arquivos binários de entrada, os resultados completos, scripts, testes e documentação. A versão publicada foi validada com uma árvore de Git idêntica à do checkout local anterior à atualização deste guia.

## Para continuar o trabalho no computador

Primeiro, **clone o repositório remoto**, pois ele agora contém os commits oficiais. Não use o ZIP/bundle local antigo para sobrescrever o histórico remoto: ele tem commits equivalentes em conteúdo, mas com identificadores de commit diferentes.

```powershell
git clone --branch develop https://github.com/RicardoSenna4/PROJETO_PEERS.git
cd PROJETO_PEERS
git config user.name "Ricardo Sena"
git config user.email "116093383+RicardoSenna4@users.noreply.github.com"
python -m pip install -r requirements.txt
python -m pytest -q
```

Depois de cada tarefa:

```powershell
git status
git add -A
git commit -m "feat: descricao objetiva da tarefa"
powershell -ExecutionPolicy Bypass -File scripts/publicar_github.ps1
```

O script consulta `origin/develop`, recusa histórico divergente e não usa `--force`. Ele não altera `main`.

## Autoria e rastreabilidade

A publicação remota pela conexão GitHub foi verificada com autor e committer `Ricardo Sena` e conta `RicardoSenna4`. Para os próximos commits locais, utilize a identidade Git acima. Não declare um commit publicado antes de verificar a URL no GitHub. As mensagens de commit descrevem o código ou documento alterado, não a ferramenta utilizada.

## Preservação de dados

Não remover, anonimizar, truncar ou substituir o arquivo `input/Base_Dados_OrbitShop_v3.xlsx`, nem o PowerPoint original. A base é fictícia conforme declaração do proprietário. Confira os hashes de integridade em `docs/INTEGRIDADE_DADOS.md`.
