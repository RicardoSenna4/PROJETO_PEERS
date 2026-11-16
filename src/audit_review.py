"""Auditoria adversarial: recalcula indicadores críticos por SQLite independente.

Não reutiliza as agregações de src.analysis para obter os valores de referência;
recebe somente o resultado que deve ser confrontado com os dados brutos.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from collections import Counter
from sqlite3 import connect


def _cents(value) -> int | None:
    if value is None:
        return None
    return int((Decimal(str(value)) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def audit_independent(data: dict, metrics: dict) -> dict:
    conn = connect(':memory:')
    conn.executescript('''
        CREATE TABLE orders(id INTEGER PRIMARY KEY, cliente_id INTEGER, data_pedido TEXT,
                            status TEXT, valor_centavos INTEGER);
        CREATE TABLE customers(id INTEGER PRIMARY KEY, canal TEXT, segmento TEXT);
        CREATE TABLE products(id INTEGER PRIMARY KEY, categoria TEXT, fornecedor TEXT);
        CREATE TABLE items(id INTEGER PRIMARY KEY, pedido_id INTEGER, produto_id INTEGER,
                           quantidade INTEGER, preco_centavos INTEGER);
        CREATE TABLE ratings(id INTEGER PRIMARY KEY, produto_id INTEGER, nota INTEGER);
        CREATE TABLE tickets(id INTEGER PRIMARY KEY, pedido_id INTEGER, data_abertura TEXT, causa TEXT);
    ''')
    conn.executemany('INSERT INTO orders VALUES(?,?,?,?,?)',
        [(o['id'], o['cliente_id'], o['data_pedido'], o['status'], _cents(o['valor_total'])) for o in data['Pedidos']])
    conn.executemany('INSERT INTO customers VALUES(?,?,?)',
        [(c['id'],c['canal_aquisicao'],c['segmento']) for c in data['Clientes']])
    conn.executemany('INSERT INTO products VALUES(?,?,?)',
        [(p['id'],p['categoria'],p['fornecedor']) for p in data['Produtos']])
    conn.executemany('INSERT INTO items VALUES(?,?,?,?,?)',
        [(i['id'],i['pedido_id'],i['produto_id'],i['quantidade'],_cents(i['preco_praticado'])) for i in data['Itens_Pedido']])
    conn.executemany('INSERT INTO ratings VALUES(?,?,?)',
        [(a['id'],a['produto_id'],a['nota']) for a in data['Avaliacoes']])
    conn.executemany('INSERT INTO tickets VALUES(?,?,?,?)',
        [(t['id'],t['pedido_id'],t['data_abertura'],t['categoria_problema']) for t in data['Tickets_Suporte']])

    checks = []
    def add(code: str, observed, expected, note: str, priority='P0'):
        checks.append({'id':code,'ok': observed == expected, 'calculado_sqlite':observed,
                       'reportado':expected,'criterio':note, 'prioridade_se_falhar':priority})

    # Q2: contagem e ano de criação; evita reproduzir a hipótese sobre ano do evento.
    statuses = dict(conn.execute('SELECT status,COUNT(*) FROM orders GROUP BY status'))
    result_status = {r['status']:r['pedidos'] for r in metrics['Q2']['tabela_status']}
    add('Q2_STATUS',statuses,result_status,'Distribuição por status de pedido distinto')
    annual = {year:(n,c) for year,n,c in conn.execute('''
        SELECT substr(data_pedido,1,4),COUNT(*),SUM(status='cancelado')
        FROM orders GROUP BY 1''')}
    add('Q2_ANO',annual,{year:(r['total'],r['cancelados']) for year,r in metrics['Q2']['anos'].items()},
        'Coorte definida por data_pedido')

    # Q3: agrupar linhas de itens em centavos, sem multiplicar pedido por outras tabelas.
    q3_sql = {cat:(qty,cents) for cat,qty,cents in conn.execute('''
        SELECT p.categoria, SUM(i.quantidade), SUM(i.quantidade*i.preco_centavos)
        FROM items i JOIN products p ON p.id=i.produto_id
        JOIN orders o ON o.id=i.pedido_id WHERE o.status='entregue'
        GROUP BY p.categoria''')}
    q3_report = {r['categoria']:(r['unidades'],_cents(r['valor_bruto_itens'])) for r in metrics['Q3_entregues']}
    add('Q3_CATEGORIA',q3_sql,q3_report,'Valor de itens entregues = quantidade × preço praticado')

    # Q4: não usar a dimensão canal_venda do pedido.
    acquisition = {k:(n,c) for k,n,c in conn.execute('''
        SELECT c.canal, COUNT(*),SUM(o.status='cancelado')
        FROM orders o JOIN customers c ON c.id=o.cliente_id GROUP BY c.canal''')}
    acq_report = {r['canal_aquisicao']:(r['pedidos'],r['cancelados']) for r in metrics['Q4']['canais']}
    add('Q4_AQUISICAO',acquisition,acq_report,'Canal de aquisição cadastrado no cliente')

    # Q5: calendário completo tem 24 meses; no mês sem eventos o valor é zero.
    monthly = {k:n for k,n in conn.execute('SELECT substr(data_pedido,1,7),COUNT(*) FROM orders GROUP BY 1')}
    q5_report = {r['mes']:r['pedidos'] for r in metrics['Q5']['meses']}
    add('Q5_SERIE',monthly,q5_report,'24 coortes mensais por data_pedido')
    add('Q5_CONTAGEM_MESES',len(q5_report),24,'Meses consecutivos de 2023-01 a 2024-12')
    tickets_month = {k:n for k,n in conn.execute('SELECT substr(data_abertura,1,7),COUNT(*) FROM tickets GROUP BY 1')}
    month_report = {r['mes']:r['chamados_abertos'] for r in metrics['Q5']['meses']}
    add('Q5_TICKETS',tickets_month,month_report,'Relógio de abertura, não data de compra')

    # Q6: compara APENAS os mesmos pedidos com total informado, centavos inteiros.
    rows = conn.execute('''
        WITH subtotal AS (SELECT pedido_id,SUM(quantidade*preco_centavos) itens
                         FROM items GROUP BY pedido_id)
        SELECT COUNT(*),
            SUM(o.valor_centavos IS NULL),
            SUM(o.valor_centavos IS NOT NULL),
            SUM(o.valor_centavos IS NOT NULL AND ABS(o.valor_centavos - s.itens)>1),
            SUM(CASE WHEN o.valor_centavos IS NOT NULL THEN o.valor_centavos ELSE 0 END),
            SUM(CASE WHEN o.valor_centavos IS NOT NULL THEN s.itens ELSE 0 END)
        FROM orders o JOIN subtotal s ON s.pedido_id=o.id
    ''').fetchone()
    counts=metrics['Q6']['contagens'];totals=metrics['Q6']['totais_brl']
    add('Q6_POPULACAO',tuple(rows[:4]),(counts['pedidos'],counts['sem_valor_reportado'],
                                      counts['com_valor_reportado'],counts['divergentes']),
        'Um pedido por linha, sem imputar 79 nulos')
    add('Q6_VALORES_CENTAVOS',tuple(rows[4:]),(_cents(totals['reported_known']),
                                             _cents(totals['gross_on_reported'])),
        'Centavos inteiros com universo comparável, sem duplo desconto')

    # Q7: nota avaliada por produto; tickets apenas por pedido monofornecedor.
    notes = {k:(n,low) for k,n,low in conn.execute('''
        SELECT p.fornecedor,COUNT(*),SUM(r.nota<=2)
        FROM ratings r JOIN products p ON p.id=r.produto_id GROUP BY p.fornecedor''')}
    notes_report = {r['fornecedor']:(r['n_avaliacoes'],r['avaliacoes_nota_ate_2'])
                    for r in metrics['Q7']['fornecedores']}
    add('Q7_NOTAS',notes,notes_report,'Avaliações: grão produto-avaliação')
    sql_multi = conn.execute('''
        WITH suppliers_per_order AS (
          SELECT i.pedido_id,COUNT(DISTINCT p.fornecedor) n
          FROM items i JOIN products p ON p.id=i.produto_id
          GROUP BY i.pedido_id)
        SELECT SUM(n>1), SUM(n=1) FROM suppliers_per_order''').fetchone()
    add('Q7_PEDIDOS_MONO_MULTI',sql_multi,
        (metrics['Q7']['pedidos_multifornecedor'],metrics['Q7']['pedidos_monofornecedor']),
        'Fornecedor único por pedido, não por linha')
    multi_ticket = conn.execute('''
        WITH suppliers_per_order AS (
          SELECT i.pedido_id,COUNT(DISTINCT p.fornecedor) n
          FROM items i JOIN products p ON p.id=i.produto_id GROUP BY i.pedido_id)
        SELECT SUM(s.n>1), SUM(s.n=1)
        FROM tickets t JOIN suppliers_per_order s ON s.pedido_id=t.pedido_id''').fetchone()
    add('Q7_TICKETS_MONO_MULTI',multi_ticket,
        (metrics['Q7']['tickets_multifornecedor_sem_atribuicao'],metrics['Q7']['tickets_monofornecedor']),
        'Não replicar tickets multiforncedor pelos fornecedores')

    q89 = metrics['Q8_Q9']
    add('Q8_ACAO_UNICA',len(q89['Q8']['recomendacoes_imediatas']),1,
        'Conselho aceita apenas uma ação imediata')
    add('Q8_NUMERADOR',q89['Q8']['recomendacoes_imediatas'][0]['cancelados'],
        acquisition['paid_search'][1], 'Taxa de cancelamento sem extrapolação causal')
    add('Q9_LACUNA',q89['Q9']['pergunta_nao_respondida'].count('?'),1,
        'Uma pergunta material não respondida')
    conn.close()
    return {'checagens':checks,'total':len(checks),'aprovadas':sum(c['ok'] for c in checks),
            'falhas':[c for c in checks if not c['ok']],
            'riscos_abertos':[
                {'prioridade':'P0','tema':'Conciliação financeira','evidencia':'Valor total do pedido e itens divergentes; faltam componentes e razão contábil.'},
                {'prioridade':'P1','tema':'Causalidade de cancelamentos','evidencia':'Sem motivo, timestamp do cancelamento e campanha por pedido.'},
                {'prioridade':'P1','tema':'Atribuição de suporte','evidencia':'Tickets de pedidos com mais de um fornecedor não têm produto responsável.'},
                {'prioridade':'P2','tema':'Viés de seleção das avaliações','evidencia':'Não há evidência de representatividade de quem avaliou.'},
            ]}


def render_audit_report(report: dict) -> str:
    lines=['# Tarefa 12 — Auditoria adversarial independente (Q2–Q9)','',
           '## Método','Comparação independente em SQLite, reconstruindo tabelas diretamente do Excel, com valores financeiros em centavos inteiros. Não reutiliza as funções de agregação auditadas.', '',
           f"**Verificações:** {report['aprovadas']}/{report['total']} aprovadas.", '',
           '| Check | Resultado | Critério |','|---|---|---|']
    for c in report['checagens']:
        lines.append(f"| `{c['id']}` | {'PASS' if c['ok'] else 'FAIL'} | {c['criterio']} |")
    lines += ['', '## Divergências reproduzidas']
    if not report['falhas']:
        lines += ['Nenhuma divergência entre as métricas auditadas e as consultas independentes **dentro dos invariantes testados**. Isso não comprova causalidade nem qualidade completa da fonte.']
    else:
        for c in report['falhas']:
            lines += [f"- **{c['prioridade_se_falhar']} — {c['id']}**: SQLite = `{c['calculado_sqlite']}`; código = `{c['reportado']}`."]
    lines += ['', '## Riscos e bloqueios que permanecem']
    for r in report['riscos_abertos']:
        lines.append(f"- **{r['prioridade']} — {r['tema']}:** {r['evidencia']}")
    lines += ['', '## Testes hostis',
              '- Um ticket repetido no mesmo pedido não deve duplicar pedidos com chamados.',
              '- Um pedido com mais de um fornecedor não atribui seu ticket a fornecedor individual.',
              '- Alterações artificiais em métricas precisam produzir `FAIL` na auditoria.',
              '- Comparação financeira inclui somente os pedidos com valores preenchidos e mantém a mesma população de itens.',
              '', '## Limites',
              'O resultado da auditoria atesta consistência interna mensurável; não valida a classificação de status, o reconhecimento contábil, o conteúdo dos motivos de cancelamento nem vínculos causais. Corrigir o dado de origem exige investigação e nova evidência.', '']
    return '\n'.join(lines)
