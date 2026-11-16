"""Gera memo e relatório a partir de outputs/metricas.json (sem números digitados manualmente)."""
import json
from pathlib import Path
from decimal import Decimal
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.utils import simpleSplit
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'outputs/metricas.json').read_text(encoding='utf-8'))

def n(v):return f'{int(v):,}'.replace(',','.')
def pct(v):return f'{v:.2f}'.replace('.',',')+'%'
def cur(v):
    d=Decimal(str(v));return 'R$ '+f'{d:,.2f}'.replace(',','§').replace('.',',').replace('§','.')
def million(v): return f'R$ {float(v)/1_000_000:.2f}'.replace('.',',')+' mi'
def rows_md(data,keys,labels=None):
    labels=labels or keys
    return '| '+' | '.join(labels)+' |\n| '+' | '.join(['---']*len(keys))+' |\n'+'\n'.join('| '+' | '.join(str(row.get(k,'')) for k in keys)+' |' for row in data)+'\n'

q2=m['Q2'];q3=m['Q3_entregues'];q4=m['Q4'];q5=m['Q5'];q6=m['Q6'];q7=m['Q7']
paid=q4['canais'][0];delta=q7['fornecedores'][0]
rev_sorted=sorted(q3,key=lambda x:Decimal(x['valor_bruto_itens']),reverse=True)
vol_sorted=sorted(q3,key=lambda x:x['unidades'],reverse=True)

q1='''**Q1 — Três perguntas (congeladas antes da leitura da base)**

1. **Camila:** os 40% representam aumento no número absoluto de cancelamentos ou na taxa de cancelamento, e qual denominador foi usado?
2. **Rogério:** qual evento faz um pedido contar como cancelado no seu relatório e em que momento ele é reconhecido?
3. **Ambos:** vocês usam os mesmos períodos de referência, filtros de clientes e canais e critérios de inclusão de pedidos?'''

memo=f'''# ORBITSHOP | Memo ao conselho

{q1}

**Q2 — Cancelamentos.** Dos {n(q2['n'])} pedidos, {n(next(r['pedidos'] for r in q2['tabela_status'] if r['status']=='cancelado'))} ({pct(next(r['percentual'] for r in q2['tabela_status'] if r['status']=='cancelado'))}) estão cancelados. A taxa passou de {pct(q2['anos']['2023']['taxa_cancelamento_pct'])} em 2023 para {pct(q2['anos']['2024']['taxa_cancelamento_pct'])} em 2024 (+{q2['variacao_taxa_pontos_percentuais']:.2f} p.p.), mas o número caiu {abs(q2['variacao_cancelados_pct']):.1f}%. Nenhuma das declarações da diretoria se reproduz nesta definição.

**Q3 — Categorias.** Entre pedidos entregues, Eletrônicos lidera valor bruto de itens ({million(q3[0]['valor_bruto_itens'])}) e unidades ({n(q3[0]['unidades'])}). Os rankings divergem: Moda é terceira em unidades e quinta em valor, devido ao menor preço médio.

**Q4 — Aquisição.** `paid_search` cancela {pct(paid['taxa_cancelamento_pct'])} ({n(paid['cancelados'])}/{n(paid['pedidos'])}), ante 11,67%–12,38% nos demais canais; concentra {pct(q4['fracao_cancelamentos_paid_search_pct'])} dos cancelamentos. Seu ticket médio registrado em pedidos entregues é {cur(paid['ticket_medio_entregue_reportado'])}, sem superioridade material sobre os demais.

**Q5 — Sazonalidade.** Novembro/2023 teve {n(q5['maior_mes_por_ano']['2023']['pedidos'])} pedidos; hipótese: ação promocional, não comprovada. Dos {n(q5['chamados_nov_dez_2023'])} chamados abertos em nov.–dez., {n(q5['chamados_nov_dez_ligados_pedidos_nov'])} referem-se a compras de novembro.

**Q6 — Integridade.** Há {q6['contagens']['sem_valor_reportado']} totais ausentes. Nenhum dos {n(q6['contagens']['com_valor_reportado'])} demais reconcilia com os itens brutos; a reaplicação de descontos foi descartada por dupla dedução. O total registrado ({million(q6['totais_brl']['reported_known'])}) não é receita auditada; valores dos itens são apenas proxy, não receita reconhecida.

**Q7 — Fornecedores.** DeltaFornece tem nota média {str(f"{delta['nota_media']:.2f}").replace('.',',')}/5 ({n(delta['n_avaliacoes'])} avaliações), mas sua taxa de chamados em pedidos exclusivamente seus ({pct(delta['incidencia_chamado_mono_pct'])}) não explica isoladamente o pico.

**Q8 — Decisão.** Congelar a expansão de `paid_search` até apurar a causa dos cancelamentos, acompanhando sua taxa semanal; adia-se a intervenção no fornecedor com pior avaliação.

**Q9 — Lacuna.** Solicitar motivos e histórico de cancelamentos, eventos de pagamento e campanhas por pedido, para distinguir fraude, falha operacional e perfil de aquisição.

**Uso de IA.** ChatGPT auxiliou na implementação e análise. O protótipo reaplicava indevidamente descontos; a correção usa apenas o preço praticado e preserva {n(q6['contagens']['desconto_desconhecido_pedidos'])} pedidos com descontos desconhecidos. Foram executados testes automatizados.
'''
# Count textual words excluding markup
import re
words=re.findall(r'\b[\wÀ-ÿ][\wÀ-ÿ.,–%/-]*\b', re.sub(r'\*|`|#','',memo))
(ROOT/'MEMO_FINAL.md').write_text(memo+'\n<!-- Contagem aproximada: '+str(len(words))+' palavras. -->\n',encoding='utf-8')
print('MEMO word count:',len(words))
if len(words)>400:
    raise SystemExit('Memo excede limite de 400 palavras')

