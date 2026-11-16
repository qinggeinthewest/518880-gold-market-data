"""Read user's Cloudflare Worker; publish only fresh, verifiable China-market data.

Uses Python standard library, no user credentials or trading access.
"""
import json
import math
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

WORKER = os.getenv('WORKER_URL', 'https://gold-etf-518880.qinggeinthewest.workers.dev/?format=json')
SHANGHAI = ZoneInfo('Asia/Shanghai')
ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / 'docs' / 'latest.json'
OUT_MD = ROOT / 'docs' / 'latest.md'


def strict_float(x):
    if not isinstance(x, (float, int)) or isinstance(x, bool) or not math.isfinite(x):
        raise ValueError('Nonfinite or nonnumeric price field')
    return float(x)


def fetch_payload():
    r = Request(WORKER, headers={'User-Agent': '518880-MarketSnapshot/1.0', 'Accept': 'application/json'})
    with urlopen(r, timeout=22) as resp:
        if resp.status != 200:
            raise ValueError(f'Worker HTTP {resp.status}')
        content = resp.read(900000)
        if len(content) >= 900000:
            raise ValueError('Response too large')
        return json.loads(content)


def check(p, now):
    if not isinstance(p, dict) or p.get('symbol') != '518880':
        raise ValueError('Wrong instrument')
    q, h = p.get('quote'), p.get('history')
    if not isinstance(q, dict) or not isinstance(h, dict):
        raise ValueError('Missing quote/history')
    if q.get('source') not in ('腾讯财经', '新浪财经'):
        raise ValueError('Unexpected quote provider')
    if h.get('source') not in ('sina_kline_money', 'sina_kline_cn'):
        raise ValueError('Unexpected K-line provider')
    p0 = strict_float(q.get('price_yuan'))
    pc = strict_float(q.get('previous_close_yuan'))
    hi = strict_float(q.get('high_yuan'))
    lo = strict_float(q.get('low_yuan'))
    if min(p0, pc, hi, lo) <= 0 or lo > p0 + 0.01 or p0 > hi + 0.01:
        raise ValueError('Inconsistent quote fields')
    ms = q.get('exchange_time_ms')
    if not isinstance(ms, (int, float)) or isinstance(ms, bool):
        raise ValueError('Missing exchange timestamp')
    quote_dt = datetime.fromtimestamp(ms/1000, tz=timezone.utc)
    quote_bj = quote_dt.astimezone(SHANGHAI)
    age = (now - quote_dt).total_seconds()/60
    if age < -2 or age > 20:
        raise ValueError(f'Stale/future quote: {age:.1f} minutes')
    if quote_bj.weekday() >= 5:
        raise ValueError('No weekend signals')
    minutes = quote_bj.hour*60 + quote_bj.minute
    if not (9*60+30 <= minutes <= 11*60+30 or 13*60 <= minutes <= 15*60):
        raise ValueError('Exchange timestamp outside regular trading hours')
    if quote_bj.date() != now.astimezone(SHANGHAI).date():
        raise ValueError('Quote date not current Shanghai date')
    rows = h.get('recent_completed_rows')
    if not isinstance(rows, list) or len(rows) < 60 or h.get('completed_rows', 0) < 60:
        raise ValueError('Insufficient K-line history')
    last_day = datetime.strptime(str(h.get('last_completed_date')), '%Y-%m-%d').date()
    days_ago = (now.astimezone(SHANGHAI).date() - last_day).days
    if days_ago < 0 or days_ago > 10:
        raise ValueError('K-line history too old/future')
    for key in ('ma5', 'ma10', 'ma20', 'ma60', 'atr14', 'high60', 'low10'):
        if strict_float(h.get(key)) <= 0:
            raise ValueError(f'Invalid technical metric: {key}')
    if p.get('usable_for_signals') is not True or p.get('trading_session') is not True:
        raise ValueError('Worker marked data ineligible, or outside trading session')
    if not isinstance(p.get('quote_crosscheck'), list) or len(p.get('quote_crosscheck')) < 2:
        raise ValueError('Insufficient cross-source quote verification')
    check_prices = [strict_float(v.get('price_yuan')) for v in p['quote_crosscheck']]
    if (max(check_prices)/min(check_prices)-1) > 0.004:
        raise ValueError('Cross-source prices diverge >0.4%')
    return round(age, 2)


def publish(p, now, age):
    q, h = p['quote'], p['history']
    selected = {
        'instrument': 'SSE:518880',
        'snapshot_published_utc': now.isoformat(),
        'quote_age_minutes_at_publish': age,
        'quote': q,
        'quote_crosscheck': p.get('quote_crosscheck', []),
        'history': h,
        'sources': {
            'quote': 'Tencent Finance / Sina Finance via Cloudflare Worker',
            'history': 'Sina Money domestic K-line interface via Cloudflare Worker',
        },
        'scope': 'ETF market data only; does not validate SGE Au99.99, USD/CNY, TIPS or DXY; no investment signals calculated here',
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(selected, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    qtime = q['exchange_time_beijing']
    lastrows = h['recent_completed_rows'][-10:]
    lines = [
        '# 518880 中国市场行情快照',
        '',
        f'- 快照发布UTC时间：{now.strftime("%Y-%m-%d %H:%M:%S")}',
        f'- 最新成交北京时间（数据源字段）：{qtime}',
        f'- 最新成交价格：{q["price_yuan"]}元（昨收 {q["previous_close_yuan"]}元）',
        f'- 今日开高低：{q["open_yuan"]} / {q["high_yuan"]} / {q["low_yuan"]}元',
        f'- 成交量：{q["volume_hands"]}手；成交额：{q["turnover_yuan"]}元',
        f'- 已完成日K线截至：{h["last_completed_date"]}；{h["completed_rows"]}个已完成交易日',
        f'- MA5/10/20/60：{h["ma5"]} / {h["ma10"]} / {h["ma20"]} / {h["ma60"]}',
        f'- ATR14：{h["atr14"]}；过去60个完成日最高价：{h["high60"]}',
        '- 报价来源：腾讯财经、 新浪财经（相互交叉检查）；日K线：新浪Money；均非上交所官方认证收盘价',
        '- 本文不包含Au99.99、USD/CNY、TIPS、DXY，绝不能仅凭本文发出买入信号。',
        '- 注意：快照仅代表发布当时行情，后续阅读必须核对时间；网页读取时间不是成交时间。',
        '',
        '## 最近十个已完成交易日K线（日期 开 高 低 收）',
        '',
    ]
    for x in lastrows:
        lines.append(f'- {x["date"]} {x["open"]} {x["high"]} {x["low"]} {x["close"]}')
    OUT_MD.write_text('\n'.join(lines)+'\n', encoding='utf-8')


def main():
    now = datetime.now(timezone.utc)
    try:
        payload = fetch_payload()
        age = check(payload, now)
    except Exception as e:
        print(f'No eligible fresh snapshot; keeping existing files unchanged: {type(e).__name__}: {e}')
        return 0
    publish(payload, now, age)
    print('Published fresh validated snapshot; quote_age_minutes=', age)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
