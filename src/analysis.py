"""Métricas puras do case OrbitShop, com grão e denominadores explícitos."""
from __future__ import annotations
from collections import Counter, defaultdict
from decimal import Decimal
from statistics import mean, median
from typing import Any

CENT = Decimal('0.01')


def money(value: Any) -> Decimal:
    return Decimal(str(value))


def cent(value: Decimal) -> Decimal:
    return value.quantize(CENT)


def percent(n: int | float, d: int | float) -> float | None:
    return round(100*n/d, 4) if d else None


def indexed(rows: list[dict], key: str='id') -> dict:
    ids = [r[key] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f'Chave {key} com duplicatas')
    return {r[key]:r for r in rows}


def audit(data: dict) -> dict:
    names=('Clientes','Produtos','Pedidos','Itens_Pedido','Tickets_Suporte','Avaliacoes')
    keys={name:indexed(data[name]) for name in names}
    orders=keys['Pedidos'];clients=keys['Clientes'];products=keys['Produtos']
    membership=defaultdict(set)
    for row in data['Itens_Pedido']:
        membership[row['pedido_id']].add(row['produto_id'])
    summary={}
    for name in names:
        rows=data[name]
        summary[name]={
            'registros':len(rows),
            'colunas':list(rows[0]) if rows else [],
            'ausentes':{col:sum(r[col] is None or r[col]=='' for r in rows) for col in (rows[0] if rows else {})},
            'ids_duplicados':len(rows)-len(keys[name]),
        }
    fk_checks={
        'Pedidos.cliente_id':sum(r['cliente_id'] not in clients for r in data['Pedidos']),
        'Itens_Pedido.pedido_id':sum(r['pedido_id'] not in orders for r in data['Itens_Pedido']),
        'Itens_Pedido.produto_id':sum(r['produto_id'] not in products for r in data['Itens_Pedido']),
        'Tickets_Suporte.pedido_id':sum(r['pedido_id'] not in orders for r in data['Tickets_Suporte']),
        'Tickets_Suporte.cliente_id':sum(r['cliente_id'] not in clients for r in data['Tickets_Suporte']),
        'Avaliacoes.pedido_id':sum(r['pedido_id'] not in orders for r in data['Avaliacoes']),
        'Avaliacoes.produto_id':sum(r['produto_id'] not in products for r in data['Avaliacoes']),
        'Avaliacoes.cliente_id':sum(r['cliente_id'] not in clients for r in data['Avaliacoes']),
    }
    logic={
        'tickets_cliente_diferente_pedido':sum(r['cliente_id']!=orders[r['pedido_id']]['cliente_id'] for r in data['Tickets_Suporte']),
        'avaliacoes_cliente_diferente_pedido':sum(r['cliente_id']!=orders[r['pedido_id']]['cliente_id'] for r in data['Avaliacoes']),
        'avaliacoes_produto_fora_pedido':sum(r['produto_id'] not in membership[r['pedido_id']] for r in data['Avaliacoes']),
        'tickets_anteriores_a_compra':sum(r['data_abertura']<orders[r['pedido_id']]['data_pedido'] for r in data['Tickets_Suporte']),
        'avaliacoes_anteriores_a_compra':sum(r['data_avaliacao']<orders[r['pedido_id']]['data_pedido'] for r in data['Avaliacoes']),
        'pedidos_sem_itens':sum(not membership[o['id']] for o in data['Pedidos']),
    }
    return {'tabelas':summary,'chaves_estrangeiras_orfas':fk_checks,'anomalias_relacionais':logic}


def status_metrics(orders: list[dict]) -> dict:
    counts=Counter(o['status'] for o in orders)
    n=len(orders)
    status=[{'status':k,'pedidos':v,'percentual':percent(v,n)} for k,v in counts.most_common()]
    years={}
    for y in ('2023','2024'):
        subset=[o for o in orders if o['data_pedido'][:4]==y]
        canc=sum(o['status']=='cancelado' for o in subset)
        years[y]={'total':len(subset),'cancelados':canc,'taxa_cancelamento_pct':percent(canc,len(subset))}
    a,b=years['2023'],years['2024']
    return {'tabela_status':status,'n':n,'anos':years,
            'variacao_cancelados_pct':percent(b['cancelados']-a['cancelados'],a['cancelados']),
            'variacao_taxa_pontos_percentuais':round(b['taxa_cancelamento_pct']-a['taxa_cancelamento_pct'],4),
            'variacao_taxa_relativa_pct':percent(b['taxa_cancelamento_pct']-a['taxa_cancelamento_pct'],a['taxa_cancelamento_pct'])}


