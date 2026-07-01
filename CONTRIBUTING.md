# Contributing to The Philosophical Ledger

This repo is worked on by Gagan Sachdeva plus AI collaborators (Claude and Codex), and is
open to human contributors who want to improve the essays, the Situation Room, or the
intelligence engine. It is a **static site with a stdlib-only Python pipeline** — no framework,
no build step, no Node tooling. Keep it that way.

## 0. Read this first

**Before changing anything, read [`HANDOFF-codex.md`](./HANDOFF-codex.md).** It is the operating
manual: the design system, the information-architecture decisions, the pipeline rules, every
feature and "why" behind it, the open items, and the step-by-step **"Publishing a new essay"
checklist**. The `README.md` is the public summary; the HANDOFF is the source of truth for how
to work here without breaking invariants.

## 1. The non-negotiables

These are invariants — changing them breaks the site's coherence or the pipeline's correctness.

- **No fourth font.** The type system is **Fraunces** (display) · **Spectral** (body) ·
  **IBM Plex Mono** (labels), site-wide, every page. Do not introduce another face.
- **No build step.** Plain HTML/CSS/JS + a stdlib Python pipeline. Do not add a bundler,
  framework, or Node dependency.
- **Never hand-edit `radar.html`, `feed.xml`, or `radar/<date>.html`.** They are *baked*. Edit
  `automation/radar.template.html` and/or `data/`, then run `automation/render_radar.py` (or let
  CI bake). Archived `radar/*` editions are frozen snapshots — leave them.
- **The duplicated logic must stay in lockstep:**
  - The **layer classifier** (`LAYER_RE` / `classify_layer`) is duplicated in
    `automation/render_radar.py`, `automation/build_knowledge_graph.py`, and `assets/radar.js` —
    **change all three together.**
  - The **story scorer + age calc** (`score_story` / `age_in_days` in `render_radar.py` and
    `scoreStory` / `ageInDays` in `assets/radar.js`) must produce the same lead/order. The
    server bake and the client hydration must agree.
- **The gate accounting invariant:** `mapped + unresolved + noise == stimuli`. A structural
  signal that hasn't bound into a direction stays in `other` — never silently counted as
  explained.

## 2. Local workflow

```bash
git clone https://github.com/gagans23/gaganai.git
cd gaganai
python3 -m http.server 8080          # preview at http://localhost:8080

# Regenerate the intelligence from the existing ledger (no API key needed, deterministic):
python3 automation/build_knowledge_graph.py
python3 automation/build_signal_gate.py
python3 automation/render_radar.py
```

The gate, graph, and radar bake are **deterministic** — same ledger → same output. Only the
cloud generator (`automation/gcc-ai-newsletter/run_daily.py`) needs the `PARALLEL_API_KEY`
secret; without it the daily job no-ops cleanly.

## 3. Before a structural change: make a backup

Before large IA/design/pipeline changes, tag and push a backup so the work is reversible:

```bash
git tag backup/<name>-$(date +%Y%m%d)
git branch backup/<name>-$(date +%Y%m%d)
git push origin refs/heads/backup/<name>-<date> refs/tags/backup/<name>-<date>
# recover with: git reset --hard backup/<name>-<date>
```

## 4. Publishing a new essay

Follow the **"Publishing a new essay (article) — checklist"** in `HANDOFF-codex.md`. The short
version: copy `writing/the-amnesia-tax.html` as the structural reference, set the full head
metadata (OG/Twitter/canonical/Article JSON-LD), use the 3-door nav (Writing · Signal · About),
add the `.next-essay` CTA and update the previous essay's CTA to point to the new one, add the
entry to `writing/index.html` and `sitemap.xml`, and use the shared type system + drop cap.

## 5. Design + accessibility rules

- **Dark-lead → light-body rhythm.** The homepage hero, the signal page, and the about page open
  with a dark lead band (`#0a0d0e`); inner content is warm paper (`#f2efe6`). New top-level
  pages should follow the same opener pattern (kicker → h1 → standfirst → dateline), dark or
  light, with the same type scale.
- **OpenType features** stay on: `onum` for body, `dlig` for display, `lnum/tnum` for stats.
- **Motion respects `prefers-reduced-motion`** — every animation has a reduced-motion fallback
  (no animation; content still fully visible).
- **Keyboard focus:** visible `:focus-visible` amber outline (already in the shared CSS).
- **Contrast:** body/label colours must pass AA on the warm paper. The muted/slate vars are
  tuned for this; don't lighten them past the current values.

## 6. Commit + deploy

- **Commit prefix** shows authorship: `[codex]`, `[claude]`, `[cloud]` (the bot), or a human
  contributor's name. Example: `[claude] Add a reading-progress bar to essays`.
- **Push to `origin/main`.** GitHub Pages auto-deploys on push; no manual publish step.
- **Cache-busting:** CSS/JS carry `?v=` query strings — bump the version when you change a
  shared asset so browsers refetch. HTML is cached by the browser for ~10 minutes
  (`max-age=600`); a hard reload may be needed to see HTML changes immediately.
- **Don't commit the baked radar locally when you edit the radar template/CSS** — let CI bake
  (the `bake-radar` workflow) to avoid `feed.xml` rebase collisions. If you do rebake locally
  to verify, discard the baked files before committing: `git checkout -- radar.html feed.xml radar/`.

## 7. The pipeline (don't break it)

- `automation/update_daily_intelligence.sh` publishes **DATA ONLY** — it does not commit baked
  HTML (except via the in-workflow bake job).
- `.github/workflows/daily-intelligence.yml` runs the generator + graph + gate + an in-workflow
  **bake** job atomically at 06:00 GST, gated on `PARALLEL_API_KEY`. GitHub won't fire a
  downstream `on: push` workflow from a `GITHUB_TOKEN` push, so baking in-workflow is what keeps
  the radar fresh after a generation.
- `.github/workflows/bake-radar.yml` is the safety net (template/data-change trigger + 06:30
  schedule). `.github/workflows/monthly-brief.yml` publishes the prior month's brief on the 1st.

## 8. Reporting issues / ideas

The site's open items (e.g. widen the source pipeline beyond Google News RSS; the case-study
content gap) are tracked in `HANDOFF-codex.md` under "Open items." Concrete improvements that
match the project's narrow purpose (governed AI decisions for regulated-institution leaders)
are welcome; generic AI-news-broadening is not the goal.

---

*Questions about the architecture are answered in `README.md`; questions about how to work in
the repo are answered in `HANDOFF-codex.md`. This file is the short rulebook.*
