#!/usr/bin/env python3
"""Build the month-end "connect the dots" brief.

Reads the persistent signal ledger (data/signal-ledger.jsonl) for one calendar
month and writes an editorial retrospective: how the month moved across the five
layers, which entities and threads dominated, and the throughline that connects
them. Also refreshes briefs/index.html.

Fully automated: the month-end GitHub Action runs this and commits the result.
Deterministic and stdlib-only — the same ledger always yields the same brief.

Usage:
  python3 automation/build_monthly_brief.py [--month YYYY-MM] [--ledger PATH]
Defaults to the current UTC month.
"""
import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER = REPO / "data" / "signal-ledger.jsonl"
BRIEFS = REPO / "briefs"

LAYER_LABEL = {5: "Agents & Applications", 4: "Models & Intelligence",
               3: "AI Factories & Cloud", 2: "Silicon & Networks", 1: "Energy & Power"}
LAYER_GLOSS = {
    5: "where AI meets work — agents in production, banking, government, enterprise",
    4: "frontier labs, model releases, evals and open weights",
    3: "data centres, sovereign compute, cloud capacity",
    2: "chips, accelerators, fabs and export controls",
    1: "the watts underneath it all — grid, generation, power deals",
}
MONTHS = ["", "January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def safe_url(v):
    s = str(v or "").strip()
    return esc(s) if s.lower().startswith(("http://", "https://")) else "#"


def parse_month_key(rec):
    """Best-effort month key (YYYY-MM) for a ledger record from its firstSeen
    'Month DD, YYYY' string, falling back to signalDate RFC822."""
    fs = rec.get("firstSeen", "") or ""
    m = re.match(r"([A-Za-z]+)\s+\d{1,2},\s+(\d{4})", fs)
    if m:
        mon = MONTHS.index(m.group(1)) if m.group(1) in MONTHS else 0
        if mon:
            return f"{m.group(2)}-{mon:02d}"
    # fallback: RFC822 like 'Thu, 18 Jun 2026 10:00:00 GMT'
    sd = rec.get("signalDate", "") or ""
    m2 = re.search(r"(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})", sd)
    if m2:
        abbr = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, "Jul": 7,
                "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}.get(m2.group(2), 0)
        if abbr:
            return f"{m2.group(3)}-{abbr:02d}"
    return ""


def load_month(ledger_path, month_key):
    recs = []
    if not ledger_path.exists():
        return recs
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if parse_month_key(r) == month_key:
            recs.append(r)
    return recs


def analyse(recs):
    layer_count = defaultdict(int)
    ent_count = defaultdict(int)
    ent_score = defaultdict(int)
    ent_type = {}
    theme_count = defaultdict(int)
    co = defaultdict(int)
    days = set()
    for r in recs:
        layer_count[r.get("layer", 5)] += 1
        if r.get("theme"):
            theme_count[r["theme"]] += 1
        days.add(r.get("firstSeen", ""))
        ents = r.get("entities", []) or []
        for e in ents:
            ent_count[e] += 1
            ent_score[e] += int(r.get("score", 0) or 0)
        for a, b in combinations(sorted(set(ents)), 2):
            co[(a, b)] += 1
    top_ent = sorted(ent_count, key=lambda e: (-ent_count[e], -ent_score[e]))
    top_threads = sorted(co.items(), key=lambda kv: -kv[1])
    top_themes = sorted(theme_count, key=lambda t: -theme_count[t])
    top_stories = sorted(recs, key=lambda r: -int(r.get("score", 0) or 0))
    hot_layer = max(layer_count, key=layer_count.get) if layer_count else None
    return {
        "layer_count": layer_count, "ent_count": ent_count, "ent_score": ent_score,
        "theme_count": theme_count, "top_ent": top_ent, "top_threads": top_threads,
        "top_themes": top_themes, "top_stories": top_stories, "hot_layer": hot_layer,
        "days": sorted(d for d in days if d),
    }


def synth_narrative(a, recs, month_name):
    """Deterministic 'connect the dots' synthesis from the month's structure."""
    paras = []
    n = len(recs)
    hot = a["hot_layer"]
    if hot:
        share = a["layer_count"][hot]
        paras.append(
            f"Across {n} verified signals this {month_name}, the centre of gravity sat at "
            f"<strong>L{hot} — {LAYER_LABEL[hot]}</strong> ({share} of {n} stories), "
            f"{LAYER_GLOSS[hot]}. That is where the month's pressure concentrated.")
    if a["top_ent"]:
        names = a["top_ent"][:5]
        lead = names[0]
        paras.append(
            f"The name the month kept returning to was <strong>{esc(lead)}</strong> "
            f"({a['ent_count'][lead]} signals), alongside "
            + ", ".join(esc(x) for x in names[1:]) +
            ". These were not isolated mentions — they recurred, which is the difference "
            "between noise and a trend.")
    if a["top_threads"]:
        (x, y), w = a["top_threads"][0]
        extra = ""
        if len(a["top_threads"]) > 1:
            (p, q), w2 = a["top_threads"][1]
            extra = f" The second-strongest thread tied <strong>{esc(p)}</strong> to <strong>{esc(q)}</strong> ({w2}×)."
        paras.append(
            f"The strongest connection of the month was <strong>{esc(x)} ↔ {esc(y)}</strong>, "
            f"co-appearing in {w} separate verified stories.{extra} When two names keep showing "
            "up in the same story, the dots are already connected — the question is who moves first.")
    if a["top_themes"]:
        t = a["top_themes"][:3]
        paras.append("The throughline themes: " + ", ".join(f"<em>{esc(x)}</em>" for x in t) +
                     ". Read together, they describe a market moving from AI advice to controlled "
                     "AI action — governed autonomy, not demos.")
    return paras


def render_brief(month_key, month_name, year, a, recs):
    days_span = f"{a['days'][0]} → {a['days'][-1]}" if a["days"] else "—"
    n = len(recs)
    layer_rows = "".join(
        f'<div class="lrow"><span class="lnum">L{L}</span>'
        f'<span class="lname">{esc(LAYER_LABEL[L])}</span>'
        f'<span class="lbar"><i style="width:{(a["layer_count"].get(L,0)/max(n,1))*100:.0f}%"></i></span>'
        f'<span class="lcount">{a["layer_count"].get(L,0)}</span></div>'
        for L in (5, 4, 3, 2, 1))
    ent_chips = "".join(
        f'<span class="echip">{esc(e)}<b>{a["ent_count"][e]}</b></span>'
        for e in a["top_ent"][:14])
    thread_rows = "".join(
        f'<li><span>{esc(x)} <em>↔</em> {esc(y)}</span><b>{w}×</b></li>'
        for (x, y), w in a["top_threads"][:8]) or "<li>No repeated threads yet this month.</li>"
    story_rows = "".join(
        f'<article class="story"><div class="srank">{i+1:02d}</div>'
        f'<div><h4><a href="{safe_url(r.get("url"))}" rel="noreferrer">{esc(r.get("title"))}</a></h4>'
        f'<p>{esc((r.get("whyItMatters") or "")[:200])}</p>'
        f'<span class="smeta">L{r.get("layer",5)} · {esc(r.get("region",""))} · score {r.get("score",0)}</span></div></article>'
        for i, r in enumerate(a["top_stories"][:8]))
    narrative = "".join(f"<p>{p}</p>" for p in synth_narrative(a, recs, month_name))
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(month_name)} {year} in AI · Connect the Dots · Gagan Sachdeva</title>
<meta name="description" content="How {esc(month_name)} {year} moved across the AI stack — from energy to agents. The month's dominant threads, recurring names and the throughline that connects them.">
<meta property="og:title" content="{esc(month_name)} {year} in AI — Connect the Dots">
<meta property="og:description" content="A month-end retrospective from the AI Situation Room: layer momentum, the names that recurred, and the threads worth watching.">
<meta property="og:type" content="article">
<meta property="og:url" content="https://gagansachdeva.com/briefs/{month_key}.html">
<meta property="og:image" content="https://gagansachdeva.com/assets/og-card-20260611.jpg">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="https://gagansachdeva.com/briefs/{month_key}.html">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{--paper:#f2efe6;--card:#fff;--ink:#181b22;--muted:#5b6270;--slate:#8a8f9c;--rule:#ddd8c9;--signal:#b3661f;--max:880px;--serif:"Source Serif 4",Georgia,serif;--display:"Fraunces",Georgia,serif;--mono:"IBM Plex Mono",ui-monospace,monospace}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--paper);color:var(--ink);font-family:var(--serif);font-size:18px;line-height:1.7;-webkit-font-smoothing:antialiased}}
a{{color:inherit}}
.wrap{{max-width:var(--max);margin:0 auto;padding:0 24px}}
.mono{{font-family:var(--mono);font-size:.7rem;letter-spacing:.12em;text-transform:uppercase}}
header{{border-bottom:1px solid var(--rule);position:sticky;top:0;background:rgba(242,239,230,.94);backdrop-filter:blur(8px);z-index:50}}
.nav{{display:flex;align-items:center;justify-content:space-between;height:60px;max-width:1100px;margin:0 auto;padding:0 24px}}
.nav a{{text-decoration:none}}.nav .brand{{font-family:var(--display);font-weight:600;font-size:1.05rem}}
.nav ul{{display:flex;gap:22px;list-style:none}}
.nav ul a{{font-family:var(--mono);font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:var(--slate)}}
.nav ul a:hover{{color:var(--signal)}}
@media(max-width:760px){{.nav ul{{display:none}}}}
.masthead{{padding:54px 0 34px;border-bottom:1px solid var(--rule)}}
.kicker{{color:var(--signal);margin-bottom:14px}}
h1{{font-family:var(--display);font-weight:700;font-size:clamp(2.1rem,5vw,3.2rem);line-height:1.06;letter-spacing:-.01em}}
.standfirst{{color:var(--muted);margin-top:16px;font-size:1.08rem;max-width:640px}}
.factbar{{display:flex;flex-wrap:wrap;gap:28px;margin-top:26px;padding-top:20px;border-top:1px solid var(--rule)}}
.factbar .lbl{{color:var(--slate)}}.factbar .val{{font-family:var(--display);font-size:1.1rem;margin-top:3px;display:block}}
section{{padding:46px 0;border-bottom:1px solid var(--rule)}}
h2{{font-family:var(--display);font-weight:600;font-size:1.6rem;margin-bottom:8px}}
.sub{{color:var(--muted);margin-bottom:24px;font-size:.97rem}}
.narrative p{{margin-bottom:18px}}
.narrative strong{{font-weight:600}}
.lrow{{display:grid;grid-template-columns:38px 1fr 200px 40px;align-items:center;gap:14px;padding:11px 0;border-bottom:1px dashed var(--rule)}}
.lnum{{font-family:var(--mono);font-size:.8rem;color:var(--signal)}}
.lname{{font-family:var(--display);font-size:1.02rem}}
.lbar{{background:var(--rule);height:7px;border-radius:4px;overflow:hidden}}
.lbar i{{display:block;height:100%;background:var(--signal)}}
.lcount{{font-family:var(--mono);font-size:.82rem;text-align:right;color:var(--muted)}}
@media(max-width:680px){{.lrow{{grid-template-columns:34px 1fr 40px}}.lbar{{display:none}}}}
.echips{{display:flex;flex-wrap:wrap;gap:8px}}
.echip{{font-family:var(--mono);font-size:.72rem;letter-spacing:.04em;border:1px solid var(--rule);background:var(--card);border-radius:999px;padding:6px 12px;color:var(--ink)}}
.echip b{{color:var(--signal);margin-left:7px}}
.threads{{list-style:none}}
.threads li{{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--rule);font-family:var(--display);font-size:1.05rem}}
.threads li em{{color:var(--signal);font-style:normal;margin:0 4px}}
.threads li b{{font-family:var(--mono);font-size:.8rem;color:var(--muted)}}
.story{{display:grid;grid-template-columns:48px 1fr;gap:16px;padding:18px 0;border-bottom:1px solid var(--rule)}}
.srank{{font-family:var(--display);font-size:1.3rem;color:var(--slate)}}
.story h4{{font-family:var(--display);font-weight:600;font-size:1.1rem;line-height:1.3}}
.story h4 a{{text-decoration:none}}.story h4 a:hover{{color:var(--signal)}}
.story p{{color:var(--muted);font-size:.92rem;margin-top:6px}}
.smeta{{font-family:var(--mono);font-size:.64rem;letter-spacing:.08em;text-transform:uppercase;color:var(--slate);margin-top:8px;display:block}}
.cta{{display:inline-block;margin-top:6px;font-family:var(--mono);font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;color:var(--signal);text-decoration:none}}
footer{{padding:40px 0;display:flex;justify-content:space-between;color:var(--slate);font-family:var(--mono);font-size:.66rem;letter-spacing:.08em;text-transform:uppercase}}
footer a{{text-decoration:none}}
.disclaimer{{color:var(--slate);font-size:.8rem;margin-top:10px}}
.room-nav{{border-bottom:1px solid var(--rule);background:rgba(242,239,230,.7)}}
.room-nav .wrap{{display:flex;gap:6px;flex-wrap:wrap;padding-top:10px;padding-bottom:10px}}
.room-nav a{{font-family:var(--mono);font-size:.66rem;letter-spacing:.1em;text-transform:uppercase;color:var(--slate);text-decoration:none;padding:7px 14px;border-radius:999px;border:1px solid transparent}}
.room-nav a:hover{{color:var(--signal)}}
.room-nav a[aria-current]{{color:var(--signal);border-color:var(--rule);background:var(--card)}}
</style>
</head>
<body>
<header><div class="nav">
  <a class="brand" href="https://gagansachdeva.com/index.html">Gagan Sachdeva</a>
  <ul>
    <li><a href="https://gagansachdeva.com/writing/index.html">Writing</a></li>
    <li><a href="https://gagansachdeva.com/signal.html" aria-current="page">Situation Room</a></li>
    <li><a href="https://gagansachdeva.com/podcasts.html">Library</a></li>
    <li><a href="https://gagansachdeva.com/index.html#about">About</a></li>
  </ul>
