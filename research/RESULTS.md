# V3.0 independent research: BUY / SELL / ERROR-CORRECTION

## Data gate
- Status: **PROVISIONAL_UNAUDITED**
- Notes: Matched rolling 3-year portfolios calculated. Historical returns/adjustments and distribution events not independently audited; overlapping windows are correlated.
- Source: sina_money_raw; completed bars: 3233; adjustment: unadjusted_needs_distribution_review
- Research only; NO orders or live strategy changes. Cash yield assumption = 0% p.a.
- Signals are based on the previous completed close; all fills at the next session open; trading costs = 10 bps per side (assumed).
- ETF distributions and adjust factors need independent audit. V2.0 MACRO data are incomplete; no faithful V2.0 numerical comparison yet.

## Matched rolling three-year windows
Each window starts with a fresh portfolio of 10% ETF core + 5% satellite cash + 85% other cash. Adjacent windows overlap and must NOT be treated as independent observations.

| Strategy | Avg satellite P&L (portfolio pp) | vs immediate addition (pp) | vs DCA (pp) | Win share vs immediate | Avg max DD of total portfolio | Worst max DD | Avg trade count |
|---|---:|---:|---:|---:|---:|---:|---:|
| B0_lump | +0.986 | +0.000 | -0.054 | 0% | -2.75% | -7.55% | 47.1 |
| B1_DCA | +1.040 | +0.054 | +0.000 | 60% | -2.71% | -7.56% | 48.4 |
| B2_cash | +0.000 | -0.986 | -1.040 | 0% | -2.42% | -7.64% | 0.0 |
| S1_TSMOM252 | +0.735 | -0.251 | -0.305 | 10% | -2.70% | -7.55% | 70.5 |
| S2_DONCHIAN55_20 | +0.384 | -0.602 | -0.655 | 0% | -2.62% | -7.59% | 59.9 |
| S3_MA50_200 | +0.764 | -0.222 | -0.276 | 40% | -2.65% | -7.55% | 66.4 |
| S1_TSMOM252_ATR | +0.535 | -0.451 | -0.505 | 0% | -2.77% | -7.59% | 149.7 |
| S2_DONCHIAN55_20_ATR | +0.213 | -0.772 | -0.826 | 0% | -2.50% | -7.61% | 56.2 |
| S3_MA50_200_ATR | +0.545 | -0.440 | -0.494 | 0% | -2.68% | -7.59% | 124.8 |

## Rolling window coverage

| Window | Start | End |
|---|---|---|
| 1 | 2014-08-11 | 2017-09-12 |
| 2 | 2015-08-20 | 2018-09-21 |
| 3 | 2016-08-31 | 2019-10-14 |
| 4 | 2017-09-13 | 2020-10-27 |
| 5 | 2018-09-25 | 2021-11-09 |
| 6 | 2019-10-15 | 2022-11-22 |
| 7 | 2020-10-28 | 2023-12-05 |
| 8 | 2021-11-10 | 2024-12-19 |
| 9 | 2022-11-23 | 2026-01-05 |
| 10 | 2023-09-27 | 2026-11-16 |

## Interpretation / no premature winner

- Holdings acquired before the window start are not carried into subsequent windows: this removes artificial 13-year drift of the 10% core.
- The 15% exposure target can still be exceeded after sudden price moves; core-only violations are flagged, not silently sold.
- ATR correction is tested as a paired overlay, not presumed to improve performance.
- **These outputs are provisional.** Independent validation of dividend/split treatment, macro-factor histories, rolling OOS and sensitivity to costs/latency is required before selecting a live signal.
