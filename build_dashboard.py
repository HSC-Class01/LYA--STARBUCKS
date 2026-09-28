from pathlib import Path
import json, html
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'; SITE=ROOT/'site'; SITE.mkdir(exist_ok=True)

def fmt(x):
    if pd.isna(x): return '—'
    return f'{x:,.1f}' if isinstance(x,float) else f'{x:,}'

def table(df, cols):
    if df.empty: return '<p class="empty">데이터가 아직 없습니다. GitHub Actions에서 DART_API_KEY를 설정한 뒤 업데이트를 실행하세요.</p>'
    heads=''.join(f'<th>{html.escape(c)}</th>' for c in cols)
    rows=[]
    for _,r in df.iterrows():
        rows.append('<tr>'+''.join(f'<td>{fmt(r.get(c))}</td>' for c in cols)+'</tr>')
    return f'<div class="table-wrap"><table><thead><tr>{heads}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'

a=pd.read_csv(DATA/'financials_analysis.csv') if (DATA/'financials_analysis.csv').exists() else pd.DataFrame()
f=pd.read_csv(DATA/'filings.csv') if (DATA/'filings.csv').exists() else pd.DataFrame()
meta=json.loads((DATA/'metadata.json').read_text()) if (DATA/'metadata.json').exists() else {'updated_at':'미수집'}
annual=a[a.period_type=='annual'].sort_values('year') if not a.empty else pd.DataFrame()
half=a[a.period_type=='half_year'].sort_values('year') if not a.empty else pd.DataFrame()
q=a[a.period_type.isin(['quarterly_q1','quarterly_q3','quarterly'])].sort_values(['year','period_type']) if not a.empty else pd.DataFrame()
labels={'quarterly_q1':'1Q','quarterly_q3':'3Q','quarterly':'Quarter'}
for df in [annual,half,q]:
    if not df.empty: df['period']=df.period_type.map(labels).fillna(df.period_type)
latest=annual.iloc[-1] if len(annual) else None
cards=''.join([f'<div class="card"><span>{t}</span><strong>{fmt(latest.get(c)) if latest is not None else "—"}</strong></div>' for t,c in [('매출액','revenue'),('영업이익','operating_profit'),('당기순이익','net_income'),('부채비율','debt_ratio')]])

def chart_data(df):
    if df.empty: return {'x':[],'revenue':[],'op':[],'net':[]}
    return {'x':df.year.astype(str).tolist(),'revenue':df.revenue.fillna(0).tolist(),'op':df.operating_profit.fillna(0).tolist(),'net':df.net_income.fillna(0).tolist()}
cd=json.dumps(chart_data(annual),ensure_ascii=False)
annual_cols=['year','revenue','gross_profit','operating_profit','net_income','assets','liabilities','equity','current_ratio','debt_ratio','roe','roa']
half_cols=['year','period','revenue','operating_profit','net_income','assets','liabilities','equity','current_ratio','debt_ratio']
q_cols=['year','period','revenue','operating_profit','net_income','current_ratio','debt_ratio']
peer='''<table><thead><tr><th>Peer firm</th><th>국내 사업</th><th>비고</th></tr></thead><tbody>
<tr><td>커피빈코리아</td><td>커피전문점</td><td>국내 직영 중심 커피 브랜드</td></tr>
<tr><td>투썸플레이스</td><td>카페·디저트</td><td>국내 커피·디저트 전문점</td></tr>
<tr><td>이디야</td><td>커피전문점</td><td>국내 커피 프랜차이즈</td></tr>
<tr><td>할리스</td><td>커피전문점</td><td>국내 커피·베이커리</td></tr>
<tr><td>엠즈씨드(폴 바셋)</td><td>커피전문점</td><td>매일유업 계열 커피 브랜드</td></tr>
</tbody></table>'''

html_doc=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Starbucks Korea Financial Dashboard</title><script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script><style>
:root{{--lav:#b8a1e6;--yellow:#fff1a8;--ink:#242329;--muted:#77727e;--line:#e9e5ef;--white:#fff}}*{{box-sizing:border-box}}body{{margin:0;background:#faf9fc;color:var(--ink);font-family:Inter,Apple SD Gothic Neo,Arial,sans-serif}}header{{padding:56px 7vw 42px;background:linear-gradient(135deg,#cbb7ef,#a98bdd);color:white}}header .eyebrow{{letter-spacing:.12em;font-size:12px;font-weight:700;opacity:.85}}h1{{font-size:clamp(34px,6vw,72px);margin:12px 0 8px;line-height:1}}header p{{margin:0;opacity:.9}}main{{max-width:1250px;margin:auto;padding:28px 22px 80px}}section{{margin:28px 0;background:white;border:1px solid var(--line);border-radius:24px;padding:26px;box-shadow:0 12px 35px rgba(55,38,84,.06)}}section.yellow{{background:var(--yellow)}}h2{{margin:0 0 18px;font-size:24px}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:18px 0}}.card{{background:white;border:1px solid var(--line);border-radius:18px;padding:18px}}.card span{{display:block;color:var(--muted);font-size:13px;margin-bottom:10px}}.card strong{{font-size:25px}}#chart{{height:390px}}.table-wrap{{overflow:auto;border:1px solid var(--line);border-radius:16px}}table{{border-collapse:collapse;width:100%;min-width:850px;background:#fff}}th,td{{padding:12px 14px;border-bottom:1px solid var(--line);text-align:right;font-size:13px;white-space:nowrap}}th:first-child,td:first-child{{text-align:left;position:sticky;left:0;background:inherit}}thead th{{background:#f6f3fa;font-weight:700;color:#555}}tbody tr:last-child td{{border-bottom:0}}.empty{{color:var(--muted);padding:24px}}.source{{font-size:12px;color:var(--muted)}}@media(max-width:800px){{.cards{{grid-template-columns:repeat(2,1fr)}}section{{padding:18px}}}}
</style></head><body><header><div class="eyebrow">DART × GITHUB AUTOMATION</div><h1>Starbucks Korea<br>Financial Dashboard</h1><p>2010–present · 사업보고서 · 반기보고서 · 분기보고서</p></header><main><div class="cards">{cards}</div><section><h2>Performance Overview</h2><div id="chart"></div><p class="source">단위: {html.escape('million KRW')} · 마지막 수집: {html.escape(meta.get('updated_at',''))}</p></section><section class="yellow"><h2>Annual</h2>{table(annual,annual_cols)}</section><section><h2>Half-year</h2>{table(half,half_cols)}</section><section class="yellow"><h2>Quarterly</h2>{table(q,q_cols)}</section><section><h2>Domestic Peer Firms</h2>{peer}<p class="source">Peer firms are presented as a reference set, not as a ranking or recommendation.</p></section></main><script>const d={cd};Plotly.newPlot('chart',[{{x:d.x,y:d.revenue,name:'Revenue',type:'scatter',mode:'lines+markers'}},{{x:d.x,y:d.op,name:'Operating profit',type:'scatter',mode:'lines+markers'}},{{x:d.x,y:d.net,name:'Net income',type:'scatter',mode:'lines+markers'}}],{{margin:{{l:50,r:20,t:10,b:45}},paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',legend:{{orientation:'h'}},hovermode:'x unified',yaxis:{{title:'million KRW'}}}},{{responsive:true,displayModeBar:false}});</script></body></html>'''
(SITE/'index.html').write_text(html_doc,encoding='utf-8')
