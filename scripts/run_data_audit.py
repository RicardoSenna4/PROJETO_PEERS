"""Exporta auditoria da Tarefa 2 sem mutações no Excel original.

    python -m scripts.run_data_audit
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
from src.workbook import load_xlsx
from src.data_quality import build_quality_report, dictionary_csv_rows, make_audit_markdown


def main() -> None:
    parser = argparse.ArgumentParser(description='Auditoria estruturada da base OrbitShop')
    parser.add_argument('--input', default='input/Base_Dados_OrbitShop_v3.xlsx')
    parser.add_argument('--output-dir', default='outputs')
    parser.add_argument('--report', default='docs/02_AUDITORIA_DADOS.md')
    args = parser.parse_args()
    input_path, output_dir, report_path = Path(args.input), Path(args.output_dir), Path(args.report)
    data = load_xlsx(input_path)
    data.pop('Leia-me', None)
    audit = build_quality_report(data, input_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    (output_dir / 'auditoria_qualidade.json').write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding='utf-8')
    records = dictionary_csv_rows(audit)
    with (output_dir / 'dicionario_dados.csv').open('w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    report_path.write_text(make_audit_markdown(audit), encoding='utf-8')
    print(f'Auditoria concluída: {report_path} | {output_dir / "auditoria_qualidade.json"}')
    print(f"Valores ausentes: pedidos={audit['tables']['Pedidos']['fields']['valor_total']['missing']}; "
          f"descontos={audit['tables']['Itens_Pedido']['fields']['desconto_aplicado']['missing']}")
    print(f"Itens com desconto conhecido e preco praticado compativel: "
          f"{audit['discounts_and_price']['price_matches_catalog_minus_discount_within_1_cent']} / "
          f"{audit['discounts_and_price']['known']}")

if __name__ == '__main__':
    main()
