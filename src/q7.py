"""Q7: fornecedores, avaliações e suporte; nunca imputar tickets multiforncedor."""
from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean, median

from .analysis import indexed, percent


def build_q7(data: dict) -> dict:
    products = indexed(data['Produtos'])
    orders = indexed(data['Pedidos'])
    product_supplier = {pid: p['fornecedor'] for pid, p in products.items()}
    suppliers = sorted(set(product_supplier.values()))
    order_suppliers = defaultdict(set)
    supplier_orders = defaultdict(set)
    delivered_units = Counter()

    for item in data['Itens_Pedido']:
        oid = item['pedido_id']
        supplier = product_supplier[item['produto_id']]
        order_suppliers[oid].add(supplier)
        supplier_orders[supplier].add(oid)
        if orders[oid]['status'] == 'entregue':
            delivered_units[supplier] += item['quantidade']

    ratings = defaultdict(list)
    for r in data['Avaliacoes']:
        ratings[product_supplier[r['produto_id']]].append(r['nota'])

    tickets_by_order = defaultdict(list)
    open_months = Counter()
    month_causes = Counter()
    for t in data['Tickets_Suporte']:
        tickets_by_order[t['pedido_id']].append(t)
        month = t['data_abertura'][:7]
        open_months[month] += 1
        month_causes[month, t['categoria_problema']] += 1

    multi_ids = {oid for oid, ss in order_suppliers.items() if len(ss) > 1}
    mono_ids = {oid for oid, ss in order_suppliers.items() if len(ss) == 1}
    results = []
    for supplier in suppliers:
        own = {oid for oid in supplier_orders[supplier] if oid in mono_ids}
        rated = ratings[supplier]
        ticket_orders = {oid for oid in own if tickets_by_order[oid]}
        ticket_count = sum(len(tickets_by_order[oid]) for oid in own)
        low = sum(v <= 2 for v in rated)
        by_month = Counter(t['data_abertura'][:7] for oid in own for t in tickets_by_order[oid])
        results.append({
            'fornecedor': supplier,
            'n_avaliacoes': len(rated),
            'nota_media': round(mean(rated), 4) if rated else None,
            'nota_mediana': median(rated) if rated else None,
            'avaliacoes_nota_ate_2': low,
            'avaliacoes_negativas_pct': percent(low, len(rated)),
            'pedidos_com_fornecedor': len(supplier_orders[supplier]),
            'unidades_em_pedidos_entregues': delivered_units[supplier],
            'pedidos_monofornecedor': len(own),
            'pedidos_com_apenas_este_fornecedor': len(own),  # compatibilidade Q7 anterior
            'pedidos_mono_com_chamado': len(ticket_orders),
            'incidencia_chamado_mono_pct': percent(len(ticket_orders), len(own)),
            'tickets_em_pedidos_mono': ticket_count,
            'tickets_nesses_pedidos': ticket_count,  # compatibilidade com testes existentes
            'tickets_mono_nov_dez_2023': by_month['2023-11'] + by_month['2023-12'],
            'pedidos_multi_com_fornecedor': len(supplier_orders[supplier] - own),
        })
    results.sort(key=lambda r: (r['nota_media'] is None, r['nota_media'] if r['nota_media'] is not None else 99))

    multi_tickets = [t for t in data['Tickets_Suporte'] if t['pedido_id'] in multi_ids]
    mono_tickets = [t for t in data['Tickets_Suporte'] if t['pedido_id'] in mono_ids]
    peak_tickets = [t for t in data['Tickets_Suporte'] if t['data_abertura'][:7] in ('2023-11','2023-12')]
    nov_orders = {oid for oid,o in orders.items() if o['data_pedido'].startswith('2023-11')}
    peak_from_nov = [t for t in peak_tickets if t['pedido_id'] in nov_orders]
    detail = []
    for (month, cause), n in sorted(month_causes.items()):
        detail.append({'mes_abertura':month,'categoria_problema':cause,'tickets':n})

    # O fornecedor do produto avaliado é conhecido; o responsável por tickets
    # de pedido com diversos fornecedores é desconhecido.
    return {
        'fornecedores': results,
        'pedidos_multifornecedor': len(multi_ids),
        'pedidos_monofornecedor': len(mono_ids),
        'tickets_multifornecedor_sem_atribuicao': len(multi_tickets),
        'chamados_multifornecedor_sem_atribuicao': len(multi_tickets),
        'tickets_monofornecedor': len(mono_tickets),
        'chamados_monofornecedor': len(mono_tickets),
        'tickets_total': len(data['Tickets_Suporte']),
        'proporcao_tickets_sem_atribuicao_pct': percent(len(multi_tickets), len(data['Tickets_Suporte'])),
        'tickets_nov_dez_2023': len(peak_tickets),
        'tickets_nov_dez_2023_coorte_nov': len(peak_from_nov),
        'tickets_out_2023': open_months['2023-10'],
        'tickets_nov_2023': open_months['2023-11'],
        'tickets_dez_2023': open_months['2023-12'],
        'pico_causa_por_mes': detail,
        'chamados_trimestre_final_2023_por_causa': dict(Counter({cause: sum(n for (month,cat),n in month_causes.items() if cat==cause and month in ('2023-10','2023-11','2023-12')) for cause in {cat for (month,cat) in month_causes}})),
        'restricao_atribuicao': 'Ticket ligado ao pedido, não a produto ou fornecedor; comparar somente monofornecedor, sem inferir culpa.',
    }


