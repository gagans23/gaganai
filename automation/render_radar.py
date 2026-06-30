#!/usr/bin/env python3
"""Bake the AI Situation Room edition into static HTML.

Mirrors assets/radar.js exactly (scoring, filtering, markup) so the
server-rendered page and the client-side hydration always agree.
Crawlers, link previews and no-JS readers see the full edition;
radar.js re-renders the same content on load.

Usage:  python3 automation/render_radar.py
Reads:  data/radar-signals.js, automation/radar.template.html
Writes: radar.html, feed.xml, radar/<date>.html, radar/index.html
"""
import json
import html as htmlmod
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "radar-signals.js"
TEMPLATE = ROOT / "automation" / "radar.template.html"
OUT = ROOT / "radar.html"
FEED = ROOT / "feed.xml"
ARCHIVE_DIR = ROOT / "radar"
SITE = "https://gagansachdeva.com"

DESK_PRIORITY = {
    "GCC Institutions": 7, "Banking AI": 6, "Governance & Regulation": 5,
    "Agentic Systems": 4, "Enterprise Strategy": 3,
    "Compute & Infrastructure": 2, "Workforce Faultline": 1,
}
SOURCE_PRIORITY = {
    "official": 6, "company": 5, "investor": 4, "press": 4,
    "jobs": 3, "research": 3, "developer": 2, "analysis": 1,
}
GENERIC_RE = re.compile(r"top\s*\d+|weekly briefing|trend reports?|competitors|roundup|digest")


def esc(v):
    return htmlmod.escape(str(v or ""), quote=True)


def safe_url(v):
    """Escape a URL for an href, allowing only http(s) — blocks javascript:/data: etc."""
    s = str(v or "").strip()
    return esc(s) if s.lower().startswith(("http://", "https://")) else "#"


def load_data():
    raw = DATA.read_text(encoding="utf-8")
    body = raw.replace("window.GAGANAI_RADAR =", "", 1).strip().rstrip(";")
    return json.loads(body)


