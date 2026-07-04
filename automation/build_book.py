#!/usr/bin/env python3
"""Build the book's PDF and EPUB from the single source HTML.

Source of truth: agentic-ai/the-curious-minds-guide-to-agentic-ai.html
Outputs (overwritten in place):
  agentic-ai/The-Curious-Minds-Guide-to-Agentic-AI.pdf
  agentic-ai/The-Curious-Minds-Guide-to-Agentic-AI.epub

Why this shape:
  - PDF  = system Chrome `--print-to-pdf` on the HTML → inline SVG stays vector, crisp.
  - EPUB = every figure's inline <svg> is rasterised to a PNG (via Chrome), the SVG is
    swapped for an <img>, and pandoc assembles the chaptered EPUB. Raster PNGs render in
    EVERY reader (Kindle included), not just SVG-capable ones — that's the "images end to
    end" guarantee.

Requires: Google Chrome (macOS app), pandoc. stdlib-only otherwise.
Run:  python3 automation/build_book.py
"""
import html
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BOOK = REPO / "agentic-ai" / "the-curious-minds-guide-to-agentic-ai.html"
COVER = REPO / "agentic-ai" / "book-cover-digital.png"
PDF_OUT = REPO / "agentic-ai" / "The-Curious-Minds-Guide-to-Agentic-AI.pdf"
EPUB_OUT = REPO / "agentic-ai" / "The-Curious-Minds-Guide-to-Agentic-AI.epub"
BUILD = REPO / "agentic-ai" / ".bookbuild"          # scratch (gitignored)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link href="https://fonts.googleapis.com/css2?'
         'family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;0,9..144,700;1,9..144,400'
         '&family=Spectral:ital,wght@0,400;0,500;0,600;1,400'
         '&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">')


def chrome(*args):
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--hide-scrollbars", *args],
                   check=True, capture_output=True, timeout=120)


