/**
 * 518880 Cloudflare Cron publisher.
 *
 * Reads the existing public quote Worker; validates a fresh SSE:518880
 * snapshot; atomically commits docs/latest.json + docs/latest.md to GitHub.
 * Does not calculate or generate trading signals.
 *
 * Bind one Cloudflare Secret: GITHUB_TOKEN
 * Cron Trigger (UTC weekdays): */5 1-3,5-7 * * 1-5
 *
 * Do not expose the token in HTTP responses, logs or the repository.
 */
const REPOSITORY = "qinggeinthewest/518880-gold-market-data";
const SOURCE_URL = "https://gold-etf-518880.qinggeinthewest.workers.dev/?format=json";
const API = "https://api.github.com/repos/" + REPOSITORY;

function beijingParts(date = new Date()) {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Shanghai",
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", hourCycle: "h23",
  }).formatToParts(date);
  const p = Object.fromEntries(parts.map(x => [x.type, x.value]));
  return { date: p.year + "-" + p.month + "-" + p.day,
    hour: Number(p.hour), minute: Number(p.minute),
    weekday: new Date(Date.UTC(Number(p.year), Number(p.month) - 1, Number(p.day))).getUTCDay() };
}

function inTradingTime(p) {
  const n = p.hour * 60 + p.minute;
  return p.weekday >= 1 && p.weekday <= 5 &&
    ((n >= 570 && n <= 690) || (n >= 780 && n <= 900));
}
function positive(n) { return typeof n === "number" && Number.isFinite(n) && n > 0; }

function validate(payload, now) {
  if (!payload || payload.symbol !== "518880" || payload.usable_for_signals !== true ||
      payload.trading_session !== true) throw new Error("Source instrument/session invalid");
  const q = payload.quote, h = payload.history;
  if (!q || !h || !["腾讯财经", "新浪财经"].includes(q.source) ||
      !["sina_kline_money", "sina_kline_cn"].includes(h.source))
    throw new Error("Unexpected quote/history source");
  if (![q.price_yuan, q.previous_close_yuan, q.open_yuan, q.high_yuan,
        q.low_yuan].every(positive) || q.low_yuan > q.price_yuan + 0.01 ||
      q.price_yuan > q.high_yuan + 0.01)
    throw new Error("Invalid quote prices");
  const ts = q.exchange_time_ms;
  if (!Number.isSafeInteger(ts)) throw new Error("Missing quote timestamp");
  const ageMs = now.getTime() - ts;
  if (ageMs < -120000 || ageMs > 20 * 60000)
    throw new Error("Quote age out of range: " + (ageMs / 60000).toFixed(1) + " minutes");
  const nowBJ = beijingParts(now), quoteBJ = beijingParts(new Date(ts));
  if (nowBJ.date !== quoteBJ.date || !inTradingTime(quoteBJ))
    throw new Error("Quote is not from current Beijing trading session");
  if (!Array.isArray(payload.quote_crosscheck) || payload.quote_crosscheck.length < 2)
    throw new Error("Fewer than two independent domestic quote sources");
  const prices = payload.quote_crosscheck.map(x => x.price_yuan);
  const sources = new Set(payload.quote_crosscheck.map(x => x.source));
  if (!prices.every(positive) || sources.size < 2 ||
      Math.max(...prices) / Math.min(...prices) - 1 > 0.004)
    throw new Error("Source cross-check failed");
  if (!Array.isArray(h.recent_completed_rows) ||
      h.recent_completed_rows.length < 60 || h.completed_rows < 60 ||
      h.last_row_provisional !== false)
    throw new Error("Insufficient or unfinished historical candles");
  const last = h.recent_completed_rows.at(-1);
  if (last?.date !== h.last_completed_date ||
      h.last_completed_date >= quoteBJ.date)
    throw new Error("Last completed candle date invalid");
  for (const k of ["ma5", "ma10", "ma20", "ma60", "atr14", "high60", "low10"])
    if (!positive(h[k])) throw new Error("Missing historical indicator: " + k);
  const lastDay = Date.parse(h.last_completed_date + "T00:00:00Z");
  const currentDay = Date.parse(quoteBJ.date + "T00:00:00Z");
  if (!(lastDay < currentDay) || currentDay - lastDay > 10 * 86400000)
    throw new Error("Historical candles are outdated");
  return Number((ageMs / 60000).toFixed(2));
}

async function github(path, token, method = "GET", data) {
  const r = await fetch(API + path, {
    method,
    headers: {
      Authorization: "Bearer " + token,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "518880-Cloudflare-Cron-Publisher",
      "Content-Type": "application/json",
    },
    body: data === undefined ? undefined : JSON.stringify(data),
  });
  if (!r.ok) throw new Error("GitHub " + method + " " + path + " failed: " + r.status);
  const str = await r.text();
  return str ? JSON.parse(str) : null;
}

function toUtf8Base64(content) {
  const bytes = new TextEncoder().encode(content);
  let binary = "";
  for (let i = 0; i < bytes.length; i += 8192) {
    binary += String.fromCharCode(...bytes.slice(i, i + 8192));
  }
  return btoa(binary);
}

