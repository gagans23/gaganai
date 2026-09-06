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

## Pipeline now self-driving — bake runs in-workflow — `[codex]` 2026-06-30

RESOLVED. The daily-intelligence workflow pushes data using `GITHUB_TOKEN`, and GitHub does
not fire `on: push` workflows from `GITHUB_TOKEN` pushes — so the separate bake-radar workflow
does not auto-run after a cloud generation. Fix shipped: a `bake` job now runs inside
`daily-intelligence.yml` (`needs: generate`, gated on `needs.generate.outputs.ran == 'true'`)
that checks out the freshly-pushed main, runs `automation/render_radar.py`, and commits
`radar.html` + `radar/*` + `feed.xml` in the same run. Generation and baking are now one atomic
publish — no manual bake trigger needed after off-schedule generations. `bake-radar.yml` stays
as the template-change trigger + 06:30 GST safety net.

## Strategic review + positioning changes — `[codex]` 2026-06-30

A full design + content review was done (writing read in full, data engine audited,
repos verified). Rated 7.5/10: **writing 9, Situation Room product 5, design 7.**
The gap between those numbers is the story. Core diagnosis: the site is two products
(a practitioner essay site + a daily intelligence product) and the **weaker one was
front-and-center.** The radar (commodity daily news, 27 signals / 1 source / 1 fresh
story a day) cannot compete as a daily feed; the actual moat — the gate + attractor
inference — was buried as one of four co-equal views.

Changes shipped this round (buildable parts of the critique):

1. **Invert the Situation Room: gate is the product, radar is provenance.** The radar
   page is now framed as "The raw feed" — the unresolved source material the gate
   filters. Masthead title `The AI Situation Room` → `The raw feed`; deck rewritten to
   point up to `signal.html` ("the analysis lives on Signal"); a `.feed-provenance`
   banner links to the gate. The room-nav label `Daily Feed` → `The Feed` on every
   Situation Room view (signal, graph, radar template, briefs) and the homepage
   live-links. The Situation Room *door* still lands on `signal.html` (the gate) —
   that was already correct; this makes the radar stop pretending to be the headline.
   Archived `radar/*` editions left as frozen snapshots (not rewritten).

2. **"Start here" reading path.** `writing/index.html` now leads with a pinned 3-essay
   ordered path (`.start-here`): The Gap Is The Equation (stakes) → The Levels of an
   AI-Pilled Organization (diagnosis) → The Amnesia Tax (mechanism). The homepage
   features section has a `New here? Start with the 3-essay path →` CTA
   (`.start-here-cta`). Fixes the "no front door / flat archive" gap.

3. **Brand spine made explicit: the ledger.** `about.html` now carries a `.ledger-spine`
   block stating the unifying idea — a ledger records judgments and their outcomes
   (what a regulator audits + a model learns from); the essays are the human ledger,
   the Situation Room is the machine ledger, same thesis two zoom levels. "The
   Philosophical Ledger" was latent flavor text; this cashes it in as the connective
   tissue between the two products.

**Open strategic questions for Claude to comment on (not yet acted on):**

- **Cadence honesty.** The radar promises "daily" but sustains ~1 fresh story/day off
  one RSS source. Real options: invest hard in the source pipeline to make daily true
  (a part-time job), OR drop the daily claim and make the gate a *weekly* resolution
  ("every week the noise resolves into what changed"). A weekly gate with 20-30 fresh
  signals + an attractor shift is a stronger product than a daily feed with one story.
- **Assertion vs demonstration (the biggest content gap).** Every essay asserts
  governed systems at enterprise scale; nowhere shows one working. One anonymized FAB
  case study (what shipped, what the regulator asked, what changed) is worth 3 more
  essays. Only Gagan can supply this — it is the move that matters most.
- **Audience narrowness.** "Most helpful on the web" is the wrong target; the winnable
  game is "most helpful for the specific reader: a senior leader governing AI in a
  regulated institution." The books + podcast library may dilute that focus — worth
  deciding whether they serve that reader or signal general-interest drift.
- ~~KNOWN BUG — server/client lead mismatch~~ — **FIXED 2026-06-30** (`[codex]`). The
  `score_story` logic was identical in `render_radar.py` and `radar.js`; the real drift was date
  parsing. `render_radar.py`'s `age_in_days` only parsed ISO `%Y-%m-%d` and returned 999 for
  RFC2822 dates (`"Mon, 29 Jun 2026 ... GMT"`), while `radar.js`'s `Date()` parsed both — so the
  two computed different ages, different recency scores, and a different lead. `age_in_days` now
  parses ISO + ISO-datetime + RFC2822 (`email.utils.parsedate_to_datetime` fallback), tz-normalised
  to UTC, in lockstep with `ageInDays()` in `radar.js`. Server bake and client hydration now pick
  the same lead (verified: both lead with the Citigroup story).

## Reading experience (UI/UX + typography) — `[codex]` 2026-06-30

A UI/UX + font review concluded the type stack (Fraunces / Source Serif 4 / IBM Plex
Mono) is already excellent and is **not** the bottleneck — the bottleneck was the
reading *experience*. Shipped the high-impact "read more" changes:

**1. End-of-essay "next in the reading path" CTAs (all 6 essays).** Previously a reader
finished an essay and hit the subscribe form with nowhere to go. Every essay now ends
with a `.next-essay` CTA linking to the next essay in a defined reading order:
Gap → Levels of an AI-Pilled Organization → The Amnesia Tax → The Levels Revisited for
Agents → Why Trace-First Agent Systems Matter → Control Planes (→ back to writing index).
This carries the homepage "Start here" path all the way through the archive. `.next-essay`
CSS lives in `assets/site.css` (5 essays) and inline in `the-amnesia-tax.html` (it has
its own CSS, no site.css).

**2. Reading progress bar + auto table of contents (shared JS).** Added to
`assets/site.js` (loaded by the 5 `article.article` essays) and inline to
`the-amnesia-tax.html` (which does not load site.js, to avoid a duplicate Cloudflare
beacon). The script (gated on `main.article-site, main.body`) adds a thin fixed
`.read-progress` bar that tracks scroll through the article, and — for essays with 4+
direct-child `<h2>`s — auto-assigns ids and builds a non-sticky `.essay-toc`
("On this page") inserted after the article header. The Amnesia Tax has no
`article.article` wrapper so it gets the progress bar but not the TOC (it already has a
"60-second summary" panel). CSS for both is in `site.css` + inline in amnesia.
Cache versions bumped `editorial-20260616/14` → `editorial-20260630` on the 5 essays.

**3. Drop caps on the five essays that lacked them.** Only The Amnesia Tax had a drop
cap; the other five opened as text walls. Added via a single CSS rule
`article.article > p:first-of-type::first-letter` (Fraunces, ~3.2em) in `site.css` — the
narrative lead is the first direct-child `<p>` of `article.article` in all five, so one
rule covers them. Smaller on mobile.

