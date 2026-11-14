# Integridade e inventário dos dados originais

A planilha e a apresentação do case são fictícias, conforme declaração do proprietário. Estão preservadas **integralmente** no caminho `input/`, sem supressão de registros.

| Arquivo | Tamanho (bytes) | SHA-256 |
|---|---:|---|
| `input/Base_Dados_OrbitShop_v3.xlsx` | 2,819,930 | `f400a18e7cc838a201981c8a3ae2234e1a32a385ba1a3b91348f4f7770ca6f4b` |
| `input/Case_OrbitShop_Individual_v2.pptx` | 194,747 | `ed902d4c507dd767c52143c4a528720f24da0b779833fcf78c1a1ca78af8f1f5` |

A base contém seis abas com, respectivamente: `Clientes` 3.000, `Produtos` 200, `Pedidos` 15.000, `Itens_Pedido` 36.740, `Tickets_Suporte` 4.000, `Avaliacoes` 8.000 registros. O arquivo original é a fonte da verdade; os CSVs de saída são derivados e não substituem os registros.

Os valores de SHA-256 acima podem ser recalculados localmente com `sha256sum input/*` (Linux/macOS) ou `Get-FileHash input/* -Algorithm SHA256` (PowerShell).

**Nenhum dado original foi excluído**. Arquivos temporários de cache e instalações locais (`.venv`, `__pycache__`, `.pytest_cache`) permanecem fora do Git.
