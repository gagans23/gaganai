#!/usr/bin/env python3
"""Bake writing-feed.xml — the RSS feed for the Writing section.

Source of truth: data/writing.json (same manifest that drives the homepage
"latest field note" card). feed.xml remains the AI Situation Room's feed;
this one carries the essays. Regenerate whenever an essay is published:
    python3 automation/build_writing_feed.py
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "data" / "writing.json"
OUT = REPO / "writing-feed.xml"
SITE = "https://gagansachdeva.com"


def rfc822(date_str):
    """YYYY-MM-DD (or YYYY-MM) -> RFC 822 pubDate at 06:00 GMT."""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
    except (TypeError, ValueError):
        try:
            d = datetime.strptime(date_str, "%Y-%m")
        except (TypeError, ValueError):
            return None
    d = d.replace(hour=6, tzinfo=timezone.utc)
    return d.strftime("%a, %d %b %Y %H:%M:%S GMT")


def main():
    items = json.loads(MANIFEST.read_text(encoding="utf-8"))["items"]
    entries = []
    newest = None
    for e in items:
        link = f"{SITE}/{e['href']}"
        pub = rfc822(e.get("date"))
        if pub and newest is None:
            newest = pub  # manifest is newest-first
        entries.append(
            "  <item>\n"
            f"    <title>{escape(e['title'])}</title>\n"
            f"    <link>{escape(link)}</link>\n"
            f"    <guid isPermaLink=\"true\">{escape(link)}</guid>\n"
            + (f"    <pubDate>{pub}</pubDate>\n" if pub else "")
            + (f"    <category>{escape(e['category'])}</category>\n" if e.get("category") else "")
            + f"    <description>{escape(e.get('summary') or '')}</description>\n"
            "  </item>")
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "<channel>\n"
        "  <title>The Philosophical Ledger — Writing</title>\n"
        f"  <link>{SITE}/writing/index.html</link>\n"
        f'  <atom:link href="{SITE}/writing-feed.xml" rel="self" type="application/rss+xml"/>\n'
        "  <description>Essays and field notes by Gagan Sachdeva on agentic AI, institutional trust, banking, governance, and the operating model of enterprises.</description>\n"
        "  <language>en</language>\n"
        + (f"  <lastBuildDate>{newest}</lastBuildDate>\n" if newest else "")
        + "\n".join(entries)
        + "\n</channel>\n</rss>\n")
    OUT.write_text(xml, encoding="utf-8")
    print(f"writing-feed.xml: {len(entries)} essays, lastBuildDate {newest}")


if __name__ == "__main__":
    main()