status=[{'status':r['status'],'pedidos':n(r['pedidos']),'percentual':pct(r['percentual'])} for r in q2['tabela_status']]
cat_r=[{'categoria':r['categoria'],'receita':cur(r['valor_bruto_itens']),'unidades':n(r['unidades']),
        'preco':cur(r['preco_medio_ponderado'])} for r in rev_sorted]
chan_r=[{'canal':r['canal_aquisicao'],'n':n(r['pedidos']),'c':n(r['cancelados']),'taxa':pct(r['taxa_cancelamento_pct']),
         'ticket':cur(r['ticket_medio_entregue_reportado']),'faltantes':r['entregues_sem_valor']} for r in q4['canais']]
sup_r=[{'fornecedor':r['fornecedor'],'av':n(r['n_avaliacoes']),'media':f"{r['nota_media']:.2f}",
      'neg':pct(r['avaliacoes_negativas_pct']),'suporte':pct(r['incidencia_chamado_mono_pct']),
      'mono':n(r['pedidos_monofornecedor'])} for r in q7['fornecedores']]
months_r=[{'mes':r['mes'],'pedidos':n(r['pedidos']),'tickets':n(r['chamados_abertos'])} for r in q5['meses']]

report=f'''# Relatório técnico — OrbitShop (Q1–Q9)

**Fonte da verdade:** `input/Base_Dados_OrbitShop_v3.xlsx` e `input/Case_OrbitShop_Individual_v2.pptx`. Indicadores gerados por `python -m src.run`. Gráficos e CSVs em `outputs/`. Documento técnico auxiliar: o memo é a entrega executiva de uma página.

## Q1 — Perguntas preservadas antes da análise

{q1}

## Auditoria de dados

{rows_md([{'tabela':name,'n':n(v['registros']),'nulos':', '.join(f'{k}: {val}' for k,val in v['ausentes'].items() if val) or 'nenhum'} for name,v in m['auditoria']['tabelas'].items()],['tabela','n','nulos'],['Tabela','Registros','Campos ausentes'])}

As chaves estrangeiras declaradas retornaram **zero órfãos**; `Tickets_Suporte` e `Avaliacoes` respeitam cliente do pedido, datas posteriores à compra e avaliação de produto realmente comprado. O grão das tabelas foi preservado (não somar `Pedidos.valor_total` após join com múltiplos itens).

## Q2 — Status e contradição dos executivos

{rows_md(status,['status','pedidos','percentual'],['Status','Pedidos','% do total'])}

2023: **{n(q2['anos']['2023']['cancelados'])} cancelados / {n(q2['anos']['2023']['total'])} pedidos = {pct(q2['anos']['2023']['taxa_cancelamento_pct'])}**. 2024: **{n(q2['anos']['2024']['cancelados'])} / {n(q2['anos']['2024']['total'])} = {pct(q2['anos']['2024']['taxa_cancelamento_pct'])}**.

Portanto, a quantidade caiu **{pct(abs(q2['variacao_cancelados_pct']))}** e a taxa subiu **{q2['variacao_taxa_pontos_percentuais']:.3f} p.p.** ({pct(q2['variacao_taxa_relativa_pct'])} de crescimento relativo da taxa). Os 40% alegados e os 18%→16% alegados não se reproduzem na base sob a mesma coorte (ano de `data_pedido`). Não há histórico de data de cancelamento para comparar períodos por evento de cancelamento.

![Q2](../outputs/q2_status.png)

## Q3 — Categorias (pedidos entregues, valores brutos de itens)

{rows_md(cat_r,['categoria','receita','unidades','preco'],['Categoria','Valor bruto de itens','Unidades','Preço médio ponderado'])}

**Ranking de valor:** {' > '.join(r['categoria'] for r in rev_sorted)}.

**Ranking de volume:** {' > '.join(r['categoria'] for r in vol_sorted)}.

As listas não coincidem integralmente: Moda passa de terceira em quantidade para quinta em valor. A diferença é compatível com a variação de preço médio ponderado. Esses valores são **valor bruto comercial potencial dos itens de pedidos com status `entregue`**, não receitas contábeis; os cenários `Q3_nao_cancelados` e `Q3_todos` estão em `outputs/` para sensibilidade.

## Q4 — Aquisição de clientes e cancelamentos

{rows_md(chan_r,['canal','n','c','taxa','ticket','faltantes'],['Canal de aquisição','Pedidos','Cancelados','Taxa','Ticket médio*','Nulos*'])}

*Ticket médio calculado exclusivamente nos pedidos entregues com `Pedidos.valor_total` informado; **não representa receita comprovada**, devido à Q6. A amostra total de pedidos entregues é {n(sum(r['entregues'] for r in q4['canais']))}; com valor válido, {n(sum(r['entregues_com_valor'] for r in q4['canais']))}. O canal `paid_search` reúne **{pct(q4['fracao_cancelamentos_paid_search_pct'])}** dos cancelamentos embora represente **{pct(paid['participacao_pct'])}** dos pedidos. O padrão persiste em estratos B2B e B2C e nos dois anos (arquivo `outputs/q4_estratos.csv`). Associação não demonstra causalidade, e variações de ticket registrado devem ser interpretadas com cautela.

![Q4](../outputs/q4_aquisicao.png)

## Q5 — Série mensal e hipóteses

{rows_md(months_r,['mes','pedidos','tickets'],['Mês','Pedidos criados','Chamados abertos'])}

- **Novembro/2023** teve {n(q5['maior_mes_por_ano']['2023']['pedidos'])} pedidos vs 500–600 na maioria dos meses: hipótese não comprovada de campanha/promoção; solicitar calendário de campanhas.
- **Maio/2024**, com {n(q5['maior_mes_por_ano']['2024']['pedidos'])} pedidos, foi o maior mês de 2024, mas a amplitude anual é modesta; hipótese: variação sazonal/comercial normal, sem comprovação.
- O pico de chamados foi em **novembro ({n(next(r['chamados_abertos'] for r in q5['meses'] if r['mes']=='2023-11'))}) e dezembro/2023 ({n(next(r['chamados_abertos'] for r in q5['meses'] if r['mes']=='2023-12'))})**. Dos {n(q5['chamados_nov_dez_2023'])} chamados abertos nos dois meses, {n(q5['chamados_nov_dez_ligados_pedidos_nov'])} ({pct(q5['pct_chamados_nov_dez_ligados_pedidos_nov'])}) se referem a pedidos feitos em novembro. O volume extra de pedidos contribui para o pico; o dataset não estabelece que a operação piorou.
- Na coorte de novembro/2023, {n(next(r['pedidos_com_ticket'] for r in q5['coortes_suporte'] if r['mes_compra']=='2023-11'))} de {n(q5['maior_mes_por_ano']['2023']['pedidos'])} pedidos abriram ao menos um chamado ({pct(next(r['incidencia_pedidos_com_ticket_pct'] for r in q5['coortes_suporte'] if r['mes_compra']=='2023-11'))}), similar aos meses vizinhos. Taxas por coorte em `outputs/q5_coortes_suporte.csv`.

![Q5](../outputs/q5_mensal.png)

## Q6 — Reconciliação financeira crítica

- {n(q6['contagens']['pedidos'])} pedidos; **{n(q6['contagens']['sem_valor_reportado'])} com `valor_total` ausente**; {n(q6['contagens']['desconto_desconhecido_pedidos'])} pedidos contendo desconto sem informação em pelo menos um item.
- Dos {n(q6['contagens']['com_valor_reportado'])} valores disponíveis, **{n(q6['contagens']['gross_equal_within_cent'])} conciliam** à soma de `quantidade × preco_praticado` por pedido, com tolerância de R$ 0,01. O cenário de reaplicar o desconto foi descartado por **dupla dedução** do preço praticado.
- **Soma de `Pedidos.valor_total` não nulos**: {cur(q6['totais_brl']['reported_known'])}. **Soma bruta dos itens nos mesmos pedidos**: {cur(q6['totais_brl']['gross_on_reported'])}. **Diferença assinada (reportado − bruto)**: {cur(q6['totais_brl']['gross_signed_residual'])}. A soma de diferenças absolutas é {cur(q6['totais_brl']['gross_abs_residual'])}; {n(q6['contagens']['reported_less_gross'])} totais menores e {n(q6['contagens']['reported_greater_gross'])} maiores.
- **Todos os itens, inclusive pedidos sem total reportado**: {cur(q6['totais_brl']['gross_all'])}; apenas status `entregue`: {cur(q6['totais_brl']['gross_delivered'])}. **Não reaplicar desconto** ao preço praticado já líquido de descontos conhecidos. Para valores ausentes, preservar a ausência e solicitar a regra financeira à empresa.
- **Escolha para conselho:** não apresentar o valor registrado como receita auditada, nem a soma bruta como receita reconhecida. Para evidenciar escala comercial, reportar volume de pedidos, quantidade de itens e **valor bruto de itens em pedidos entregues** com rótulo de *proxy não contábil*, condicionando qualquer afirmação de receita/margem à conciliação com transações financeiras, reembolsos, frete, impostos e descontos efetivos. O arquivo `outputs/q6_reconciliacao_pedido.csv` contém todos os {n(q6['contagens']['pedidos'])} confrontos.

## Q7 — Avaliações de fornecedores e chamados de suporte

{rows_md(sup_r,['fornecedor','av','media','neg','mono','suporte'],['Fornecedor','Avaliações','Nota média','% nota ≤ 2','Pedidos mono','Ticket/mono'])}

O fornecedor **{delta['fornecedor']}** é um outlier negativo de avaliações: {pct(delta['avaliacoes_negativas_pct'])} das {n(delta['n_avaliacoes'])} avaliações têm nota ≤2, ante taxas significativamente inferiores nos outros fornecedores. Contudo, os {n(delta['tickets_nesses_pedidos'])} chamados nos {n(delta['pedidos_monofornecedor'])} pedidos exclusivamente de seus produtos representam {pct(delta['incidencia_chamado_mono_pct'])}, sem taxa anormalmente alta comparada aos pares.

**Cautela de granularidade:** {n(q7['pedidos_multifornecedor'])} pedidos contêm mais de um fornecedor e **{n(q7['chamados_multifornecedor_sem_atribuicao'])} chamados** referem-se a esses pedidos; o fornecedor responsável pelo ticket não é identificado. As colunas "fornecedor presente no pedido" são associações, não atribuição de culpa. As categorias dos chamados no último trimestre de 2023 são múltiplas: {', '.join(f'{k} {n(v)}' for k,v in q7['chamados_trimestre_final_2023_por_causa'].items())}. O pico está temporalmente ligado ao volume excepcional de compras em novembro, portanto o problema da Delta é apenas parte da história.

![Q7](../outputs/q7_fornecedores.png)

## Q8 — Uma ação e seu custo de oportunidade

**Ação imediata recomendada:** congelar **a expansão de investimento em `paid_search`** até esclarecer os motivos dos cancelamentos desse canal, sem assumir que toda campanha atual deve ser desligada. O canal concentra **{n(paid['cancelados'])} cancelamentos ({pct(q4['fracao_cancelamentos_paid_search_pct'])} do total)**, taxa **{pct(paid['taxa_cancelamento_pct'])}** contra 11,67%–12,38% nos outros canais; a diferença se mantém por ano e segmento. **Indicador de sucesso:** queda sustentada da taxa de cancelamento do canal usando a mesma definição e coortes comparáveis, monitorando também pedidos e conversão. **Trade-off explícito:** adiar intervenção imediata na qualidade do fornecedor Delta; o risco é perder crescimento de vendas provenientes de mídia paga. *Sem reconciliação financeira não é possível prometer recuperação de margem em reais.*

## Q9 — Pergunta sem resposta e dados faltantes

**Por que os pedidos originados de `paid_search` cancelam mais: problema de pagamento, fraude, expectativa comercial, estoque ou logística?** Exigir motivo de cancelamento por pedido, data/hora de mudanças de status, tentativas/autorização/estorno de pagamento, campanha/anúncio e custo de aquisição, registros de estoque/prazo e eventos do funil. Também requisitar componentes financeiros necessários para reconciliar `valor_total` com itens. Sem isso, a ação é preventiva e sujeita a revisão, não uma conclusão causal.

## Uso de IA e verificação

IA foi utilizada para prototipar o leitor XLSX, cálculos, visualização e redação. **Erro de simplificação identificado:** aplicar `desconto_aplicado` novamente ao `preco_praticado`, que já embute o desconto. Correção: somente `quantidade × preco_praticado` como proxy e 79 `valor_total` nulos mantidos. Há 301 pedidos com informação de desconto ausente. Houve ainda correção de uma dependência indevida do canal `paid_search` em teste sintético, e otimização de teste que reconstruía o índice de pedidos repetidamente. Foram executados **74 testes** com pytest, além de cruzamentos independentes com SQLite para status e aquisição. O relatório não atribui à IA verificação humana externa que não ocorreu.

## Limites

Os status são fotografias atuais sem histórico de eventos. Não há comprovantes de pagamento, histórico de cancelamento, origem por produto dos tickets em pedidos multifornnecedor, cronograma de campanhas ou despesas de aquisição. Valores brutos não equivalem a faturamento e variações associativas não demonstram causalidade.
'''
(ROOT/'docs/RELATORIO_TECNICO.md').write_text(report,encoding='utf-8')

