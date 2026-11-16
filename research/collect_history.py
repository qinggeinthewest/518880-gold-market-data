"""V3 research-only full-history acquisition. No personal data or broker access."""
import json, hashlib, time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'history.json'
STATUS=ROOT/'data_status.json'
BJ=timezone(timedelta(hours=8))

def fetch(url):
    req=Request(url,headers={'User-Agent':'Mozilla/5.0 518880 historical-research','Accept':'application/json,text/plain,*/*','Referer':'https://finance.sina.com.cn/'})
    with urlopen(req,timeout=16) as r:
        raw=r.read(2_800_000)
        if len(raw)>=2_800_000: raise ValueError('response too large')
        return json.loads(raw.decode('utf-8-sig'))

def validate(rows):
    seen={}
    for x in rows:
        try:
            d=str(x['date'])[:10]
            datetime.strptime(d,'%Y-%m-%d')
            o,h,l,c=map(float,[x['open'],x['high'],x['low'],x['close']])
            if not(0<l<=min(o,c) and h>=max(o,c) and h>=l):continue
            seen[d]={'date':d,'open':o,'high':h,'low':l,'close':c,'volume':float(x.get('volume',0))}
        except (ValueError,TypeError,KeyError):pass
    a=sorted(seen.values(),key=lambda x:x['date'])
    if len(a)<100: raise ValueError(f'only {len(a)} valid rows')
    now=datetime.now(BJ)
    # No partially formed current-day bar before 15:15 Beijing.
    if a[-1]['date']==now.strftime('%Y-%m-%d') and (now.hour,now.minute)<(15,15):a.pop()
    return a

def eastmoney():
    url='https://push2his.eastmoney.com/api/qt/stock/kline/get?'+urlencode({
        'secid':'1.518880','fields1':'f1,f2,f3,f4,f5,f6',
        'fields2':'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
        'klt':'101','fqt':'2','beg':'20130101','end':'20500101','lmt':'5000'})
    d=fetch(url)
    if not isinstance(d,dict) or not d.get('data') or not d['data'].get('klines'):
        raise ValueError('no eastmoney K lines')
    rows=[]
    for line in d['data']['klines']:
        v=line.split(',')
        if len(v)>=7:rows.append({'date':v[0],'open':v[1],'close':v[2],'high':v[3],'low':v[4],'volume':v[5]})
    return validate(rows),'eastmoney_hfq','hfq_as_published_needs_corporate_event_review'

def sina_money():
    url='https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?'+urlencode({
        'symbol':'sh518880','scale':'240','ma':'no','datalen':'4500'})
    d=fetch(url)
    if not isinstance(d,list):raise ValueError('Sina did not provide a JSON list')
    rows=[{'date':v.get('day'),'open':v.get('open'),'close':v.get('close'),
           'high':v.get('high'),'low':v.get('low'),'volume':v.get('volume',0)} for v in d if isinstance(v,dict)]
    return validate(rows),'sina_money_raw','unadjusted_needs_distribution_review'

def main():
    errors=[];candidates=[]
    for name,fn in [('Eastmoney',eastmoney),('Sina Money',sina_money)]:
        try:
            rows,source,adjustment=fn()
            candidates.append((rows,source,adjustment))
            print(f'{name}: {len(rows)} completed bars, {rows[0]["date"]} through {rows[-1]["date"]}')
        except Exception as e:
            errors.append(f'{name}: {type(e).__name__} {str(e)[:180]}')
            print(errors[-1])
    status={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'sources_attempted':['Eastmoney hfq','Sina Money raw'],'errors':errors,'ready':False}
    if not candidates:
        STATUS.write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        return
    # Prefer longer series; for nearly equal lengths prefer the adjusted Eastmoney series.
    candidates.sort(key=lambda x:(len(x[0]),x[1]=='eastmoney_hfq'),reverse=True)
    rows,source,adjustment=candidates[0]
    # Guard against silently overwriting a longer previously archived history.
    if OUT.exists():
        try:
            prev=json.loads(OUT.read_text(encoding='utf-8'))
            if len(prev.get('rows',[]))>len(rows) and prev.get('rows',[])[-1]['date']>=rows[-1]['date']:
                rows=prev['rows'];source=prev['source'];adjustment=prev['adjustment']
                status['retained_longer_archive']=True
        except Exception:pass
    jumps=[{'date':x['date'],'change':round(x['close']/rows[i-1]['close']-1,3)}
        for i,x in enumerate(rows) if i>0 and abs(x['close']/rows[i-1]['close']-1)>0.20]
    data={'symbol':'SSE:518880','source':source,'adjustment':adjustment,'download_utc':status['checked_at_utc'],'rows':rows,
          'possible_price_discontinuities':jumps,
          'research_limitations':'Historical vendor data; corporate actions/distributions and total-return convention not independently reconciled.'}
    payload=json.dumps(data,ensure_ascii=False,indent=2)
    OUT.write_text(payload+'\n',encoding='utf-8')
    status.update({'source':source,'adjustment':adjustment,'bars':len(rows),
                   'first':rows[0]['date'],'last':rows[-1]['date'],'possible_price_discontinuities':jumps,
                   'sha256':hashlib.sha256(payload.encode()).hexdigest(),
                   'ready':len(rows)>=800,
                   'historically_adjusted_returns_verified':False})
    STATUS.write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('V3 data gate:', 'SUFFICIENT_BARS_BUT_NOT_CORPORATE_ACTION_VERIFIED' if status['ready'] else 'INSUFFICIENT_BARS')
if __name__=='__main__':main()
