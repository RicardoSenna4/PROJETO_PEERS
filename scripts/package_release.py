"""Cria ZIP de entrega com todos os dados originais e código reprodutível."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = ('input', 'src', 'tests', 'scripts', 'docs', 'outputs', '.github')
ROOT_FILES = ('README.md', 'AGENTS.md', 'requirements.txt', '.gitignore',
              'Q1_CONGELADA_PRE_ANALISE.md', 'MEMO_FINAL.md', 'MEMO_ORBITSHOP.pdf',
              'TAREFAS_2_3_EXECUCAO.md', 'TAREFAS_4_5_EXECUCAO.md')
EXCLUDE_DIRS = {'.git', '__pycache__', '.pytest_cache', '.venv', '_render_final', '_memo_render', '_pdf_check'}
EXCLUDE_SUFFIXES = ('.pyc', '.pyo', '.swp')
REQUIRED = (
    'input/Base_Dados_OrbitShop_v3.xlsx', 'input/Case_OrbitShop_Individual_v2.pptx',
    'Q1_CONGELADA_PRE_ANALISE.md', 'MEMO_FINAL.md', 'MEMO_ORBITSHOP.pdf',
    'src/run.py', 'src/audit_review.py', 'scripts/verify_reproducibility.py',
    'outputs/q2_status.csv', 'outputs/q2_status.png',
    'outputs/q6_reconciliacao_pedido.csv', 'docs/RELATORIO_TECNICO.md',
)


def paths_for_release(root: Path) -> list[Path]:
    files: list[Path] = []
    for name in ROOT_FILES:
        path = root / name
        if path.exists():
            files.append(path)
    for section in FOLDERS:
        folder = root / section
        if not folder.exists():
            continue
        for path in folder.rglob('*'):
            if path.is_file() and not any(p in EXCLUDE_DIRS for p in path.relative_to(root).parts) \
                    and path.suffix not in EXCLUDE_SUFFIXES:
                files.append(path)
    files = sorted(set(files), key=lambda f: f.relative_to(root).as_posix())
    present = {p.relative_to(root).as_posix() for p in files}
    missing = set(REQUIRED) - present
    if missing:
        raise FileNotFoundError(f'Arquivos exigidos não encontrados: {sorted(missing)}')
    return files


def package(root: Path, dest: Path) -> dict:
    files = paths_for_release(root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    manifest_lines = []
    with zipfile.ZipFile(dest, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=7) as archive:
        for path in files:
            relpath = path.relative_to(root).as_posix()
            data = path.read_bytes()
            manifest_lines.append(f'{hashlib.sha256(data).hexdigest()}  {relpath}')
            archive.writestr('OrbitShop_PEERS/' + relpath, data)
        archive.writestr('OrbitShop_PEERS/MANIFEST_SHA256.txt', '\n'.join(manifest_lines) + '\n')
    with zipfile.ZipFile(dest, 'r') as archive:
        if archive.testzip() is not None:
            raise AssertionError('ZIP inválido')
        names = set(archive.namelist())
        if any('OrbitShop_PEERS/' + item not in names for item in REQUIRED):
            raise AssertionError('ZIP não contém todos os arquivos obrigatórios')
        content = archive.read('OrbitShop_PEERS/MANIFEST_SHA256.txt').decode('utf-8')
        for line in content.splitlines():
            expected, rel = line.split('  ', 1)
            got = hashlib.sha256(archive.read('OrbitShop_PEERS/' + rel)).hexdigest()
            if expected != got:
                raise AssertionError(f'Falha de integridade: {rel}')
    return {'archive': str(dest), 'files': len(files), 'size_bytes': dest.stat().st_size,
            'data_preserved': True, 'manifest_entries': len(manifest_lines)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, default=ROOT.parent / 'OrbitShop_Case_Peers_Entrega_Final.zip')
    args = parser.parse_args()
    result = package(args.root.resolve(), args.output.resolve())
    print(result)


if __name__ == '__main__':
    main()
