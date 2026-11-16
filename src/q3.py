"""Q3: rankings por valor comercial praticado e volume de unidades.

Não converter o valor calculado em receita contábil: o case não fornece
reconciliação do valor registrado com os itens nem reconhecimento financeiro.
"""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from .analysis import categories_metrics, indexed, money


STATUS_CENARIOS = {
    'entregues': frozenset({'entregue'}),
    'nao_cancelados': frozenset({'entregue', 'em_transito', 'devolvido'}),
    'todos': frozenset({'entregue', 'em_transito', 'devolvido', 'cancelado'}),
}


def _validate_item_join(data: dict) -> None:
    """Valida cardinalidade 1:1 das dimensões e a integridade dos itens."""
    orders = indexed(data['Pedidos'])
    products = indexed(data['Produtos'])
    indexed(data['Itens_Pedido'])
    for item in data['Itens_Pedido']:
        if item['pedido_id'] not in orders:
            raise ValueError(f"Item {item['id']} faz referência a pedido inexistente")
        if item['produto_id'] not in products:
            raise ValueError(f"Item {item['id']} faz referência a produto inexistente")
        qty = item['quantidade']
        if not isinstance(qty, int) or isinstance(qty, bool) or qty <= 0:
            raise ValueError(f"Item {item['id']} possui quantidade inválida")
        if item['preco_praticado'] is None or money(item['preco_praticado']) < 0:
            raise ValueError(f"Item {item['id']} possui preço praticado inválido")


def build_q3(data: dict) -> dict:
    """Tabelas reproduzíveis sem expandir pedidos via joins com avaliações/tickets."""
    _validate_item_join(data)
    orders = indexed(data['Pedidos'])
    scenarios = {}
    for key, statuses in STATUS_CENARIOS.items():
        rows = categories_metrics(data, set(statuses))
        expected_items = [i for i in data['Itens_Pedido']
                          if orders[i['pedido_id']]['status'] in statuses]
        expected_units = sum(i['quantidade'] for i in expected_items)
        expected_value = sum((money(i['quantidade']) * money(i['preco_praticado'])
                              for i in expected_items), Decimal('0'))
        total_units = sum(r['unidades'] for r in rows)
        total_value = sum((money(r['valor_bruto_itens']) for r in rows), Decimal('0'))
        if (sum(r['linhas'] for r in rows) != len(expected_items)
                or total_units != expected_units or abs(total_value-expected_value) > Decimal('0.01')):
            raise AssertionError('Agregação Q3 não reconcilia com os itens elegíveis')
        scenarios[key] = {
            'status': sorted(statuses),
            'n_pedidos_elegiveis': sum(o['status'] in statuses for o in data['Pedidos']),
            'n_linhas_itens': len(expected_items),
            'unidades': total_units,
            'valor_comercial_itens': str(total_value),
            'ranking_receita': rows,
        }

    delivered = scenarios['entregues']
    revenue = delivered['ranking_receita']
    rev_order = sorted(revenue, key=lambda r: (-money(r['valor_bruto_itens']), r['categoria']))
    vol_order = sorted(revenue, key=lambda r: (-r['unidades'], r['categoria']))
    rank_revenue = {r['categoria']: idx for idx, r in enumerate(rev_order, start=1)}
    rank_volume = {r['categoria']: idx for idx, r in enumerate(vol_order, start=1)}
    total_value = money(delivered['valor_comercial_itens'])
    total_units = delivered['unidades']
    comparison = []
    for r in rev_order:
        category = r['categoria']
        category_value = money(r['valor_bruto_itens'])
        comparison.append({
            'categoria': category,
            'posicao_valor': rank_revenue[category],
            'posicao_volume': rank_volume[category],
            'variacao_posicao_volume_menos_valor': rank_volume[category] - rank_revenue[category],
            'valor_comercial_itens_brl': r['valor_bruto_itens'],
            'participacao_valor_pct': round(float(100 * category_value / total_value), 2) if total_value else 0,
            'unidades': r['unidades'],
            'participacao_volume_pct': round(100 * r['unidades'] / total_units, 2) if total_units else 0,
            'preco_medio_ponderado_brl': r['preco_medio_ponderado'],
            'pedidos_distintos_na_categoria': r['pedidos_distintos'],
            'linhas_itens': r['linhas'],
        })
    return {
        'criterio_principal': 'somente pedidos entregues',
        'metrica_valor': 'SOMA(quantidade * preco_praticado); proxy, não receita reconhecida',
        'metrica_volume': 'SOMA(quantidade) em unidades, não quantidade de pedidos',
        'comparacao': comparison,
        'ranking_volume': sorted(comparison, key=lambda r: r['posicao_volume']),
        'rankings_coincidem': all(rank_revenue[k] == rank_volume[k] for k in rank_revenue),
        'cenarios': scenarios,
    }


def _brl(value: str | Decimal | int) -> str:
    value = Decimal(str(value)).quantize(Decimal('0.01'))
    raw = f'{value:,.2f}'
    return 'R$ ' + raw.replace(',', '#').replace('.', ',').replace('#', '.')


def _pct(value: float) -> str:
    return f'{value:.2f}'.replace('.', ',') + '%'


def _integer(value: int) -> str:
    return f'{value:,}'.replace(',', '.')


