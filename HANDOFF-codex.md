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

**Next moat moves considered but not built (need data/history):** a "what changed since last
gate" delta requires storing gate history (the gate is regenerated each run with no snapshot
kept) — would need `build_signal_gate.py` to persist a history file. Board-meeting PDF export
and role-filtered (CRO/CTO/COO) views are buildable on the current data.

## Conventions
- Commit prefix to show authorship: `[claude]`, `[codex]`; the cloud bot uses `[cloud]`.
- Canonical deploy clone is local-only; everything syncs through `origin/main`. Always commit + push.

## Open items
1. ~~Optional dedicated `/about.html`~~ — **DONE 2026-06-30** (`[codex]`). See the
   "About page + share-ready essays" section above.
2. ~~Rotate the Parallel API key~~ — **set 2026-06-30** (`[codex]`); the daily cloud
   generation is verified working end-to-end (a manual `workflow_dispatch` run produced
   `212a74f` + a rebake, and the live radar now leads with a fresh banking story). CAUTION:
   the key value was pasted into a chat transcript to set it, so it must be rotated AGAIN
   through a non-chat channel (GitHub Settings → Secrets, or `gh secret set` run in your own
   terminal) once you're satisfied the pipeline is healthy. Do not paste key material into chat.
