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

### Landing hierarchy — `[codex]` 2026-06-29, second pass

The homepage was deliberately compressed from eleven promotional sections into one visitor journey:
**direct hero → live signal → compact four-door index → field notes + diagnostic → work + proof →
library → human about → subscribe**.

- Keep the live Situation Room immediately below the hero. It is the unique product demonstration,
  not a supporting promo to bury below generic navigation.
- The hero leads with the practitioner promise: systems that let institutions trust AI enough to
  act. “Intelligence is becoming infrastructure” remains the framing line, not the primary claim.
- Beliefs, capabilities, GitHub, and résumé proof now live together in `build-proof-section`; do not
  split them back into repetitive full-height sections.
- On mobile the video is replaced by `hero-poster.webp`, so the message and both actions load without
  motion or a 1,000px opening screen.
- Treat roughly 600–750 homepage words and 7–8 desktop viewports as a useful editorial ceiling.

### Signal decision brief — `[codex]` 2026-06-29

`signal.html` is now an executive decision brief, not a methodology-first visualization. Preserve the
order: **decision promise → four direction cards → evidence map → full decision briefs → method →
rejected items**.

- `data/attractors.json` is the editorial source of truth for each direction's `strengthLabel`,
  `strengthDetail`, `decision`, `actNow`, `watchNext`, and `disconfirming` fields.
- `automation/build_signal_gate.py` propagates those fields and distinguishes `stats.mapped` from
  `stats.unresolved`. Keep the accounting invariant: `mapped + unresolved + noise == stimuli`.
- A structural signal that has not accumulated enough evidence to join an attractor stays visible in
  `other`; do not silently count it as explained. The headline facts currently read 26 verified / 19
  mapped / 4 directions / 1 unresolved.
- `assets/signal-brief.css` owns the decision-brief layer. The older inline CSS remains critical-path,
  including the required `.room-nav` rules.
- The desktop convergence SVG uses short, stable direction labels. On mobile it is hidden and replaced
  by four stacked evidence paths; never shrink the 1100px SVG into an unreadable thumbnail again.
- Source lists, methodology tests, and rejected items are progressively disclosed. Depth should come
  from **Act now / Watch next / What would change our mind**, not from placing every source above the fold.

## About page + share-ready essays — `[codex]` 2026-06-30

Two related changes shipped together (commit `61d613d` for metadata, then the about page):

**Dedicated `/about.html` (open item #1, now done).** A standalone ledger page using the shared
`assets/editorial-shell.css` shell and the same warm-paper type/colour system. Structure:
story → the work (proof band + systems grid + blockquote + build links) → four beliefs →
credentials & proof → subscribe/contact. It carries `Person` + `AboutPage` JSON-LD (jobTitle,
worksFor = First Abu Dhabi Bank, `sameAs` LinkedIn/GitHub/Medium) and full OG/Twitter/canonical
metadata. The homepage `#about` section stays as a compact teaser with a `The full story →` link
(`.about-more` in `site-home.css`) to `about.html`.

**Every essay is now share-ready.** The four older essays (`why-trace-first`,
`the-gap-is-the-equation`, `levels-of-ai-pilled`, `agent-control-plane`) previously had no
`og:image`/`og:url`/`twitter:card`/`canonical`/RSS link, so sharing them produced no preview card
and left no canonical URL. All six essays now carry those plus `Article` JSON-LD (headline, author,
`datePublished`, `dateModified`, image). `levels-revisited` also gained the favicon + RSS link it
was missing. `datePublished` follows the granularity each essay already displays on the site (full
dates where shown, `YYYY-MM` otherwise); `dateModified` is the last commit date.

**Removed:** `assets/landing-hero-ai-institutions.png` (2.1 MB, unreferenced anywhere).

**Nav convention (keep).** The four-door **About** link is now `about.html` on every page. This was
updated in: all root pages, all `writing/*.html` + `writing/index.html`, `briefs/index.html` +
`briefs/2026-06.html`, `index.html` (primary nav + the 4-door hub card), `automation/radar.template.html`
(rebaked into `radar.html` via `render_radar.py`), and `automation/build_monthly_brief.py` (so future
briefs point to `about.html`). Archived radar editions under `radar/*` are intentionally left as
frozen snapshots and were not rewritten. `sitemap.xml` now lists `about.html`.

## Situation Room enrichment — `[codex]` 2026-06-30

Experience-layer upgrades to the four Situation Room views (signal, radar, graph,
briefs). These make the room feel alive and connected; they need fresh signal flow
(the `PARALLEL_API_KEY` open item) to fully pay off.

**Signal page (`signal.html`) — freshness + cross-links.** The page hydrates client-side
from `data/signal-gate.json` (it is NOT baked by `build_signal_gate.py` — that script
writes data only). Added:
- A "Last verified / Next review" stamp in `.brief-meta`: `#updatedMeta` (gate
  `generated`), `#windowMeta` (gate `window.from → window.to`), and a new `#nextReview`
  computed as `generated + 3 days`. Returning readers can now tell whether the brief is
  current.
- A `#newestMoves` block under the factbar listing the 3 most-recent verified moves
  across all attractors + `other`, sorted by signal date desc. Computed client-side from
  the gate (signal `date` strings are `Date`-parseable).
- Cross-links in every attractor's evidence-drawer `trace-grid` (now 6 steps,
  `grid-template-columns:repeat(auto-fit,minmax(130px,1fr))`): **Graph** → `graph.html`,
  **Feed** → `radar.html`, **Brief** → `briefs/index.html`. The `#evidence` footer now
  links to both the graph and the daily feed.
