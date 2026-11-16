# V3.0 independent research: BUY / SELL / ERROR-CORRECTION

## Data gate
- Status: **PROVISIONAL_UNAUDITED**
- Notes: Matched rolling 3-year portfolios calculated. Historical returns/adjustments and distribution events not independently audited; overlapping windows are correlated.
- Source: eastmoney_hfq; completed bars: 3233; adjustment: hfq_as_published_needs_corporate_event_review
- Research only; NO orders or live strategy changes. Cash yield assumption = 0% p.a.
- Signals are based on the previous completed close; all fills at the next session open; trading costs = 10 bps per side (assumed).
- ETF distributions and adjust factors need independent audit. V2.0 MACRO data are incomplete; no faithful V2.0 numerical comparison yet.

## Matched rolling three-year windows
Each window starts with a fresh portfolio of 10% ETF core + 5% satellite cash + 85% other cash. The table isolates satellite signal skill **without dynamic cap trimming**, because cap-triggered churn otherwise dominates comparisons. A separate strict-cap stress profile is retained. Adjacent windows overlap and are NOT independent.

| Strategy | Avg satellite P&L (portfolio pp) | vs immediate addition (pp) | vs DCA (pp) | Win share vs immediate | Avg max DD of total portfolio | Worst max DD | Avg trade count |
|---|---:|---:|---:|---:|---:|---:|---:|
| B0_lump | +2.122 | +0.000 | -0.010 | 0% | -3.50% | -10.72% | 1.0 |
| B1_DCA | +2.132 | +0.010 | +0.000 | 50% | -3.44% | -10.66% | 6.0 |
| B2_cash | +0.000 | -2.122 | -2.132 | 0% | -2.42% | -7.64% | 0.0 |
| S1_TSMOM252 | +1.781 | -0.341 | -0.351 | 10% | -3.40% | -10.46% | 16.0 |
| S2_DONCHIAN55_20 | +0.886 | -1.236 | -1.246 | 0% | -3.03% | -9.20% | 12.3 |
| S3_MA50_200 | +1.969 | -0.153 | -0.163 | 30% | -3.21% | -9.48% | 12.5 |
| S1_TSMOM252_ATR | +1.028 | -1.094 | -1.104 | 0% | -3.29% | -9.48% | 55.2 |
| S2_DONCHIAN55_20_ATR | +0.407 | -1.715 | -1.725 | 0% | -2.76% | -8.79% | 20.1 |
| S3_MA50_200_ATR | +1.164 | -0.958 | -0.968 | 0% | -3.09% | -8.73% | 41.5 |

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
- **Signal-study table does not enforce the 15% total portfolio cap.** It is NOT a deployable allocation strategy by itself. A separate constrained stress run is included in RESULTS.json.
- If long-term core exceeds 15% itself, a sell/rebalance policy is required for actual deployment; it is currently flagged rather than silently sold.
- ATR correction is tested as a paired overlay, not presumed to improve performance.
- **These outputs are provisional.** Independent validation of dividend/split treatment, macro-factor histories, rolling OOS and sensitivity to costs/latency is required before selecting a live signal.
