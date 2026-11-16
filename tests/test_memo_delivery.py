"""Critérios objetivos do memo exigido pelo enunciado (Q1 no topo; 1 pág.; ≤400 palavras)."""
from pathlib import Path
import re
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]


def text_and_words():
    memo = (ROOT / 'MEMO_FINAL.md').read_text(encoding='utf-8').split('<!--', 1)[0]
    words = re.findall(r'\b[\wÀ-ÿ][\wÀ-ÿ.,–%/-]*\b', re.sub(r'\*|`|#', '', memo))
    return memo, len(words)


def test_memo_is_one_a4_page_with_at_most_400_words():
    _, n = text_and_words()
    assert n <= 400
    pages = PdfReader(str(ROOT / 'MEMO_ORBITSHOP.pdf')).pages
    assert len(pages) == 1
    assert abs(float(pages[0].mediabox.width) - 595.28) < 1
    assert abs(float(pages[0].mediabox.height) - 841.89) < 1


def test_q1_questions_preserved_verbatim_and_before_data():
    memo, _ = text_and_words()
    original = (ROOT / 'Q1_CONGELADA_PRE_ANALISE.md').read_text(encoding='utf-8')
    lines = [line for line in original.splitlines() if re.match(r'^\d\. \*\*', line)]
    assert len(lines) == 3
    assert all(line in memo for line in lines)
    assert memo.index('**Q1') < memo.index('**Q2')


def test_all_questions_one_action_and_ai_disclosure():
    memo, _ = text_and_words()
    assert all(f'**Q{i} —' in memo for i in range(1,10) if i != 1)
    assert '**Uso de IA.**' in memo
    assert 'ChatGPT' in memo
    assert 'R$ 38,42 mi' in memo and 'R$ 175,86 mi' in memo
    assert 'não' in memo.lower()
    assert 'Suspender apenas a expansão' in memo