async function readCurrent(token) {
  const file = await github("/contents/docs/latest.json?ref=main", token);
  if (file.encoding !== "base64" || !file.content)
    throw new Error("Cannot decode GitHub latest.json");
  const binary = atob(file.content.replace(/\\s/g, ""));
  const bytes = Uint8Array.from(binary, c => c.charCodeAt(0));
  return JSON.parse(new TextDecoder().decode(bytes));
}

function makeMarkdown(data) {
  const q = data.quote, h = data.history;
  const lines = [
    "# 518880 中国市场行情快照",
    "",
    "- 快照发布UTC时间：" + data.snapshot_published_utc,
    "- 最新成交北京时间：" + q.exchange_time_beijing,
    "- 最新成交价格：" + q.price_yuan + "元（昨收 " + q.previous_close_yuan + "元）",
    "- 今日开高低：" + q.open_yuan + " / " + q.high_yuan + " / " + q.low_yuan + "元",
    "- 成交量：" + q.volume_hands + "手；成交额：" + q.turnover_yuan + "元",
    "- 已完成日K线截至：" + h.last_completed_date + "；" + h.completed_rows + "个已完成交易日",
    "- MA5/10/20/60：" + [h.ma5,h.ma10,h.ma20,h.ma60].join(" / "),
    "- ATR14：" + h.atr14 + "；过去60个完成日最高价：" + h.high60,
    "- 腾讯财经／新浪财经价格交叉验证；日K线来自新浪Money。",
    "- 注意：没有独立验证上金所Au99.99、在岸USD/CNY、TIPS或DXY，不得直接生成交易信号。",
    "- 读取时必须独立校验成交时间，切勿把发布时刻当成交时刻。",
    "",
    "## 最近十个已完成交易日K线（日期 开 高 低 收）",
    "",
  ];
  for (const x of h.recent_completed_rows.slice(-10))
    lines.push("- " + [x.date,x.open,x.high,x.low,x.close].join(" "));
  return lines.join("\n") + "\n";
}

async function publish(env) {
  if (!env.GITHUB_TOKEN) throw new Error("Missing GITHUB_TOKEN secret");
  const now = new Date();
  const nowBJ = beijingParts(now);
  if (!inTradingTime(nowBJ)) {
    console.log("Skip: outside Beijing A-share trading hours");
    return;
  }
  const srcResponse = await fetch(SOURCE_URL, {
    headers: { Accept: "application/json" },
    cf: { cacheTtl: 0, cacheEverything: false },
  });
  if (!srcResponse.ok) throw new Error("Quote Worker HTTP " + srcResponse.status);
  const payload = await srcResponse.json();
  const age = validate(payload, now);
  const existing = await readCurrent(env.GITHUB_TOKEN);
  const newTs = payload.quote.exchange_time_ms;
  if (existing?.quote?.exchange_time_ms >= newTs) {
    console.log("Skip: same or older exchange quote");
    return;
  }

  const selected = {
    instrument: "SSE:518880",
    snapshot_published_utc: now.toISOString(),
    quote_age_minutes_at_publish: age,
    quote: payload.quote,
    quote_crosscheck: payload.quote_crosscheck,
    history: payload.history,
    sources: {
      quote: "Tencent Finance / Sina Finance via existing Cloudflare Worker",
      history: "Sina Money domestic K-line via existing Cloudflare Worker",
    },
    scope: "ETF market data only; Au99.99, onshore USD/CNY, TIPS and DXY unverified",
  };
  const json = JSON.stringify(selected, null, 2) + "\n";
  const md = makeMarkdown(selected);

  // One atomic Git commit updates both files. A concurrent branch update
  // rejects the non-fast-forward push; the next Cron run will retry.
  const head = await github("/git/ref/heads/main", env.GITHUB_TOKEN);
  const oldSha = head.object.sha;
  const commit = await github("/git/commits/" + oldSha, env.GITHUB_TOKEN);
  const [blobJson, blobMd] = await Promise.all([
    github("/git/blobs", env.GITHUB_TOKEN, "POST", { content: json, encoding: "utf-8" }),
    github("/git/blobs", env.GITHUB_TOKEN, "POST", { content: md, encoding: "utf-8" }),
  ]);
  const tree = await github("/git/trees", env.GITHUB_TOKEN, "POST", {
    base_tree: commit.tree.sha,
    tree: [
      { path: "docs/latest.json", mode: "100644", type: "blob", sha: blobJson.sha },
      { path: "docs/latest.md", mode: "100644", type: "blob", sha: blobMd.sha },
    ],
  });
  const next = await github("/git/commits", env.GITHUB_TOKEN, "POST", {
    message: "Update 518880 quote snapshot (Cloudflare Cron)",
    tree: tree.sha,
    parents: [oldSha],
  });
  await github("/git/refs/heads/main", env.GITHUB_TOKEN, "PATCH", {
    sha: next.sha, force: false,
  });
  console.log("Published 518880", payload.quote.exchange_time_beijing, "age_minutes", age);
}

export default {
  async fetch() {
    return new Response("518880 publisher running; scheduled updates only.", {
      headers: { "content-type": "text/plain; charset=utf-8" },
    });
  },
  async scheduled(_controller, env, ctx) {
    ctx.waitUntil(publish(env));
  },
};
