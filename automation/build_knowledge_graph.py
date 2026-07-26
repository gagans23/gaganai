#!/usr/bin/env python3
"""Build the AI Situation Room knowledge graph.

Accumulates a persistent ledger of every curated daily signal, then derives a
graph of entities (companies, models, people, places), themes and the five
Jensen-Huang layers, with the edges between them. The graph powers the
interactive /graph.html explorer and the month-end "connect the dots" brief.

stdlib-only and idempotent — safe to run every day (in CI or locally). Running
twice on the same data produces the same ledger and the same graph.

Inputs : data/radar-signals.js  (today's curated signals — the gold source)
         data/signal-ledger.jsonl (persistent, one JSON object per signal)
Outputs: data/signal-ledger.jsonl (appended, deduped)
         data/knowledge-graph.json (rebuilt from the full ledger)

Keep LAYER_RE / classify_layer in lockstep with automation/render_radar.py.
"""
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SIGNALS_JS = REPO / "data" / "radar-signals.js"
LEDGER = REPO / "data" / "signal-ledger.jsonl"
GRAPH = REPO / "data" / "knowledge-graph.json"

# ---------------------------------------------------------------- layers ----
# Mirror of render_radar.py. L5 is the default sink.
LAYERS = [
    (5, "Agents & Applications"),
    (4, "Models & Intelligence"),
    (3, "AI Factories & Cloud"),
    (2, "Silicon & Networks"),
    (1, "Energy & Power"),
]
LAYER_RE = {
    1: re.compile(r"\b(energy|power plants?|gigawatts?|megawatts?|nuclear|electricity|grid)\b"),
    2: re.compile(r"\b(chips?|semiconductors?|gpus?|silicon|tsmc|chip fabs?|fabrication|foundr(?:y|ies)|wafers?|ai accelerators?|export controls?)\b"),
    3: re.compile(r"\b(data cent(?:re|er)s?|datacenters?|ai factor(?:y|ies)|hyperscalers?|cloud regions?|compute capacity|sovereign compute|colocation|ai infrastructure|infrastructure buildouts?)\b"),
    4: re.compile(r"\b(frontier|open[- ]weights?|model (?:launch|release|upgrade|update|famil\w+|roadmap)s?|(?:coding|reasoning|foundation|multimodal) models?|training runs?|benchmarks?|fine[- ]tun\w*|gpt[- ]?[\d o.]*\d|gemini|claude|opus|sonnet|haiku|llama|deepseek|qwen|grok)\b"),
}


def classify_layer(sig):
    text = f"{sig.get('title','')} {sig.get('whatChanged','')} {sig.get('desk','')}".lower()
    for layer in (1, 2, 3):
        if LAYER_RE[layer].search(text):
            return layer
    if sig.get("desk") == "Compute & Infrastructure":
        return 3
    if LAYER_RE[4].search(text):
        return 4
    return 5


# ---------------------------------------------------------------- entities --
# Curated lexicon: canonical label -> (type, alias-regex). Order matters only
# for readability; matching is independent. Kept deliberately focused on the
# AI x GCC x financial-services beat this radar covers. Extend as the beat moves.
def _alts(*words):
    return re.compile(r"\b(" + "|".join(words) + r")\b", re.I)

