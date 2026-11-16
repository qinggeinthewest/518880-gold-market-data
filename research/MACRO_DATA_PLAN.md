# V3 macro-series acquisition and V2.0 fidelity gate

**Status:** research source inventory; V2.0 full-factor backtest NOT YET EXECUTED. No assumptions about missing data.

## Required series / primary sources
1. CNY spot gold: Shanghai Gold Exchange official daily Au99.99 history.
   - 2024 onward: https://www.sge.com.cn/sjzx/quotation_daily_new
   - Before 2024: follow official site's separate history query. Record instrument, session window, official settlement/close, original publication date and units (CNY per gram).
   - SGE's trading day aggregates previous evening plus current day, including activity after 15:00 SSE ETF close. **Do not feed same-day finished SGE data into a 15:00 ETF entry decision**. Unless verified publish time earlier, delay to next available ETF session.
2. Onshore interbank USD/CNY, not retail bank FX rates and not USDCNH: China Foreign Exchange Trade System / eligible domestic vendor with reliable historical close timestamp.
3. 10-year real yield: US Treasury / FRED DFII10, explicitly record *observation date* and earliest public availability; e.g. https://fred.stlouisfed.org/series/DFII10
4. DXY: ICE administered U.S. Dollar Index (not the Fed's broad trade-weighted USD index); https://developer.ice.com/fixed-income-data-services/catalog/ice-data-indices-currency-indices . If no freely licensed reliable daily history is available, **do not replace DXY silently with another index**.
5. XAU/USD gold: reliable international spot-gold source; use for attribution only, not direct trigger of 518880.
6. Fee/slippage series and ETF distributions/splits: fund manager and SSE corporate-action announcements.

## Validation procedure
- Join all series by **first actionable timestamp**, not merely shared calendar date. A Friday U.S. close and following Monday Chinese ETF trade are different available-information boundaries.
- Keep explicit "not observed" missing values; no forward interpolation over a macro event. Holiday alignment must be handled separately for China and the U.S.
- Only after these series pass a history, coverage, publication-lag and quote-integrity audit may the **original V2.0 macro thresholds** be backtested faithfully next to S1-S3. Technical-only versions MUST be named differently and excluded from V2.0 verdicts.
- Core rebalancing / sell risk must be studied separately: test no discretionary core sale versus transparent predeclared >15%-weight defensive trim to a fixed target (e.g. 10%); count costs and tax sensitivity before using in live advice. Core sale is not currently live.
- In every proposed trade, data quality failure means "no new action", not a backtested profitable hold or an automatic sell.

## Next milestone
Record the first validated official Au99.99 historical sample, test multi-day alignment on 2024-2026, then source pre-2024 history and USD/CNY/TIPS/DXY; run a frozen V2.0 with no retroactive parameter tuning.