def categories_metrics(data: dict, eligible_status: set[str]|None=None) -> list[dict]:
    if eligible_status is None: eligible_status={'entregue'}
    orders=indexed(data['Pedidos']); products=indexed(data['Produtos'])
    accum=defaultdict(lambda:{'quantidade':0,'linhas':0,'bruto':Decimal(0),'pedidos':set()})
    for i in data['Itens_Pedido']:
        if orders[i['pedido_id']]['status'] not in eligible_status:continue
        category=products[i['produto_id']]['categoria']
        cur=accum[category]
        cur['quantidade']+=i['quantidade']
        cur['linhas']+=1
        cur['pedidos'].add(i['pedido_id'])
        cur['bruto']+=money(i['quantidade'])*money(i['preco_praticado'])
    out=[]
    for name,cur in accum.items():
        out.append({'categoria':name,'unidades':cur['quantidade'],'valor_bruto_itens':str(cent(cur['bruto'])),
                    'linhas':cur['linhas'],'pedidos_distintos':len(cur['pedidos']),
                    'preco_medio_ponderado':str(cent(cur['bruto']/cur['quantidade'])) if cur['quantidade'] else None})
    return sorted(out,key=lambda d:money(d['valor_bruto_itens']),reverse=True)


def acquisition_metrics(data: dict) -> dict:
    customers=indexed(data['Clientes'])
    grouped=defaultdict(lambda:{'pedidos':0,'cancelados':0,'entregues':0,'soma_entregue_valor_valido':Decimal(0),
                            'entregues_com_valor':0,'entregues_sem_valor':0,'b2b_pedidos':0})
    strata=defaultdict(lambda:[0,0])
    for o in data['Pedidos']:
        cli=customers[o['cliente_id']]; canal=cli['canal_aquisicao'];d=grouped[canal]
        d['pedidos']+=1; d['cancelados']+=int(o['status']=='cancelado')
        d['b2b_pedidos']+=int(cli['segmento']=='B2B')
        for key in ((canal,cli['segmento']),(canal,o['data_pedido'][:4])):
            strata[key][0]+=1;strata[key][1]+=int(o['status']=='cancelado')
        if o['status']=='entregue':
            d['entregues']+=1
            if o['valor_total'] is not None:
                d['entregues_com_valor']+=1
                d['soma_entregue_valor_valido']+=money(o['valor_total'])
            else:d['entregues_sem_valor']+=1
    customer_counts=Counter(c['canal_aquisicao'] for c in customers.values())
    active=defaultdict(set)
    for o in data['Pedidos']:active[customers[o['cliente_id']]['canal_aquisicao']].add(o['cliente_id'])
    out=[]
    for canal,d in grouped.items():
        out.append({'canal_aquisicao':canal,'clientes_cadastrados':customer_counts[canal],
           'clientes_com_pedido':len(active[canal]),'pedidos':d['pedidos'],'participacao_pct':percent(d['pedidos'],len(data['Pedidos'])),
           'cancelados':d['cancelados'],'taxa_cancelamento_pct':percent(d['cancelados'],d['pedidos']),
           'entregues':d['entregues'],'entregues_com_valor':d['entregues_com_valor'],
           'entregues_sem_valor':d['entregues_sem_valor'],
           'ticket_medio_entregue_reportado':str(cent(d['soma_entregue_valor_valido']/d['entregues_com_valor'])) if d['entregues_com_valor'] else None,
           'pedidos_b2b':d['b2b_pedidos']})
    out.sort(key=lambda d:d['taxa_cancelamento_pct'],reverse=True)
    overall=sum(d['cancelados'] for d in out)
    return {'canais':out,'fracao_cancelamentos_paid_search_pct':percent(next((d['cancelados'] for d in out if d['canal_aquisicao']=='paid_search'),0),overall),
      'estratos':[{'canal':key[0],'estrato':key[1],'pedidos':v[0],'cancelados':v[1],
                   'taxa_cancelamento_pct':percent(v[1],v[0])} for key,v in sorted(strata.items())]}