ENTITY_LEXICON = {
    # Frontier labs / models
    "OpenAI": ("lab", _alts("openai")),
    "Anthropic": ("lab", _alts("anthropic")),
    "Claude": ("model", _alts("claude")),
    "Google DeepMind": ("lab", _alts("deepmind", "google deepmind")),
    "Gemini": ("model", _alts("gemini")),
    "GPT": ("model", _alts("gpt-?\\d?\\w*", "chatgpt")),
    "Llama": ("model", _alts("llama")),
    "Mistral": ("lab", _alts("mistral")),
    "xAI": ("lab", _alts("xai", "grok")),
    "DeepSeek": ("lab", _alts("deepseek")),
    "Cohere": ("lab", _alts("cohere")),
    "Alibaba": ("bigtech", _alts("alibaba", "alibaba cloud")),
    "Qwen": ("model", _alts("qwen")),
    "Meta": ("bigtech", _alts("meta", "facebook")),
    # Big tech / cloud
    "Google": ("bigtech", _alts("google", "alphabet", "google cloud")),
    "Microsoft": ("bigtech", _alts("microsoft", "azure")),
    "Amazon": ("bigtech", _alts("amazon", "aws")),
    "Nvidia": ("chip", _alts("nvidia")),
    "AMD": ("chip", _alts("amd")),
    "TSMC": ("chip", _alts("tsmc")),
    "Intel": ("chip", _alts("intel")),
    "Oracle": ("bigtech", _alts("oracle")),
    "Salesforce": ("enterprise", _alts("salesforce")),
    "ServiceNow": ("enterprise", _alts("servicenow")),
    "SAP": ("enterprise", _alts("\\bsap\\b")),
    "IBM": ("enterprise", _alts("\\bibm\\b")),
    # Consulting
    "Accenture": ("consulting", _alts("accenture")),
    "Deloitte": ("consulting", _alts("deloitte")),
    "McKinsey": ("consulting", _alts("mckinsey")),
    "PwC": ("consulting", _alts("pwc")),
    "BCG": ("consulting", _alts("\\bbcg\\b", "boston consulting")),
    "EY": ("consulting", _alts("\\bey\\b", "ernst . young")),
    # Banks / financial services
    "HSBC": ("bank", _alts("hsbc")),
    "JPMorgan": ("bank", _alts("jpmorgan", "jp morgan", "chase")),
    "Citi": ("bank", _alts("citi", "citigroup", "citibank")),
    "Goldman Sachs": ("bank", _alts("goldman")),
    "Morgan Stanley": ("bank", _alts("morgan stanley")),
    "Emirates NBD": ("bank", _alts("emirates nbd")),
    "First Abu Dhabi Bank": ("bank", _alts("first abu dhabi", "\\bfab\\b")),
    "Mashreq": ("bank", _alts("mashreq")),
    "Saudi National Bank": ("bank", _alts("saudi national bank", "\\bsnb\\b")),
    "Al Rajhi": ("bank", _alts("al rajhi")),
    "Standard Chartered": ("bank", _alts("standard chartered")),
    "QNB": ("bank", _alts("qnb", "qatar national bank")),
    "ADCB": ("bank", _alts("adcb", "abu dhabi commercial bank")),
    "ADIB": ("bank", _alts("adib", "abu dhabi islamic bank")),
    "Dubai Islamic Bank": ("bank", _alts("dubai islamic bank")),
    "NBK": ("bank", _alts("nbk", "national bank of kuwait")),
    "Bank Muscat": ("bank", _alts("bank muscat")),
    "Riyad Bank": ("bank", _alts("riyad bank")),
    "DBS": ("bank", _alts("dbs")),
    "Bank of America": ("bank", _alts("bank of america", "bofa")),
    "Wells Fargo": ("bank", _alts("wells fargo")),
    "UBS": ("bank", _alts("ubs")),
    "BNP Paribas": ("bank", _alts("bnp paribas", "bnp")),
    "Santander": ("bank", _alts("santander")),
    # GCC sovereign / national champions
    "G42": ("gcc", _alts("\\bg42\\b")),
    "Mubadala": ("gcc", _alts("mubadala")),
    "PIF": ("gcc", _alts("\\bpif\\b", "public investment fund")),
    "stc": ("gcc", _alts("\\bstc\\b")),
    "e&": ("gcc", _alts("etisalat", "e& ")),
    "ADNOC": ("gcc", _alts("adnoc")),
    "Aramco": ("gcc", _alts("aramco")),
    "Humain": ("gcc", _alts("humain")),
    "Core42": ("gcc", _alts("core42")),
    "Presight": ("gcc", _alts("presight")),
    "ADIA": ("gcc", _alts("adia", "abu dhabi investment authority")),
    "QIA": ("gcc", _alts("qia", "qatar investment authority")),
    # Places
    "UAE": ("place", _alts("uae", "united arab emirates", "abu dhabi", "dubai")),
    "Saudi Arabia": ("place", _alts("saudi arabia", "\\bksa\\b", "riyadh")),
    "United States": ("place", _alts("\\bu\\.?s\\.?a?\\b", "united states", "washington")),
    "European Union": ("place", _alts("\\beu\\b", "european union", "brussels")),
    "China": ("place", _alts("china", "beijing")),
    "United Kingdom": ("place", _alts("\\buk\\b", "united kingdom", "london", "britain")),
    # Cross-cutting tech concepts (small set; themes carry most of this)
    "Agents": ("concept", _alts("agents?", "agentic")),
    "Governance": ("concept", _alts("governance", "guardrails?", "kill[- ]switch\\w*", "oversight")),
    "Sovereign AI": ("concept", _alts("sovereign ai", "sovereign compute", "national ai")),
}

ENTITY_TYPE_RANK = {  # for tie-break / display only
    "lab": 0, "model": 1, "bigtech": 2, "chip": 3, "bank": 4,
    "gcc": 5, "consulting": 6, "enterprise": 7, "place": 8, "concept": 9,
}


def signal_text(sig):
    return " ".join(str(sig.get(k, "")) for k in
                     ("title", "whatChanged", "whyItMatters", "readThrough",
                      "category", "region", "desk")) + " " + " ".join(sig.get("tags", []) or [])


def extract_entities(sig):
    text = signal_text(sig)
    found = []
    for label, (etype, rx) in ENTITY_LEXICON.items():
        if rx.search(text):
            found.append(label)
    return found


# ---------------------------------------------------------------- ledger ----
def load_signals_js(path):
    if not path.exists():
        return None, []
    src = path.read_text(encoding="utf-8")
    m = re.search(r"window\.GAGANAI_RADAR\s*=\s*(\{.*\})\s*;?\s*$", src, re.S)
    if not m:
        return None, []
    data = json.loads(m.group(1))
    return data.get("reviewed"), data.get("signals", []) or []


