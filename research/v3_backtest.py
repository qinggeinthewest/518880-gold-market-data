"""V3 pre-registered long-only gold satellite backtest; research only, standard library."""
import json, math, statistics
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parent
N_WARMUP=253
N_OOS=252
POLICIES=['B0_lump','B1_DCA','B2_cash','S1_TSMOM252','S2_DONCHIAN55_20','S3_MA50_200',
          'S1_TSMOM252_ATR','S2_DONCHIAN55_20_ATR','S3_MA50_200_ATR']

def ma(rows,end,n):
    return sum(x['close'] for x in rows[end-n:end])/n

def atr14(rows):
    out=[None]*len(rows)
    tr=[0.0]
    for i in range(1,len(rows)):
        x=rows[i]; p=rows[i-1]['close']
        tr.append(max(x['high']-x['low'],abs(x['high']-p),abs(x['low']-p)))
    av=sum(tr[1:15])/14
    out[14]=av
    for i in range(15,len(rows)):
        av=(av*13+tr[i])/14
        out[i]=av
    return out

def stats(equity):
    if len(equity)<3:return {}
    r=[equity[i]/equity[i-1]-1 for i in range(1,len(equity))]
    years=(len(equity)-1)/252
    cagr=(equity[-1]/equity[0])**(1/years)-1
    dd=0; peak=equity[0]; underwater=0; longest=0
    for v in equity:
        peak=max(peak,v)
        dd=min(dd,v/peak-1)
        if v<peak: underwater+=1;longest=max(longest,underwater)
        else: underwater=0
    vol=statistics.stdev(r)*math.sqrt(252) if len(r)>1 else 0
    sharpe=(statistics.mean(r)/statistics.stdev(r))*math.sqrt(252) if statistics.stdev(r)>0 else None
    return {'total_return_pct':round((equity[-1]/equity[0]-1)*100,3),
            'cagr_pct':round(cagr*100,3),'max_drawdown_pct':round(dd*100,3),
            'volatility_pct':round(vol*100,3),'sharpe_rf0':round(sharpe,3) if sharpe is not None else None,
            'longest_underwater_trading_days':longest}

def desired(rows,i,policy,holding):
    p=rows[i-1]['close']
    if policy.startswith('S1_'):return p>rows[i-253]['close']
    if policy.startswith('S2_'):
        if holding:return p>=min(x['low'] for x in rows[i-21:i-1])
        return p>max(x['high'] for x in rows[i-56:i-1])
    if policy.startswith('S3_'):
        long200=ma(rows,i,200)
        if holding:return p>=long200
        return p>long200 and ma(rows,i,50)>long200
    return None

def simulate(rows,policy,cost=0.001,delay=0):
    # 10% core + isolated 5% satellite cash + remaining 85% non-gold.
    # Real-cost cash debits are at next session open; no borrowed cash.
    core=0.0;sat=0.0;sat_cash=5.0;other_cash=85.0;core_cash=10.0
    peak_close=None; cooldown=-1;trades=[];equities=[];sat_values=[]
    cap_breach_days=0;core_cap_days=0;atr=atr14(rows);entry_mae=[]
    active_entry=None
    for i in range(N_WARMUP,len(rows)):
        r=rows[i];p=r['open'];idx=i-N_WARMUP
        if core==0.0:
            core=core_cash/(p*(1+cost));core_cash=0.0
        prior_i=i-1-delay
        holding=sat>1e-10
        # Delayed order sensitivity: signals are formed only from prior completed bars.
        if policy.startswith('S') and prior_i>=N_WARMUP:
            signal_i=prior_i+1
            want=desired(rows,signal_i,policy,holding)
        elif policy.startswith('S'):
            want=False
        elif policy=='B0_lump':want=True
        elif policy=='B1_DCA':want=idx in (0,21,42,63,84,105)
        else:want=False
        reason='TREND'
        if policy.endswith('_ATR') and holding and peak_close is not None and prior_i>=14:
            if rows[prior_i]['close']<peak_close-2.5*atr[prior_i]:
                want=False;reason='CORRECTION_ATR';cooldown=i+5
        if policy.endswith('_ATR') and i<=cooldown:want=False
        if policy.startswith('S') and holding and not want:
            sat_cash+=sat*p*(1-cost)
            trades.append({'date':r['date'],'side':'SELL','reason':reason,'price':p,'qty':sat})
            sat=0.0;peak_close=None;active_entry=None
        wealth=other_cash+core*p+sat_cash+sat*p
        allowable=max(0,0.15*wealth-core*p)
        # Drift repair: sell satellite only; never silently sell long-term core.
        if sat*p>allowable+1e-9:
            sell_qty=min(sat,(sat*p-allowable)/p)
            sat-=sell_qty;sat_cash+=sell_qty*p*(1-cost)
            trades.append({'date':r['date'],'side':'SELL','reason':'CAP_TRIM','price':p,'qty':sell_qty})
        if core*p>0.15*(other_cash+core*p+sat_cash+sat*p):core_cap_days+=1
        if want:
            if policy=='B1_DCA':
                amount=min(5/6,sat_cash,max(0,allowable-sat*p))
            elif policy=='B0_lump' and idx==0:
                amount=min(sat_cash,max(0,allowable-sat*p))
            elif policy.startswith('S') and sat<1e-10:
                amount=min(sat_cash,max(0,allowable-sat*p))
            else:amount=0
            if amount>1e-8:
                qty=amount/(p*(1+cost))
                sat+=qty;sat_cash-=amount
                trades.append({'date':r['date'],'side':'BUY','reason':'ENTRY','price':p,'qty':qty})
                if policy.startswith('S'):peak_close=rows[i-1]['close'];active_entry=r['date']
        v=other_cash+core*r['close']+sat_cash+sat*r['close']
        equities.append(v);sat_values.append(sat_cash+sat*r['close'])
        if (core+sat)*r['close']>0.15*v+1e-9:cap_breach_days+=1
        if sat>1e-10:peak_close=max(peak_close or r['close'],r['close'])
    train=equities[:-N_OOS];oos=equities[-N_OOS-1:]
    if len(train)<250:raise ValueError('Training segment too short')
    out={'policy':policy,'cost_per_side_bps':cost*10000,'bars':len(equities),
         'training':stats(train),'holdout':stats(oos),'full':stats(equities),
         'sleeve_pnl_initial100':round(sat_values[-1]-5,4),
         'trades':len(trades),'buy_count':sum(t['side']=='BUY' for t in trades),
         'sell_count':sum(t['side']=='SELL' for t in trades),
         'correction_exit_count':sum(t['reason']=='CORRECTION_ATR' for t in trades),
         'cap_trim_count':sum(t['reason']=='CAP_TRIM' for t in trades),
         'closing_gold_weight_pct':round((core+sat)*rows[-1]['close']/equities[-1]*100,3),
         'gold_weight_exceed_15_days':cap_breach_days,'core_alone_exceed_15_days':core_cap_days,
         'trade_log':trades}
    return out

