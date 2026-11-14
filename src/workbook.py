"""Leitor de XLSX de dados (OOXML) usando apenas a biblioteca padrão.

Leitura sem escrita/alteração da planilha. Suporta os tipos usados na base OrbitShop.
Para XLSX fora deste esquema, use um leitor Excel geral.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import ZipFile
import re

M = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
P = '{http://schemas.openxmlformats.org/package/2006/relationships}'


def _col_index(addr: str) -> int:
    chars = re.match(r'[A-Z]+',addr.upper()).group(0)
    n = 0
    for c in chars: n = n * 26 + ord(c) - 64
    return n - 1


def _shared(z: ZipFile) -> list[str]:
    if 'xl/sharedStrings.xml' not in z.namelist(): return []
    root = ET.fromstring(z.read('xl/sharedStrings.xml'))
    return [''.join(t.text or '' for t in si.iter(M+'t')) for si in root.findall(M+'si')]


def _sheets(z: ZipFile) -> dict[str,str]:
    workbook = ET.fromstring(z.read('xl/workbook.xml'))
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    mapping = {r.attrib['Id']:r.attrib['Target'] for r in rels.findall(P+'Relationship')}
    result = {}
    for s in workbook.findall('.//'+M+'sheet'):
        target=mapping[s.attrib[R+'id']].lstrip('/')
        if not target.startswith('xl/'): target='xl/'+target
        result[s.attrib['name']]=target
    return result


def load_xlsx(path: str|Path) -> dict[str,list[dict[str,Any]]]:
    """Devolve listas de registros por aba; blanks como None, números como float/int."""
    result = {}
    with ZipFile(path) as z:
        shared = _shared(z)
        for name, target in _sheets(z).items():
            rows=[]
            with z.open(target) as fp:
                for _event, elem in ET.iterparse(fp,events=('end',)):
                    if elem.tag != M+'row': continue
                    by_index={}
                    for c in elem.findall(M+'c'):
                        idx=_col_index(c.attrib['r'])
                        t=c.get('t')
                        v=c.find(M+'v')
                        if t=='inlineStr':
                            inline=c.find(M+'is')
                            val=''.join(e.text or '' for e in inline.iter(M+'t')) if inline is not None else None
                        elif v is None or v.text is None:
                            val=None
                        elif t=='s': val=shared[int(v.text)]
                        elif t in ('str','e'): val=v.text
                        elif t=='b': val=v.text == '1'
                        else:
                            num=float(v.text)
                            val=int(num) if num.is_integer() else num
                        by_index[idx] = val
                    if by_index:
                        rows.append(by_index)
                    elem.clear()
            if not rows: continue
            header_row=rows[0]
            header={idx:str(v).strip() for idx,v in header_row.items() if v is not None}
            result[name]=[{key: row.get(idx) for idx,key in header.items()} for row in rows[1:]]
    return result
