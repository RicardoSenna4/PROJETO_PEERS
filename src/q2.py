"""Apresentação auditável da Q2: status e cancelamentos por coorte anual."""
from __future__ import annotations


def q2_years_rows(metrics: dict) -> list[dict]:
    """Uma linha por ano da compra. Não representa o ano do cancelamento."""
    return [
        {
            'ano': year,
            'pedidos': values['total'],
            'cancelados': values['cancelados'],
            'taxa_cancelamento_pct': values['taxa_cancelamento_pct'],
        }
        for year, values in sorted(metrics['anos'].items())
    ]


def _int(n: int) -> str:
    return f'{n:,}'.replace(',', '.')


def _pct(n: float | None) -> str:
    return 'n/d' if n is None else f'{n:.2f}'.replace('.', ',') + '%'


def render_q2_report(m: dict) -> str:
    """Relatório conciso, a partir da mesma função que alimenta CSV e gráfico."""
    rows = m['tabela_status']
    annual = q2_years_rows(m)
    cancelled = next((r for r in rows if r['status'] == 'cancelado'), None)
    if cancelled is None:
        raise ValueError('Q2 sem status cancelado; conferir o universo analisado')
    lines = [
        '# Tarefa 5 — Q2: pedidos por status',
        '',
        '## Definição',
        '',
        'Unidade: **pedido distinto**, com `Pedidos.id` único. Universo: todos os pedidos com '
        '`data_pedido` entre 2023-01-01 e 2024-12-31. O status é a **fotografia atual** '
        'da base e o ano é o **ano da compra**, não o ano em que ocorreu um cancelamento.',
        '',
        '## Distribuição geral',
        '',
        '| Status | Pedidos | Participação |',
        '|---|---:|---:|',
    ]
    for row in rows:
        lines.append(f"| `{row['status']}` | {_int(row['pedidos'])} | {_pct(row['percentual'])} |")
    lines += [
        f"| **Total** | **{_int(m['n'])}** | **100,00%** |",
        '',
        'Visualização: [`outputs/q2_status.png`](../outputs/q2_status.png). '
        'Exportação: [`outputs/q2_status.csv`](../outputs/q2_status.csv).',
        '',
        '## Cancelamentos por coorte anual',
        '',
        '| Ano do pedido | Total | Cancelados | Taxa |',
        '|---|---:|---:|---:|',
    ]
    for row in annual:
        lines.append(f"| {row['ano']} | {_int(row['pedidos'])} | {_int(row['cancelados'])} | {_pct(row['taxa_cancelamento_pct'])} |")
    lines += [
        '',
        f"- Total cancelado: **{_int(cancelled['pedidos'])}** de **{_int(m['n'])}** "
        f"(**{_pct(cancelled['percentual'])}**).",
        f"- Variação da quantidade cancelada, 2024 versus 2023: **{_pct(m['variacao_cancelados_pct'])}**.",
        '- Variação absoluta da taxa: **'
        + (f"{m['variacao_taxa_pontos_percentuais']:+.2f}".replace('.', ',') if m['variacao_taxa_pontos_percentuais'] is not None else 'n/d')
        + ' ponto percentual**.',
        f"- Variação relativa da taxa: **{_pct(m['variacao_taxa_relativa_pct'])}**.",
        '',
        '## Interpretação e confronto das falas',
        '',
        'A quantidade de cancelamentos **diminuiu**, enquanto a taxa aumentou ligeiramente, '
        'porque o total de pedidos caiu ainda mais. Usando esta mesma população, período '
        'e definição, as falas de crescimento de 40% e queda da taxa de 18% para 16% '
        '**não são confirmadas**. As alegações podem ter usado janelas, status, '
        'eventos de cancelamento ou denominadores diferentes; isso não é verificável '
        'sem os critérios e o histórico dos relatórios originais.',
        '',
        '## Controles de qualidade',
        '',
        f"- Soma dos status: **{_int(sum(r['pedidos'] for r in rows))}**; "
        f"total de pedidos: **{_int(m['n'])}**.",
        f"- Soma das duas coortes: **{_int(sum(r['pedidos'] for r in annual))}**.",
        '- Teste independente: agrupamento por `id`, `status` e `ano` com SQLite.',
        '- Limitação: falta a data/histórico do evento de cancelamento, portanto não '
        'é possível afirmar a tendência de cancelamentos ocorridos em cada ano.',
        '',
    ]
    return '\n'.join(lines)
