"""Métricas puras do case OrbitShop, com grão e denominadores explícitos."""
from __future__ import annotations
from collections import Counter, defaultdict
from decimal import Decimal
from datetime import date
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
    """Q2: status atual por pedido, ano definido por data_pedido (coorte)."""
    indexed(orders)  # Uma linha por pedido: somar linhas duplicadas infla o denominador.
    allowed = {'entregue', 'cancelado', 'em_transito', 'devolvido'}
    for order in orders:
        if order['status'] not in allowed:
            raise ValueError(f"Status de pedido inesperado: {order['status']!r}")
        try:
            creation_date = date.fromisoformat(str(order['data_pedido']))
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Data de pedido inválida: {order['data_pedido']!r}") from exc
        if creation_date.year not in (2023, 2024):
            raise ValueError('Q2 exige pedidos de janeiro/2023 a dezembro/2024')

    counts = Counter(o['status'] for o in orders)
    n = len(orders)
    status = [{'status': k, 'pedidos': v, 'percentual': percent(v, n)}
              for k, v in counts.most_common()]
    years = {}
    for year in ('2023', '2024'):
        subset = [o for o in orders if o['data_pedido'][:4] == year]
        cancelled = sum(o['status'] == 'cancelado' for o in subset)
        years[year] = {'total': len(subset), 'cancelados': cancelled,
                       'taxa_cancelamento_pct': percent(cancelled, len(subset))}
    a, b = years['2023'], years['2024']
    rate_a = a['cancelados'] / a['total'] if a['total'] else None
    rate_b = b['cancelados'] / b['total'] if b['total'] else None
    delta_rate = (rate_b - rate_a) if rate_a is not None and rate_b is not None else None
    return {
        'tabela_status': status,
        'n': n,
        'anos': years,
        'variacao_cancelados_pct': percent(b['cancelados'] - a['cancelados'], a['cancelados']),
        'variacao_taxa_pontos_percentuais': round(100 * delta_rate, 4) if delta_rate is not None else None,
        'variacao_taxa_relativa_pct': percent(delta_rate, rate_a) if delta_rate is not None else None,
    }


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
    """Compatibilidade: implementação revisada da Tarefa 7."""
    from .q4 import build_q4
    return build_q4(data)


def monthly_metrics(data: dict) -> dict:
    """Compatibilidade: implementação revisada da Tarefa 8."""
    from .q5 import build_q5
    return build_q5(data)


def reconcile(data: dict) -> tuple[dict, list[dict]]:
    """Compatibilidade: implementação revisada da Tarefa 9 sem duplo desconto."""
    from .q6 import build_q6
    return build_q6(data)


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