def age_in_days(value):
    """Age in days. Parses ISO dates/datetimes AND RFC2822 (e.g.
    "Mon, 29 Jun 2026 00:04:00 GMT") so the server bake and the radar.js
    client hydration (which uses Date()) compute identical ages and therefore
    identical story scores and the same lead. Keep in lockstep with ageInDays()
    in assets/radar.js."""
    if not value:
        return 999
    s = str(value).strip()
    parsed = None
    try:
        parsed = datetime.fromisoformat(s)
    except ValueError:
        pass
    if parsed is None:
        try:
            parsed = datetime.strptime(s, "%a, %d %b %Y %H:%M:%S %Z")
        except ValueError:
            try:
                from email.utils import parsedate_to_datetime
                parsed = parsedate_to_datetime(s)
            except Exception:
                return 999
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)
    return max(0, int((datetime.now(timezone.utc) - parsed).total_seconds() // 86400))


def is_current(s):
    return s.get("freshness") == "fresh" or age_in_days(s.get("date") or s.get("publication_date") or "") <= 21


def should_show(s):
    text = f"{s.get('title','')} {s.get('source','')}".lower()
    generic = bool(GENERIC_RE.search(text))
    if generic and s.get("freshness") == "carry-forward":
        return False
    if s.get("freshness") == "carry-forward" and age_in_days(s.get("date") or s.get("publication_date") or "") > 35:
        return False
    if (s.get("newsQuality") or 50) < 50:
        return False
    return True


def score_story(s):
    desk = DESK_PRIORITY.get(s.get("desk"), 0)
    source = SOURCE_PRIORITY.get(str(s.get("source_type") or "").lower(), 0)
    fr = s.get("freshness")
    freshness = 80 if fr == "fresh" else 0 if fr == "carry-forward" else 20
    recency = max(0, 60 - min(age_in_days(s.get("date") or s.get("publication_date") or ""), 60))
    gcc = 35 if s.get("region") == "GCC" else 20 if s.get("gccRelevance") == "High read-through" else 0
    return desk * 100 + source * 40 + freshness + recency + gcc + (s.get("score") or 0)


def source_badge(s):
    return " / ".join(esc(x) for x in [s.get("region"), s.get("desk"), s.get("source")] if x)


def quality_badge(s):
    return f"{esc(s.get('sourceGrade') or 'C')} source / {esc(s.get('newsQuality') or 50)} quality"


def render_lead(s):
    if not s:
        return ('<div class="empty-state"><strong>No current stories are ready for the front page.</strong>'
                '<p>The feed needs fresher reported news before this edition should lead with a headline.</p></div>')
    return f"""
      <div class="lead-story-topline">
        <span>{esc(s.get('date'))}</span>
        <span>{source_badge(s)}</span>
        <span>{quality_badge(s)}</span>
      </div>
      <h3>{esc(s.get('title'))}</h3>
      <p class="lead-story-summary">{esc(s.get('whatChanged'))}</p>
      <div class="lead-story-analysis">
        <article>
          <span>Why this matters</span>
          <p>{esc(s.get('whyItMatters'))}</p>
        </article>
        <article>
          <span>What to watch</span>
          <p>{esc(s.get('readThrough'))}</p>
        </article>
      </div>
      <div class="lead-story-actions">
        <a href="{safe_url(s.get('url'))}" target="_blank" rel="noreferrer">Read original source</a>
      </div>
    """


def story_card(s):
    return f"""
    <article class="story-card">
      <div class="story-card-topline">
        <span>{esc(s.get('date'))}</span>
        <span>{source_badge(s)}</span>
        <span>{quality_badge(s)}</span>
      </div>
      <h4>{esc(s.get('title'))}</h4>
      <p>{esc(s.get('whatChanged'))}</p>
      <div class="story-card-footer">
        <strong>{esc(s.get('whyItMatters'))}</strong>
        <a href="{safe_url(s.get('url'))}" target="_blank" rel="noreferrer">{esc(s.get('source'))}</a>
      </div>
    </article>
    """


# --- Gagan's read: the five-layer cake (after Jensen Huang's stack) ---
# Keep LAYERS and classify_layer in lockstep with assets/radar.js.
LAYERS = [
    (5, "Agents & Applications", "Where AI meets work — agents in production, banking, government, enterprise, people."),
    (4, "Models & Intelligence", "Frontier labs, model releases, training, open weights, evals."),
    (3, "AI Factories & Cloud", "Data centres, sovereign compute, cloud capacity."),
    (2, "Silicon & Networks", "Chips, accelerators, fabs, export controls."),
    (1, "Energy & Power", "The watts underneath it all — grid, generation, power deals."),
]
LAYER_RE = {
    1: re.compile(r"\b(energy|power plants?|gigawatts?|megawatts?|nuclear|electricity|grid)\b"),
    2: re.compile(r"\b(chips?|semiconductors?|gpus?|silicon|tsmc|chip fabs?|fabrication|foundr(?:y|ies)|wafers?|ai accelerators?|export controls?)\b"),
    3: re.compile(r"\b(data cent(?:re|er)s?|datacenters?|ai factor(?:y|ies)|hyperscalers?|cloud regions?|compute capacity|sovereign compute|colocation|ai infrastructure|infrastructure buildouts?)\b"),
    4: re.compile(r"\b(models?|frontier labs?|open[- ]weights?|training runs?|benchmarks?|reasoning|fine[- ]tun\w*|inference)\b"),
}


def classify_layer(s):
    text = f"{s.get('title','')} {s.get('whatChanged','')} {s.get('desk','')}".lower()
    for layer in (1, 2, 3):
        if LAYER_RE[layer].search(text):
            return layer
    if s.get("desk") == "Compute & Infrastructure":
        return 3
    if re.search(r"\b(agents?|agentic)\b", text):
        return 5
    if LAYER_RE[4].search(text):
        return 4
    return 5


def render_cake(current):
    groups = {n: [] for n, _, _ in LAYERS}
    for s in current:
        groups[classify_layer(s)].append(s)
    hot = max(groups, key=lambda n: len(groups[n])) if current else None

    bands = []
    for n, name, desc in LAYERS:
        stories = groups[n]
        moves = "".join(
            f"<article><h4>{esc(s.get('title'))}</h4><p>{esc(s.get('readThrough') or s.get('whyItMatters'))}</p></article>"
            for s in stories[:2]
        )
        moves_html = f'<div class="cake-moves">{moves}</div>' if moves else ""
        count = (f'<span class="cake-count">{len(stories)} moving</span>' if stories
                 else '<span class="cake-count cake-count-quiet">quiet</span>')
        hot_cls = " is-hot" if n == hot and stories else ""
        quiet_cls = " is-quiet" if not stories else ""
        bands.append(
            f'<article class="cake-layer cake-l{n}{hot_cls}{quiet_cls}">'
            f'<div class="cake-head"><span class="cake-num">L{n}</span><h3>{esc(name)}</h3>{count}</div>'
            f'<p class="cake-desc">{esc(desc)}</p>{moves_html}</article>'
        )

    if hot and groups[hot]:
        hot_name = next(name for n, name, _ in LAYERS if n == hot)
        note = (f"Today the pressure is on L{hot} — {hot_name.lower()}: "
                f"{len(groups[hot])} of {len(current)} verified stories move that layer.")
    else:
        note = "No verified current stories cleared the bar today, so every layer reads quiet."
    return "".join(bands), note


def edition_iso(reviewed):
    try:
        return datetime.strptime(reviewed, "%B %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def rfc822(iso_date):
    try:
        parsed = datetime.strptime(iso_date[:10], "%Y-%m-%d").replace(hour=6, tzinfo=timezone.utc)
    except ValueError:
        parsed = datetime.now(timezone.utc)
    return parsed.strftime("%a, %d %b %Y %H:%M:%S GMT")


def bake_feed(reviewed, iso, lead, stories):
    items = []
    if lead:
        items.append(f"""    <item>
      <title>{esc(f"Edition {reviewed}: {lead.get('title')}")}</title>
      <link>{SITE}/radar/{iso}.html</link>
      <guid isPermaLink="true">{SITE}/radar/{iso}.html</guid>
      <pubDate>{rfc822(iso)}</pubDate>
      <description>{esc(f"{lead.get('whatChanged')} Why it matters: {lead.get('whyItMatters')}")}</description>
    </item>""")
    for s in stories:
        desc = f"{s.get('whatChanged') or ''} Why it matters: {s.get('whyItMatters') or ''}".strip()
        items.append(f"""    <item>
      <title>{esc(s.get('title'))}</title>
      <link>{safe_url(s.get('url'))}</link>
      <guid isPermaLink="false">{safe_url(s.get('url'))}</guid>
      <pubDate>{rfc822(str(s.get('date') or iso))}</pubDate>
      <description>{esc(desc)}</description>
    </item>""")
    FEED.write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>AI Situation Room · The Philosophical Ledger</title>
    <link>{SITE}/radar.html</link>
    <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml" />
    <description>A daily front page of verified AI and agentic-systems news with the read-through for leaders: banking, governance, GCC, compute and enterprise strategy.</description>
    <language>en</language>
    <lastBuildDate>{rfc822(iso)}</lastBuildDate>
{chr(10).join(items)}
  </channel>
</rss>
""", encoding="utf-8")


def bake_archive(page_html, iso):
    ARCHIVE_DIR.mkdir(exist_ok=True)
    archived = page_html
    # static snapshot: drop hydration scripts so old editions are never re-rendered with current data
    archived = re.sub(r'\s*<script src="(?:data/radar-signals|assets/radar)\.js[^"]*" defer></script>', "", archived)
    archived = archived.replace("<head>", '<head>\n    <base href="../" />', 1)
    archived = archived.replace(f'{SITE}/radar.html', f'{SITE}/radar/{iso}.html')
    archived = archived.replace(
        '<main class="radar-page" data-radar-app>',
        '<main class="radar-page" data-radar-app>\n      <p style="margin:0 0 18px;padding:10px 14px;border:1px solid rgba(20,17,12,0.25);font-size:13px;">'
        f'Archived edition of {iso}. <a href="radar.html" style="font-weight:700;text-decoration:underline;">Read today&#x27;s edition</a>.</p>', 1)
    (ARCHIVE_DIR / f"{iso}.html").write_text(archived, encoding="utf-8")

    editions = sorted((p.stem for p in ARCHIVE_DIR.glob("????-??-??.html")), reverse=True)
    rows = "".join(
        f'<li><a href="{d}.html">{datetime.strptime(d, "%Y-%m-%d").strftime("%B %-d, %Y")}</a></li>' for d in editions)
    (ARCHIVE_DIR / "index.html").write_text(f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Edition Archive · AI Situation Room · Gagan Sachdeva</title>
    <meta name="description" content="Every archived edition of the AI Situation Room: daily verified AI and agentic-systems news with the read-through for leaders." />
    <link rel="canonical" href="{SITE}/radar/index.html" />
    <link rel="icon" href="../favicon.svg" type="image/svg+xml" />
    <link rel="alternate" type="application/rss+xml" title="AI Situation Room" href="{SITE}/feed.xml" />
    <style>
      * {{ box-sizing: border-box; margin: 0; }}
      body {{ background: #f8f3e8; color: #14110c; font-family: Georgia, "Times New Roman", serif; padding: 48px 24px; }}
      main {{ max-width: 640px; margin: 0 auto; }}
      p.eyebrow {{ font-family: -apple-system, sans-serif; font-size: 12px; letter-spacing: 0.28em; text-transform: uppercase; opacity: 0.65; margin-bottom: 14px; }}
      h1 {{ font-size: clamp(30px, 5vw, 44px); line-height: 1.1; margin-bottom: 14px; }}
      p.note {{ line-height: 1.6; opacity: 0.85; margin-bottom: 34px; }}
      ul {{ list-style: none; }}
      li {{ border-top: 1px solid rgba(20, 17, 12, 0.2); }}
      li a {{ display: block; padding: 14px 4px; color: inherit; text-decoration: none; font-size: 19px; }}
      li a:hover {{ background: rgba(20, 17, 12, 0.05); }}
      nav.back {{ margin-top: 36px; font-family: -apple-system, sans-serif; font-size: 14px; }}
      nav.back a {{ color: inherit; font-weight: 700; }}
    </style>
  </head>
  <body>
    <main>
      <p class="eyebrow">The Philosophical Ledger</p>
      <h1>Edition archive.</h1>
      <p class="note">Every baked edition of the AI Situation Room, kept exactly as published. Today&#x27;s page is always at <a href="../radar.html">radar.html</a>; subscribe via <a href="../feed.xml">RSS</a>.</p>
      <ul>{rows}</ul>
      <nav class="back"><a href="../radar.html">&larr; Today&#x27;s edition</a> &middot; <a href="../index.html">Home</a></nav>
    </main>
  </body>
</html>
""", encoding="utf-8")
    return len(editions)


def main():
    data = load_data()
    signals = sorted(data.get("signals", []), key=lambda s: s.get("date", ""), reverse=True)
    visible = sorted([s for s in signals if should_show(s)], key=score_story, reverse=True)
    current = [s for s in visible if is_current(s)]
    lead = visible[0] if visible else None

    fresh_n = sum(1 for s in visible if s.get("freshness") == "fresh")
    gcc_n = sum(1 for s in visible if s.get("region") == "GCC")
    if fresh_n:
        note = f"{fresh_n} fresh stories and {gcc_n} GCC-relevant stories are on today's page."
    elif current:
        note = f"{len(current)} source-backed current stories and {gcc_n} GCC-relevant stories are on today's page."
    else:
        note = "The edition is using archived source-backed context until the next current story clears the page-one bar."

    rest = current[1:9] if lead else current[:8]
    fresh_rest = [s for s in rest if s.get("freshness") == "fresh"]
    ongoing = [s for s in rest if s.get("freshness") != "fresh"]

    def group(label, items):
        if not items:
            return ""
        return f'<h4 class="story-group-head">{esc(label)} <span class="ct">{len(items)}</span></h4>' + "".join(story_card(s) for s in items)

    story_list = (group("New today", fresh_rest) + group("Ongoing context", ongoing)) or (
        '<div class="empty-state"><strong>No current supporting stories are ready.</strong>'
        '<p>The edition needs fresher reported stories before it should look like a full front page.</p></div>')

    cake_html, cake_note = render_cake(current)

    chatter_items = []
    for i, item in enumerate((data.get("marketChatter") or [])[:8]):
        platform = item.get("platform") or item.get("name") or "Market"
        handle = item.get("handle") or item.get("role") or "watch stream"
        text = item.get("text") or item.get("role") or item.get("signal") or ""
        chatter_items.append(
            f"<details class=\"chatter-card\"{' open' if i == 0 else ''}>"
            f"<summary><span class=\"chatter-platform\">{esc(platform)}</span>"
            f"<strong>{esc(item.get('name'))}</strong><small>{esc(handle)}</small></summary>"
            f"<p>{esc(text)}</p><div class=\"chatter-read\">"
            f"<span>{esc(item.get('signal') or 'Market discussion, not primary reporting.')}</span>"
            f"<a href=\"{esc(item.get('url'))}\" target=\"_blank\" rel=\"noreferrer\">Open thread</a></div></details>")

    reviewed = data.get("reviewed") or ""
    version = ("baked-" + re.sub(r"[^A-Za-z0-9]", "", reviewed) or "baked") + "-r8"

    out = TEMPLATE.read_text(encoding="utf-8")
    for token, value in {
        "{{REVIEWED}}": esc(reviewed),
        "{{PRIMARY_DESK}}": esc((visible[0].get("desk") if visible else "") or "Agentic Systems"),
        "{{PRIMARY_REGION}}": esc((visible[0].get("region") if visible else "") or "Global"),
        "{{FRONT_PAGE_NOTE}}": esc(note),
        "{{LEAD_STORY}}": render_lead(lead),
        "{{STORY_LIST}}": story_list,
        "{{LAYER_CAKE}}": cake_html,
        "{{CAKE_NOTE}}": esc(cake_note),
        "{{MARKET_CHATTER}}": "".join(chatter_items),
        "{{VERSION}}": version,
    }.items():
        out = out.replace(token, value)

    leftover = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if leftover:
        sys.exit(f"Unfilled template tokens: {leftover}")

    OUT.write_text(out, encoding="utf-8")

    iso = edition_iso(reviewed)
    bake_feed(reviewed, iso, lead, current[1:10] if lead else current[:10])
    n_editions = bake_archive(out, iso)
    print(f"Baked radar.html — edition {reviewed}, lead: {lead.get('title') if lead else 'none'}, "
          f"{len(current)} current stories, version {version}")
    print(f"Baked feed.xml and radar/{iso}.html ({n_editions} archived editions)")


if __name__ == "__main__":
    main()
