#!/usr/bin/env python3
"""Bake data/search-index.json — the corpus behind /search.html ("Ask the Ledger").

Sources (all already canonical elsewhere):
  - essays        data/writing.json + each essay's body text
  - book          agentic-ai/the-curious-minds-guide-to-agentic-ai.html
                  (parts, chapters, glossary terms)
  - directions    data/attractors.json (the Signal decision briefs)

Entry shape: {t: title, h: href, k: kind, s: snippet, x: extra lowercase match text}
kinds: essay | part | chapter | term | direction

Also indexes: data/signal-ledger.jsonl (verified moves, daily), briefs/*.html,
and key site pages. The daily-intelligence workflow reruns this after the gate,
so the moves stay fresh without manual rebakes. Manual rebake:
    python3 automation/build_search_index.py
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BOOK = REPO / "agentic-ai" / "the-curious-minds-guide-to-agentic-ai.html"
OUT = REPO / "data" / "search-index.json"

TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")


def text_of(html_fragment, limit=None):
    t = WS.sub(" ", TAG.sub(" ", html_fragment)).strip()
    t = (t.replace("&amp;", "&").replace("&#8217;", "'").replace("&#8216;", "'")
         .replace("&#8220;", '"').replace("&#8221;", '"').replace("&#8212;", "—")
         .replace("&mdash;", "—").replace("&middot;", "·").replace("&rarr;", "→")
         .replace("&lt;", "<").replace("&gt;", ">").replace("&nbsp;", " ")
         .replace("&#183;", "·").replace("&#8211;", "–"))
    return t[:limit] if limit else t


def main():
    items = []

    # ── essays ──────────────────────────────────────────────────────────────
    manifest = json.loads((REPO / "data" / "writing.json").read_text(encoding="utf-8"))
    for e in manifest["items"]:
        body = ""
        try:
            src = (REPO / e["href"]).read_text(encoding="utf-8")
            m = re.search(r"<main.*?>(.*?)</main>", src, re.S) or re.search(r"<article.*?>(.*?)</article>", src, re.S)
            if m:
                inner = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", m.group(1), flags=re.S)
                body = text_of(inner, 3200).lower()
        except OSError:
            pass
        items.append({"t": e["title"], "h": e["href"], "k": "essay",
                      "s": (e.get("summary") or "")[:200],
                      "x": " ".join(filter(None, [e.get("category", "").lower(), body]))})

    # ── book: parts, chapters, glossary ─────────────────────────────────────
    book = BOOK.read_text(encoding="utf-8")
    book_href = "agentic-ai/the-curious-minds-guide-to-agentic-ai.html"
    for m in re.finditer(
            r'<section class="partdivider" id="(part-\d+)">.*?<h1 class="pdtitle">(.*?)</h1>.*?<p class="pddeck">(.*?)</p>',
            book, re.S):
        items.append({"t": f"Book · {text_of(m.group(2))}", "h": f"{book_href}#{m.group(1)}",
                      "k": "part", "s": text_of(m.group(3), 180), "x": ""})
    for m in re.finditer(r'<section id="(s\d+-ch\d+)">(.*?)</section>', book, re.S):
        sec = m.group(2)
        h2 = re.search(r'<h2 class="chap">(.*?)</h2>', sec, re.S)
        if not h2:
            continue
        title = text_of(re.sub(r'<span class="sub">.*?</span>', "", h2.group(1), flags=re.S))
        p = re.search(r"<p[^>]*>(.*?)</p>", sec, re.S)
        body = re.sub(r"<(script|style|svg)[^>]*>.*?</\1>", " ", sec, flags=re.S)
        items.append({"t": f"Book · {title}", "h": f"{book_href}#{m.group(1)}", "k": "chapter",
                      "s": text_of(p.group(1), 180) if p else "",
                      "x": text_of(body, 2000).lower()})
    gloss = re.search(r'<dl class="gloss">(.*?)</dl>', book, re.S)
    if gloss:
        for dt, dd in re.findall(r"<dt>(.*?)</dt>\s*<dd>(.*?)</dd>", gloss.group(1), re.S):
            items.append({"t": f"Glossary · {text_of(dt)}", "h": f"{book_href}#s9-ch3",
                          "k": "term", "s": text_of(dd, 180), "x": text_of(dd, 400).lower()})

    # ── signal directions ────────────────────────────────────────────────────
    try:
        attractors = json.loads((REPO / "data" / "attractors.json").read_text(encoding="utf-8"))
        for a in attractors.get("attractors", []):
            items.append({"t": f"Signal · {a['title']}", "h": f"signal.html#attractor-{a['id']}",
                          "k": "direction", "s": (a.get("decision") or a.get("thesis") or "")[:200],
                          "x": " ".join([a.get("thesis", ""), a.get("why", "")])[:600].lower()})
    except (OSError, json.JSONDecodeError):
        pass

    # ── verified moves: the evidence ledger (updated daily by the pipeline) ──
    ledger = REPO / "data" / "signal-ledger.jsonl"
    if ledger.exists():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not r.get("title") or not r.get("url"):
                continue
            when = r.get("firstSeen") or ""
            why = (r.get("whyItMatters") or r.get("whatChanged") or "")[:170]
            items.append({"t": r["title"][:140], "h": r["url"], "k": "move",
                          "s": f"{when} — {why}" if when else why,
                          "x": " ".join(filter(None, [
                              str(r.get("whatChanged", "")), str(r.get("category", "")),
                              str(r.get("desk", "")), " ".join(r.get("entities") or []),
                              " ".join(r.get("tags") or [])]))[:700].lower()})

    # ── monthly briefs ───────────────────────────────────────────────────────
    for bf in sorted((REPO / "briefs").glob("2*.html")):
        html = bf.read_text(encoding="utf-8")
        t = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
        para = re.search(r"<p[^>]*>(.*?)</p>", html, re.S)
        body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S)
        items.append({"t": f"Brief · {text_of(t.group(1)) if t else bf.stem}",
                      "h": f"briefs/{bf.name}", "k": "brief",
                      "s": text_of(para.group(1), 180) if para else "",
                      "x": text_of(body, 1500).lower()})

    # ── site pages (discoverability: 'podcasts', 'about', 'graph'…) ─────────
    for page in ["about.html", "my-books.html", "podcasts.html", "books.html",
                 "graph.html", "signal.html", "radar.html", "agentic-ai/index.html"]:
        f = REPO / page
        if not f.exists():
            continue
        html = f.read_text(encoding="utf-8")
        t = re.search(r"<title>(.*?)</title>", html, re.S)
        desc = re.search(r'<meta name="description" content="(.*?)"', html, re.S)
        items.append({"t": text_of(t.group(1)).split("·")[0].strip() if t else page,
                      "h": page, "k": "page",
                      "s": text_of(desc.group(1), 180) if desc else "",
                      "x": (text_of(desc.group(1), 300).lower() if desc else "")})

    out = {"generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "items": items}
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    kinds = {}
    for i in items:
        kinds[i["k"]] = kinds.get(i["k"], 0) + 1
    print(f"search index: {len(items)} entries {kinds} -> {OUT.relative_to(REPO)} "
          f"({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
