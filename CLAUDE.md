# Claude working notes

Read `HANDOFF-codex.md` before changing this site. It is the operating manual for IA, design,
pipeline invariants, and publishing.

Homepage writing freshness is intentionally data-backed:

- `data/writing.json` is the homepage source for the "latest field note" card.
- `index.html` only contains a correct fallback; do not hardcode an older essay as "Latest."
- When adding a new essay, update `writing/index.html`, `sitemap.xml`, and `data/writing.json`
  in the same change.
- If no new essay exists, keep the homepage honest: say "Latest in the archive" rather than
  implying fresh publication.

Homepage live-signal freshness is also data-backed:

- The "Today in the Situation Room" section reads `data/signal-gate.json` and
  `data/knowledge-graph.json` from `assets/site-home.js` with `cache: "no-store"`.
- Keep the visible freshness pill, rebuilt date, source-file line, and live-integrity explainer.
- If signal data is older than three days, the UI must mark it stale; do not imply fresh evidence
  just because the page was recently deployed.
- Daily evolution comes from the 06:00 GST `daily-intelligence.yml` workflow: generator → graph →
  gate → committed JSON → homepage hydration.

Preserve the current homepage direction: warm editorial paper, dark premium latest-card, visible
freshness label, and no extra fonts or build step.
