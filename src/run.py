"""CLI: python -m src.run --input input/Base_Dados_OrbitShop_v3.xlsx --output outputs"""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
from .workbook import load_xlsx
from .analysis import analyze
from .validation import validate_input
from .q2 import q2_years_rows, render_q2_report
from .q3 import build_q3, render_q3_report, plot_q3
from .q4 import render_q4_report, plot_q4
from .q5 import render_q5_report, plot_q5
from .q6 import render_q6_report
from .q7 import render_q7_report
from .q8_q9 import render_decision_report
from .audit_review import audit_independent, render_audit_report


def write_csv(path:Path, rows:list[dict]):
    if not rows: return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader();writer.writerows(rows)


def charts(metrics:dict,out:Path):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print('AVISO: matplotlib não disponível; arquivos tabulares e JSON produzidos, gráficos não gerados.')
        return
    plt.rcParams.update({'font.size':10,'figure.dpi':140,'savefig.dpi':170})
    s=metrics['Q2']['tabela_status']; names=[x['status'] for x in s];vals=[x['pedidos'] for x in s]
    fig,ax=plt.subplots(figsize=(8,3.5));bars=ax.bar(names,vals)
    ax.bar_label(bars,labels=[f"{v:,} ({x['percentual']:.2f}%)".replace(',','.') for x,v in zip(s,vals)],padding=3,fontsize=9)
    ax.set_ylim(0,max(vals)*1.23);ax.set_ylabel('Quantidade de pedidos');ax.set_title('Q2 | Status dos pedidos (2023–2024)',loc='left',weight='bold')
    ax.spines[['top','right']].set_visible(False);fig.tight_layout();fig.savefig(out/'q2_status.png');plt.close(fig)
    months=metrics['Q5']['meses']
    fig,ax=plt.subplots(figsize=(11,3.7)); x=range(len(months)); ax.plot(x,[m['pedidos'] for m in months],marker='o',markersize=3,label='Pedidos')
    ax.plot(x,[m['chamados_abertos'] for m in months],marker='s',markersize=2,label='Chamados abertos')
    ax.set_xticks(list(x)[::2],[months[k]['mes'] for k in list(x)[::2]],rotation=35,ha='right')
    ax.set_title('Q5 | Pedidos e abertura de chamados por mês',loc='left',weight='bold');ax.set_ylabel('Quantidade')
    ax.legend(frameon=False);ax.grid(axis='y',alpha=.2);ax.spines[['top','right']].set_visible(False)
    ax.annotate('2.317 pedidos',xy=(10,2317),xytext=(12,2090),arrowprops={'arrowstyle':'->'},fontsize=9)
    fig.tight_layout();fig.savefig(out/'q5_mensal.png');plt.close(fig)
    c=metrics['Q4']['canais']
    fig,ax=plt.subplots(figsize=(8,3.4)); bars=ax.barh([r['canal_aquisicao'] for r in reversed(c)],[r['taxa_cancelamento_pct'] for r in reversed(c)])
    ax.bar_label(bars,labels=[f"{r['taxa_cancelamento_pct']:.1f}%" for r in reversed(c)],padding=3)
    ax.set_xlim(0,36);ax.set_xlabel('Cancelamentos / pedidos do canal (%)')
    ax.set_title('Q4 | Cancelamento por aquisição',loc='left',weight='bold');ax.spines[['top','right']].set_visible(False)
    fig.tight_layout();fig.savefig(out/'q4_aquisicao.png');plt.close(fig)
    supp=metrics['Q7']['fornecedores']
    fig,ax=plt.subplots(figsize=(9,3.8));bars=ax.barh([r['fornecedor'] for r in reversed(supp)],[r['nota_media'] for r in reversed(supp)])
    ax.set_xlim(0,5);ax.set_xlabel('Nota média das avaliações (1 a 5)');ax.set_title('Q7 | Avaliação por fornecedor',loc='left',weight='bold')
    ax.bar_label(bars,labels=[f"{r['nota_media']:.2f} (n={r['n_avaliacoes']})" for r in reversed(supp)],padding=3,fontsize=8)
    ax.spines[['top','right']].set_visible(False);fig.tight_layout();fig.savefig(out/'q7_fornecedores.png');plt.close(fig)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',default='input/Base_Dados_OrbitShop_v3.xlsx')
    p.add_argument('--output',default='outputs')
    p.add_argument('--q2-report',default='docs/05_Q2_DISTRIBUICAO_STATUS.md')
    p.add_argument('--q3-report',default='docs/06_Q3_CATEGORIAS.md')
    p.add_argument('--q4-report',default='docs/07_Q4_AQUISICAO.md')
    p.add_argument('--q5-report',default='docs/08_Q5_SERIE_MENSAL.md')
    p.add_argument('--q6-report',default='docs/09_Q6_RECONCILIACAO.md')
    p.add_argument('--q7-report',default='docs/10_Q7_FORNECEDORES.md')
    p.add_argument('--decision-report',default='docs/11_Q8_Q9_DECISAO.md')
    p.add_argument('--audit-report',default='docs/12_AUDITORIA_ADVERSARIAL.md')
    args=p.parse_args();out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    data=load_xlsx(args.input);data.pop('Leia-me',None)
    validate_input(data)
    metrics,reconciliation=analyze(data)
    q3 = build_q3(data)
    (out/'metricas.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf-8')
    for path,rows in {
      'q2_status.csv':metrics['Q2']['tabela_status'],
      'q3_comparacao_entregues.csv':q3['comparacao'], 'q3_ranking_volume.csv':q3['ranking_volume'],
      'q2_por_ano.csv':q2_years_rows(metrics['Q2']),'q3_categorias_entregues.csv':metrics['Q3_entregues'],
      'q3_categorias_nao_cancelados.csv':metrics['Q3_nao_cancelados'],'q3_categorias_todos.csv':metrics['Q3_todos'],
      'q4_canais.csv':metrics['Q4']['canais'],'q4_estratos.csv':metrics['Q4']['estratos'],
      'q4_segmentos.csv':metrics['Q4']['estratos_segmento'], 'q4_anos.csv':metrics['Q4']['estratos_ano'],
      'q4_segmento_ano.csv':metrics['Q4']['estratos_segmento_ano'],
      'q6_status.csv':metrics['Q6']['por_status'],'q6_cupom.csv':metrics['Q6']['por_cupom'],
      'q5_mensal.csv':metrics['Q5']['meses'],'q5_coortes_suporte.csv':metrics['Q5']['coortes_suporte'],
      'q6_reconciliacao_pedido.csv':reconciliation,'q7_fornecedores.csv':metrics['Q7']['fornecedores'],
      'q7_causas_mensais.csv':metrics['Q7']['pico_causa_por_mes']
    }.items():write_csv(out/path,rows)
    charts(metrics,out)
    plot_q3(q3,out)
    plot_q4(metrics['Q4'],out)
    plot_q5(metrics['Q5'],out)
    q3_report = Path(args.q3_report)
    q3_report.parent.mkdir(parents=True, exist_ok=True)
    q3_report.write_text(render_q3_report(q3), encoding='utf-8')
    q2_report = Path(args.q2_report)
    q2_report.parent.mkdir(parents=True, exist_ok=True)
    q2_report.write_text(render_q2_report(metrics['Q2']), encoding='utf-8')
    for name,content in ((args.q4_report,render_q4_report(metrics['Q4'])),
                         (args.q5_report,render_q5_report(metrics['Q5'])),
                         (args.q6_report,render_q6_report(metrics['Q6'])),
                         (args.q7_report,render_q7_report(metrics['Q7'])),
                         (args.decision_report,render_decision_report(metrics['Q8_Q9']))):
        path=Path(name);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(content,encoding='utf-8')
    (out/'q8_q9_decisao.json').write_text(json.dumps(metrics['Q8_Q9'],ensure_ascii=False,indent=2),encoding='utf-8')
    report = audit_independent(data, metrics)
    (out/'q12_auditoria.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    audit_path = Path(args.audit_report)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(render_audit_report(report),encoding='utf-8')
    if report['falhas']:
        raise SystemExit('FALHA na auditoria adversarial: '+str([x['id'] for x in report['falhas']]))
    print(f'Auditoria independente: {report["aprovadas"]}/{report["total"]} verificações aprovadas')
    print('Análise concluída: '+str(out.resolve()))
    print('Pedidos=',metrics['Q2']['n'],'cancelados=',next(r for r in metrics['Q2']['tabela_status'] if r['status']=='cancelado'))
    print('Reconciliação=',metrics['Q6']['contagens'])

if __name__=='__main__':main()