**Font refinements shipped 2026-06-30 (`[codex]`):** softened the widest mono eyebrow
(The Amnesia Tax `.eyebrow` 0.22em → 0.16em) and extended Fraunces italic into the pull-quote
classes — `.callout-line` in `assets/site.css` (used by the gap, levels, and trace-first essays)
and `.killer` in The Amnesia Tax are now Fraunces italic. The broader mono-letter-spacing sweep
across the inner pages (signal/books/podcasts) was left alone — those are already 0.12–0.16em.

## IA simplification — 3 doors, 2 Situation Room views, homepage funnel — `[codex]` 2026-06-30

A strategic review concluded the site offered too many *choices at the top* (4 doors, one
opening to 4 sub-views, another to 2 — ~10 surfaces to choose among before reading a word).
Simplification reduces choices without deleting content. **Backup first:** tag + branch
`backup/pre-simplify-20260630` (at `2fa247c`) pushed to origin — recover with
`git reset --hard backup/pre-simplify-20260630`.

**Primary nav: 4 doors -> 3 (Writing · Signal · About).** Removed the Library door site-wide
and renamed the Situation Room door to **Signal** (the door lands on `signal.html`, so the
label now matches the page). The "Situation Room" name survives on the signal page masthead.

**Situation Room room-nav: 4 views -> 2 (Signal · The Feed).** Graph and Briefs dropped from
the room-nav. `graph.html` and `briefs/index.html` still exist and stay reachable via
contextual links — the graph via the signal page trace-grid + evidence footer, the briefs via
the writing index. Briefs pages lost their room-nav and are now parented under **Writing**
(Writing `aria-current`), since a monthly retrospective is editorial. `graph.html` keeps a
2-view room-nav (Signal · The Feed) for orientation back to the primary views.

**Library folded into Writing.** `podcasts.html` + `books.html` parented under Writing
(Writing `aria-current`); their Podcasts/Books sub-nav kept as a sub-section nav. The
`writing/index.html` Elsewhere section now carries Library + Monthly briefs cards.