def monthly_metrics(data: dict) -> dict:
    order_month=Counter(o['data_pedido'][:7] for o in data['Pedidos'])
    support_month=Counter(t['data_abertura'][:7] for t in data['Tickets_Suporte'])
    months=[f'{year}-{month:02d}' for year in (2023,2024) for month in range(1,13)]
    table=[{'mes':month,'pedidos':order_month.get(month,0),'chamados_abertos':support_month.get(month,0)} for month in months]
    peak_by_year={str(y):max((r for r in table if r['mes'].startswith(str(y))),key=lambda r:r['pedidos']) for y in (2023,2024)}
    order_cohort=Counter(o['data_pedido'][:7] for o in data['Pedidos'])
    orders=indexed(data['Pedidos'])
    cohort_tickets=Counter(orders[t['pedido_id']]['data_pedido'][:7] for t in data['Tickets_Suporte'])
    cohort=[{'mes_compra':k,'pedidos':order_cohort[k],'tickets_vinculados':cohort_tickets[k],
             'taxa_ticket_por_pedido_pct':percent(cohort_tickets[k],order_cohort[k])} for k in months]
    opened_nov_dec=[t for t in data['Tickets_Suporte'] if t['data_abertura'][:7] in ('2023-11','2023-12')]
    linked_to_nov=sum(orders[t['pedido_id']]['data_pedido'][:7]=='2023-11' for t in opened_nov_dec)
    return {'meses':table,'maior_mes_por_ano':peak_by_year,'coortes_suporte':cohort,
       'chamados_nov_dez_2023':len(opened_nov_dec),'chamados_nov_dez_ligados_pedidos_nov':linked_to_nov,
       'pct_chamados_nov_dez_ligados_pedidos_nov':percent(linked_to_nov,len(opened_nov_dec))}


def reconcile(data: dict) -> tuple[dict,list[dict]]:
    """Cenário líquido só nos pedidos sem nenhum desconto desconhecido."""
    by_order=defaultdict(list)
    for row in data['Itens_Pedido']:by_order[row['pedido_id']].append(row)
    result=[]
    totals=defaultdict(Decimal)
    counts=Counter()
    for o in data['Pedidos']:
        lines=by_order[o['id']]
        gross=sum((money(i['quantidade'])*money(i['preco_praticado']) for i in lines),Decimal(0))
        knows=all(i['desconto_aplicado'] is not None for i in lines)
        net_known=sum((money(i['quantidade'])*money(i['preco_praticado'])*(1-money(i['desconto_aplicado'])) for i in lines),Decimal(0)) if knows else None
        net_zero=sum((money(i['quantidade'])*money(i['preco_praticado'])*(1-money(i['desconto_aplicado'] or 0)) for i in lines),Decimal(0))
        reported=money(o['valor_total']) if o['valor_total'] is not None else None
        rg=reported-gross if reported is not None else None
        rn=reported-net_known if reported is not None and knows else None
        counts['pedidos']+=1
        counts['desconto_desconhecido_pedidos']+=int(not knows)
        totals['gross_all']+=gross
        totals['net_zero_all']+=net_zero
        if o['status']=='entregue':
            totals['gross_delivered']+=gross
            totals['net_zero_delivered']+=net_zero
        if reported is None:
            counts['sem_valor_reportado']+=1
        else:
            counts['com_valor_reportado']+=1
            totals['reported_known']+=reported
            totals['gross_on_reported']+=gross
            totals['net_zero_on_reported']+=net_zero
            totals['gross_signed_residual']+=rg
            totals['gross_abs_residual']+=abs(rg)
            totals['net_zero_signed_residual']+=reported-net_zero
            counts['gross_equal_within_cent']+=int(abs(rg)<=CENT)
            counts['reported_less_gross']+=int(rg < -CENT)
            counts['reported_greater_gross']+=int(rg > CENT)
            if knows:
                counts['complete_net_orders']+=1
                totals['reported_complete_net']+=reported
                totals['net_known_on_complete']+=net_known
                totals['net_signed_residual_complete']+=rn
                counts['net_equal_within_cent']+=int(abs(rn)<=CENT)
            else:
                counts['discount_unknown_and_reported']+=1
            if o['status']=='entregue': totals['reported_delivered_known']+=reported
        result.append({'pedido_id':o['id'],'status':o['status'],
              'valor_total_reportado':str(cent(reported)) if reported is not None else '',
              'valor_bruto_itens':str(cent(gross)),
              'valor_liquido_desconto_conhecido':str(cent(net_known)) if net_known is not None else '',
              'valor_liquido_assumindo_nulo_zero':str(cent(net_zero)),
              'descontos_totalmente_conhecidos':knows,
              'diferenca_reportado_menos_bruto':str(cent(rg)) if rg is not None else '',
              'diferenca_reportado_menos_liquido_conhecido':str(cent(rn)) if rn is not None else ''})
    r_nonull=[r for r in result if r['diferenca_reportado_menos_bruto']]
    rank=sorted(r_nonull,key=lambda r:abs(money(r['diferenca_reportado_menos_bruto'])),reverse=True)
    summary={'contagens':dict(counts),'totais_brl':{k:str(cent(v)) for k,v in totals.items()},
        'pct_nao_conciliado_bruto':percent(counts['com_valor_reportado']-counts['gross_equal_within_cent'],counts['com_valor_reportado']),
        'maiores_divergencias_brutas':rank[:5],
        'politica':'Valores brutos: soma de quantidade × preço praticado; alternativa líquida aplica desconto_aplicado como fração adicional apenas nos pedidos completos. Tolerância: diferença absoluta <= R$0,01, após agregar valores sem arredondar linhas. Não inclui frete, tributos, reembolso, taxas ou comprovantes de pagamento.'}
    return summary,result


