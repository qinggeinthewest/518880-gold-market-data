"""Independent smoke tests for V3 backtest mechanics; run before research."""
from datetime import date,timedelta
from v3_backtest import simulate

def series(n=1200, trend=0.002):
    d0=date(2013,7,29)
    rows=[]
    for i in range(n):
        p=2.5+i*trend
        rows.append({'date':(d0+timedelta(days=i)).isoformat(),
                     'open':p,'high':p+0.015,'low':p-0.015,
                     'close':p,'volume':100000})
    return rows

def main():
    rows=series()
    a=simulate(rows,'B0_lump',start=253,end=1009)
    b=simulate(rows,'B2_cash',start=253,end=1009)
    c=simulate(rows,'S1_TSMOM252',start=253,end=1009)
    d=simulate(series(trend=0),'S1_TSMOM252',start=253,end=1009)
    assert a['trade_log'][0]['side']=='BUY', 'B0 must acquire satellite at next open'
    assert a['trade_log'][0]['date']==rows[253]['date'], 'B0 entry date incorrect'
    assert b['buy_count']==0 and b['trades']==0, 'cash benchmark must not trade satellite'
    assert c['buy_count']>0, 'positive 252-day trend should enter satellite'
    assert d['buy_count']==0, 'flat trend should not trigger buy'
    assert all(x['date']>=rows[253]['date'] for x in c['trade_log']), 'future fills leaked into the past'
    assert a['full']['cagr_pct'] is not None
    print('V3 SMOKE TESTS: PASS; entry, no-position, trend, 252-day warmup, timing.')
if __name__=='__main__':main()
