"""Verifica reprodução de ponta a ponta em dois workspaces descartáveis.

Não altera os dados originais nem depende de saídas anteriores existentes.
Executa análise+memo em duas cópias limpas e compara artefatos textuais.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
INPUTS = (
    "input/Base_Dados_OrbitShop_v3.xlsx",
    "input/Case_OrbitShop_Individual_v2.pptx",
    "Q1_CONGELADA_PRE_ANALISE.md",
)
SOURCE_PARTS = ("input", "src", "scripts", "tests")


def sha256(path: Path) -> str:
    """SHA-256 de um arquivo sem carregar seu conteúdo inteiro na memória."""
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def export_inventory(root: Path) -> dict[str, str]:
    """Inventário dos resultados textuais reproduzíveis."""
    candidates = list((root / "outputs").rglob("*.csv"))
    candidates += list((root / "outputs").rglob("*.json"))
    candidates += list((root / "docs").glob("0*_Q*.md"))
    candidates += [root / "docs/RELATORIO_TECNICO.md", root / "MEMO_FINAL.md"]
    return {p.relative_to(root).as_posix(): sha256(p) for p in sorted(candidates) if p.is_file()}


def copy_fresh(src: Path, dst: Path) -> None:
    for part in SOURCE_PARTS:
        shutil.copytree(src / part, dst / part,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"))
    shutil.copy2(src / "Q1_CONGELADA_PRE_ANALISE.md", dst / "Q1_CONGELADA_PRE_ANALISE.md")
    shutil.copy2(src / "requirements.txt", dst / "requirements.txt")


def execute(src: Path, workspace: Path, *, with_tests: bool = False) -> dict:
    copy_fresh(src, workspace)
    def run(*args: str) -> None:
        subprocess.run([sys.executable, *args], cwd=workspace, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                       env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    run("-m", "src.run")
    run("scripts/build_deliverables.py")
    if with_tests:
        run("-m", "pytest", "-q")
    pdf = workspace / "MEMO_ORBITSHOP.pdf"
    pages = len(PdfReader(str(pdf)).pages)
    if pages != 1:
        raise AssertionError(f"Memo deve ter uma página: {pages}")
    memo = (workspace / "MEMO_FINAL.md").read_text(encoding="utf-8")
    # Mesma regex usada no gerador, desconsiderando a anotação de contagem.
    body = memo.split("<!--", 1)[0]
    words = re.findall(r"\b[\wÀ-ÿ][\wÀ-ÿ.,–%/-]*\b", re.sub(r"\*|`|#", "", body))
    if len(words) > 400:
        raise AssertionError(f"Memo excedeu 400 palavras: {len(words)}")
    q1 = (workspace / "Q1_CONGELADA_PRE_ANALISE.md").read_text(encoding="utf-8")
    for key in ("**Camila:**", "**Rogério:**", "**Ambos:**"):
        original = next((line.split("**", 2)[-1].strip() for line in q1.splitlines() if key in line), None)
        if original is None or original not in body:
            raise AssertionError(f"Q1 não preservada: {key}")
    metrics = json.loads((workspace / "outputs/metricas.json").read_text(encoding="utf-8"))
    if metrics["Q2"]["n"] != 15000:
        raise AssertionError("Total de pedidos inesperado")
    return {"pages": pages, "words": len(words), "outputs": export_inventory(workspace)}


def verify(source: Path, *, run_tests: bool = False) -> dict:
    originals = {part: sha256(source / part) for part in INPUTS}
    with TemporaryDirectory(prefix="orbitshop_repro_") as temp:
        tempdir = Path(temp)
        # Primeiro reproduzir ambos os processos sem interferência da suíte; depois
        # executar os testes no primeiro workspace, já regenerado.
        first = execute(source, tempdir / "run_a")
        second = execute(source, tempdir / "run_b")
        if first["outputs"] != second["outputs"]:
            a = first["outputs"]; b = second["outputs"]
            mismatch = sorted(k for k in a.keys() | b.keys() if a.get(k) != b.get(k))
            raise AssertionError(f"Resultados não reproduzíveis: {mismatch}")
        if run_tests:
            subprocess.run([sys.executable, '-m', 'pytest', '-q'], cwd=tempdir / 'run_a',
                           check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if originals != {part: sha256(source / part) for part in INPUTS}:
            raise AssertionError("Arquivos originais foram alterados")
    return {"inputs_sha256": originals, "output_files_identical": len(first["outputs"]),
            "tests_in_clean_workspace": run_tests, "memo_pages": first["pages"],
            "memo_words": first["words"], "reproducible": True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT)
    parser.add_argument("--with-tests", action="store_true", help="também executa pytest no primeiro workspace")
    args = parser.parse_args()
    result = verify(args.source.resolve(), run_tests=args.with_tests)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
