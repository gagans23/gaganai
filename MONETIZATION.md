# Monetization Gateway plan — gagansachdeva.com

Prepared 2026-07-08 for Cloudflare's Monetization Gateway (announced 2026-07-01,
early access via waitlist: https://blog.cloudflare.com/monetization-gateway/).
Protocol: x402 — non-paying callers receive HTTP 402 + payment terms; settlement
in USDC to the seller wallet. Enforcement happens at Cloudflare's edge; nothing
changes on GitHub Pages.

## Strategy (agreed)

Reach is the site's engine. Human readers and AI *citation* stay free everywhere.
We charge only autonomous consumers of two high-value machine assets, and we
never put a price between a human and the content.

robots.txt already carries the matching public stance:
`Content-Signal: search=yes, ai-input=yes, ai-train=no`.

## Status / prerequisites

- [x] Domain proxied through Cloudflare (done — analytics setup, June 2026)
- [ ] Waitlist joined (Gagan — Google Form linked from the blog post)
- [ ] Access granted to Monetization Gateway in dashboard
- [ ] Seller wallet created/connected for USDC settlement (Gagan — never Claude)
- [ ] Rules below configured
- [ ] End-to-end 402 test passed (see bottom)

## Payment rules (configure when access lands)

| # | Path(s) | Price (suggest) | Exemptions | Rationale |
|---|---------|-----------------|------------|-----------|
| 1 | `/data/signal-gate.json` | $0.01 / request | verified search crawlers | Daily resolved intelligence (the gate's output) — highest-value machine asset |
| 2 | `/data/knowledge-graph.json` | $0.01 / request | verified search crawlers | Entity/edge graph built from the ledger |
| 3 | `/data/signal-ledger.jsonl` | $0.05 / request | verified search crawlers | The full persistent ledger — bulk asset, priced above the derived views |
| 4 | `/feed.xml` | $0.005 / request | verified search crawlers, feed readers if distinguishable | Machine syndication of the daily edition |
| 5 | `/agentic-ai/The-Curious-Minds-Guide-to-Agentic-AI.pdf` and `.epub` | $2.00 / request | none needed (humans arrive via the gate page, agents fetch direct) | Humans "pay" with an email; agents pay in USDC — same funnel, two currencies |

Explicitly FREE (never add rules): `/`, `/writing/*`, `/signal.html`, `/radar.html`,
`/graph.html`, `/briefs/*`, `/about.html`, `/agentic-ai/` (landing + online read),
`/radar/*` archives, all `/assets/*`.

Notes:
- Keep rule scope to exact paths above; wildcard rules risk catching human-facing pages.
- `data/radar-signals.js` stays free — the human radar page loads it in-browser.
- Revisit prices after 30 days of AI Crawl Control data (see below).

## Before access lands (available today)

1. Cloudflare dashboard → zone → **AI Crawl Control**: enable visibility, note which
   AI crawlers hit the site and how often — this data sets real prices.
2. Leave all crawlers ALLOWED for now (reach strategy); the gateway will charge the
   two machine assets rather than block anyone.

## End-to-end test (run after configuring)

```bash
# expect HTTP 402 + x402 payment-terms headers on priced paths:
curl -si https://gagansachdeva.com/data/signal-gate.json | head -20
# expect HTTP 200 (free) on human pages:
curl -so /dev/null -w "%{http_code}\n" https://gagansachdeva.com/signal.html
# the signal page itself must still hydrate: its own fetch of signal-gate.json is
# same-origin browser traffic — confirm in the browser after rules go live, and if
# the gateway cannot exempt it, switch rule 1 to a copy at /api/signal-gate.json
# and keep /data/* free (site JS depends on it).
```

⚠️ The biggest implementation risk is exactly that last line: signal.html, graph.html
and the homepage fetch `/data/*.json` from browsers. If gateway exemptions can't
distinguish same-origin browser fetches from agent fetches, DO NOT price `/data/*`
directly — mirror the files to `/api/*` for agents and price only `/api/*`.
