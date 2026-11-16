# V3.0 518880 backtest — automated, research only

## Data and validation

- Status: **PROVISIONAL_UNAUDITED**
- Notes: Research calculations completed, but corporate-action/distribution-adjusted total returns and independent out-of-sample validity are NOT certified.
- Data: eastmoney_hfq, 3233 completed trading days; adjustment: hfq_as_published_needs_corporate_event_review
- No trading advice or replacement of live V2 signals.

## Pre-registered portfolio comparisons

10% core + up to 5% satellite; remaining 85% cash; equal next-day-open fills; all costs explicit.

| Policy | Full sample CAGR | Full max DD | Holdout return | Holdout max DD | Holdout Sharpe | Trades | Correction exits |
|---|---:|---:|---:|---:|---:|---:|---:|
| B0_lump | 1.66% | -11.31% | -2.88% | -11.31% | -0.297 | 56 | 0 |
| B1_DCA | 1.68% | -11.28% | -2.87% | -11.28% | -0.298 | 63 | 0 |
| B2_cash | 1.56% | -11.42% | -2.91% | -11.42% | -0.297 | 0 | 0 |
| S1_TSMOM252 | 1.64% | -11.34% | -2.89% | -11.34% | -0.297 | 202 | 0 |
| S2_DONCHIAN55_20 | 1.58% | -11.40% | -2.90% | -11.40% | -0.297 | 153 | 0 |
| S3_MA50_200 | 1.64% | -11.33% | -2.89% | -11.33% | -0.297 | 175 | 0 |
| S1_TSMOM252_ATR | 1.63% | -11.35% | -2.89% | -11.35% | -0.297 | 426 | 47 |
| S2_DONCHIAN55_20_ATR | 1.59% | -11.39% | -2.90% | -11.39% | -0.297 | 144 | 23 |
| S3_MA50_200_ATR | 1.62% | -11.36% | -2.89% | -11.36% | -0.297 | 309 | 36 |

**DO NOT RANK AS VERIFIED** until distributions/corporate actions are audited, multi-period out-of-sample checks pass and macro data are available for faithful V2.0 comparisons.

## Execution and correction rules

- Indicators use only completed close bars; orders execute at next session open.
- Satellite exits on trend loss, 55/20 Donchian exit, MA200 exit, or pre-registered 2.5 ATR correction; 5-session cooling-off after correction.
- Any 15% portfolio excess is trimmed from satellite at next open, with core protected; residual core-only breaches are flagged.
- Costs use 10 bps per side (commission + slippage, illustrative), with sensitivity checks at 5 and 20 bps.
- Current V2.0 multi-factor strategy requires daily Au99.99/USD-CNY/TIPS/DXY data and is not ranked here.