def supplier_metrics(data: dict) -> dict:
    orders=indexed(data['Pedidos']); products=indexed(data['Produtos'])
    values=defaultdict(list)
    exposure=defaultdict(set)
    delivered_units=Counter()
    suppliers_by_order=defaultdict(set)
    for i in data['Itens_Pedido']:
        supplier=products[i['produto_id']]['fornecedor']
        exposure[supplier].add(i['pedido_id'])
        suppliers_by_order[i['pedido_id']].add(supplier)
        if orders[i['pedido_id']]['status']=='entregue':delivered_units[supplier]+=i['quantidade']
    for r in data['Avaliacoes']:
        values[products[r['produto_id']]['fornecedor']].append(r['nota'])
    tickets_by_order=Counter(t['pedido_id'] for t in data['Tickets_Suporte'])
    supplier_orders=defaultdict(set)
    for oid,ss in suppliers_by_order.items():
        if len(ss)==1:supplier_orders[next(iter(ss))].add(oid)
    out=[]
    for s,notes in values.items():
        unique=supplier_orders[s]
        all_exposure=exposure[s]
        note_negative=sum(n<=2 for n in notes)
        all_tickets_present=sum(tickets_by_order[oid] for oid in all_exposure)
        single_tickets=sum(tickets_by_order[oid] for oid in unique)
        out.append({'fornecedor':s,'n_avaliacoes':len(notes),'nota_media':round(mean(notes),4),
          'nota_mediana':median(notes),'avaliacoes_nota_ate_2':note_negative,
          'avaliacoes_negativas_pct':percent(note_negative,len(notes)),
          'pedidos_com_fornecedor':len(all_exposure),'unidades_em_pedidos_entregues':delivered_units[s],
          'pedidos_com_apenas_este_fornecedor':len(unique),'tickets_nesses_pedidos':single_tickets,
          'tickets_pct_pedidos_monofornecedor':percent(single_tickets,len(unique)),
          'tickets_pedidos_contendo_fornecedor_nao_atribuidos':all_tickets_present})
    out.sort(key=lambda r:r['nota_media'])
    affected={oid for oid,ss in suppliers_by_order.items() if len(ss)>1}
    ticket_multi=sum(t['pedido_id'] in affected for t in data['Tickets_Suporte'])
    ticket_single=len(data['Tickets_Suporte'])-ticket_multi
    q4=[t for t in data['Tickets_Suporte'] if '2023-10'<=t['data_abertura'][:7]<='2023-12']
    return {'fornecedores':out,'pedidos_multifornecedor':len(affected),
      'pedidos_monofornecedor':len(orders)-len(affected),'chamados_multifornecedor_sem_atribuicao':ticket_multi,
      'chamados_monofornecedor':ticket_single,
      'chamados_trimestre_final_2023_por_causa':dict(Counter(t['categoria_problema'] for t in q4))}


def analyze(data: dict) -> tuple[dict,list[dict]]:
    summary=audit(data)
    if any(summary['chaves_estrangeiras_orfas'].values()) or any(summary['anomalias_relacionais'].values()):
        raise ValueError(f'Falha relacional que precisa ser investigada: {summary}')
    r6, detail =reconcile(data)
    return {'auditoria':summary,'Q2':status_metrics(data['Pedidos']),
        'Q3_entregues':categories_metrics(data, {'entregue'}),
        'Q3_nao_cancelados':categories_metrics(data, {'entregue','em_transito','devolvido'}),
        'Q3_todos':categories_metrics(data, {'entregue','em_transito','devolvido','cancelado'}),
        'Q4':acquisition_metrics(data),'Q5':monthly_metrics(data),'Q6':r6,
        'Q7':supplier_metrics(data)}, detail