# PDF memo: compacto, one-page, com título e Q1 imediatamente abaixo
font_reg='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font_bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DV',font_reg));pdfmetrics.registerFont(TTFont('DV-Bold',font_bold))
pdfmetrics.registerFontFamily('DV',normal='DV',bold='DV-Bold',italic='DV',boldItalic='DV-Bold')

file=ROOT/'MEMO_ORBITSHOP.pdf'
doc=SimpleDocTemplate(str(file),pagesize=A4,rightMargin=39,leftMargin=39,topMargin=38,bottomMargin=35,
    title='Memo Executivo — OrbitShop',author='Case individual — Peers Consulting')
style=ParagraphStyle('body',fontName='DV',fontSize=9.15,leading=14.15,spaceAfter=8,textColor=colors.HexColor('#263247'))
qstyle=ParagraphStyle('question',parent=style,fontSize=8.8,leading=13.0,spaceAfter=6)
titlestyle=ParagraphStyle('title',fontName='DV-Bold',fontSize=16.2,leading=20,spaceAfter=14,textColor=colors.HexColor('#132B43'))
subtitle=ParagraphStyle('sub',parent=style,fontName='DV-Bold',fontSize=9,leading=13.5,spaceBefore=6,spaceAfter=5,textColor=colors.HexColor('#142A42'))

