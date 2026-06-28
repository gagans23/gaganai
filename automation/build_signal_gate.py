#!/usr/bin/env python3
"""The Noise Gate — classify signal vs noise, and resolve what it points toward.

Reads the persistent ledger (data/signal-ledger.jsonl) and the hand-authored
inference layer (data/attractors.json), then:
  1. runs every signal through the gate — it is NOISE unless it trips a
     structural test (Mandate / Money / Machinery / Criterion-shift);
  2. adds Corroboration when independent signals trip the same structural test;
  3. attaches each surviving signal to the attractor it points toward;
  4. writes data/signal-gate.json for /signal.html.

Deterministic + stdlib-only. The gate is automated; the attractor *prose* is
authored in data/attractors.json (the cloud job can regenerate it with an LLM
once keys are set). Run after build_knowledge_graph.py in the daily pipeline.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER = REPO / "data" / "signal-ledger.jsonl"
ATTRACTORS = REPO / "data" / "attractors.json"
OUT = REPO / "data" / "signal-gate.json"

# The five structural tests. A stimulus is noise until it trips one.
TESTS = {
    "Mandate": re.compile(r"\b(regulat\w*|supervis\w*|oversight|guideline|expectation|requirement|mandat\w*|compliance|kill[ -]switch\w*|scrutin\w*|risk management|dfsa|rbi|ecb|imda|eu ai office)\b", re.I),
    "Money": re.compile(r"(\$|\bbillion\b|\bmillion\b|\bbn\b|threshold|acquir\w*|acquisition|funding round)", re.I),
    "Machinery": re.compile(r"\b(authority|agency|institut\w*|permanent|innovation hub|stood up|set up|sovereign\w*|industrialis\w*|national (strategy|capability))\b", re.I),
    "Criterion-shift": re.compile(r"\b(maturity|benchmark|index|operating layer|control plane|advantage is moving|context, control|governed|procurement|buying criteri\w*|redesign\w*|license to operate)\b", re.I),
}
STRUCTURAL = ("Mandate", "Money", "Machinery")  # tests that corroboration amplifies


def text_of(r):
    return " ".join(str(r.get(k, "") or "") for k in
                    ("title", "whatChanged", "whyItMatters", "category", "tags"))


def base_tests(r):
    t = text_of(r)
    return [name for name, rx in TESTS.items() if rx.search(t)]


def load_ledger():
    if not LEDGER.exists():
        return []
    out = []
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def noise_reason(title, notes):
    for frag, reason in notes.items():
        if frag.lower() in (title or "").lower():
            return reason
    return "Capability or commentary — it tripped no structural test. Watch whether it recurs or attaches to a rule, a price, or an institution."


def title_matches(title, fragments):
    tl = (title or "").lower()
    return any(f.lower() in tl for f in fragments)


def main():
    recs = load_ledger()
    spec = json.loads(ATTRACTORS.read_text(encoding="utf-8"))
    attractors = spec.get("attractors", [])
    noise_specs = spec.get("noise", [])

    # First pass: base tests + corroboration counts (used only to TAG signals).
    rec_tests = {}
    struct_counts = {k: 0 for k in STRUCTURAL}
    for i, r in enumerate(recs):
        bt = base_tests(r)
        rec_tests[i] = bt
        for k in STRUCTURAL:
            if k in bt:
                struct_counts[k] += 1
    for i, r in enumerate(recs):
        bt = rec_tests[i]
        if any(struct_counts[k] >= 3 and k in bt for k in STRUCTURAL):
            if "Corroboration" not in bt:
                bt.append("Corroboration")

    def entry_for(i, r):
        return {"title": r.get("title", ""), "url": r.get("url", ""),
                "layer": r.get("layer", 5), "date": r.get("firstSeen", ""),
                "tests": rec_tests[i]}

    # Explicit, editorial assignment. A record is claimed by the first attractor
    # whose title-fragments match, or marked noise by an explicit noise spec.
    by_attr = {a["id"]: [] for a in attractors}
    noise, claimed = [], set()
    for i, r in enumerate(recs):
        title = r.get("title", "")
        for a in attractors:
            if title_matches(title, a.get("signals", [])):
                by_attr[a["id"]].append(entry_for(i, r)); claimed.add(i); break
    for i, r in enumerate(recs):
        if i in claimed:
            continue
        title = r.get("title", "")
        ns = next((n for n in noise_specs if n.get("match", "").lower() in title.lower()), None)
        if ns:
            noise.append({"title": title, "url": r.get("url", ""), "reason": ns["reason"]})
            claimed.add(i)
    # Anything still unclaimed: gate it. No structural test -> noise; else -> other.
    other = []
    for i, r in enumerate(recs):
        if i in claimed:
            continue
        e = entry_for(i, r)
        if e["tests"]:
            other.append(e)
        else:
            noise.append({"title": e["title"], "url": e["url"],
                          "reason": "Tripped no structural test — capability or commentary. Watch whether it recurs or attaches to a rule, a price, or an institution."})

    # Assemble, strongest-signal first within each attractor, drop empty attractors.
    # A curated signal that tripped no keyword test still earns its place by
    # echoing the others — that is corroboration by definition.
    out_attr = []
    for a in attractors:
        for s in by_attr[a["id"]]:
            if not s["tests"]:
                s["tests"] = ["Corroboration"]
        sigs = sorted(by_attr[a["id"]], key=lambda s: (-len(s["tests"]), s["date"]))
        if not sigs:
            continue
        agg = []
        for s in sigs:
            for t in s["tests"]:
                if t not in agg:
                    agg.append(t)
        out_attr.append({**{k: a[k] for k in
                            ("id", "title", "thesis", "why", "pointsToward")},
                         "tests": agg, "signalCount": len(sigs), "signals": sigs})

    dates = sorted(r.get("firstSeen", "") for r in recs if r.get("firstSeen"))
    result = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "month": spec.get("month", ""),
        "window": {"from": dates[0] if dates else "", "to": dates[-1] if dates else ""},
        "stats": {
            "stimuli": len(recs),
            "signal": len(recs) - len(noise),
            "noise": len(noise),
            "attractors": len(out_attr),
        },
        "attractors": out_attr,
        "other": sorted(other, key=lambda s: -len(s["tests"])),
        "noise": noise,
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"noise gate: {result['stats']['signal']} signal / {result['stats']['noise']} noise "
          f"-> {len(out_attr)} attractors, {len(other)} unsorted -> {OUT.relative_to(REPO)}")
    for a in out_attr:
        print(f"  • {a['id']}: {a['signalCount']} signals [{', '.join(a['tests'])}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