def render(obj):
    lines=['# V3.0 518880 backtest — automated, research only','',
           '## Data and validation','',
           f"- Status: **{obj['status']}**",
           f"- Notes: {obj['notes']}",
           f"- Data: {obj.get('source','n/a')}, {obj.get('bars',0)} completed trading days; adjustment: {obj.get('adjustment','n/a')}",
           '- No trading advice or replacement of live V2 signals.',
           '']
    if 'results' not in obj:return '\n'.join(lines)+'\n'
    lines+=['## Pre-registered portfolio comparisons','','10% core + up to 5% satellite; remaining 85% cash; equal next-day-open fills; all costs explicit.','',
            '| Policy | Full sample CAGR | Full max DD | Holdout return | Holdout max DD | Holdout Sharpe | Trades | Correction exits |',
            '|---|---:|---:|---:|---:|---:|---:|---:|']
    for o in obj['results']:
        h=o['holdout']; f=o['full']
        lines.append(f"| {o['policy']} | {f['cagr_pct']:.2f}% | {f['max_drawdown_pct']:.2f}% | {h['total_return_pct']:.2f}% | {h['max_drawdown_pct']:.2f}% | {h['sharpe_rf0']} | {o['trades']} | {o['correction_exit_count']} |")
    lines+=['','**DO NOT RANK AS VERIFIED** until distributions/corporate actions are audited, multi-period out-of-sample checks pass and macro data are available for faithful V2.0 comparisons.','',
            '## Execution and correction rules','',
            '- Indicators use only completed close bars; orders execute at next session open.',
            '- Satellite exits on trend loss, 55/20 Donchian exit, MA200 exit, or pre-registered 2.5 ATR correction; 5-session cooling-off after correction.',
            '- Any 15% portfolio excess is trimmed from satellite at next open, with core protected; residual core-only breaches are flagged.',
            '- Costs use 10 bps per side (commission + slippage, illustrative), with sensitivity checks at 5 and 20 bps.',
            '- Current V2.0 multi-factor strategy requires daily Au99.99/USD-CNY/TIPS/DXY data and is not ranked here.',
            '']
    return '\n'.join(lines)

def main():
    path=ROOT/'history.json'
    status={'status':'BLOCKED','notes':'Long history not yet acquired; 120-bar quote cache is insufficient.'}
    if path.exists():
        data=json.loads(path.read_text(encoding='utf-8'))
        rows=data.get('rows',[])
        status.update({'bars':len(rows),'source':data.get('source'),'adjustment':data.get('adjustment')})
        if len(rows)>=800:
            try:
                all_results=[simulate(rows,p) for p in POLICIES]
                for o in all_results:o.pop('trade_log',None)
                status.update({'status':'PROVISIONAL_UNAUDITED',
                  'notes':'Research calculations completed, but corporate-action/distribution-adjusted total returns and independent out-of-sample validity are NOT certified.',
                  'results':all_results,
                  'sensitivity_5bps':{p:simulate(rows,p,cost=0.0005)['holdout'] for p in POLICIES if p.startswith('S')},
                  'sensitivity_20bps':{p:simulate(rows,p,cost=0.002)['holdout'] for p in POLICIES if p.startswith('S')},
                  'one_extra_day_delay':{p:simulate(rows,p,delay=1)['holdout'] for p in POLICIES if p.startswith('S')}})
            except Exception as e:status.update({'status':'ERROR','notes':f'{type(e).__name__}: {e}'})
    (ROOT/'RESULTS.json').write_text(json.dumps(status,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (ROOT/'RESULTS.md').write_text(render(status),encoding='utf-8')
    print('Research status:',status['status'],'bars:',status.get('bars',0))
if __name__=='__main__':main()
