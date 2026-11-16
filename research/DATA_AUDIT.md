# V3.0 data quality / corporate actions audit (2026-11-16)

Instrument SSE:518880. Purpose: validate historical ETF return series before drawing trading conclusions.

## Independent provider comparison (performed via authenticated GitHub file reads)
- Archived Eastmoney \`fqt=2\` (HFQ parameter) snapshot: 3,233 daily completed OHLCV bars, 2013-07-29–2026-11-16.
- Independent Sina Money unadjusted daily feed: 3,233 bars, same dates.
- All **3,233 dates overlap**. Max absolute close-price difference: **0.001 CNY**, max relative discrepancy **0.024655%**; average absolute relative close-price deviation approx **0.00003795%**.
- Only **five** daily closing prices (2020-08-21 and 2020-08-24–27) differ by 0.001 CNY; other closing prices agree within 0.00001 relative deviation.
- This is unusually good historical price agreement. It does NOT automatically validate intraday fills, volumes, bid-ask spread, source licensing, or corporate-action treatment.
- Corporate actions reported by fund manager: 2013-07-24 share conversion ratio 0.37761358, **before 2013-07-29 exchange listing**; the manager's distribution table lists that conversion and no intervening post-listing distributions at the time checked.
  Source: https://www.huaan.com.cn/funds/518880/index.shtml
- Independent fund information portal reports zero cash dividends since inception and the same prelisting 2013 conversion.
  Source: https://fundf10.eastmoney.com/fhsp_518880.html

## Decision
- Use Eastmoney archived daily history as the *preferred* backtesting series when dates are equally recent.
- When Eastmoney is briefly unreachable, keep a valid equally fresh preferred archive instead of overwriting it with the raw backup. A fresh later date may be appended only after rechecking consistency.
- Price-history quality has advanced materially; **do not certify strategy superiority** on this alone. Need audit of ETF liquidity/slippage, actual transaction costs, window dependence, out-of-sample strategy robustness, and V2 macro history.
- Vendor coverage, discrepancies, and data date are recorded; no account or portfolio identifiers are stored.