def ledger_key(sig):
    # A signal is the same story across days if url+title match.
    return (sig.get("url", ""), sig.get("title", ""))


def append_today_to_ledger(reviewed, signals):
    """Append today's signals to the persistent ledger, deduped by (url,title)
    keeping the earliest-seen date so 'firstSeen' is stable."""
    seen = {}
    if LEDGER.exists():
        for line in LEDGER.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            seen[(rec.get("url", ""), rec.get("title", ""))] = rec

    added = 0
    for sig in signals:
        key = ledger_key(sig)
        rec = {
            "url": sig.get("url", ""),
            "title": sig.get("title", ""),
            "category": sig.get("category", ""),
            "theme": sig.get("theme", ""),
            "region": sig.get("region", ""),
            "tags": sig.get("tags", []) or [],
            "score": sig.get("score", 0),
            "desk": sig.get("desk", ""),
            "layer": classify_layer(sig),
            "entities": extract_entities(sig),
            "signalDate": sig.get("date", ""),
            "whatChanged": (sig.get("whatChanged", "") or "")[:400],
            "whyItMatters": (sig.get("whyItMatters", "") or "")[:400],
        }
        if key in seen:
            # keep earliest firstSeen, refresh the rest
            rec["firstSeen"] = seen[key].get("firstSeen", reviewed)
            rec["lastSeen"] = reviewed
            seen[key] = rec
        else:
            rec["firstSeen"] = reviewed
            rec["lastSeen"] = reviewed
            seen[key] = rec
            added += 1

    # Rewrite ledger sorted by firstSeen for stable diffs.
    recs = sorted(seen.values(), key=lambda r: (r.get("firstSeen", ""), r.get("title", "")))
    LEDGER.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n",
                      encoding="utf-8")
    return recs, added


# ---------------------------------------------------------------- graph -----
def build_graph(recs):
    layer_label = {n: lbl for n, lbl in LAYERS}

    ent_count = defaultdict(int)
    ent_type = {}
    ent_layers = defaultdict(lambda: defaultdict(int))
    ent_themes = defaultdict(lambda: defaultdict(int))
    ent_first = {}
    ent_last = {}
    ent_score = defaultdict(int)
    theme_count = defaultdict(int)
    layer_count = defaultdict(int)
    co_edges = defaultdict(int)  # (a,b) sorted -> weight

    for r in recs:
        ents = r.get("entities", []) or []
        layer = r.get("layer", 5)
        theme = r.get("theme", "")
        layer_count[layer] += 1
        if theme:
            theme_count[theme] += 1
        for e in ents:
            ent_count[e] += 1
            ent_type[e] = ENTITY_LEXICON.get(e, ("concept", None))[0]
            ent_layers[e][layer] += 1
            ent_score[e] += int(r.get("score", 0) or 0)
            if theme:
                ent_themes[e][theme] += 1
            fs = r.get("firstSeen", "")
            ls = r.get("lastSeen", "")
            ent_first.setdefault(e, fs)
            ent_last[e] = ls
        for a, b in combinations(sorted(set(ents)), 2):
            co_edges[(a, b)] += 1

    nodes = []
    for e, c in ent_count.items():
        dominant_layer = max(ent_layers[e], key=ent_layers[e].get) if ent_layers[e] else 5
        nodes.append({
            "id": e,
            "type": ent_type.get(e, "concept"),
            "count": c,
            "score": ent_score[e],
            "layer": dominant_layer,
            "themes": sorted(ent_themes[e], key=ent_themes[e].get, reverse=True),
            "firstSeen": ent_first.get(e, ""),
            "lastSeen": ent_last.get(e, ""),
        })
    nodes.sort(key=lambda n: (-n["count"], -n["score"], n["id"]))

    edges = [{"source": a, "target": b, "weight": w}
             for (a, b), w in sorted(co_edges.items(), key=lambda kv: -kv[1])]

    graph = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "stats": {
            "articles": len(recs),
            "entities": len(nodes),
            "edges": len(edges),
        },
        "layers": [{"id": n, "label": layer_label[n], "count": layer_count.get(n, 0)}
                   for n, _ in LAYERS],
        "themes": [{"id": t, "count": c}
                   for t, c in sorted(theme_count.items(), key=lambda kv: -kv[1])],
        "nodes": nodes,
        "edges": edges,
    }
    return graph


def main():
    reviewed, signals = load_signals_js(SIGNALS_JS)
    if not signals:
        print("No signals found in data/radar-signals.js — nothing to do.", file=sys.stderr)
        # Still (re)build graph from existing ledger if present.
        if not LEDGER.exists():
            return 0
        recs = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]
        GRAPH.write_text(json.dumps(build_graph(recs), ensure_ascii=False, indent=2) + "\n")
        return 0

    recs, added = append_today_to_ledger(reviewed, signals)
    graph = build_graph(recs)
    GRAPH.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"knowledge graph: {len(recs)} ledger records (+{added} new), "
          f"{graph['stats']['entities']} entities, {graph['stats']['edges']} edges "
          f"-> {GRAPH.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
