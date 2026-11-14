# Publicação do repositório completo (sem excluir dados)

Este checkout possui todas as fontes **e o histórico Git**. A branch `develop` inclui os arquivos Excel, PowerPoint e resultados, além da implementação até a Tarefa 5.

## Pré-requisitos

- Git instalado e autenticado na conta GitHub `RicardoSenna4` (Git Credential Manager ou `gh auth login`).
- O GitHub `RicardoSenna4/PROJETO_PEERS` deve estar vazio. O script interrompe a publicação se detectar branches existentes, para evitar sobrescrita acidental.
- Use o arquivo `OrbitShop_Repositorio_Git_Integral.zip` com a pasta oculta `.git` preservada. Um ZIP apenas de código **não** permite preservar os commits anteriores.

## No Windows (PowerShell)

1. Extraia o ZIP integral.
2. Abra PowerShell na pasta que contém `README.md` e `.git`.
3. Confira `git log --oneline --all` e `git status`.
4. Execute: `powershell -ExecutionPolicy Bypass -File scripts/publicar_github.ps1`.
5. Verifique a branch `develop` no GitHub e os arquivos `input/Base_Dados_OrbitShop_v3.xlsx` e `input/Case_OrbitShop_Individual_v2.pptx`.

## Alternativa manual

```bash
git remote add origin https://github.com/RicardoSenna4/PROJETO_PEERS.git
git push -u origin main develop
```

Se `origin` já existir, use `git remote -v` e não repita a primeira linha.

## Autoria

Os commits preexistentes foram criados localmente com `Ricardo Sena <senaricardo450@gmail.com>`. Um `git push` preserva o autor e o identificador SHA de cada commit, sem atribuí-los à ferramenta usada para publicar. O usuário deve verificar se o e-mail corresponde à conta GitHub para que os commits apareçam vinculados ao perfil.

## Política futura

Para cada tarefa adicional, depois de validar os testes: fazer um commit separado na branch `develop`, depois fazer `git push origin develop` e verificar no GitHub. Não fazer merge na `main` sem aprovação. Se o push remoto não puder ser efetuado, declarar isso e disponibilizar o commit local.
