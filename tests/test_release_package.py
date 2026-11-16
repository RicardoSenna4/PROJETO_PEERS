"""Teste de empacotamento: arquivo íntegro e nenhuma remoção dos dados originais."""
from pathlib import Path
from zipfile import ZipFile

from scripts.package_release import package, paths_for_release

ROOT = Path(__file__).resolve().parents[1]


def test_package_keeps_unaltered_inputs_and_artifacts(tmp_path):
    path = tmp_path / 'case.zip'
    report = package(ROOT, path)
    assert report['data_preserved'] and report['files'] >= 60
    with ZipFile(path) as archive:
        assert archive.read('OrbitShop_PEERS/input/Base_Dados_OrbitShop_v3.xlsx') == (ROOT/'input/Base_Dados_OrbitShop_v3.xlsx').read_bytes()
        assert archive.read('OrbitShop_PEERS/input/Case_OrbitShop_Individual_v2.pptx') == (ROOT/'input/Case_OrbitShop_Individual_v2.pptx').read_bytes()
        assert 'OrbitShop_PEERS/MEMO_ORBITSHOP.pdf' in archive.namelist()
        assert 'OrbitShop_PEERS/outputs/q2_status.png' in archive.namelist()


def test_no_cached_files_in_release():
    paths = [str(p.relative_to(ROOT)) for p in paths_for_release(ROOT)]
    assert not any('__pycache__' in p or '.pytest_cache' in p for p in paths)
    assert len(paths) == len(set(paths))
