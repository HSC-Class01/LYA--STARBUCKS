import io, json, os, re, zipfile
from pathlib import Path
from datetime import datetime
import requests
import pandas as pd
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
RAW = DATA / 'raw_reports'
CONFIG = json.loads((ROOT/'config/company.json').read_text(encoding='utf-8'))
BASE = 'https://opendart.fss.or.kr/api'
KEY = os.environ.get('DART_API_KEY', '').strip()

if not KEY:
    raise SystemExit('DART_API_KEY is required. Add it as a GitHub Actions repository secret.')

SESSION = requests.Session()
SESSION.headers.update({'User-Agent':'LYA-STARBUCKS-DART-Agent/1.0'})


def dart_get(endpoint, params, timeout=60):
    p = {'crtfc_key': KEY, **params}
    r = SESSION.get(f'{BASE}/{endpoint}', params=p, timeout=timeout)
    r.raise_for_status()
    if 'json' in r.headers.get('content-type','') or r.text.lstrip().startswith('{'):
        data = r.json()
        if data.get('status') not in (None, '000'):
            if data.get('status') == '013':
                return {'status':'013','list':[]}
            raise RuntimeError(f"DART {endpoint}: {data.get('status')} {data.get('message')}")
        return data
    return r.content


def load_corp_code():
    if CONFIG.get('corp_code'):
        return CONFIG['corp_code']
    raw = dart_get('corpCode.xml', {})
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        xml = z.read('CORPCODE.xml')
    soup = BeautifulSoup(xml, 'xml')
    aliases = CONFIG['aliases']
    for item in soup.find_all('list'):
        name = item.corp_name.text.strip()
        if any(a in name for a in aliases):
            return item.corp_code.text.strip()
    raise RuntimeError('Could not resolve Starbucks Korea corporation code.')


def get_filings(corp_code):
    rows=[]
    for year in range(CONFIG['start_year'], datetime.now().year + 1):
        bgn=f'{year}0101'; end=f'{year}1231'
        data=dart_get('list.json', {'corp_code':corp_code,'bgn_de':bgn,'end_de':end,'pblntf_ty':'A','page_no':1,'page_count':100})
        for x in data.get('list',[]):
            nm=x.get('report_nm','')
            if any(t in nm for t in ['사업보고서','반기보고서','분기보고서']):
                if '정정' in nm: continue
                rows.append({
                    'year':year,'report_name':nm,'report_type':classify_report(nm),
                    'rcept_no':x.get('rcept_no'),'rcept_dt':x.get('rcept_dt'),
                    'corp_name':x.get('corp_name'),
                    'dart_url':f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={x.get('rcept_no')}"
                })
    return pd.DataFrame(rows).drop_duplicates(['rcept_no'])


def classify_report(name):
    if '사업보고서' in name: return 'annual'
    if '반기보고서' in name: return 'half_year'
    if '1분기' in name: return 'quarterly_q1'
    if '3분기' in name: return 'quarterly_q3'
    if '분기보고서' in name: return 'quarterly'
    return 'other'


def get_financials(corp_code):
    frames=[]
    for year in range(max(CONFIG['start_year'], 2015), datetime.now().year+1):
        for report_type, code in CONFIG['report_types'].items():
            try:
                d=dart_get('fnlttSinglAcntAll.json', {'corp_code':corp_code,'bsns_year':year,'reprt_code':code,'fs_div':'OFS'})
            except Exception as e:
                print(f'warning: {year} {report_type}: {e}')
                continue
            for x in d.get('list',[]):
                frames.append({
                    'year':year,'period_type':report_type,'fs_div':x.get('fs_div'),
                    'sj_div':x.get('sj_div'),'account_id':x.get('account_id'),
                    'account_nm':x.get('account_nm'),'thstrm_nm':x.get('thstrm_nm'),
                    'thstrm_amount':to_number(x.get('thstrm_amount')),
                    'frmtrm_nm':x.get('frmtrm_nm'),'frmtrm_amount':to_number(x.get('frmtrm_amount')),
                    'bfefrmtrm_nm':x.get('bfefrmtrm_nm'),'bfefrmtrm_amount':to_number(x.get('bfefrmtrm_amount')),
                    'currency':x.get('currency')
                })
    return pd.DataFrame(frames)


def to_number(v):
    if v is None or v == '': return None
    s=str(v).replace(',','').replace(' ','').replace('－','-').replace('△','-')
    m=re.search(r'-?\d+(?:\.\d+)?',s)
    return float(m.group()) if m else None


def normalize_metric(df, names):
    if df.empty: return pd.DataFrame()
    m=df[df.account_nm.fillna('').apply(lambda x: any(n in x.replace(' ','') for n in names))].copy()
    if m.empty: return m
    # prefer profit-and-loss and balance-sheet rows consistently
    return m.sort_values(['year','period_type']).drop_duplicates(['year','period_type'], keep='first')


def build_analysis(fin):
    if fin.empty: return pd.DataFrame()
    metric_map={
      'revenue':['매출액','수익(매출액)','영업수익'],
      'gross_profit':['매출총이익'],
      'operating_profit':['영업이익'],
      'net_income':['당기순이익'],
      'assets':['자산총계'],
      'liabilities':['부채총계'],
      'equity':['자본총계'],
      'current_assets':['유동자산'],
      'current_liabilities':['유동부채'],
      'cash':['현금및현금성자산','현금및현금성자산(금융기관예치금포함)'],
      'inventory':['재고자산'],
    }
    keys=['year','period_type']
    out=fin[keys].drop_duplicates().copy()
    for col,names in metric_map.items():
        mm=normalize_metric(fin,names)[keys+['thstrm_amount']].rename(columns={'thstrm_amount':col})
        out=out.merge(mm,on=keys,how='left')
    for c in ['gross_profit','operating_profit','net_income','revenue']:
        if c in out: out[c+'_margin']=out[c]/out['revenue']*100
    out['current_ratio']=out['current_assets']/out['current_liabilities']*100
    out['debt_ratio']=out['liabilities']/out['equity']*100
    out['roe']=out['net_income']/out['equity']*100
    out['roa']=out['net_income']/out['assets']*100
    out['asset_turnover']=out['revenue']/out['assets']
    return out


def save_raw_filings(filings):
    if not CONFIG.get('store_raw_reports'): return
    RAW.mkdir(parents=True,exist_ok=True)
    for _,r in filings.iterrows():
        rcp=r['rcept_no']
        if not rcp: continue
        target=RAW/f"{r['year']}_{r['report_type']}_{rcp}.zip"
        if target.exists(): continue
        try:
            content=dart_get('document.xml', {'rcept_no':rcp}, timeout=120)
            target.write_bytes(content)
        except Exception as e:
            print(f'raw report warning {rcp}: {e}')


def main():
    DATA.mkdir(exist_ok=True)
    corp=load_corp_code()
    filings=get_filings(corp)
    filings.to_csv(DATA/'filings.csv',index=False,encoding='utf-8-sig')
    save_raw_filings(filings)
    financials=get_financials(corp)
    financials.to_csv(DATA/'financials_raw.csv',index=False,encoding='utf-8-sig')
    analysis=build_analysis(financials)
    analysis.to_csv(DATA/'financials_analysis.csv',index=False,encoding='utf-8-sig')
    (DATA/'metadata.json').write_text(json.dumps({'updated_at':datetime.now().isoformat(),'corp_code':corp,'company':CONFIG['company_display_name']},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'updated: filings={len(filings)}, financial_rows={len(financials)}, analysis_rows={len(analysis)}')

if __name__=='__main__': main()
