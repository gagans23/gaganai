# Handoff — gagansachdeva.com

**Repo:** github.com/gagans23/gaganai · **branch:** main
Static site on GitHub Pages (custom domain gagansachdeva.com, proxied through Cloudflare).
This doc is the shared context for working in this repo (Claude + Codex).

## Design system (keep)
Editorial: **Fraunces** (display), **Source Serif 4** (body), **IBM Plex Mono** (labels);
warm paper palette `#f2efe6` / amber `#b3661f` / `#9b6b2d`. The homepage is intentionally the
dark cinematic **cover**; inner pages are the warm paper **ledger**, but both use the same type,
amber signal colour, marginalia, and navigation language. Cloudflare Web Analytics beacon
(`token bdc556ad04c94787a68f270df061e5e4`) is in every page before `</head>`.

### Design implementation — `[codex]` 2026-06-29

This is shared Claude + Codex context. If Claude changes these surfaces, preserve the system rather
than treating them as isolated decoration:

- `assets/editorial-shell.css` is the shared inner-page ledger shell: visible four-door mobile nav,
  sticky altitude bar, ledger marginalia, brand mark, and print rules. Root pages load `assets/...`;
  briefs and writing load `../assets/...`.
- `index.html` + `assets/site-home.js` load the current signal gate and graph data into the live
  Situation Room module. It must fail softly when either data file is unavailable.
- The homepage provenance visual is the canonical explainer for **ledger → graph → gate → brief**.
  Motion explains data flow and must continue to respect reduced-motion preferences.
- `signal.html` exposes a provenance trace for every attractor. Its SVG spine is seeded from the
  generation date; do not reintroduce `Math.random()`, because the same ledger should produce the
  same picture.
- `graph.html` has three data-derived guided threads that dim unrelated nodes. Its graph layout is
  also seeded for visual stability.
- Monthly briefs are numbered (`Issue YYYY.MM`) with print/PDF treatment. Change
  `automation/build_monthly_brief.py` and regenerate; do not polish only the baked brief HTML.
- `automation/radar.template.html` loads the shared shell. CI still owns the resulting `radar.html`.

## Information architecture — 4 doors (keep)
Primary nav on every page: **Writing · Situation Room · Library · About**.
- **Situation Room** is ONE hub of four views sharing a secondary `.room-nav` "altitude" bar:
  **Signal · Daily Feed (radar) · Graph · Briefs**. The door lands on `signal.html` (lead = inference).
- **Library** groups **Podcasts + Books** (its own `.room-nav`).
- **About** = homepage `#about` section (folds in Beliefs / Build / GitHub / bio).
- The homepage body mirrors these doors: hero → 4-door hub → Writing → Situation Room → Library → About cluster → Subscribe.

When adding a page: give it the 4-door primary nav; add the altitude bar if it's a Situation Room view.
`.room-nav` CSS is inlined per page using that page's own CSS vars.

## The intelligence engine (stdlib-only, runs in the daily pipeline)
- `data/signal-ledger.jsonl` — persistent, append-only ledger of every curated signal (deduped by url+title).
- `automation/build_knowledge_graph.py` → `data/knowledge-graph.json` (powers `/graph.html`).
- `automation/build_signal_gate.py` → `data/signal-gate.json` (powers `/signal.html`, "The Noise Gate":
  signal-vs-noise classification + what it points toward). Inference prose is hand-authored in
  `data/attractors.json` (each attractor explicitly owns its signals by title fragment).
- `automation/build_monthly_brief.py` → `briefs/<YYYY-MM>.html` + `briefs/index.html` (month-end retrospective).
- **Layer classifier** (`LAYER_RE` / `classify_layer`) is duplicated in `automation/render_radar.py`,
  `automation/build_knowledge_graph.py`, and `assets/radar.js` — **change all three together.**

## Pipeline rules (do not break)
- `automation/update_daily_intelligence.sh` publishes **DATA ONLY**: `data/radar-signals.js`,
  `data/podcast-intelligence.js`, `data/signal-archive.json`, `data/signal-ledger.jsonl`,
  `data/knowledge-graph.json`, `data/signal-gate.json`. It does **not** commit baked HTML.
- The **"Bake radar edition"** GitHub Action (`.github/workflows/bake-radar.yml`) rebakes
  `radar.html` + `feed.xml` + `radar/*` from `automation/radar.template.html` on data/template pushes.
  **Never hand-edit `radar.html`** — edit the template and let CI bake.
- **Cloud generation:** `.github/workflows/daily-intelligence.yml` runs the generator + graph + gate
  daily at 06:00 GST, gated on the `PARALLEL_API_KEY` repo secret (Settings → Secrets → Actions).
  `.github/workflows/monthly-brief.yml` auto-publishes the prior month's brief on the 1st.
  Generation is fully cloud-side now; the local Mac launchd job was retired.
- Cake CSS and `.room-nav` CSS are **inlined** in `radar.template.html` on purpose, so a reverted
  `radar.css` can't strip them.

## Conventions
- Commit prefix to show authorship: `[claude]`, `[codex]`; the cloud bot uses `[cloud]`.
- Canonical deploy clone is local-only; everything syncs through `origin/main`. Always commit + push.

## Open items
1. Optional dedicated `/about.html` (currently a homepage section).
2. Rotate the Parallel API key (it was exposed in a prior chat) and re-run
   `gh secret set PARALLEL_API_KEY --repo gagans23/gaganai`.
