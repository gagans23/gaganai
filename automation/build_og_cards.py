#!/usr/bin/env python3
"""Generate a branded 1200x630 Open Graph card for every essay.

Reads data/writing.json (the essays manifest) and renders one dark editorial
card per essay — Fraunces title on the site's premium dark gradient, mono
kicker/byline in amber — into assets/og/<slug>.png via headless Chrome.

Run after adding an essay to data/writing.json:
    python3 automation/build_og_cards.py            # builds missing cards
    python3 automation/build_og_cards.py --force    # rebuilds all

Then point the essay's og:image / twitter:image / JSON-LD image at
https://gagansachdeva.com/assets/og/<slug>.png (1200x630).
"""
import argparse
import html
import json
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "data" / "writing.json"
OUT = REPO / "assets" / "og"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link href="https://fonts.googleapis.com/css2?'
         'family=Fraunces:opsz,wght@9..144,600;9..144,700'
         '&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">')

CARD = """<!doctype html><meta charset="utf-8">{fonts}
<style>
  html,body{{margin:0;padding:0}}
  body{{width:1200px;height:630px;overflow:hidden;
    background:
      radial-gradient(circle at 82% 10%,rgba(213,154,83,.20),transparent 34%),
      linear-gradient(145deg,#070a0b,#111719 62%,#0a0d0e);
    font-family:'IBM Plex Mono',monospace;color:#f8f3e8;position:relative}}
  .grid{{position:absolute;inset:0;opacity:.16;
    background-image:linear-gradient(rgba(248,243,232,.09) 1px,transparent 1px),
      linear-gradient(90deg,rgba(248,243,232,.09) 1px,transparent 1px);
    background-size:46px 46px;
    -webkit-mask-image:linear-gradient(135deg,transparent,black 32%,transparent 88%)}}
  .card{{position:relative;height:100%;box-sizing:border-box;padding:58px 64px 52px;
    display:flex;flex-direction:column;justify-content:space-between}}
  .top{{display:flex;justify-content:space-between;align-items:center;gap:24px}}
  .kicker{{font-size:20px;font-weight:600;letter-spacing:.2em;color:#d59a53}}
  .chip{{font-size:16px;font-weight:500;letter-spacing:.12em;text-transform:uppercase;
    color:#d59a53;border:1.5px solid rgba(213,154,83,.55);border-radius:999px;
    padding:8px 18px;background:rgba(213,154,83,.08);white-space:nowrap}}
  h1{{margin:0;font-family:'Fraunces',Georgia,serif;font-weight:700;
    font-size:{title_px}px;line-height:1.04;letter-spacing:-.015em;max-width:1010px}}
  .bottom{{display:flex;justify-content:space-between;align-items:baseline;gap:24px;
    border-top:1px solid rgba(248,243,232,.18);padding-top:26px}}
  .byline{{font-size:19px;letter-spacing:.03em;color:rgba(248,243,232,.68)}}
  .byline b{{color:#f8f3e8;font-weight:600}}
  .site{{font-size:19px;font-weight:600;letter-spacing:.06em;color:#d59a53}}
</style>
<body><div class="grid"></div><div class="card">
  <div class="top"><span class="kicker">THE PHILOSOPHICAL LEDGER</span><span class="chip">{category}</span></div>
  <h1>{title}</h1>
  <div class="bottom"><span class="byline"><b>Gagan Sachdeva</b> &nbsp;&middot;&nbsp; {date} &nbsp;&middot;&nbsp; {mins}</span><span class="site">gagansachdeva.com</span></div>
</div></body>"""


def title_size(t):
    n = len(t)
    if n <= 26:
        return 92
    if n <= 40:
        return 76
    if n <= 58:
        return 64
    return 54


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="rebuild existing cards")
    args = ap.parse_args()

    items = json.loads(MANIFEST.read_text(encoding="utf-8"))["items"]
    OUT.mkdir(parents=True, exist_ok=True)
    built = skipped = 0
    for e in items:
        slug = Path(e["href"]).stem
        png = OUT / f"{slug}.png"
        if png.exists() and not args.force:
            skipped += 1
            continue
        page = CARD.format(
            fonts=FONTS,
            title_px=title_size(e["title"]),
            category=html.escape(e.get("category") or "Field note"),
            title=html.escape(e["title"]),
            date=html.escape(e.get("dateLabel") or ""),
            mins=html.escape(e.get("readTime") or ""),
        )
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
            f.write(page)
            tmp = Path(f.name)
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                        "--hide-scrollbars", "--force-device-scale-factor=1",
                        "--virtual-time-budget=6000", "--window-size=1200,630",
                        f"--screenshot={png}", tmp.as_uri()],
                       check=True, capture_output=True, timeout=90)
        tmp.unlink()
        print(f"  built assets/og/{slug}.png ({png.stat().st_size // 1024} KB)")
        built += 1
    print(f"og cards: {built} built, {skipped} up to date")


if __name__ == "__main__":
    main()