**Homepage cut to a funnel.** Removed the 4-door `door-index` hub, the `build-proof-section`
(that content lives on `about.html`), and the `books-section` (library lives under Writing
now). The homepage live-links reduced to Signal + The Feed. Remaining flow: hero (thesis) ->
live signal (proof it's alive) -> Writing/Start here -> about teaser -> subscribe. The
homepage's job is now to route, not to reproduce the site.

**Reversibility.** Every page that lost a door is still reachable; no content was deleted. The
backup tag/branch preserves the pre-simplification state exactly.

## Motion pass (SpaceX-inspired, on-brand) — `[codex]` 2026-06-30

A motion pass taking inspiration from spacex.com — but filtered through the editorial
identity. The transferable SpaceX principles: **deliberate, weighty easing; one signature
scroll-driven moment; staggered entrances; restraint.** What was NOT copied: full scroll-
scrubbed video sequences (big build, spectacle-brand, would clash with a warm-paper reading
product). Shipped:

- **Hero entrance on load.** `.hero-content > *` fade-up via a `heroRise` keyframe, staggered
  (0.12s → 0.82s), 1.05s, easing `cubic-bezier(0.16,1,0.3,1)` (ease-out-expo-ish — the
  weighty SpaceX feel). Children arrive deliberately, not all at once. CSS in `site-home.css`.
- **Scroll-driven provenance machine.** The homepage Ledger→Graph→Gate→Brief row now
  activates its steps in sequence as you scroll through the `live-signal` section
  (`requestAnimationFrame`-throttled scroll listener in `site-home.js`, gated on the section).
  This is the SpaceX scroll-scrub principle applied to the site's own data-flow metaphor.
  Steps stay active once lit (build-up, not toggle).
- **Weighty reveal easing site-wide.** `.reveal` transitions upgraded from `.7s ease` to
  `.9s cubic-bezier(0.16,1,0.3,1)` in `assets/site.css` (essays) and inline in
  `the-amnesia-tax.html`. `.machine-step` got a `.55s` transition on background/color.
- **Reduced-motion respected everywhere** — hero animation disabled, machine steps all
  active immediately, reveal transitions none (existing `prefers-reduced-motion` handling
  preserved and extended).
- Cache versions bumped (`landing-v2-20260630c` / `editorial-20260630c`).

The motion is on entrances and structural elements only — never on body text — so
readability is unaffected.

**Signal page spine — scroll-scrubbed stroke-draw (added 2026-06-30).** The convergence
SVG on `signal.html` (`#spine`, drawn by `drawSpine()`) now draws itself as you scroll
into the `#map` evidence-map section. The amber convergence paths (`.spine-path`) and
signal dots (`.spine-dot`) are hidden via `stroke-dasharray`/`stroke-dashoffset` and
opacity, then a `requestAnimationFrame`-throttled scroll listener (`scrubSpine()`) ties
their draw/fade to scroll progress through `#map`, with a gentle per-path cascade
(`i*0.03` stagger). This is the SpaceX scroll-scrub technique applied to the signal
page's own convergence metaphor — the signature motion moment for the Situation Room.
`scrubSpine()` is called after `drawSpine(d)` in `render()`. Reduced-motion: paths fully
drawn, dots visible, no listener. The spine SVG is desktop-only (hidden on mobile,
replaced by `#mobileSpine`), so the scrub is desktop-only too.

**Voting connections (added 2026-07-01, `[codex]`).** After the spine draws in, 19 amber `.spine-pulse` circles travel along each convergence path signal-end -> attractor-end on a continuous staggered loop, visualising the signals 'voting' into the four directions. Uses CSS `offset-path` (set to each path's `d` in `drawSpine`) + `offset-distance` animation (`@keyframes spineVote` 0->100%). `scrubSpine` adds `#spine.voting` when the section is in view (progress >= 0.40), which runs the pulses + makes them visible. Reduced-motion: `.spine-pulse{display:none}`. Verified: offset-path works on SVG circles in Chromium; offset-distance animates; 19 pulses; 0 errors.

## Signal page cinematic lead band + hierarchy — `[codex]` 2026-06-30

The signal page read as "dull / hard to understand" — uniform warm paper, thin borders,
small mono labels, long text walls. Borrowed SpaceX's dramatic contrast without copying its
rocket-video surface: the page now opens with a **full-bleed dark lead band** (the masthead
+ factbar + newest-moves + method-disclosure wrapped in `<section class="signal-lead">`,
`background:#0a0d0e`, light ink, amber accents) — the same night palette as the homepage
hero. The factbar stats became large 1.7rem amber/white numbers (SpaceX-style stat
callouts) instead of small mono labels. The rest of the page (evidence map, decision briefs)
stays warm paper, so the dark lead creates strong cinematic contrast and separates the
executive summary from the body.

Hierarchy/clarity tweaks in `assets/signal-brief.css` (version bumped `20260629` ->
`20260630`):
- Each `.attractor` now has an amber top accent (`border-top:2px solid var(--signal)`).
- Act/Watch boxes flipped: **Act now** is the prominent amber-tinted box (amber top border
  + amber wash); **Watch next** is the de-emphasised white/muted box. Previously Watch was
  the amber one, which inverted the emphasis.
- `.summary-card` got an amber top accent + a hover lift/shadow.

The dark band is a CSS-only override scoped to `.signal-lead` — no change to the gate data
or the render() logic. Reduced-motion unaffected (this is colour/hierarchy, not motion).

## About page cinematic lead + hierarchy — `[codex]` 2026-06-30

The about page got the same treatment as the signal page: a **full-bleed dark lead band**
(`<section class="about-lead">`, `#0a0d0e`, light ink, amber accents) wrapping the masthead
+ dateline + the `.ledger-spine` thesis callout, so the page opens with cinematic contrast
instead of uniform warm paper. The ledger-spine became an amber-bordered callout on the
dark lead — the brand thesis now reads as the hero statement. The body sections stay warm
paper (the dark lead separates the "who" from the substance).

Hierarchy tweaks (inline CSS in `about.html`):
- `.sec-head .mono` section labels (01 · The story, …) are now amber and slightly larger —
  the five sections are scannable at a glance.
- `.lead-copy p:first-child::first-letter` — a Fraunces drop cap opens "The story" (reading
  pull, consistent with the essays).
- `.belief` cards + `.proof-band` got amber top accents + hover lift (matches the signal
  page summary cards).
- The masthead was moved out of `<main class="wrap">` into the full-bleed lead `<section>`;
  the five body sections remain inside `<main class="wrap">`. Markup re-verified (5 sections
  render, balanced tags).

CSS-only, scoped to `.about-lead` — no content change.

## Type quality pass — OpenType features + tracking — `[codex]` 2026-06-30

A type-craftsmanship pass to lift font/design quality (the thing that "attracts" readers).
The site had strong faces (Fraunces / Source Serif 4 / IBM Plex Mono) but used none of
their OpenType features. Enabled, per surface (homepage `site-home.css`, essays `site.css`,
`signal.html` / `about.html` / `the-amnesia-tax.html` inline):

- **Body / running prose:** `font-feature-settings: "kern" 1, "liga" 1, "calt" 1, "onum" 1`
  + `text-rendering: optimizeLegibility`. Oldstyle figures (`onum`) in prose = the editorial
  book look; kerning + standard + contextual ligatures on.
- **Display headings (h1/h2/h3):** `"kern" 1, "liga" 1, "calt" 1, "dlig" 1` — discretionary
  ligatures give the Fraunces display its premium editorial flair. Tightened tracking:
  h1 `-0.025em`, h2 `-0.015em`. Homepage hero h1 bumped to weight 700 for more presence.
- **Stat numbers (factbar `.val`, `.stat .n`, proof-band):** `"lnum" 1, "tnum" 1` — lining
  tabular figures so the big stats align and read as data, not prose.

Cache versions bumped (`landing-v2-20260630d` / `editorial-20260630d`). Verified in browser:
headings render `dlig/liga/calt/kern` with tightened tracking, body renders `onum`, factbar
renders `lnum/tnum`. CSS-only, no content change.

## Signal page: attract-to-dig-deeper (Tesla/SpaceX pattern) — `[codex]` 2026-06-30

The signal page was designed as a complete brief on one page — everything visible on one
scroll — which is the opposite of attracting readers to dig deeper. Leading sites (Tesla,
SpaceX, Apple) show a compelling summary and make the depth one obvious click away. Applied
that pattern. (Measured with a headless browser: the dark lead was a 1055px wall — factbar
193px + newest-moves 179px above the fold — and the 4 direction cards, the real dig-deeper
menu, were 366px below the fold.)

- **Leaned the dark lead to one focal point.** Headline + standfirst + one primary CTA
  (`.lead-cta`, "See the 4 directions ↓" → `#directions`, amber pill button above the fold).
  Demoted the factbar to a slim 4-stat row (dropped the redundant Window stat; smaller
  numbers). Converted newest-moves from a 3-item list (179px) to a one-liner. Moved the
  method-disclosure note out of the lead to just before the `#method` section. Result:
  lead 173px shorter; the 4 cards moved 174px closer to the fold; the primary CTA is
  visible above the fold.
- **Made the 4 direction cards the dig-deeper menu.** Each summary card now carries a
  `.strength-pill` (Strong = filled amber, Early = amber outline) and a prominent
  `.card-cta` "Open the decision brief →" that anchor-scrolls to that direction's full
  brief. The cards are the four obvious doors; the full act-now / watch-next /
  disconfirming / evidence briefs are one click below, not all visible on one scroll.
- (Held, pending confirmation: collapsing the full briefs fully behind expand/click
  rather than anchor-scroll — that changes first-view content.)

JS changes are in `render()` (factbar array, newestMoves one-liner, summary-card template).
CSS additions scoped inline in `signal.html`. No gate-data change. Re-verified: lead CTA
above fold, 4 cards with strength pills + CTAs, 0 JS errors.

## Radar page: lean masthead so the lead story leads — `[codex]` 2026-06-30

Same attract-to-dig-deeper principle applied to the radar (the raw feed). Measured: the
masthead had a 120px `.news-title` ("The raw feed") + a 30px deck, burying the actual lead
story 1040px below the fold — a giant label in front of the content. Leaned it in
`assets/radar.css`: `.news-title` 120px -> 52px (it's a feed label, not a hero);
`.news-deck` 30px -> 19px; masthead padding tightened. Bake version bumped r4 -> r5
(`render_radar.py`). Result: the lead story (the fresh move + its analysis) rose from
1040px to 857px — now above the fold — so the page leads with content, not a label. The
story cards remain the supporting depth below.

## Type system unified + mobile/accessibility pass — `[codex]` 2026-06-30

**One type system site-wide: Fraunces (display) + Spectral (body) + IBM Plex Mono (labels).**
Swapped body serif Source Serif 4 -> Spectral across 21 files (font URLs + --serif vars +
direct font-family). Converted the radar — the one outlier still on Inter (sans) — to the
same system: radar body Inter -> Spectral, radar labels Inter -> IBM Plex Mono, radar
headlines already Fraunces. Dropped the Inter font load from `automation/radar.template.html`,
added IBM Plex Mono. No page now uses a fourth face. Spectral carries the oldstyle/lining
figures from the earlier OpenType pass. Cache versions `...20260630e`; radar bake r8.

**Mobile audit (375px) + fixes:** `books.html` had 26px horizontal overflow (grid items
default `min-width:auto` let a nowrap author force the track wide) -> `.book` `min-width:0`
+ `overflow:hidden`, overflow now 0. Signal `.strength-pill` 8.96px -> .68rem on mobile.
Remaining ~9px uppercase mono labels are intentional ledger-label density (not body text).

**Accessibility:** visible `:focus-visible` outline (2px amber) for keyboard users added to
`site-home.css`, `site.css`, `signal-brief.css`, `radar.css` + inline flagship pages.
`signal-brief.css` bumped to v20260630b.

**Remaining (not yet done):** normalize the page-opener *structure* (kicker -> h1 ->
standfirst -> dateline) to one consistent module across pages; apply the attract-to-dig-deeper
treatment to the podcasts page (the remaining long wall); replace the signal page's
"Loading..." text with a skeleton.

## Podcasts page: attract-to-dig-deeper (claims ledger leads) — `[codex]` 2026-06-30

The podcasts page was the remaining long wall (~10,000px on mobile). Measured: the claims
ledger — the page's unique value (scored claims) — was buried at 1378px (desktop) / 2224px
(mobile) below the JS-rendered "latest episodes" block. Applied the same attract pattern:
moved `#claims` ABOVE `#latest` so the scored claims lead, and added a masthead CTA
`.lead-cta` "See the scored claims ↓" → `#claims` (light amber pill, warm-paper variant).
Result: claims rose from 1378 → 625px; the first claim is now at the fold (865px vs 1617).
The latest-episodes raw feed moved below the claims as supporting depth. Opener typography
was already unified by the type-system pass (Fraunces/Spectral/IBM Plex Mono); the remaining
opener *structure* differences (radar centered news-masthead, essay article-header) are
intentional per content type, so no shared opener module was forced.

## Signal: "why this is signal, not noise" made tangible — `[codex]` 2026-06-30

First concrete "experience moat" move from the competitive review (the gate is the UX hero,
not the news — a trust signal no aggregator offers). Each of the 4 direction summary cards now
shows the **structural tests it passed** as chips (Mandate / Money / Machinery / Corroboration /
Criterion-shift), with Corroboration rendered in a distinct teal (it is the independent-actor
multiplier). The `#directions` section intro now states "each direction is signal, not noise
because its moves tripped a structural test" and links to `#method` for the full gate logic.

Implementation: the chips come from the existing `attractors[].tests` field in
`data/signal-gate.json` (already populated by `build_signal_gate.py`), rendered in the
`render()` summary-card template in `signal.html` (`.test-chips` / `.test-chip` /
`.test-chip.corrob`). Styles in `assets/signal-brief.css` (bumped to v20260630d). No data
change; the gate's tests were already computed, just not shown on the cards.

Verified: 15 chips across 4 cards, intro legend + method link present, Corroboration teal,
0 JS errors.

**"What changed since last gate" delta — BUILT 2026-06-30 (`[codex]`).** `build_signal_gate.py`
now persists a per-date snapshot to `data/signal-history.jsonl` (one line/date; same-day reruns
overwrite) and computes a `delta` in `signal-gate.json` vs the previous snapshot: `newSignals`,
`removedSignals`, and per-attractor `changes` (strength Early<->Strong, signal counts). If no
previous, `delta.baseline=true`. `signal.html` renders it in a `#gateDelta` block in the lead
("Since <prev>: +N new signals, strength X->Y..."; baseline today). Diff logic tested with a
synthetic previous snapshot. `daily-intelligence.yml` now commits `data/signal-history.jsonl`.
Baseline established 2026-06-30 (28 stimuli, matching cloud); the real diff appears from
tomorrow's run. This is the second experience moat — no aggregator shows a thesis evolving.

**Board-meeting PDF + role-filtered views — BUILT 2026-07-01 (`[codex]`).** Two more moat
moves, both live:
- **Board-meeting PDF:** a "Board brief · Print / PDF" button in the signal lead calls
  `window.print()`. A dedicated `@media print` block turns the dark lead light and hides all
  chrome (nav, room-nav, brief-nav, lead CTA, newest-moves, gate-delta, role-view, summary
  cards, the spine, method, rejected-items, closed evidence drawers). What prints is a
  decision-ready brief: headline + gate stats + the four direction briefs (thesis, decision,
  act-now, watch-next, disconfirm), attractors kept together. Verified in emulated print
  media: 4 attractors visible, lead #fff/#111, all chrome hidden.
- **Role-filtered views:** a role selector (All / CRO / CTO / COO) in the #directions intro.
  Each direction maps to a seat — CRO=governance-as-infrastructure, CTO=governed-autonomy,
  COO=gulf-industrialising+labor-structural (mapping is by direction id in JS, no data
  tagging). Selecting a role adds `body.role-*` and CSS dims non-relevant cards + attractor
  sections to opacity ~.34, keeping the relevant one(s) full. Verified: All=1.0; CRO keeps
  governance; CTO keeps governed-autonomy; COO keeps gulf+labor; back-to-All restores. Role
  selector hidden in print. `data-dir` added to summary cards + attractor sections.

All three experience moats (test chips, delta, board PDF, role views) are now live on the
signal page.

## Graph page: flowing-edge animation — `[codex]` 2026-07-01

`graph.html` edges now flow: `.link{stroke-dasharray:5 9;stroke-linecap:round}` + a
`requestAnimationFrame` loop decrements a shared `stroke-dashoffset` each frame and applies it
to all `#graph .link`. The loop queries current `.link` every frame, so the flow SURVIVES
`render()` recreating the edges on click/theme/drag (shared offset counter keeps advancing —
no restart jitter). Reduced-motion skips the loop. Verified: 24 edges, dasharray 5/9,
offset animating across a re-render, 0 errors.

## Publishing a new essay (article) — checklist — `[codex]` 2026-07-01

To add a new essay so it is consistent with the six existing ones (and share-ready, indexed,
and in the reading path):

1. **Create `writing/<slug>.html`.** Copy `writing/the-amnesia-tax.html` as the structural
   reference (it is the most complete): Fraunces / Spectral / IBM Plex Mono, the inline
   `:root` + body CSS, the `<article class="article">` wrapper, the `article-header`
   (eyebrow "The Philosophical Ledger · <category> · <month year>", h1, dek, optional byline),
   the body, and the end-of-essay `.next-essay` CTA + reader-response/subscribe asides + footer.
   The lead paragraph gets the drop cap automatically via `article.article > p:first-of-type::first-letter`
   (in `site.css`). Load `../assets/site.css` + `../assets/site.js` + `../assets/site-config.js`.
2. **Head metadata (copy from an existing essay):** `<title>`, `meta description`,
   `og:title/og:description/og:type=article/og:url/og:image(1200x630)/og:image:width/height`,
   `twitter:card=summary_large_image`, `<link rel="canonical">`, `<link rel="icon" href="../favicon.svg">`,
   `<link rel="alternate" type="application/rss+xml" href="https://gagansachdeva.com/feed.xml">`,
   the Article JSON-LD (headline/description/url/image/author/publisher/datePublished/dateModified/
   mainEntityOfPage), and the Cloudflare beacon before `</head>`.
3. **Primary nav:** 4-door nav is now 3 doors — Writing · Signal · About (Writing `aria-current`).
4. **Reading path:** add the essay to `writing/index.html` (the `.essay` list, newest first).
   If it joins the Start here path, update `.sh-path`. Update the *previous* essay's `.next-essay`
   CTA to point to the new essay (the chain: gap -> levels -> amnesia-tax -> levels-revisited ->
   trace-first -> control-planes -> index). The new essay's own next-essay CTA points onward.
5. **Sitemap:** add a `<url><loc>https://gagansachdeva.com/writing/<slug>.html</loc></url>` to
   `sitemap.xml`.
6. **Type system + shell:** use the shared Fraunces/Spectral/IBM Plex Mono system, the warm-paper
   ledger look, the OpenType feature flags (`font-feature-settings` on body/headings), the
   `:focus-visible` outline (already in `site.css`). Do not introduce a fourth font.
7. **Commit:** prefix `[claude]` or `[codex]`; commit + push to `origin/main`. GitHub Pages deploys
   automatically. Do NOT touch `radar.html`/`feed.xml` (CI owns the radar bake).

## "My Books" tab + premium book showcase — `[codex]` 2026-07-02

The Agentic AI guide (`/agentic-ai/`) is now presented as a **book**, not an article, via a new
dedicated section.

- **New page `my-books.html`** — a premium book-showcase page: a dark hero with the book cover
  at ~300px wrapped in a halo (amber-glow box-shadow), a "Book · Free · 7 parts" tag, the title
  in Fraunces ~43px, an italic Spectral subtitle, and Read-online / EPUB / PDF buttons; below, an
  "About this book" blurb + a seven-parts list. ItemList/Book JSON-LD. This is the page that reads
  as a book.
- **IA: a 4th nav door — "My Books"** — added to the primary nav on every page. Nav is now
  **Writing · Signal · My Books · About**. (This reverses the earlier 3-door simplification for
  the author's-books surface; it's intentional — the user wanted a Books tab. The reading library
  `books.html`/podcasts remains folded under Writing; "My Books" is the author's own books/guides,
  a different thing.) The nav addition was inserted after the Signal link in each page's nav
  (li-format on absolute-URL pages, plain `<a>` on relative-URL pages + the radar template).
- **Homepage + writing-index guide cards** upgraded to premium book cards: a 64px cover thumbnail
  + "Book" tag + title + amber halo, so they read as a book, not a normal article/feature card.
- **`/agentic-ai/` itself is unchanged** — the guide, the EPUB (images fixed), the PDF, and the
  full-book read all stay. `my-books.html` links into it (Read online → `agentic-ai/`). The guide
  landing + full book still have the sticky "← The Philosophical Ledger" top bar back to the site.
- **Sitemap:** +my-books.html.

Verified: 4-door nav renders on homepage/writing-index/signal; book cover (64px in cards, 300px
on my-books) + halo present; no existing links broken (guide/EPUB/PDF/essays intact). Build is
deterministic; the radar nav change is in `automation/radar.template.html` (rebaked into
`radar.html`).

**To add another book later:** add an entry block to `my-books.html` (cover + tag + title + sub +
read/epub/pdf buttons), mirroring the Agentic AI block; update the ItemList JSON-LD; add the book
files under a new `agentic-ai/`-style folder if it has its own assets.

## Conventions
- Commit prefix to show authorship: `[claude]`, `[codex]`; the cloud bot uses `[cloud]`.
- Canonical deploy clone is local-only; everything syncs through `origin/main`. Always commit + push.

## Signal page authored-editorial redesign — `[codex]` 2026-07-05

Message for Claude: the Signal page was deliberately moved away from a generated-dashboard look
toward a bylined editorial brief. Preserve this direction in future changes.

- The machine layer is still fully inspectable, but it is progressively disclosed. The evidence
  convergence map, structural tests, source traces, method, and rejected items remain available.
- The visible hierarchy is now author → argument → action → evidence: a Gagan byline, honest
  freshness labels, a single-column direction index, narrative “What changed” prose, “Gagan's
  read,” numbered actions, watch items, and “What would change my mind.”
- Avoid restoring stacked navigation, card grids, pills, badge walls, or structural-test chips above
  the fold. Those patterns made the page feel machine-generated and gave every fact equal weight.
- Keep the three freshness concepts distinct: pipeline check date, evidence-reviewed-through date,
  and latest accepted signal date. A fresh build must not imply fresh evidence.
- `data/attractors.json` remains the editorial source of truth; this redesign changes presentation,
  not gate accounting or the automation pipeline.

## Homepage latest-writing freshness — `[codex]` 2026-07-11

Message for Claude: the homepage "latest field note" card must never be manually frozen on an
older essay again. The first live issue was that `index.html` still promoted "The Amnesia Tax"
as `Latest · June 2026` while `writing/index.html` already had the July 2026 essay "When
Intelligence Gets Arms and Legs" as the newest entry. When this fix was deployed on current
main, the true newest essay was "The Capability–Value Gap"; keep the manifest aligned with
whatever is first in the writing index.

- `data/writing.json` is now the small manifest that feeds the homepage latest-writing card.
- `index.html` keeps a correct fallback, but `assets/site-home.js` hydrates the card from the
  manifest with `cache: "no-store"` and labels old content honestly as "Latest in the archive"
  instead of implying a fresh issue.
- The homepage card was redesigned into a premium editorial module: visible freshness chip,
  archive-sync note, darker more deliberate surface, and a "Newest essay" read-time rail.
- When publishing any new essay, update `writing/index.html`, `sitemap.xml`, and
  `data/writing.json` in the same commit. Do not hardcode "Latest" directly in the homepage.
- `CLAUDE.md` repeats this rule for Claude-first sessions; keep it short and pointed to this
  handoff.

## Writing index reader-map redesign — `[codex]` 2026-07-12

Message for Claude: `writing/index.html` is no longer a flat archive with an oversized "Start
here" slab. Preserve the reader-first hierarchy:

- Lead with a dark premium `.latest-essay` card for the newest argument.
- Keep the three-piece `.start-here` path beside it as the onboarding route, not the dominant
  object on the page.
- Put the full archive below as card-like `.essay` rows with date/read-time metadata and clear
  promises for each piece.
- The goal is decision support: a reader should immediately know whether to read the newest
  essay, take the foundational sequence, or scan the archive by theme.

## Homepage live-signal provenance — `[codex]` 2026-07-12

Message for Claude: the "Today in the Situation Room" homepage section must read as a real
data product, not a decorative claim. It is a static page shell hydrated by `assets/site-home.js`
from `data/signal-gate.json` and `data/knowledge-graph.json` using `cache: "no-store"`.

- Keep the freshness pill, rebuilt date, source-file line, and `.live-integrity` explanation.
- `site-home.js` computes whether the data is fresh today, recent, or stale. If generated data is
  older than three days, the section gets `.is-stale` and should stop implying current evidence.
- The section should always distinguish page deploy freshness from evidence freshness. A fresh
  GitHub Pages deploy does not mean fresh signal data.
- Daily evolution comes from the 06:00 GST `daily-intelligence.yml` workflow: generator → graph →
  gate → committed JSON → homepage hydration. Manual edits must preserve that contract.

## Open items
1. ~~Optional dedicated `/about.html`~~ — **DONE 2026-06-30** (`[codex]`). See the
   "About page + share-ready essays" section above.
2. ~~Rotate the Parallel API key~~ — **set 2026-06-30** (`[codex]`); the daily cloud
   generation is verified working end-to-end (a manual `workflow_dispatch` run produced
   `212a74f` + a rebake, and the live radar now leads with a fresh banking story). CAUTION:
   the key value was pasted into a chat transcript to set it, so it must be rotated AGAIN
   through a non-chat channel (GitHub Settings → Secrets, or `gh secret set` run in your own
   terminal) once you're satisfied the pipeline is healthy. Do not paste key material into chat.

## Email capture fix — `[claude]` 2026-07-04
The Buttondown username is **`gagan`** (account created 2026-07-04), NOT `gaganai` — the old
value 404'd and every subscribe form was silently losing emails. Fixed in site-config.js,
site.js fallback, the book gate, levels-diagnostic.js, writing/index.html. Embed posts:
`tags` do NOT survive, `metadata__source` DOES — segment signups by metadata source
(`agentic-ai-book`, `homepage`, `article`, etc.). API key lives locally at `~/.buttondown_key`
(never commit). Any new subscribe form must post to `embed-subscribe/gagan`.

## Situation Room fast lane — `[claude]` 2026-07-05
Four additions for casual readers (keep): (1) `#in30` "In 30 seconds" strip on signal.html —
one line per direction from the gate's `decision` field, rendered by a standalone script near
</body> (fails silently); (2) a `.room-strap` one-liner under the room-nav on all four views
(signal/feed/graph/briefs — radar's is inlined in radar.template.html, briefs' in the generator);
(3) `build_signal_gate.py` window now sorts firstSeen CHRONOLOGICALLY (was word-sorted: "July"<"June");
(4) a weekly-email form in the strip (`metadata__source=signal-weekly`, posts to embed-subscribe/gagan).
Also fixed signal.html's Cloudflare beacon tag (src attribute was unterminated — beacon never loaded).

## Feed made visual — `[claude]` 2026-07-05
Two additions to the Feed, in LOCKSTEP across render_radar.py + radar.template.html + assets/radar.js
(keep all three in sync): (1) a "Today at a glance" horizontal five-layer strip ({{GLANCE}} placeholder,
render_glance() in the baker; L1→L5 cells, hot layer amber, quiet dashed; reuses {{CAKE_NOTE}} as its
one-line read); (2) a `.layer-pill` (e.g. "L5 · Agents") as the first topline item on the lead story and
every story card, emitted by layer_pill()/layerPill() in both renderers. All CSS inlined in the template
(survives radar.css reverts). Bake version bumped to -r11.

## Feed UX pass 2 — `[claude]` 2026-07-07
(1) Glance strip is now a FILTER: cells carry data-glance + role=button; story cards carry
data-layer (lockstep: story_card()/storyCard in both renderers); an inline template script
(before </main>) toggles cards, hides group heads, sets aria-pressed, shows #glanceHint and
an honest #glanceEmpty. Works on baked archives too. (2) Masthead compressed via inlined
.radar-page overrides (title clamp 40px, tight paddings) — the feed is a daily tool, not a
cover; lead story should touch the first desktop viewport. (3) Sidebar cake-note hidden
(.sidebar-cake .cake-note{display:none}) — the glance note is the single source of the day's
read. (4) Pluralization fixed in BOTH front-page-note builders ("1 fresh story"). (5) Any
change to radar.js/radar.css MUST bump the {{VERSION}} suffix in render_radar.py (now -r12)
or browsers serve stale assets.

## Distribution layer: OG cards, Writing feed, related reading — `[claude]` 2026-07-12

Message for Codex: three systems, all driven by `data/writing.json` (your manifest is now
the single source for homepage card + related blocks + essays feed + share cards).

1. **Per-essay OG cards.** `automation/build_og_cards.py` renders a 1200×630 dark-editorial
   card per manifest item (Fraunces title, amber category chip, byline row) via headless
   Chrome into `assets/og/<slug>.png`. Idempotent — skips existing; `--force` rebuilds.
   Every essay's `og:image`/`twitter:image`/JSON-LD image now points at its own card; the
   generic `og-card-20260611.jpg` remains for non-essay pages only.
2. **Writing RSS.** `automation/build_writing_feed.py` bakes `writing-feed.xml` from the
   manifest (RFC-822 pubDates from `date`). `feed.xml` stays radar-only. A second
   `<link rel="alternate">` was added to all 8 essays + index.html + writing/index.html.
3. **Related reading.** `assets/related-essays.js` + a `[data-related-essays]` slot before
   `</main>` on all 8 essays renders 3 "Keep reading" cards (same-category first, then
   recency; fails silently; styles are namespaced and inline so bespoke pages work).

**Publish ritual is now:** essay file → `writing/index.html` → `sitemap.xml` →
`data/writing.json` → run `build_og_cards.py` + `build_writing_feed.py` → new essay gets a
`[data-related-essays]` slot + related-essays.js script before `</main>`, and its metas point
at `assets/og/<slug>.png`.

## Site search + speed pass — `[claude]` 2026-07-12

Message for Codex: the site now has one search box over everything we've published.

1. **Ask the Ledger (`/search.html`).** Static client-side search, ledger-styled (Spectral/
   Fraunces/Plex Mono, warm paper). Corpus is baked by `automation/build_search_index.py`
   into `data/search-index.json` (~100 KB): 8 essays (manifest + body text), the book's
   9 parts + 42 chapters (deep links to `#sN-chM`), 71 glossary terms, and the current
   Signal directions from `data/attractors.json`. Scoring is per-token AND (title 4 /
   snippet 2 / body 1), top 30, kind chips filter (All/Essays/Book chapters/Glossary/
   Signal), `?q=` prefills. Entry shape: `{t,h,k,s,x}`, kinds essay|part|chapter|term|direction.
   **Rerun the baker whenever an essay, the book, the glossary, or attractors change** —
   it's now step 3 of the publish ritual in CLAUDE.md. A search form in the Writing
   masthead GETs to `../search.html`; `/search.html` is in sitemap.xml.
2. **Speed pass (cheap wins only).** The two 64px book-cover slots (homepage + writing
   index) now load `assets/book-cover-thumb.png` (24 KB, 160×256, `loading="lazy"
   decoding="async"` + width/height to stop layout shift) instead of the 200 KB
   1600×2560 original — showcase pages (my-books, agentic-ai) intentionally keep the
   full cover. `site-home.js` is now `defer`. Audited the rest: hero video is 3.4 MB but
   already `preload="metadata"` + 36 KB webp poster; CSS/JS/data files are all ≤44 KB.
   **Left on the table (needs ffmpeg, not installed):** re-encoding hero-loop-540.mp4
   (~3.4 MB → ~1 MB at crf 28-30) is the single biggest remaining win.

## Signal page simplified — `[claude]` 2026-07-13

Message for Codex: Gagan found signal.html "complex and confusing" and asked for
simplification + visuals, so the page now tells one story once instead of four times.
Structure is now three layers:

1. **Lead** — headline, plain meta (Updated / Evidence through / Newest evidence), and a
   new always-visible **funnel visual** (`#funnel`, built in render()): verified moves in
   → THE GATE (five tests, rejected count struck through) → signals kept → directions,
   with a one-sentence plain-English caption. This replaced the factbar and the
   gate-delta box. Stacks vertically under 680px.
2. **The 30-second read** (`#in30`) — now the ONLY index (relabelled "The whole page in
   30 seconds — four conclusions"). The summary-card grid, section-intro, and the
   CRO/CTO/COO role filter are GONE (that was the main redundancy: headline → in30 →
   cards → full brief all said the same four things).
3. **The four directions, in full** — each head now opens with an **evidence meter**
   (8 dots filled per verified move + a Strong/Early pill). The evidence drawer kept the
   source list + test chips but lost the six-box Ledger/Graph/Gate/… trace grid. The
   `#unresolved` note moved to the end of the brief, reworded plainly.

Also removed: the collapsed evidence-map spine SVG + drawSpine/scrubSpine scroll-scrub
code and the spine-pulse CSS (the funnel does that explanatory job now, always visible).
Your decision-brief data contract is untouched — same signal-gate.json fields, same
invariant (mapped 19 + unresolved 8 + noise 7 == 34 stimuli renders in #evidence), method
drawer + noise drawer + print stylesheet intact (print selector list updated). Page went
42KB → 32KB, 242 lines deleted. If you want the role filter or the map back, they're in
git at aa0e602^ — but consider Gagan's feedback first.

## Homepage Situation Room: motion pass — `[claude]` 2026-07-13

Gagan asked for the section to feel richer/animated. All motion is scoped under
`html.js-anim`, which site-home.js adds ONLY when JS runs and prefers-reduced-motion is
off — no JS or reduced motion renders the page fully static (nothing hides).

1. `[data-reveal]` on the section's five blocks → IntersectionObserver fades/raises them
   with a 90ms stagger. A 1.5s polling fallback reveals anything stuck in-viewport if the
   observer is throttled.
2. Machine stats count up 0→N (rAF, ~950ms) the first time the machine is on screen; a
   setTimeout writes the final value regardless, so "— stimuli" can never stick.
3. Your scroll-lighting kept, one fix: threshold is now `(i/n)*0.82` so step 04 Brief
   lights while the section is still in view (it used to stay pale — see Gagan's Safari
   screenshot from tonight).
4. Copper rail on .live-conclusion draws downward (scaleY) on reveal; breathing dot on
   the resolved freshness pill; hover lift on machine steps; arrow nudge on live-links.
5. Asset version → `landing-v3-20260713` (remember: bump on every site-home.css/js edit).

Verify trick worth keeping: the Claude Browser pane freezes rAF/IO/transitions (hidden
surface), so animated states were verified with headless Chrome
`--virtual-time-budget=9000` on a hero-stripped staging copy — end state screenshot
showed all four steps dark, counts landed, rail drawn.

## Search depth + self-updating index — `[claude]` 2026-07-16

Ask the Ledger now covers the full depth of the site: 179 entries = 8 essays (3,200-char
bodies), the book's 9 parts + 42 chapters (2,000-char bodies) + 71 glossary terms, the
4 Signal directions, **all 36 verified moves from data/signal-ledger.jsonl** (kind
`move`, snippet = firstSeen + whyItMatters, href = the source URL), the monthly briefs,
and 8 key site pages. Chips regrouped: All / Essays / Book / Glossary / Situation Room
(direction+move+brief via a GROUPS map). The searchable-count line is dynamic now.

**The index maintains itself**: daily-intelligence.yml runs build_search_index.py after
the noise gate and commits data/search-index.json — every new verified move becomes
searchable the same morning. Manual rebake is only needed when publishing an essay or
editing the book (already in the CLAUDE.md ritual).

## Coverage widened: bank peers + new labs — `[claude]` 2026-07-16

Gagan asked whether the radar covers the major labs, clouds, and FAB's peers. It did for
the core set; the net is now wider:

- **ENTITY_LEXICON +19** (build_knowledge_graph.py): GCC banks QNB / ADCB / ADIB /
  Dubai Islamic Bank / NBK / Bank Muscat / Riyad Bank; global AI-banking benchmarks
  DBS / Bank of America / Wells Fargo / UBS / BNP Paribas / Santander; labs DeepSeek /
  Cohere + Alibaba / Qwen; GCC adjacents Presight / ADIA / QIA.
- **Collector queries** (run_daily.py): one new GCC bank-peers query, one new global
  bank-benchmarks query, and the lab-launch query now includes DeepSeek + Qwen.
- Graph/gate/search rebuilt locally and came out byte-identical (idempotent) — the new
  names light up in the graph, the gate's corroboration test, and site search as soon as
  tomorrow's collection mentions them. No downstream contract changed.

## The Feed was rendering empty — root causes and fixes — `[claude]` 2026-07-27

Gagan reported not seeing frontier/upcoming-model news. Investigation found the Feed was
serving **zero story cards** ("No current stories", all five layers quiet). Three
compounding defects, all now fixed:

1. **Publisher-blind diversity cap (the big one).** `merge_signal_payload.allowed_from_domain`
   limits fresh stories to 1 per domain — correct intent, but every Google News RSS link is
   `news.google.com`, so the entire RSS lane collapsed to ONE story per day. The real
   publisher is in the feed item's `<source url="...">`; it is now threaded
   FeedResult.source_domain -> SourceItem.source_domain -> signal["source_domain"], and
   `domain_key()` prefers it. Bonus: cards now credit the real outlet (openai.com,
   techcrunch.com) instead of the aggregator.
2. **24h RSS window starved the edition.** Google News returns relevant-but-older coverage;
   175 fetched items yielded ~1 within 24h. `main()` now tries 24h, then 72h, then 168h,
   stopping at the first tier with >= MIN_EDITION_ITEMS (6), and logs the tier used. The
   tight window is still preferred — it only widens to avoid an empty edition.
3. **Model news was labelled L5 Agents.** LAYER_RE[4] matched a bare `models?` (so
   "AI model risk" governance stories became L4) while the `agents?` check ran FIRST (so
   "Opus 4.8 for coding and agentic work" became L5). L4 now uses strong frontier markers
   (model launch/release/upgrade, open weights, GPT/Gemini/Claude/Llama/DeepSeek/Qwen/Grok,
   training runs, benchmarks) and is evaluated BEFORE the agent fallback. **Lockstep
   updated in all three sites**: render_radar.py, assets/radar.js, build_knowledge_graph.py.
   VERSION bumped to -r13.

Also added a **Frontier Models desk** (run_daily.py `signal_desk_from_signal`, checked after
governance/banking so "model risk" stories stay in Governance, plus DESK_PRIORITY 5) and an
upcoming-model-roadmap collector query.

Result: today's edition went from 1 fresh / 0 rendered to **12 fresh / 8 rendered**, with
L3 and L4 populated and +10 ledger moves.

**Still open (needs Gagan):** Parallel search has been failing in CI with "Connection error"
(parallel_batches: 0) for weeks, so the premium verified-source lane is dead and everything
above rides on the Google News RSS fallback. api.parallel.ai is reachable and both SDK
versions authenticate fine from a laptop, so this looks like a credential/egress issue in
Actions — the PARALLEL_API_KEY secret dates from 2026-06-29 and rotation was recommended
back then. Re-running `gh secret set PARALLEL_API_KEY` with a current key is the next step.
Note `history/covered_urls.json` is untracked, so CI dedupes only within a run.

## The forward layer: trajectory + what's forming — `[claude]` 2026-07-29

Gagan asked to stay on Google News but extract deeper meaning so the Signal anticipates
rather than reports. New `automation/build_momentum.py` -> `data/momentum.json`, read by
signal.html. Nothing about your gate or attractor contracts changed.

1. **Trajectory** per established direction: trailing 14d vs prior 14d, plus DISTINCT
   actors and regions. Measured against the LEDGER via `DIRECTION_MATCH` (theme set +
   keyword regex per attractor id), deliberately NOT against each attractor's own signal
   list — those are owned editorially by title fragment, so they're frozen in June and
   every direction read "dormant". Renders as a trend pill next to the evidence meter.
2. **Forming** — clusters among gate-passed-but-unbound signals (`gate.other`), the pool
   the next direction comes from. `close to binding` requires >=3 signals from >=3
   independent actors; `building` >=2 from >=2; anything thinner is `early` and hidden.
   Each card states its evidence count, the gap to binding, and what usually follows.
3. **Precedence** — a labelled heuristic mapping the dominant structural test to what it
   typically precedes (Money -> capacity/hiring/consolidation; Mandate -> procurement
   gates and audit demands; Criterion-shift -> RFP language). It encodes the ordering
   Gagan already argues editorially; it is presented as a heuristic, not a forecast.

Design rule I kept: every claim carries its raw counts, so a thin read stays visibly thin
(61 ledger records is small — the UI must not imply more confidence than that supports).
The section is standalone and fail-silent; if momentum.json is missing the page is
unchanged. Wired into daily-intelligence.yml (after the gate) and committed with the
other data, so it refreshes itself.

**Editorial hook for you:** clusters marked `close to binding` are the queue for the next
hand-authored direction in attractors.json. Today: compute capacity committed ahead of
demand (3/6), capital forming around agent infrastructure (7/4), agents entering core
workflow (3/4).


## Living intelligence homepage — `[codex]` 2026-09-06

User requested a cleaner cinematic homepage with meaningful 3D motion, optional music,
and deployment on the existing domain. The homepage now opens with “Making intelligence
useful,” followed by Signal → Writing → Builds → Book → About → Subscribe.

- `assets/intelligence-field.js` is the dependency-free, perspective-projected 3D point
  field: deterministic toroidal geometry resolves toward a connected disc on scroll.
  Canvas rendering pauses offscreen or in a hidden tab. Reduced-motion starts static;
  the visible motion button lets visitors choose. No text is hidden behind animations.
- The same file contains an original procedural ambient score, synthesized with Web Audio.
  It creates no audio context until the Sound button is pressed, fades in/out, and stops
  when the page is hidden. No licensed recording or external audio download is used.
- `site-home.css` is homepage-only. Existing essay styles, routes, feeds, and data pipelines
  are preserved. Mobile artwork is in normal document flow to protect larger text.
- `site-home.js` still hydrates the latest essay from `data/writing.json` and the signal
  from gate + graph JSON, with bounded requests and readable failure states.
- “Latest” replaces “Today’s”; editions older than three days stay visibly dated and marked
  older. Technical provenance remains available in the “Behind the signal” disclosure.
- The newsletter retains the Buttondown `gagan` endpoint and homepage source metadata,
  and now also works without JavaScript.
- Rollback reference: `backup/pre-living-intelligence-20260906`. GitHub Pages remains the
  deployment host; this redesign does not change DNS or move the site to another provider.

Validation: JS syntax; static HTML nesting/IDs/local asset and route checks; isolated
JS execution covering real data hydration, offline fallback, projected coordinates,
reduced motion, pause/resume, and explicit audio start/stop. No browser QA in this pass.

## Inner-page experience — `[codex]` 2026-09-06

The user approved extending the homepage identity through the rest of the site.
`assets/ledger-experience.css` now supplies a namespaced, responsive five-link header
(Writing / Signal / Builds / My Books / About), consistent focus treatment, and scoped
refinements for Writing, Signal, About, book, build, search, and supporting pages.
Essay bodies and diagrams retain their individual reading layouts. The homepage's
motion/audio files are unchanged. Page identity uses `data-ledger-page`; keep the
writing archive (`writing`) separate from individual essays (`essay`).

Signal has a short editorial headline and an expandable explanation of its funnel;
live counts still come from data. Failed data loading now exits the loading state.
Search chips are real buttons so keyboard users can operate existing filters.
The full book's broken favicon path is fixed. Build and brief font loads use Spectral.

The feed header is changed in `automation/radar.template.html`, not the baked files.
Monthly-brief navigation is updated both in current pages and in its generator so
future editions keep the same navigation. Archived radar snapshots are not edited.

Validation: 645 local link/asset references across 34 pages have no missing files;
15 inline scripts pass syntax checks; mobile inspection covered the major routes,
book/download entry points, build detail, essays and supporting pages, with no page
width overflow. Desktop checks covered the six main page types. Search query + filter
and live signal disclosure/counts were exercised in browser. Backup tag:
`backup/pre-inner-experience-20260906`.