</div></header>
<nav class="room-nav" aria-label="Situation Room views"><div class="wrap">
  <a href="https://gagansachdeva.com/signal.html">Signal</a>
  <a href="https://gagansachdeva.com/radar.html">Daily Feed</a>
  <a href="https://gagansachdeva.com/graph.html">Graph</a>
  <a href="https://gagansachdeva.com/briefs/index.html" aria-current="page">Briefs</a>
</div></nav>

<div class="wrap masthead">
  <div class="mono kicker">Monthly Brief · Connect the Dots</div>
  <h1>{esc(month_name)} {year} in AI &amp; agents.</h1>
  <p class="standfirst">How the month moved across the stack — from the energy underneath to the agents on top — and the threads the daily Situation Room kept connecting.</p>
  <div class="factbar">
    <div><span class="mono lbl">Signals verified</span><span class="val">{n}</span></div>
    <div><span class="mono lbl">Window</span><span class="val">{esc(days_span)}</span></div>
    <div><span class="mono lbl">Hottest layer</span><span class="val">L{a['hot_layer'] or '—'} · {esc(LAYER_LABEL.get(a['hot_layer'],'—'))}</span></div>
    <div><span class="mono lbl">Names tracked</span><span class="val">{len(a['ent_count'])}</span></div>
  </div>
