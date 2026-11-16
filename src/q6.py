"""Q6: conciliação por pedido, sem dupla aplicação de descontos."""
from collections import Counter, defaultdict
from decimal import Decimal
from statistics import median
from .analysis import indexed, money, cent, percent, CENT

def build_q6(data):
    orders=indexed(data["Pedidos"])
    indexed(data["Itens_Pedido"])
    by_order=defaultdict(list)
    for item in data["Itens_Pedido"]:
        if item["pedido_id"] not in orders:raise ValueError("item de pedido inexistente")
        if not isinstance(item["quantidade"],int) or isinstance(item["quantidade"],bool) or item["quantidade"]<=0:
            raise ValueError("quantidade de item inválida")
        if money(item["preco_praticado"])<0:raise ValueError("preço negativo")
        by_order[item["pedido_id"]].append(item)
    totals=defaultdict(lambda:Decimal("0"))
    counts=Counter(); by_status=defaultdict(lambda:[0,0,0,Decimal(0)])
    by_coupon=defaultdict(lambda:[0,0]);residuals=[];result=[]
    for order in data["Pedidos"]:
        oid=order["id"];items=by_order.get(oid,[])
        if not items:raise ValueError("pedido sem itens")
        calculated=sum((money(i["quantidade"])*money(i["preco_praticado"]) for i in items),Decimal(0))
        reported=money(order["valor_total"]) if order["valor_total"] is not None else None
        residual=reported-calculated if reported is not None else None
        counts["pedidos"]+=1
        counts["desconto_desconhecido_pedidos"]+=int(any(i.get("desconto_aplicado") is None for i in items))
        totals["gross_all"]+=calculated
        if order["status"]=="entregue":totals["gross_delivered"]+=calculated
        st=by_status[order["status"]];st[0]+=1
        cupom=str(order.get("cupom_desconto"))
        if residual is None:
            counts["sem_valor_reportado"]+=1
        else:
            counts["com_valor_reportado"]+=1
            counts["gross_equal_within_cent"]+=int(abs(residual)<=CENT)
            counts["conciliados_ate_um_centavo"]+=int(abs(residual)<=CENT)
            counts["divergentes"]+=int(abs(residual)>CENT)
            counts["reported_less_gross"]+=int(residual<-CENT)
            counts["reported_greater_gross"]+=int(residual>CENT)
            totals["reported_known"]+=reported
            totals["gross_on_reported"]+=calculated
            totals["gross_signed_residual"]+=residual
            totals["gross_abs_residual"]+=abs(residual)
            if order["status"]=="entregue":totals["reported_delivered_known"]+=reported
            residuals.append(residual);st[1]+=1;st[2]+=int(abs(residual)>CENT);st[3]+=abs(residual)
            by_coupon[cupom][0]+=1;by_coupon[cupom][1]+=int(abs(residual)>CENT)
        result.append(dict(pedido_id=oid,status=order["status"],cupom_desconto=cupom,
            linhas_itens=len(items),
            valor_total_reportado=str(cent(reported)) if reported is not None else "",
            valor_comercial_itens=str(cent(calculated)),
            diferenca_reportado_menos_itens=str(cent(residual)) if residual is not None else "",
            diferenca_absoluta=str(cent(abs(residual))) if residual is not None else "",
            situacao_conciliacao="sem_valor_reportado" if residual is None else
                ("conciliado" if abs(residual)<=CENT else "divergente")))
    if len(result)!=len(orders):raise AssertionError("cardinalidade incorreta")
    ranked=sorted((r for r in result if r["situacao_conciliacao"]=="divergente"),
        key=lambda r:(-money(r["diferenca_absoluta"]),r["pedido_id"]))
    status=[dict(status=k,pedidos=v[0],com_valor_reportado=v[1],
        divergentes=v[2],percentual_divergente_pct=percent(v[2],v[1]),
        soma_absoluta_diferencas_brl=str(cent(v[3]))) for k,v in sorted(by_status.items())]
    return (dict(contagens=dict(counts),
        totais_brl={k:str(cent(v)) for k,v in totals.items()},
        percentual_divergentes_pct=percent(counts["divergentes"],counts["com_valor_reportado"]),
        mediana_residual_brl=str(cent(Decimal(median(residuals)))) if residuals else None,
        mediana_residual_absoluto_brl=str(cent(Decimal(median(map(abs,residuals))))) if residuals else None,
        maiores_divergencias=ranked[:10],por_status=status,
        por_cupom=[dict(cupom_desconto=k,pedidos_com_total=v[0],divergentes=v[1],
            taxa_divergencia_pct=percent(v[1],v[0])) for k,v in sorted(by_coupon.items())],
        politica="Comparar valor total reportado com quantidade vezes preço praticado nos mesmos pedidos, sem descontar de novo, tolerância ±R$0,01.",
        limites="Sem frete, cupons monetários, tributos, pagamentos, reembolsos e eventos, não é receita auditada."),
      result)

def render_q6_report(q):
    c=q["contagens"];tot=q["totais_brl"]
    lines=["# Tarefa 9 — Q6: reconciliação financeira","",
           "O preço praticado já contém desconto: não aplicar desconto novamente (dupla dedução).",
           "Pedido sem valor_total permanece ausente, não é preenchido com zero.","",
           "| Indicador | Valor |","|---|---:|",
           f'| Pedidos totais | {c["pedidos"]} |',
           f'| Total informado | {c["com_valor_reportado"]} |',
           f'| Total ausente | {c["sem_valor_reportado"]} |',
           f'| Coincidentes a ±R$0,01 | {c["conciliados_ate_um_centavo"]} |',
           f'| Divergentes | {c["divergentes"]} |',
           f'| Total reportado, universo comparável | R$ {tot["reported_known"]} |',
           f'| Total dos itens, mesmo universo | R$ {tot["gross_on_reported"]} |',
           f'| Resíduo assinado | R$ {tot["gross_signed_residual"]} |',
           f'| Soma absoluta dos resíduos | R$ {tot["gross_abs_residual"]} |',
           f'| Mediana da diferença | R$ {q["mediana_residual_brl"]} |',"",
           "Para o conselho: reportar operações e, se necessário, valor dos itens entregues como proxy comercial NÃO contábil.",
           "Nenhum dos totais comprova reconhecimento de receita. Solicitar dados de cupons, frete, tributos, estornos e pagamentos.",
           "O CSV por pedido mantém os 15 mil registros e nenhuma imputação."]
    return "\n".join(lines)+"\n"
