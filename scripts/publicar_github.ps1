# Execute no PowerShell a partir de um CLONE do repositorio remoto oficial, na branch develop.
param([string]$Repository = 'https://github.com/RicardoSenna4/PROJETO_PEERS.git')
$ErrorActionPreference = 'Stop'
$branch = (git branch --show-current).Trim()
if ($LASTEXITCODE -ne 0 -or $branch -ne 'develop') { throw 'Abra a raiz do clone Git e selecione a branch develop.' }
if ((git status --porcelain).Length -gt 0) { throw 'Ha alteracoes nao commitadas. Revise, teste e faca commit antes do push.' }
$existing = git remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0 -or $existing.Trim() -ne $Repository) { throw "origin deve apontar para $Repository. Confira git remote -v." }
git fetch origin develop
if ($LASTEXITCODE -ne 0) { throw 'Falha ao consultar o GitHub. Verifique conexao e autenticacao.' }
git merge-base --is-ancestor origin/develop HEAD
if ($LASTEXITCODE -ne 0) { throw 'Histories divergentes; nao foi efetuado push. Crie um novo clone do GitHub ou resolva manualmente.' }
git push -u origin develop
if ($LASTEXITCODE -ne 0) { throw 'O push falhou. Os commits locais continuam preservados.' }
Write-Host 'Push confirmado. Consulte os commits em https://github.com/RicardoSenna4/PROJETO_PEERS/commits/develop'
