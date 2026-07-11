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

Preserve the current homepage direction: warm editorial paper, dark premium latest-card, visible
freshness label, and no extra fonts or build step.
