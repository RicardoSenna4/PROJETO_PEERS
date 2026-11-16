"""Q5: 24 meses, picos anuais e incidência por pedidos distintos."""
from collections import Counter, defaultdict
from pathlib import Path
from datetime import date
from .analysis import indexed, percent

MONTHS=tuple(f"{y}-{m:02d}" for y in (2023,2024) for m in range(1,13))

def build_q5(data):
    orders=indexed(data["Pedidos"]);indexed(data["Tickets_Suporte"])
    by_month=Counter()
    for o in data["Pedidos"]:
        if date.fromisoformat(o["data_pedido"]).year not in (2023,2024):
            raise ValueError("pedido fora de 2023–2024")
        by_month[o["data_pedido"][:7]]+=1
    opened=Counter(); tickets=Counter(); unique=defaultdict(set)
    for t in data["Tickets_Suporte"]:
        oid=t["pedido_id"]
        if oid not in orders:raise ValueError("ticket com pedido inexistente")
        if date.fromisoformat(t["data_abertura"])<date.fromisoformat(orders[oid]["data_pedido"]):
            raise ValueError("ticket anterior ao pedido")
        opened[t["data_abertura"][:7]]+=1
        month=orders[oid]["data_pedido"][:7]
        tickets[month]+=1;unique[month].add(oid)
    series=[];cohorts=[]
    for i,month in enumerate(MONTHS):
        n=by_month[month];previous=by_month[MONTHS[i-1]] if i else None
        series.append(dict(mes=month,pedidos=n,chamados_abertos=opened[month],
            variacao_pedidos_vs_mes_anterior_pct=percent(n-previous,previous) if previous else None))
        cohorts.append(dict(mes_compra=month,pedidos=n,tickets_vinculados=tickets[month],
            pedidos_com_ticket=len(unique[month]),
            incidencia_pedidos_com_ticket_pct=percent(len(unique[month]),n)))
    if sum(x["pedidos"] for x in series)!=len(orders):raise AssertionError("pedidos não conciliam")
    if sum(x["chamados_abertos"] for x in series)!=len(data["Tickets_Suporte"]):
        raise ValueError("abertura de tickets fora da janela")
    peak={str(y):max((r for r in series if r["mes"].startswith(str(y))),key=lambda r:r["pedidos"]) for y in (2023,2024)}
    novdec=[t for t in data["Tickets_Suporte"] if t["data_abertura"][:7] in ("2023-11","2023-12")]
    linked=sum(orders[t["pedido_id"]]["data_pedido"][:7]=="2023-11" for t in novdec)
    return dict(meses=series,coortes_suporte=cohorts,maior_mes_por_ano=peak,
        chamados_nov_dez_2023=len(novdec),
        chamados_nov_dez_ligados_pedidos_nov=linked,
        pct_chamados_nov_dez_ligados_pedidos_nov=percent(linked,len(novdec)),
        metodologia="tickets por mês de abertura e incidência por pedidos distintos da coorte")

def render_q5_report(q):
    lines=["# Tarefa 8 — Q5: evolução mensal e hipóteses","","| Mês | Pedidos | Tickets abertos |",
           "|---|---:|---:|"]
    lines.extend(f'| {r["mes"]} | {r["pedidos"]} | {r["chamados_abertos"]} |' for r in q["meses"])
    for y,v in q["maior_mes_por_ano"].items():
        lines.append(f'- Pico {y}: {v["mes"]}, {v["pedidos"]} pedidos; hipótese sazonal, não comprovada.')
    lines.extend(["","Incidência da coorte é pedidos distintos com ao menos um ticket / pedidos da coorte.",
                  "Não confundir tickets por data de abertura com pedidos por data da compra.",
                  "Hipóteses exigem calendário comercial, campanhas, estoque e logística."])
    return "\n".join(lines)+"\n"

def plot_q5(q,out:Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    for key,field,title in (("pedidos","pedidos","Pedidos criados por mês"),
                            ("suporte","chamados_abertos","Tickets por abertura")):
        rows=q["meses"];x=list(range(24))
        fig,ax=plt.subplots(figsize=(10,3.8))
        ax.plot(x,[r[field] for r in rows],marker="o",markersize=3)
        ax.set_xticks(x[::2],[rows[i]["mes"] for i in x[::2]],rotation=35,ha="right")
        ax.set_title("Q5 | "+title);ax.grid(axis="y",alpha=.2)
        fig.tight_layout();fig.savefig(out/("q5_"+key+"_mes.png"));plt.close(fig)