def body_para(text):
    return Paragraph(escape(text),style)

def rich(text,style):
    return Paragraph(text,style)

story=[rich('ORBITSHOP | MEMO AO CONSELHO',titlestyle)]
# extrai os segmentos da versão .md sem alterar conteúdo
lines=memo.splitlines();
for ln in lines[2:]:
    if not ln.strip():continue
    if ln.startswith('**Q1'):
        story.append(rich('<b>Q1 — Três perguntas (antes da análise)</b>',subtitle)); continue
    if ln.startswith(('1. **Camila','2. **Rogério','3. **Ambos')):
        label,content=ln.split('** ',1) if '** ' in ln else ('',ln)
        # use markdown -> simples tags
        content=ln.replace('**','')
        story.append(rich(escape(content),qstyle));continue
    if ln.startswith('**'):
        first_end=ln.find('**',2)
        heading=ln[2:first_end]
        text=ln[first_end+2:].strip()
        story.append(rich('<b>'+escape(heading)+'</b> '+escape(text).replace('`',''),style))


def page_decor(canvas,doc):
    canvas.saveState()
    w,h=A4
    canvas.setFillColor(colors.HexColor('#253F5A'))
    canvas.rect(0,h-7,w,7,fill=1,stroke=0)
    canvas.setStrokeColor(colors.HexColor('#D8E2EA'))
    canvas.line(39,27,w-39,27)
    canvas.setFont('DV',7)
    canvas.setFillColor(colors.HexColor('#5B6470'))
    canvas.drawString(39,16,'OrbitShop | Case individual | Série C: evidências e decisões')
    canvas.drawRightString(w-39,16,'Página '+str(doc.page))
    canvas.restoreState()

doc.build(story,onFirstPage=page_decor,onLaterPages=page_decor)
print('PDF gerado em',file,'tamanho',file.stat().st_size)