- `WebPage` + `Dataset` JSON-LD added to the head.

**Radar daily feed — "New today" vs "Ongoing context".** Carry-forward stories no
longer pretend to be today's news. The story stack is split into two labelled groups:
fresh signals under "New today", carry-forwards under "Ongoing context" (each with a
count). Implemented in BOTH places that render the story list — keep them in lockstep:
- `automation/render_radar.py` (`group()` helper, emitted into `{{STORY_LIST}}`).
- `assets/radar.js` (`renderStoryList`) — the page hydrates and re-renders client-side,
  so the grouping must be mirrored here or hydration wipes it.
The "Other Stories / rest of the page one picture" heading became "On the page / Beyond
the lead." `.story-group-head` CSS is inlined in `automation/radar.template.html`
(survives a `radar.css` revert, per the existing convention). With only one fresh signal
(the lead), the live page currently shows just "Ongoing context" — that is honest, and
"New today" appears automatically once the daily pipeline delivers fresh signals.
Bake version bumped `-r3` → `-r4` to cache-bust the changed `radar.js`.

**Sitemap.** `signal.html` (daily) and `graph.html` (weekly) added to `sitemap.xml` —
previously the Situation Room's lead views were invisible to search.

## Information architecture — 4 doors (keep)
Primary nav on every page: **Writing · Situation Room · Library · About**.
- **Situation Room** is ONE hub of four views sharing a secondary `.room-nav` "altitude" bar:
  **Signal · Daily Feed (radar) · Graph · Briefs**. The door lands on `signal.html` (lead = inference).
- **Library** groups **Podcasts + Books** (its own `.room-nav`).
- **About** = dedicated `/about.html` page (since 2026-06-30). The homepage keeps a compact `#about` teaser section that links to the full page. The four-door primary nav **About** link points to `about.html` on every page (absolute `https://gagansachdeva.com/about.html` on inner pages, relative `about.html` on root pages and the radar template).
- The homepage body mirrors these doors: hero → 4-door hub → Writing → Situation Room → Library → About cluster → Subscribe.

When adding a page: give it the 4-door primary nav; add the altitude bar if it's a Situation Room view.
- `/about.html` is a top-level door (like Library): 4-door primary nav with `aria-current="page"` on About, the shared `assets/editorial-shell.css` ledger shell, and its own `Person` + `AboutPage` JSON-LD. No `.room-nav` altitude bar (it is not a Situation Room view).
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
1. ~~Optional dedicated `/about.html`~~ — **DONE 2026-06-30** (`[codex]`). See the
   "About page + share-ready essays" section above.
2. Rotate the Parallel API key (it was exposed in a prior chat) and re-run
   `gh secret set PARALLEL_API_KEY --repo gagans23/gaganai`.
