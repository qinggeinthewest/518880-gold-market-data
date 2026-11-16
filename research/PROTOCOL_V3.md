# V3.0 — 518880 Gold ETF independent strategy study (protocol frozen before results)

Status: **RESEARCH ONLY**. No orders, no live strategy replacement, no claimed performance advantage.

## Scope and investable policy
- Instrument: SSE 518880, long-only; Chinese-market historical OHLCV. No futures, leverage, shorting or intraday hindsight.
- Benchmark allocation: 10% core gold holding; separate **at most 5 percentage points** satellite. The core is *not* sold automatically by a satellite exit signal. If the core alone exceeds the 15% portfolio risk ceiling after price appreciation, issue a risk flag; model a distinct optional rebalancing scenario instead of silently liquidating core.
- Buy signals, **satellite sell signals**, and **error-correction exits** are evaluated together. A forecast correction is NOT a correction of already-confirmed market data.
- All strategies share identical sample, entry execution at the **next session opening print** after the fully observed prior-day close signal, and matched trading costs.

## Pre-registered competing strategies (do not tune on holdout)
- B0: buy the whole 5% satellite on the evaluation start date and hold. Strong benchmark.
- B1: equally add the 5% satellite in six 21-trading-day installments, hold. DCA benchmark.
- B2: keep the 5% in cash as the risk baseline.
- S1: 252-day *time-series momentum*. Enter when previous close exceeds close 252 completed sessions earlier; exit when below; never infer same-session fills.
- S2: Donchian **55-day entry / 20-day exit** using only prior completed OHLC. Enter after a close above the prior 55-day high; exit after a close below the prior 20-day low.
- S3: 50/200-day moving-average filter. Enter when previous close > its MA200 AND MA50 > MA200; exit when previous close < MA200.
- Each S strategy also has a pre-specified **correction overlay** S+ATR: satellite exit if the previous close falls below the highest observed close since entry less 2.5×previous-day ATR14, then a five-session re-entry cooldown. Compare correction on/off; these are *hypotheses*, not validated profitable rules.
- V2.0 full multifactor is a separate baseline **only once synchronized historical Au99.99, USD/CNY, DXY, TIPS, and the original V2.0 state rules have been acquired**. Do NOT mislabel technical-only proxies as a faithful V2.0 backtest.

## Data gate and leakage controls
1. Target 2013 listing onward via domestic China-market provider; fetch a **minimum of 800 completed daily OHLCV** before producing even preliminary out-of-sample comparisons; prefer 8+ years.
2. Check corporate actions (cash distributions, splits, share adjustments); if provider returns unadjusted prices and distributions have not been reconciled, report outcomes as **PROVISIONAL — not valid for live selection**. For backtest total return, use a verified adjusted total-return basis (or actual cash distributions), while trade execution uses actual tradable prices. Never recompute historical trades using future adjustment factors as if known live.
3. Split chronologically: common 253-session warmup; train/inspection segment; **last at least 252 sessions as untouched out-of-sample**. If fewer than 800 bars, do not rank strategies.
4. All signals use information known at the previous close; fills at **next session open** with costs. Apply plausible round-trip friction and sensitivity of 5/10/20 basis points per side. Never assume trades at prior close after seeing that close.
5. Report alongside portfolio CAGR: maximum drawdown, excess return versus B0 and B1, annual volatility, Sharpe (with explicit cash yield), annual turnover/trade count, actual satellite exposure, maximum adverse excursion following entry, time underwater and failed-breakout/re-entry counts. Report train and holdout separately.
6. Macro-factor overlay: chronological, timestamp-aware data only; gaps suspend factor-based decisions rather than assume improvement. Regimes must be defined before testing the holdout.
7. Robustness check: multiple market regimes, alternative cost assumptions, and 1/2-day implementation delays. Do not search hundreds of parameters and cherry-pick the best. Results are observational, not guarantees.

## Research / live-system separation
- This research runs exclusively via `v3_research.yml` and writes only under `research/`.
- **Do not modify** `scripts/pull_snapshot.py`, `.github/workflows/update_518880.yml`, or the live ChatGPT 518880 signal task until a method has passed the data and validation gates and the investor approves deployment.
- No trading API keys, brokerage secrets, personal portfolio records or API passwords belong in this public repository.


## Transparent methodology amendment: rolling-window initialization
**Added after inspecting the first engineering run on 2026-11-16, NOT a pre-registered performance optimization.** The initial backtest held the same 10% gold core from 2014 to 2026 and allowed market appreciation to inflate core exposure past the intended 15% target, leaving many later years with no satellite capacity. This is not the investor's contemplated present-day decision. To correct that modeling error, V3 now evaluates **10 matched 756-trading-day windows** starting approximately a year apart, and includes a most-recent window; every window restarts at 10% gold core, 5% satellite cash and 85% other assets. Windows overlap, so the ten outcomes are **not ten independent statistical samples**. Holdout checks and corporate-action audits remain mandatory; these results cannot be described as pristine pre-registration. This change was made for portfolio comparability, not because it improved one selected signal.
