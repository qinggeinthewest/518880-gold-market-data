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

def simulate(rows,policy,cost=0.001,delay=0,start=N_WARMUP,end=None):
    if end is None:end=len(rows)
    if end-start<500:raise ValueError('Evaluation window too short')
    # 10% core + isolated 5% satellite cash + remaining 85% non-gold.
    # Real-cost cash debits are at next session open; no borrowed cash.
    core=0.0;sat=0.0;sat_cash=5.0;other_cash=85.0;core_cash=10.0
    peak_close=None; cooldown=-1;trades=[];equities=[];sat_values=[]
    cap_breach_days=0;core_cap_days=0;atr=atr14(rows);entry_mae=[]
    active_entry=None
    for i in range(start,end):
        r=rows[i];p=r['open'];idx=i-start
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
    out={'policy':policy,'start_date':rows[start]['date'],'end_date':rows[end-1]['date'],'cost_per_side_bps':cost*10000,'bars':len(equities),
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

def aggregate_windows(windows):
    # Scores refer to the same start date and cash/ETF core for every candidate.
    base={w['window_id']:next(x for x in w['results'] if x['policy']=='B0_lump') for w in windows}
    dca={w['window_id']:next(x for x in w['results'] if x['policy']=='B1_DCA') for w in windows}
    names=[v['policy'] for v in windows[0]['results']]
    agg=[]
    for name in names:
        entries=[(w,next(x for x in w['results'] if x['policy']==name)) for w in windows]
        sleeve=[x['sleeve_pnl_initial100'] for w,x in entries]
        advantages=[x['sleeve_pnl_initial100']-base[w['window_id']]['sleeve_pnl_initial100'] for w,x in entries]
        advantages_dca=[x['sleeve_pnl_initial100']-dca[w['window_id']]['sleeve_pnl_initial100'] for w,x in entries]
        agg.append({'policy':name,'windows':len(entries),
          'average_satellite_profit_points_of_initial100':round(statistics.mean(sleeve),3),
          'median_satellite_profit_points_of_initial100':round(statistics.median(sleeve),3),
          'mean_delta_vs_lump_points':round(statistics.mean(advantages),3),
          'mean_delta_vs_DCA_points':round(statistics.mean(advantages_dca),3),
          'win_fraction_vs_lump':round(sum(x>0 for x in advantages)/len(advantages),3),
          'avg_full_maxDD_pct':round(statistics.mean(x['full']['max_drawdown_pct'] for w,x in entries),3),
          'worst_full_maxDD_pct':round(min(x['full']['max_drawdown_pct'] for w,x in entries),3),
          'mean_trades':round(statistics.mean(x['trades'] for w,x in entries),1),
          'avg_correction_exits':round(statistics.mean(x['correction_exit_count'] for w,x in entries),1),
          'mean_cap_trim_count':round(statistics.mean(x['cap_trim_count'] for w,x in entries),1)})
    return agg

def render(obj):
    lines=['# V3.0 independent research: BUY / SELL / ERROR-CORRECTION',
           '','## Data gate',
           f"- Status: **{obj['status']}**",
           f"- Notes: {obj['notes']}",
           f"- Source: {obj.get('source','n/a')}; completed bars: {obj.get('bars',0)}; adjustment: {obj.get('adjustment','n/a')}",
           '- Research only; NO orders or live strategy changes. Cash yield assumption = 0% p.a.',
           '- Signals are based on the previous completed close; all fills at the next session open; trading costs = 10 bps per side (assumed).',
           '- ETF distributions and adjust factors need independent audit. V2.0 MACRO data are incomplete; no faithful V2.0 numerical comparison yet.',
           '']
    if not obj.get('aggregate'):return '\n'.join(lines)+'\n'
    lines+=['## Matched rolling three-year windows',
            'Each window starts with a fresh portfolio of 10% ETF core + 5% satellite cash + 85% other cash. Adjacent windows overlap and must NOT be treated as independent observations.',
            '',
            '| Strategy | Avg satellite P&L (portfolio pp) | vs immediate addition (pp) | vs DCA (pp) | Win share vs immediate | Avg max DD of total portfolio | Worst max DD | Avg trade count |',
            '|---|---:|---:|---:|---:|---:|---:|---:|']
    for v in obj['aggregate']:
        lines.append(f"| {v['policy']} | {v['average_satellite_profit_points_of_initial100']:+.3f} | {v['mean_delta_vs_lump_points']:+.3f} | {v['mean_delta_vs_DCA_points']:+.3f} | {v['win_fraction_vs_lump']:.0%} | {v['avg_full_maxDD_pct']:.2f}% | {v['worst_full_maxDD_pct']:.2f}% | {v['mean_trades']:.1f} |")
    lines+=['','## Rolling window coverage','',
            '| Window | Start | End |',
            '|---|---|---|']
    for w in obj['windows']:
        lines.append(f"| {w['window_id']} | {w['start']} | {w['end']} |")
    lines+=['','## Interpretation / no premature winner','',
            '- Holdings acquired before the window start are not carried into subsequent windows: this removes artificial 13-year drift of the 10% core.',
            '- The 15% exposure target can still be exceeded after sudden price moves; core-only violations are flagged, not silently sold.',
            '- ATR correction is tested as a paired overlay, not presumed to improve performance.',
            '- **These outputs are provisional.** Independent validation of dividend/split treatment, macro-factor histories, rolling OOS and sensitivity to costs/latency is required before selecting a live signal.',
            '']
    return '\n'.join(lines)

def main():
    path=ROOT/'history.json'
    status={'status':'BLOCKED','notes':'Long, adjusted, audited history is not yet available.'}
    if path.exists():
        data=json.loads(path.read_text(encoding='utf-8'))
        rows=data.get('rows',[])
        status.update({'bars':len(rows),'source':data.get('source'),'adjustment':data.get('adjustment')})
        if len(rows)>=1100:
            try:
                length=756
                starts=list(range(N_WARMUP,len(rows)-length+1,252))
                if len(rows)-length not in starts:starts.append(len(rows)-length)
                windows=[]
                for z,start in enumerate(sorted(set(starts))):
                    end=start+length
                    vals=[simulate(rows,p,start=start,end=end) for p in POLICIES]
                    for o in vals:o.pop('trade_log',None)
                    windows.append({'window_id':z+1,'start':rows[start]['date'],'end':rows[end-1]['date'],'results':vals})
                status.update({'status':'PROVISIONAL_UNAUDITED',
                  'notes':'Matched rolling 3-year portfolios calculated. Historical returns/adjustments and distribution events not independently audited; overlapping windows are correlated.',
                  'windows':windows,'aggregate':aggregate_windows(windows),
                  'sensitivity_5bps':{p:simulate(rows,p,cost=0.0005,start=starts[-1],end=starts[-1]+length)['holdout'] for p in POLICIES if p.startswith('S')},
                  'sensitivity_20bps':{p:simulate(rows,p,cost=0.002,start=starts[-1],end=starts[-1]+length)['holdout'] for p in POLICIES if p.startswith('S')},
                  'one_extra_day_delay':{p:simulate(rows,p,delay=1,start=starts[-1],end=starts[-1]+length)['holdout'] for p in POLICIES if p.startswith('S')}})
            except Exception as e:status.update({'status':'ERROR','notes':f'{type(e).__name__}: {e}'})
        else:status.update({'notes':'Fewer than 1100 completed sessions; minimum multiwindow study cannot proceed.'})
    (ROOT/'RESULTS.json').write_text(json.dumps(status,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (ROOT/'RESULTS.md').write_text(render(status),encoding='utf-8')
    print('Research status:',status['status'],'bars:',status.get('bars',0),'windows:',len(status.get('windows',[])))
if __name__=='__main__':main()
