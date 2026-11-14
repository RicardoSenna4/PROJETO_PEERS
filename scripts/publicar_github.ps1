# Execute no PowerShell, dentro da pasta raiz do projeto, com Git autenticado na conta RicardoSenna4.
param([string]$Repository = 'https://github.com/RicardoSenna4/PROJETO_PEERS.git')
$ErrorActionPreference = 'Stop'
$branch = (git branch --show-current).Trim()
if ($LASTEXITCODE -ne 0 -or $branch -ne 'develop') { throw 'Abra a raiz do repositorio e selecione a branch develop antes de publicar.' }
if ((git status --porcelain).Length -gt 0) { throw 'Existem alteracoes pendentes. Revise e faca commit antes de publicar.' }
$existing = git remote get-url origin 2>$null
if ($LASTEXITCODE -eq 0) {
    if ($existing.Trim() -ne $Repository) { throw "O remote origin aponta para $existing e nao para $Repository" }
} else {
    git remote add origin $Repository
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao adicionar origin' }
}
$remoteHeads = git ls-remote --heads origin
if ($LASTEXITCODE -ne 0) { throw 'Nao foi possivel consultar origin. Verifique conexao e autenticacao do GitHub.' }
if ($remoteHeads) { throw 'O repositorio remoto ja contem commits. Confira e integre historicos antes de fazer push; nenhuma alteracao remota foi feita.' }
git push -u origin main develop
if ($LASTEXITCODE -ne 0) { throw 'O push falhou. Confira a mensagem anterior; os commits locais permanecem preservados.' }
Write-Host 'Publicacao concluida. Verifique os commits no GitHub:'
Write-Host 'https://github.com/RicardoSenna4/PROJETO_PEERS/commits/develop/'