</div>

<section class="wrap narrative">
  <h2>The throughline</h2>
  <p class="sub">What connected, and why it mattered.</p>
  {narrative}
</section>

<section class="wrap">
  <h2>Where the pressure sat</h2>
  <p class="sub">Verified signals by layer, L5 (agents) down to L1 (energy).</p>
  {layer_rows}
</section>

<section class="wrap">
  <h2>The names that recurred</h2>
  <p class="sub">Entities by number of verified signals this month.</p>
  <div class="echips">{ent_chips}</div>
</section>

<section class="wrap">
  <h2>Strongest threads</h2>
  <p class="sub">Pairs that kept appearing in the same story — the dots already connected.</p>
  <ul class="threads">{thread_rows}</ul>
  <a class="cta" href="https://gagansachdeva.com/graph.html">Explore the full connection graph →</a>
</section>

<section class="wrap">
  <h2>The month's strongest signals</h2>
  <p class="sub">Top verified stories by conviction score.</p>
  {story_rows}
</section>

<footer class="wrap">
  <span>{esc(month_name)} {year} Brief · The Philosophical Ledger</span>
  <span><a href="https://gagansachdeva.com/index.html">gagansachdeva.com</a></span>
</footer>
<p class="wrap disclaimer">Auto-assembled from the AI Situation Room ledger on {generated}. Every story above is a verified signal with a source link.</p>
<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token": "bdc556ad04c94787a68f270df061e5e4"}}'></script>
</body>
</html>
"""


def render_index(entries):
    cards = "".join(
        f'<a class="bcard" href="{esc(k)}.html"><span class="mono be">{esc(name)} {yr}</span>'
        f'<h3>{esc(name)} {yr} in AI &amp; agents</h3>'
        f'<span class="bmeta">{cnt} signals · hottest L{hot}</span></a>'
        for k, name, yr, cnt, hot in entries)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Monthly Briefs · Connect the Dots · Gagan Sachdeva</title>
<meta name="description" content="Month-end retrospectives from the AI Situation Room — how each month moved across the stack from energy to agents, and the threads that connected.">
<link rel="canonical" href="https://gagansachdeva.com/briefs/index.html">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{--paper:#f2efe6;--card:#fff;--ink:#181b22;--muted:#5b6270;--slate:#8a8f9c;--rule:#ddd8c9;--signal:#b3661f;--display:"Fraunces",Georgia,serif;--serif:"Source Serif 4",Georgia,serif;--mono:"IBM Plex Mono",ui-monospace,monospace}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--paper);color:var(--ink);font-family:var(--serif);font-size:18px;line-height:1.65}}
a{{color:inherit}}.wrap{{max-width:1000px;margin:0 auto;padding:0 24px}}
.mono{{font-family:var(--mono);font-size:.7rem;letter-spacing:.12em;text-transform:uppercase}}
header{{border-bottom:1px solid var(--rule)}}
.nav{{display:flex;align-items:center;justify-content:space-between;height:60px;max-width:1100px;margin:0 auto;padding:0 24px}}
.nav a{{text-decoration:none}}.nav .brand{{font-family:var(--display);font-weight:600;font-size:1.05rem}}
.nav ul{{display:flex;gap:22px;list-style:none}}.nav ul a{{font-family:var(--mono);font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:var(--slate)}}
.nav ul a:hover,.nav ul a[aria-current]{{color:var(--signal)}}
@media(max-width:760px){{.nav ul{{display:none}}}}
.masthead{{padding:54px 0 34px}}
.kicker{{color:var(--signal);margin-bottom:14px}}
h1{{font-family:var(--display);font-weight:700;font-size:clamp(2rem,4.6vw,3rem);line-height:1.08}}
.standfirst{{color:var(--muted);margin-top:14px;max-width:620px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;padding:30px 0 70px}}
.bcard{{display:block;background:var(--card);border:1px solid var(--rule);border-radius:3px;padding:22px;text-decoration:none;transition:transform .15s}}
.bcard:hover{{transform:translateY(-2px)}}
.bcard .be{{color:var(--signal)}}
.bcard h3{{font-family:var(--display);font-weight:600;font-size:1.2rem;margin:10px 0 12px;line-height:1.25}}
.bcard .bmeta{{font-family:var(--mono);font-size:.66rem;letter-spacing:.08em;text-transform:uppercase;color:var(--slate)}}
.empty{{color:var(--muted);padding:30px 0 70px}}
.room-nav{{border-bottom:1px solid var(--rule);background:rgba(242,239,230,.7)}}
.room-nav .wrap{{display:flex;gap:6px;flex-wrap:wrap;padding-top:10px;padding-bottom:10px}}
.room-nav a{{font-family:var(--mono);font-size:.66rem;letter-spacing:.1em;text-transform:uppercase;color:var(--slate);text-decoration:none;padding:7px 14px;border-radius:999px;border:1px solid transparent}}
.room-nav a:hover{{color:var(--signal)}}
.room-nav a[aria-current]{{color:var(--signal);border-color:var(--rule);background:var(--card)}}
</style>
</head>
<body>
<header><div class="nav">
  <a class="brand" href="https://gagansachdeva.com/index.html">Gagan Sachdeva</a>
  <ul>
    <li><a href="https://gagansachdeva.com/writing/index.html">Writing</a></li>
    <li><a href="https://gagansachdeva.com/signal.html" aria-current="page">Situation Room</a></li>
    <li><a href="https://gagansachdeva.com/podcasts.html">Library</a></li>
    <li><a href="https://gagansachdeva.com/index.html#about">About</a></li>
  </ul>
</div></header>
<nav class="room-nav" aria-label="Situation Room views"><div class="wrap">
  <a href="https://gagansachdeva.com/signal.html">Signal</a>
  <a href="https://gagansachdeva.com/radar.html">Daily Feed</a>
  <a href="https://gagansachdeva.com/graph.html">Graph</a>
  <a href="https://gagansachdeva.com/briefs/index.html" aria-current="page">Briefs</a>
</div></nav>
<div class="wrap masthead">
  <div class="mono kicker">Monthly Briefs</div>
  <h1>Connect the dots.</h1>
  <p class="standfirst">At the end of every month, the AI Situation Room steps back: how the month moved across the stack from energy to agents, the names that recurred, and the threads worth carrying forward.</p>
</div>
<div class="wrap">
  {'<div class="grid">'+cards+'</div>' if entries else '<p class="empty">The first monthly brief publishes at the end of this month.</p>'}
</div>
<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token": "bdc556ad04c94787a68f270df061e5e4"}}'></script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", default=datetime.now(timezone.utc).strftime("%Y-%m"))
    ap.add_argument("--ledger", default=str(LEDGER))
    args = ap.parse_args()

    year, mon = args.month.split("-")
    month_name = MONTHS[int(mon)]
    recs = load_month(Path(args.ledger), args.month)
    if not recs:
        print(f"No ledger records for {args.month} — skipping brief.")
        # still refresh index from any existing briefs
    BRIEFS.mkdir(exist_ok=True)
    if recs:
        a = analyse(recs)
        (BRIEFS / f"{args.month}.html").write_text(
            render_brief(args.month, month_name, year, a, recs), encoding="utf-8")
        print(f"brief: briefs/{args.month}.html — {len(recs)} signals, hottest L{a['hot_layer']}")

    # Rebuild index from all month briefs present on disk.
    entries = []
    for p in sorted(BRIEFS.glob("20*-*.html"), reverse=True):
        key = p.stem
        try:
            y, m = key.split("-")
            rs = load_month(Path(args.ledger), key)
            an = analyse(rs) if rs else {"hot_layer": "—"}
            entries.append((key, MONTHS[int(m)], y, len(rs), an["hot_layer"]))
        except Exception:
            continue
    (BRIEFS / "index.html").write_text(render_index(entries), encoding="utf-8")
    print(f"briefs index: {len(entries)} month(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