def render_q7_report(q7: dict) -> str:
    rows = [
        '# Tarefa 10 — Q7: desempenho de fornecedores e suporte', '',
        '## Observações e definição da métrica',
        'Avaliações têm produto identificado; tickets têm apenas pedido identificado. A comparação de chamados por fornecedor utiliza **somente pedidos monofornecedor**. A incidência é a contagem de **pedidos distintos com chamado**, dividida pelos pedidos monofornecedor; não é o número de tickets por pedido.', '',
        '| Fornecedor | Avaliações | Média | Nota ≤ 2 | Pedidos mono | Pedidos mono com chamado | Incidência |',
        '|---|---:|---:|---:|---:|---:|---:|'
    ]
    for r in q7['fornecedores']:
        rows.append(f"| {r['fornecedor']} | {r['n_avaliacoes']:,} | {r['nota_media']:.2f} | {r['avaliacoes_negativas_pct']:.2f}% | {r['pedidos_monofornecedor']:,} | {r['pedidos_mono_com_chamado']:,} | {r['incidencia_chamado_mono_pct']:.2f}% |")
    delta = next((r for r in q7['fornecedores'] if r['fornecedor'] == 'DeltaFornece ME'), None)
    rows += ['', '## Explicação do pico de suporte',
             f"Foram {q7['tickets_out_2023']} tickets em outubro de 2023, {q7['tickets_nov_2023']} em novembro e {q7['tickets_dez_2023']} em dezembro. Os dois últimos meses somam {q7['tickets_nov_dez_2023']} tickets, dos quais {q7['tickets_nov_dez_2023_coorte_nov']} estão associados a pedidos comprados em novembro.", '',
             f"{q7['pedidos_multifornecedor']:,} pedidos contêm múltiplos fornecedores; {q7['tickets_multifornecedor_sem_atribuicao']:,} de {q7['tickets_total']:,} tickets ({q7['proporcao_tickets_sem_atribuicao_pct']:.2f}%) não podem ser atribuídos individualmente a um fornecedor.", '']
    if delta:
        rows += [f"**DeltaFornece ME** apresenta média {delta['nota_media']:.2f}/5 em {delta['n_avaliacoes']} avaliações, com {delta['avaliacoes_negativas_pct']:.2f}% de notas ≤2. Sua incidência de chamados nos {delta['pedidos_monofornecedor']} pedidos monofornecedor é {delta['incidencia_chamado_mono_pct']:.2f}%. A nota pior não prova que o fornecedor causou o pico de chamados.", '']
    rows += ['## Limitações e leitura para o conselho',
             '- Avaliação negativa é associação ao produto, não prova defeito ou culpa do fornecedor.',
             '- Tickets em pedidos com múltiplos fornecedores permanecem sem atribuição; não replicar o ticket a todos os fornecedores.',
             '- Não existem causas-raiz por item nem séries de incidentes por fornecedor suficientes para identificar a origem do aumento.',
             '- O volume da coorte de novembro pode explicar parte do número absoluto de tickets, sem comprovar deterioração operacional.', '',
             'Arquivos reproduzíveis: `outputs/q7_fornecedores.csv`, `outputs/q7_causas_mensais.csv`, `outputs/q7_fornecedores.png`.']
    return '\n'.join(rows) + '\n'
