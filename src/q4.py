"""Q4: aquisição, cancelamentos, segmentação e comparação de tickets."""
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
from .analysis import indexed, money, cent, percent

def build_q4(data):
    clients=indexed(data["Clientes"])
    orders=indexed(data["Pedidos"])
    indexed(data["Itens_Pedido"])
    items=defaultdict(lambda: Decimal("0"))
    for i in data["Itens_Pedido"]:
        if i["pedido_id"] not in orders:
            raise ValueError("item de pedido inexistente")
        items[i["pedido_id"]]+=money(i["quantidade"])*money(i["preco_praticado"])
    agg=defaultdict(lambda: dict(pedidos=0,cancelados=0,entregues=0,com_valor=0,
        sem_valor=0,valor=Decimal(0),proxy=Decimal(0),clientes=set(),b2b=0))
    segment=defaultdict(lambda:[0,0])
    years=defaultdict(lambda:[0,0])
    segment_year=defaultdict(lambda:[0,0])
    for o in data["Pedidos"]:
        if o["cliente_id"] not in clients:raise ValueError("cliente inexistente")
        cl=clients[o["cliente_id"]]
        ch=cl["canal_aquisicao"];sg=cl["segmento"];yr=o["data_pedido"][:4]
        d=agg[ch];d["pedidos"]+=1;d["cancelados"]+=int(o["status"]=="cancelado")
        d["clientes"].add(cl["id"]);d["b2b"]+=int(sg=="B2B")
        for a in (segment[(ch,sg)],years[(ch,yr)],segment_year[(ch,sg,yr)]):
            a[0]+=1;a[1]+=int(o["status"]=="cancelado")
        if o["status"]=="entregue":
            if o["id"] not in items:raise ValueError("pedido entregue sem itens")
            d["entregues"]+=1;d["proxy"]+=items[o["id"]]
            if o["valor_total"] is None:d["sem_valor"]+=1
            else:
                d["com_valor"]+=1;d["valor"]+=money(o["valor_total"])
    registered=Counter(x["canal_aquisicao"] for x in data["Clientes"])
    rows=[]
    for ch,d in agg.items():
        rows.append(dict(canal_aquisicao=ch,clientes_cadastrados=registered[ch],
            clientes_com_pedido=len(d["clientes"]),pedidos=d["pedidos"],
            participacao_pct=percent(d["pedidos"],len(orders)),
            cancelados=d["cancelados"],taxa_cancelamento_pct=percent(d["cancelados"],d["pedidos"]),
            entregues=d["entregues"],entregues_com_valor=d["com_valor"],
            entregues_sem_valor=d["sem_valor"],pedidos_b2b=d["b2b"],
            participacao_b2b_pct=percent(d["b2b"],d["pedidos"]),
            ticket_medio_entregue_reportado=str(cent(d["valor"]/d["com_valor"])) if d["com_valor"] else None,
            ticket_medio_proxy_itens_entregues=str(cent(d["proxy"]/d["entregues"])) if d["entregues"] else None))
    rows.sort(key=lambda x:(-x["taxa_cancelamento_pct"],x["canal_aquisicao"]))
    if sum(x["pedidos"] for x in rows)!=len(orders):raise AssertionError("join multiplicou pedidos")
    if sum(x["cancelados"] for x in rows)!=sum(o["status"]=="cancelado" for o in orders.values()):
        raise AssertionError("cancelamentos não reconciliados")
    def strata(g,labels):
        return [dict(zip(labels,key),pedidos=n,cancelados=c,taxa_cancelamento_pct=percent(c,n))
                for key,(n,c) in sorted(g.items())]
    paid=next((r for r in rows if r["canal_aquisicao"]=="paid_search"),None)
    others=[r for r in rows if r["canal_aquisicao"]!="paid_search"]
    total_cancelled=sum(r["cancelados"] for r in rows)
    share=percent(paid["cancelados"],total_cancelled) if paid else None
    return dict(canais=rows,estratos_segmento=strata(segment,["canal_aquisicao","segmento"]),
        estratos_ano=strata(years,["canal_aquisicao","ano_pedido"]),
        estratos_segmento_ano=strata(segment_year,["canal_aquisicao","segmento","ano_pedido"]),
        estratos=strata(segment,["canal","estrato"])+strata(years,["canal","estrato"]),
        fracao_cancelamentos_paid_search_pct=share,
        paid_search_participacao_cancelamentos_pct=share,
        demais_canais_taxa_cancelamento_pct=percent(sum(r["cancelados"] for r in others),
            sum(r["pedidos"] for r in others)),
        metodologia="canal de aquisição, ticket reportado não conciliado e proxy de itens")

def render_q4_report(q):
    lines=["# Tarefa 7 — Q4: Aquisição, cancelamentos e ticket médio","","| Canal | Pedidos | Cancelados | Taxa | Ticket reportado | Proxy itens |",
           "|---|---:|---:|---:|---:|---:|"]
    for r in q["canais"]:
        lines.append(f'| {r["canal_aquisicao"]} | {r["pedidos"]} | {r["cancelados"]} | {r["taxa_cancelamento_pct"]:.2f}% | R$ {r["ticket_medio_entregue_reportado"]} | R$ {r["ticket_medio_proxy_itens_entregues"]} |')
    lines+=["","Valores apenas descritivos: valor_total não reconcilia com itens (Q6).",
            "O agrupamento usa Clientes.canal_aquisicao, não Pedidos.canal_venda.",
            "As taxas não demonstram causalidade e a análise preserva B2B/B2C e anos."]
    return "\n".join(lines)+"\n"

def plot_q4(result,out:Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rows=result["canais"]; labels=[r["canal_aquisicao"] for r in rows]
    fig,ax=plt.subplots(figsize=(8,3.8))
    values=[r["taxa_cancelamento_pct"] for r in rows]
    ax.barh(labels[::-1],values[::-1]);ax.set_xlabel("% pedidos cancelados")
    ax.set_title("Q4 | Cancelamento por aquisição");fig.tight_layout()
    fig.savefig(out/"q4_aquisicao.png");plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,3.8));x=list(range(len(rows)));w=.35
    ax.bar([i-w/2 for i in x],[float(r["ticket_medio_entregue_reportado"]) for r in rows],
        width=w,label="Valor reportado")
    ax.bar([i+w/2 for i in x],[float(r["ticket_medio_proxy_itens_entregues"]) for r in rows],
        width=w,label="Proxy itens")
    ax.set_xticks(x,labels);ax.legend();ax.set_ylabel("R$ por pedido entregue")
    ax.set_title("Q4 | Tickets comparativos, não conciliados");fig.tight_layout()
    fig.savefig(out/"q4_tickets_comparados.png");plt.close(fig)
