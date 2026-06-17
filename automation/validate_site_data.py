#!/usr/bin/env python3
"""Validate generated site data before baking or publishing."""
from __future__ import annotations

import json
import re
import sys
import email.utils
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent


def load_js_assignment(path: Path, assignment: str) -> object:
    raw = path.read_text(encoding="utf-8")
    prefix = f"window.{assignment} ="
    if not raw.lstrip().startswith(prefix):
        raise ValueError(f"{path} must start with {prefix!r}")
    body = raw.replace(prefix, "", 1).strip().rstrip(";")
    return json.loads(body)


def is_http_url(value: object) -> bool:
    parsed = urlparse(str(value or "").strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def is_safe_href(value: object) -> bool:
    text = str(value or "").strip()
    parsed = urlparse(text)
    return is_http_url(text) or (bool(text) and not parsed.scheme and not parsed.netloc and not text.startswith(("//", "#")))


def parse_date(value: object, field: str, errors: list[str], context: str) -> None:
    text = str(value or "").strip()
    if not text:
        errors.append(f"{context}: missing {field}")
        return
    for fmt in ("%Y-%m-%d", "%B %d, %Y"):
        try:
            datetime.strptime(text[:10] if fmt == "%Y-%m-%d" else text, fmt)
            return
        except ValueError:
            pass
    try:
        if email.utils.parsedate_to_datetime(text):
            return
    except (TypeError, ValueError):
        pass
    errors.append(f"{context}: invalid {field} {text!r}")


def validate_radar(errors: list[str]) -> None:
    path = ROOT / "data" / "radar-signals.js"
    data = load_js_assignment(path, "GAGANAI_RADAR")
    if not isinstance(data, dict):
        errors.append("data/radar-signals.js: payload must be an object")
        return

    parse_date(data.get("reviewed"), "reviewed", errors, "radar")
    signals = data.get("signals")
    if not isinstance(signals, list) or not signals:
        errors.append("radar: signals must be a non-empty list")
        return

    seen_urls: set[str] = set()
    required = ["title", "date", "source", "url", "whatChanged", "whyItMatters", "readThrough"]
    for index, signal in enumerate(signals, start=1):
        context = f"radar.signals[{index}]"
        if not isinstance(signal, dict):
            errors.append(f"{context}: must be an object")
            continue
        for field in required:
            if not str(signal.get(field) or "").strip():
                errors.append(f"{context}: missing {field}")
        if not is_http_url(signal.get("url")):
            errors.append(f"{context}: url must be http(s)")
        url = str(signal.get("url") or "").strip()
        if url in seen_urls:
            errors.append(f"{context}: duplicate url {url}")
        seen_urls.add(url)
        parse_date(signal.get("date"), "date", errors, context)
        for field in ("score", "newsQuality"):
            if field in signal:
                try:
                    value = int(signal[field])
                except (TypeError, ValueError):
                    errors.append(f"{context}: {field} must be numeric")
                    continue
                if not 0 <= value <= 100:
                    errors.append(f"{context}: {field} must be between 0 and 100")

    chatter = data.get("marketChatter") or []
    if not isinstance(chatter, list):
        errors.append("radar.marketChatter: must be a list")
    for index, item in enumerate(chatter, start=1):
        if isinstance(item, dict) and item.get("url") and not is_http_url(item.get("url")):
            errors.append(f"radar.marketChatter[{index}]: url must be http(s)")


def validate_podcasts(errors: list[str]) -> None:
    path = ROOT / "data" / "podcast-intelligence.js"
    data = load_js_assignment(path, "GAGANAI_PODCASTS")
    if not isinstance(data, dict):
        errors.append("data/podcast-intelligence.js: payload must be an object")
        return
    for collection in ("shows", "episodes", "themes", "lens"):
        if not isinstance(data.get(collection), list):
            errors.append(f"podcasts.{collection}: must be a list")
    for collection in ("shows", "episodes"):
        for index, item in enumerate(data.get(collection) or [], start=1):
            if not isinstance(item, dict):
                errors.append(f"podcasts.{collection}[{index}]: must be an object")
                continue
            for field in ("source", "youtube"):
                if item.get(field) and not is_http_url(item.get(field)):
                    errors.append(f"podcasts.{collection}[{index}]: {field} must be http(s)")


def validate_archive(errors: list[str]) -> None:
    path = ROOT / "data" / "signal-archive.json"
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    articles = data.get("articles") if isinstance(data, dict) else None
    if not isinstance(articles, list):
        errors.append("signal-archive: articles must be a list")
        return
    for index, article in enumerate(articles, start=1):
        if isinstance(article, dict):
            url = article.get("source_url") or article.get("url")
            if url and not is_safe_href(url):
                errors.append(f"signal-archive.articles[{index}]: url must be http(s) or a safe relative path")


def validate_sitemap(errors: list[str]) -> None:
    path = ROOT / "sitemap.xml"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    if not re.search(r"<loc>https://[^<]+</loc>", text):
        errors.append("sitemap.xml: expected at least one https <loc>")


def main() -> int:
    errors: list[str] = []
    for check in (validate_radar, validate_podcasts, validate_archive, validate_sitemap):
        try:
            check(errors)
        except Exception as exc:
            errors.append(f"{check.__name__}: {exc}")

    if errors:
        print("Site data validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Site data validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