def render_q3_report(result: dict) -> str:
    main = result['cenarios']['entregues']
    table = '\n'.join(
        f"| {r['posicao_valor']} | {r['categoria']} | {_brl(r['valor_comercial_itens_brl'])} | "
        f"{_pct(r['participacao_valor_pct'])} | {r['posicao_volume']} | "
        f"{_integer(r['unidades'])} | {_pct(r['participacao_volume_pct'])} | "
        f"{_brl(r['preco_medio_ponderado_brl'])} |"
        for r in result['comparacao'])
    volume_table = '\n'.join(
        f"| {r['posicao_volume']} | {r['categoria']} | {_integer(r['unidades'])} | "
        f"{r['posicao_valor']} | {_brl(r['valor_comercial_itens_brl'])} |"
        for r in result['ranking_volume'])
    scenarios = '\n'.join(
        f"| {key.replace('_',' ')} | {_integer(v['n_pedidos_elegiveis'])} | "
        f"{_integer(v['n_linhas_itens'])} | {_integer(v['unidades'])} | "
        f"{_brl(v['valor_comercial_itens'])} |"
        for key, v in result['cenarios'].items())
    differences = [r for r in result['comparacao'] if r['posicao_valor'] != r['posicao_volume']]
    examples = sorted(differences, key=lambda r: abs(r['variacao_posicao_volume_menos_valor']), reverse=True)[:2]
    evidence = (' Exemplos: ' + '; '.join(
        f"{r['categoria']} {r['posicao_volume']}º por unidades e {r['posicao_valor']}º por valor, "
        f"com valor médio de {_brl(r['preco_medio_ponderado_brl'])} por unidade"
        for r in examples) + '.' if examples else '')
    comparison_statement = (
        'Os rankings não coincidem.' if differences else 'Os rankings coincidem.'
    )
    return f"""# Tarefa 6 — Q3: categorias por valor comercial e por volume

## Regra de cálculo

- Fonte: abas `Pedidos`, `Itens_Pedido` e `Produtos` da planilha original.
- Grão primário: **linha de item**, unida 1:1 a pedido e produto; não juntar avaliações ou tickets.
- Filtro principal: **`Pedidos.status == 'entregue'`** (9.959 pedidos).
- Valor: `Σ(Itens_Pedido.quantidade × Itens_Pedido.preco_praticado)`. O preço praticado já contém o desconto conhecido: **não reaplicar `desconto_aplicado`**.
- Volume: `Σ(Itens_Pedido.quantidade)` (**unidades**, não pedidos ou linhas).
- O valor é um **proxy comercial de itens entregues**; não equivale a receita reconhecida, faturamento contábil ou margem. Os totais de `Pedidos.valor_total` não conciliam com os itens na Q6.

## Ranking por valor comercial (principal)

| Pos. valor | Categoria | Valor comercial | Participação valor | Pos. volume | Unidades | Participação unidades | Valor médio/unidade |
|---:|---|---:|---:|---:|---:|---:|---:|
{table}
| **Total** | **8 categorias** | **{_brl(main['valor_comercial_itens'])}** | **100%** | — | **{_integer(main['unidades'])}** | **100%** | — |

## Ranking por volume

| Pos. volume | Categoria | Unidades | Pos. valor | Valor comercial |
|---:|---|---:|---:|---:|
{volume_table}

## Interpretação

**{comparison_statement}** {evidence} A diferença de classificação é compatível com variações de valor médio ponderado por unidade; não demonstra causas comerciais ou de preferência.

## Sensibilidade ao filtro de status (não misturar universos)

| Cenário | Pedidos elegíveis | Linhas de itens | Unidades | Valor de itens |
|---|---:|---:|---:|---:|
{scenarios}

- Cenário **entregues**: principal e mais conservador como proxy de vendas efetivadas; ainda sujeito a reconciliação financeira.
- Cenário **não cancelados**: inclui devolvidos e em trânsito; não constitui receita realizada.
- Cenário **todos**: inclui cancelados e, portanto, é apenas volume/valor registrado nos itens criados.

## Verificações e arquivos

- Cada `Itens_Pedido.id` é único; `Produtos.id` e `Pedidos.id` são únicos. Não há expansão indevida no join.
- Soma das linhas elegíveis por categoria = linhas de itens elegíveis; idem para unidades e valor até R$ 0,01.
- Conferência independente via SQLite com totais em centavos inteiros, incluindo ranking.
- CSV: `outputs/q3_comparacao_entregues.csv` e `outputs/q3_ranking_volume.csv`; cenários existentes `outputs/q3_categorias_*.csv`.
- Gráficos: `outputs/q3_ranking_valor.png` e `outputs/q3_ranking_volume.png`.

**Limitações:** sem conciliação `valor_total`, sem confirmação de receita reconhecida e sem informação sobre os custos logísticos/impostos por pedido.
"""


def plot_q3(result: dict, out: Path) -> None:
    """Dois gráficos independentes: escalas monetária e física não são misturadas."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    for key, rows, field, label, title in (
        ('valor', result['comparacao'], 'valor_comercial_itens_brl', 'Valor comercial (R$ milhões)',
         'Q3 | Categorias por valor comercial — pedidos entregues'),
        ('volume', result['ranking_volume'], 'unidades', 'Unidades vendidas',
         'Q3 | Categorias por unidades — pedidos entregues'),
    ):
        descending = list(reversed(rows))
        values = ([float(Decimal(r[field])) / 1_000_000 for r in descending] if key == 'valor'
                  else [r[field] for r in descending])
        fig, ax = plt.subplots(figsize=(10, 4.5))
        bars = ax.barh([r['categoria'] for r in descending], values)
        labels = ([f'{v:.2f}' for v in values] if key == 'valor'
                  else [f'{v:,}'.replace(',', '.') for v in values])
        ax.bar_label(bars, labels=labels, padding=4, fontsize=9)
        ax.set_xlim(0, max(values) * 1.22)
        ax.set_xlabel(label)
        ax.set_title(title, loc='left', weight='bold')
        ax.spines[['top', 'right']].set_visible(False)
        fig.tight_layout()
        fig.savefig(out / f'q3_ranking_{key}.png', dpi=170)
        plt.close(fig)