def main():
    if not BOOK.exists():
        sys.exit(f"missing {BOOK}")
    if not Path(CHROME).exists():
        sys.exit("Google Chrome not found — needed to render PDF and rasterise figures.")
    if not shutil.which("pandoc"):
        sys.exit("pandoc not found — `brew install pandoc`.")

    if BUILD.exists():
        shutil.rmtree(BUILD)
    media = BUILD / "media"
    media.mkdir(parents=True)
    src = BOOK.read_text(encoding="utf-8")

    # ---- 1. PDF straight from the HTML (vector SVG) --------------------------
    print("• rendering PDF (Chrome, vector figures)…")
    chrome("--no-pdf-header-footer", "--run-all-compositor-stages-before-draw",
           "--virtual-time-budget=12000",
           f"--print-to-pdf={PDF_OUT}", BOOK.resolve().as_uri())
    print(f"  → {PDF_OUT.name} ({PDF_OUT.stat().st_size//1024} KB)")

    # ---- 2. rasterise every figure's SVG → PNG ------------------------------
    # Pull the book's <style> so figures rasterise with the real look, and the
    # EPUB keeps the book's typography.
    style = re.search(r"<style>(.*?)</style>", src, re.S)
    css = style.group(1) if style else ""

    def strip_at_blocks(text, at_rule):
        """Remove every `@media print{...}`-style block, brace-counted
        (EPUB CSS parsers reject @page margin boxes inside them)."""
        while True:
            i = text.find(at_rule)
            if i < 0:
                return text
            j = text.find("{", i)
            depth, k = 1, j + 1
            while depth and k < len(text):
                depth += {"{": 1, "}": -1}.get(text[k], 0)
                k += 1
            text = text[:i] + text[k:]
    css = strip_at_blocks(css, "@media print")
    css += ("\n/* EPUB-only additions (see step 3b) */\n"
            "h1.pdtitle{font-family:Fraunces,Georgia,serif;font-weight:700;"
            "font-size:2em;line-height:1.12;margin:1.6em 0 .3em}\n"
            ".pdtag-e{font-family:'IBM Plex Mono',monospace;font-size:.72em;"
            "letter-spacing:.18em;text-transform:uppercase;color:#C2862A;margin:0 0 .9em}\n"
            ".chapsub{font-family:Spectral,Georgia,serif;font-style:italic;"
            "color:#5C6675;margin:-.4em 0 1.1em;font-size:1.05em}\n")
    (BUILD / "book.css").write_text(css, encoding="utf-8")

    fig_re = re.compile(r'(<div class="canvas">\s*)(<svg\b.*?</svg>)(\s*</div>)', re.S | re.I)
    figs = list(fig_re.finditer(src))
    print(f"• rasterising {len(figs)} figures → PNG (Chrome, 2x)…")

    def svg_meta(svg):
        vb = re.search(r'viewbox="[\d.]+ [\d.]+ ([\d.]+) ([\d.]+)"', svg, re.I)
        w, h = (float(vb.group(1)), float(vb.group(2))) if vb else (720.0, 300.0)
        al = re.search(r'aria-label="(.*?)"', svg, re.I)
        return w, h, (html.unescape(al.group(1)) if al else "Diagram")

    DISPLAY_W = 760           # px; ×2 device scale → 1520px PNGs
    PAD = 16
    replacements = []         # (full_match_span, new_html)
    for i, m in enumerate(figs):
        svg = m.group(2)
        w, h, alt = svg_meta(svg)
        disp_h = round(DISPLAY_W * h / w)
        win_w, win_h = DISPLAY_W + 2 * PAD, disp_h + 2 * PAD
        wrapper = (f"<!doctype html><meta charset='utf-8'>{FONTS}"
                   f"<style>html,body{{margin:0}}body{{background:#FBFAF8;padding:{PAD}px}}"
                   f"svg{{display:block;width:{DISPLAY_W}px;height:auto}}</style>{svg}")
        wpath = BUILD / f"_wrap{i}.html"
        wpath.write_text(wrapper, encoding="utf-8")
        png = media / f"fig{i}.png"
        chrome("--force-device-scale-factor=2", "--virtual-time-budget=6000",
               f"--window-size={win_w},{win_h}", f"--screenshot={png}", wpath.as_uri())
        wpath.unlink()
        alt_esc = html.escape(alt, quote=True)
        replacements.append((m.start(2), m.end(2),
                             f'<img src="media/fig{i}.png" alt="{alt_esc}" '
                             f'style="display:block;width:100%;height:auto"/>'))
        print(f"  fig{i}: {png.stat().st_size//1024} KB  ({alt[:44]}…)")

    # ---- 3. EPUB source HTML: swap each inline SVG for its PNG ---------------
    out, cur = [], 0
    for s, e, img in replacements:
        out.append(src[cur:s]); out.append(img); cur = e
    out.append(src[cur:])
    epub_src = "".join(out)

    # ---- 3b. reshape for a professionally-structured EPUB --------------------
    # Web chrome has no business inside an ebook.
    epub_src = re.sub(r'<div class="readbar"></div>\s*', "", epub_src)
    epub_src = re.sub(r'<a href="\.\./" class="sitebar".*?</a>\s*', "", epub_src, flags=re.S)
    epub_src = re.sub(r'<button class="printbtn".*?</button>\s*', "", epub_src, flags=re.S)
    # The reader app supplies the cover; drop the in-content cover plate.
    epub_src = re.sub(r'<div class="coverpage">.*?</div>\s*', "", epub_src, count=1, flags=re.S)
    # pandoc only splits files on TOP-LEVEL <h1>. The part dividers bury their
    # <h1 class="pdtitle"> inside wrapper divs, so unwrap each divider into
    # top-level blocks -> one EPUB file per part + a real nested TOC.
    def _part(m):
        pid, tag, title, deck, sub = m.groups()
        # Part I's divider re-states the book title; in a reader's TOC that
        # reads as a duplicate — use its subtitle as the part name instead.
        if sub and "Curious Mind" in title:
            title, sub = sub, None
        meta = f"{tag} · {sub}" if sub else tag
        return (f'<h1 class="pdtitle" id="{pid}">{title}</h1>\n'
                f'<p class="pdtag-e"><strong>{meta}</strong></p>\n'
                f'<p class="pddeck">{deck}</p>\n')
    epub_src, nparts = re.subn(
        r'<section class="partdivider" id="(part-\d+)">\s*<div class="pdinner">\s*'
        r'<div class="pdtag">(.*?)</div>\s*<h1 class="pdtitle">(.*?)</h1>\s*'
        r'<p class="pddeck">(.*?)</p>\s*(?:<div class="pdsub">(.*?)</div>\s*)?'
        r'</div>\s*</section>', _part, epub_src, flags=re.S)
    print(f"  epub reshape: {nparts} part dividers promoted to split points")
    # Chapter subtitles inside <h2> would pollute the TOC — move them below.
    epub_src, nsubs = re.subn(
        r'(<h2 class="chap">)([^<]*)<span class="sub">(.*?)</span></h2>',
        r'\1\2</h2>\n<p class="chapsub"><em>\3</em></p>', epub_src, flags=re.S)
    print(f"  epub reshape: {nsubs} chapter subtitles moved out of headings")
    # Same nesting rule applies to the nav TOC: chapter <h2>s must be top-level
    # to appear nested under their part. Unwrap each numbered-chapter section,
    # carrying its anchor id onto the heading (in-book TOC links keep working).
    def _chapter(m):
        cid, inner = m.groups()
        return inner.replace('<h2 class="chap">', f'<h2 class="chap" id="{cid}">', 1)
    epub_src, nchaps = re.subn(
        r'<section id="(s\d+-ch\d+)">(.*?)</section>', _chapter, epub_src, flags=re.S)
    print(f"  epub reshape: {nchaps} chapters unwrapped for the nav TOC")
    # Layout-only containers (<div class="wrap">, <div class="appendix">) still
    # nest the chapter <h2>s, hiding them from pandoc's nav. Strip each such div
    # AND its matching closer with a small stack walk (regex can't pair tags).
    def strip_layout_wrappers(s, classes=("wrap", "appendix")):
        out, pos, stack, dropped = [], 0, [], 0
        for t in re.finditer(r"<(/?)div\b([^>]*)>", s, re.I):
            out.append(s[pos:t.start()])
            if not t.group(1):                      # opening <div>
                cls = re.search(r'class="([^"]*)"', t.group(2))
                hit = bool(cls and set(cls.group(1).split()) & set(classes))
                stack.append(hit)
                if hit:
                    dropped += 1
                    # keep any anchor id alive so in-book links stay valid
                    anchor = re.search(r'id="([^"]*)"', t.group(2))
                    if anchor:
                        out.append(f'<span id="{anchor.group(1)}"></span>')
                else:
                    out.append(t.group(0))
            else:                                    # closing </div>
                if not (stack and stack.pop()):
                    out.append(t.group(0))
            pos = t.end()
        out.append(s[pos:])
        assert not stack, "unbalanced <div> nesting while stripping wrappers"
        return "".join(out), dropped
    epub_src, nwraps = strip_layout_wrappers(epub_src)
    print(f"  epub reshape: {nwraps} layout wrappers stripped")
    # Website-relative links don't resolve inside an ebook.
    epub_src = epub_src.replace('href="../"', 'href="https://gagansachdeva.com/"')
    (BUILD / "book.html").write_text(epub_src, encoding="utf-8")

    # ---- 4. pandoc → chaptered EPUB with embedded PNGs ----------------------
    print("• assembling EPUB (pandoc, raster images, chaptered nav)…")
    subprocess.run([
        "pandoc", str(BUILD / "book.html"), "-f", "html", "-t", "epub3",
        "-o", str(EPUB_OUT), "--toc", "--toc-depth=2", "--split-level=1",
        "--css", str(BUILD / "book.css"),
        f"--epub-cover-image={COVER}",
        "--metadata", "title=The Curious Mind's Guide to Agentic AI",
        "--metadata", "author=Gagan Sachdeva",
        "--metadata", "lang=en",
        "--metadata", "publisher=The Philosophical Ledger",
    ], check=True, cwd=str(BUILD), capture_output=True, timeout=180)
    print(f"  → {EPUB_OUT.name} ({EPUB_OUT.stat().st_size//1024} KB)")

    shutil.rmtree(BUILD)
    print("done.")


if __name__ == "__main__":
    main()
