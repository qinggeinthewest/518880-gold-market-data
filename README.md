# 518880 ETF: automatic public-market snapshot for ChatGPT

## One-time setup

1. Create a **public** GitHub repo named `518880-gold-market-data` (any name works).
2. Unzip this package. Using your GitHub repo's `Add file > Upload files`, upload files **and preserve paths**, especially `.github/workflows/update_518880.yml` and `scripts/pull_snapshot.py`. Do not upload only the ZIP. You can instead use GitHub Desktop to commit the unzipped folder to a repo (more reliable for paths).
3. Open repo's Actions tab and, if prompted, enable workflows. Open workflow `Update 518880 public market snapshot` and use `Run workflow` once while the China stock market is open.
4. If GitHub settings override the per-job permissions, allow `Read and write permissions` for workflow tokens under repo `Settings > Actions > General > Workflow permissions`. This workflow uses the short-lived built-in GITHUB_TOKEN, never a user-created token.
5. When the first valid snapshot is published, open:
   `https://raw.githubusercontent.com/YOUR_USERNAME/518880-gold-market-data/main/docs/latest.md`
   and `https://raw.githubusercontent.com/YOUR_USERNAME/518880-gold-market-data/main/docs/latest.json`.
   Share the actual GitHub URL with ChatGPT for independent access verification.

## Architecture

- GitHub Actions scheduled workflow (UTC): `17,27,47 1-3,5-7 * * 1-5` = Beijing weekdays in 09–11 and 13–15 hour blocks.
- Fetches user's existing Cloudflare Worker `/ ?format=json` (remove space): `https://gold-etf-518880.qinggeinthewest.workers.dev/?format=json`.
- Checks China-market timestamps, quote freshness <=20 minutes, cross-source price agreement, last completed daily OHLC count >=60, and fundamental price/indicator consistency.
- Commits `docs/latest.json` and `docs/latest.md` **only when fresh validated data exist**. Otherwise it leaves previous snapshots intact. This is by design; **consumers must reject stale file timestamps.**
- No user credentials, broker access, finance accounts, or trades.
- IMPORTANT: This is an ETF market-data bridge, **NOT** a complete gold trading signal. Existing automations still need SGE Au99.99, USD/CNY, and macro filters before issuing advice.

## Reliability limits

- GitHub Actions scheduled jobs can be delayed or skipped: there is no real-time SLA. If a snapshot is stale, ChatGPT must stay silent and never treat it as a live quote.
- GitHub hosted runners may be blocked from accessing the Worker, even though browsers can. The first manual run tests this. If blocked, deploy a different publish path.
- Public GitHub repo exposes only *public market data*; do not add passwords/tokens, portfolio details, personal documents, or holdings.
- The author has not yet verified this workflow live in the user's GitHub environment.
