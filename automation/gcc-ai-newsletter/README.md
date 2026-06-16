# GCC AI Leadership Newsletter

Daily newsletter concept for LinkedIn and WhatsApp covering AI, agentic systems, cloud, banking, fintech, central banks, public sector, retail, energy, logistics, telecom, healthcare, education, and enterprise technology across the GCC.

## Local Factory

This folder is now a working local newsletter factory backed by:

- Parallel for source discovery
- Mirage for filesystem-style inspection
- Local files for drafts, WhatsApp copy, source JSON, image prompts, and publishing text
- OpenClaw for scheduled generation and future delivery orchestration

Run the daily issue from the site repo:

```bash
cd /path/to/gaganai-site
./automation/gcc-ai-newsletter/run_today.sh
```

Run without marking URLs as covered:

```bash
./automation/gcc-ai-newsletter/run_today.sh --dry-run
```

Generate a richer publishable issue with 7-day GCC priority + global context:

```bash
./automation/gcc-ai-newsletter/run_publishable.sh --dry-run
```

Allow undated sources for exploratory research only:

```bash
./automation/gcc-ai-newsletter/run_today.sh --dry-run --allow-undated
```

Daily outputs:

```text
automation/gcc-ai-newsletter/research/   raw Parallel results + filtered source list
automation/gcc-ai-newsletter/drafts/     full newsletter issue
automation/gcc-ai-newsletter/publish/    LinkedIn-ready text
automation/gcc-ai-newsletter/whatsapp/   WhatsApp short version
automation/gcc-ai-newsletter/images/     image prompt for the post visual
automation/gcc-ai-newsletter/history/    URLs already covered
assets/radar-data.js                     website Situation Room data
```

Run and publish the website radar update:

```bash
cd /path/to/gaganai-site
./automation/update_daily_intelligence.sh
```

Intraday radar-only style refresh without marking URLs as covered:

```bash
DRY_RUN=1 WINDOW_HOURS=24 ./automation/update_daily_intelligence.sh
```

The published website Radar only displays items from the filtered source list and every displayed signal includes its
source URL and publication date where available.

The strict daily mode only uses sources with visible publication dates inside the selected time window. If the system cannot verify enough fresh material, it writes a “no forced post” draft instead of recycling stale news.

Editorial depth rules:

- GCC-specific developments have priority.
- Global developments are included only as a separate context section.
- Each issue must connect the dots and explain the pattern, not merely summarize headlines.
- Each issue should include a visual mental model that can guide the post image.
- A weak daily signal should become a short restraint note, not filler.

## Publishing Goal

Publish every day at 9pm Gulf time with a concise, executive-grade post that builds Gagan's image as an informed AI and agentic systems leader.

## Daily Format

1. Hook: one strong opening line that makes leaders stop scrolling.
2. Signal: 5-7 sourced developments from the last 24-48 hours.
3. Why it matters: practical implication for GCC executives.
4. Leadership take: a clear point of view, not generic summary.
5. CTA: ask readers to comment, share, or subscribe.
6. WhatsApp short version: 3 bullets plus a link/QR placeholder.

## Coverage Map

- Countries: UAE, Saudi Arabia, Qatar, Bahrain, Kuwait, Oman
- Central banks and regulators
- Banks, fintech, payments, digital assets, open banking
- Cloud providers and hyperscalers
- AI model providers, agent platforms, enterprise software
- Telecom and data centers
- Retail, consumer, hospitality, airlines, logistics
- Energy, industrials, construction, real estate
- Government, smart cities, education, healthcare
- Cybersecurity, data governance, AI regulation

## Editorial Rules

- Do not invent facts.
- Prefer primary sources, regulator releases, company announcements, and credible business press.
- Every claim should have a source URL.
- Separate confirmed news from analysis.
- Keep LinkedIn voice confident, concise, and useful.
- Avoid hype words unless the evidence supports them.
- No investment advice.
- No copied article text.

## Launch Stages

- Stage 1: OpenClaw creates the daily draft automatically.
- Stage 2: Human approval and manual LinkedIn post.
- Stage 3: Connect official LinkedIn publishing API or approved scheduler.
- Stage 4: Add WhatsApp Channel or WhatsApp Business distribution with QR/subscription link.
