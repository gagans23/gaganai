#!/usr/bin/env python3
"""Bake data/momentum.json — the forward-looking layer of the Situation Room.

The gate answers "what is true now". This answers "where is it heading" using only
what is already in the ledger:

  1. trajectory   per established direction: trailing-14d vs prior-14d volume, plus how
                  many DISTINCT actors and regions are pushing it. Independent actors
                  repeating a move is the strongest structural tell we have.
  2. forming      clusters among signals that passed the gate but have NOT yet bound to
                  a direction. These are the candidate directions — what is assembling
                  before it is obvious.
  3. precedence   a labelled heuristic: which move type typically precedes which. Money
                  and machinery move before mandates and buying criteria do.

This is structural anticipation, not price prediction, and every claim carries its
evidence count so a thin read is visibly thin.

Rerun after build_signal_gate.py:
    python3 automation/build_momentum.py
"""
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER = REPO / "data" / "signal-ledger.jsonl"
GATE = REPO / "data" / "signal-gate.json"
OUT = REPO / "data" / "momentum.json"

WINDOW_DAYS = 14

# What a passed test usually implies next. Deliberately conservative and labelled as a
# heuristic in the UI — it encodes the ordering Gagan already argues editorially:
# capital and machinery commit first, rules and buying criteria follow.
PRECEDENCE = {
    "Money": "Capital commits before capability exists. Expect capacity, hiring, and "
             "vendor consolidation next — and procurement criteria to move once it lands.",
    "Machinery": "A one-off has become an institution. Permanence is the tell: expect "
                 "standing budget, named owners, and reporting lines to follow.",
    "Mandate": "A rule turned from suggested to required. Expect procurement gates, "
               "audit demands, and evidence requirements to reach vendors next.",
    "Criterion-shift": "What buyers are judged on is changing. Expect roadmaps and "
                       "RFP language to be rewritten around it within a cycle or two.",
    "Corroboration": "Independent actors are repeating the move. This is the signal "
                     "hardening from anecdote into pattern.",
}

# Each established direction is measured against the ledger, not against its own
# curated signal list: attractors own signals editorially (by title fragment), so their
# lists are frozen in time and would always read "dormant". Themes + keywords let new
# evidence count toward the direction it actually supports.
DIRECTION_MATCH = {
    "governance-as-infrastructure": (
        {"responsible-ai"},
        r"\b(governance|regulat|supervis|compliance|audit|central bank|authority|oversight|risk management)\b"),
    "governed-autonomy": (
        {"governed-autonomy", "control-plane"},
        r"\b(agent|autonom|control plane|guardrails?|permission|identity|observability|rollback)\b"),
    "gulf-industrialising": (
        {"gcc-state-capacity"},
        r"\b(uae|saudi|gulf|gcc|abu dhabi|dubai|riyadh|qatar|kuwait|sovereign)\b"),
    "labor-structural": (
        {"workflow-economics"},
        r"\b(jobs?|hiring|layoffs?|workforce|roles?|talent|headcount|labou?r)\b"),
}

# Cluster labels for the unresolved pool: first match wins, so order matters.
CLUSTERS = [
    ("agent-capital", r"\b(raises?|raised|funding|series [a-e]|valuation|unicorn|\$\d+ ?[mb]|billion|million)\b",
     "Capital forming around agent infrastructure"),
    ("agent-security", r"\b(security|guardrails?|prompt injection|red[- ]team|threat|attack|fraud|identity)\b",
     "Agent security and identity becoming a product category"),
    ("agent-payments", r"\b(payments?|transactions?|settlement|billing|commerce|checkout)\b",
     "Payment rails being rebuilt for machine actors"),
    ("compute-buildout", r"\b(data cent(?:re|er)|gigawatt|capacity|chips?|gpus?|nvidia|infrastructure|factory|factories)\b",
     "Compute capacity being committed ahead of demand"),
    ("workforce-redesign", r"\b(jobs?|hiring|layoffs?|workforce|roles?|talent|headcount)\b",
     "Workforce structure being redrawn around agents"),
    ("regulatory-tightening", r"\b(regulat|supervis|compliance|central bank|authority|law|act\b|oversight)\b",
     "Supervisors moving from guidance to expectation"),
    ("enterprise-adoption", r"\b(enterprise|deploy|platform|adoption|workflow|operations?)\b",
     "Agents moving into core enterprise workflow"),
]


def parse_date(value):
    if not value:
        return None
    text = str(value)[:32].strip()
    for fmt in ("%B %d, %Y", "%Y-%m-%d", "%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            dt = datetime.strptime(text, fmt)
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def trend_label(recent, prior):
    """Deliberately blunt: with counts this small, only call a clear move."""
    if recent == 0 and prior == 0:
        return "dormant", "No evidence in either window."
    if prior == 0:
        return "emerging", f"{recent} in the last {WINDOW_DAYS} days, nothing before it."
    ratio = recent / prior
    if ratio >= 1.5:
        return "accelerating", f"{recent} in the last {WINDOW_DAYS} days vs {prior} before."
    if ratio <= 0.5:
        return "cooling", f"{recent} in the last {WINDOW_DAYS} days vs {prior} before."
    return "steady", f"{recent} in the last {WINDOW_DAYS} days vs {prior} before."


def main():
    now = datetime.now(timezone.utc)
    recent_start = now - timedelta(days=WINDOW_DAYS)
    prior_start = now - timedelta(days=WINDOW_DAYS * 2)

    ledger = []
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        try:
            ledger.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    by_title = {(r.get("title") or "").strip().lower(): r for r in ledger}
    gate = json.loads(GATE.read_text(encoding="utf-8"))

    def enrich(sig):
        """Attach ledger context (entities, theme, region) to a gate signal."""
        return by_title.get((sig.get("title") or "").strip().lower(), {})

    # ── 1. trajectory of each established direction ─────────────────────────
    trajectory = []
    for att in gate.get("attractors", []):
        themes, pattern = DIRECTION_MATCH.get(att.get("id"), (set(), r"$^"))
        matcher = re.compile(pattern, re.I)
        recent = prior = 0
        actors, regions = set(), set()
        for row in ledger:
            text = f"{row.get('title','')} {row.get('whatChanged','')} {row.get('category','')} {row.get('theme','')}"
            if row.get("theme") not in themes and not matcher.search(text):
                continue
            when = parse_date(row.get("firstSeen") or row.get("signalDate"))
            if not when:
                continue
            if when >= recent_start:
                recent += 1
                actors.update(row.get("entities") or [])
                if row.get("region"):
                    regions.add(row["region"])
            elif when >= prior_start:
                prior += 1
        trend, detail = trend_label(recent, prior)
        tests = att.get("tests") or []
        trajectory.append({
            "id": att.get("id"),
            "title": att.get("title"),
            "trend": trend,
            "detail": detail,
            "recent": recent,
            "prior": prior,
            "distinctActors": len(actors),
            "distinctRegions": len(regions),
            "signalCount": att.get("signalCount"),
            "whatFollows": PRECEDENCE.get(tests[0], "") if tests else "",
        })

    # ── 2. what is forming in the unresolved pool ───────────────────────────
    buckets = defaultdict(list)
    for sig in gate.get("other", []):
        text = (sig.get("title") or "").lower()
        row = enrich(sig)
        text_full = f"{text} {row.get('whatChanged','')} {row.get('category','')}".lower()
        for cid, pattern, label in CLUSTERS:
            if re.search(pattern, text_full):
                buckets[(cid, label)].append((sig, row))
                break

    forming = []
    for (cid, label), members in buckets.items():
        actors, regions, tests = set(), set(), Counter()
        recent = 0
        for sig, row in members:
            actors.update(row.get("entities") or [])
            if row.get("region"):
                regions.add(row["region"])
            tests.update(sig.get("tests") or [])
            when = parse_date(sig.get("date"))
            if when and when >= recent_start:
                recent += 1
        dominant = tests.most_common(1)[0][0] if tests else ""
        # A cluster is close to binding when several independent actors repeat it.
        if len(members) >= 3 and len(actors) >= 3:
            readiness = "close"
            gap = "Enough independent actors to bind into a direction — needs an editorial read."
        elif len(members) >= 2 and len(actors) >= 2:
            readiness = "building"
            gap = f"{len(members)} signals from {len(actors)} actor(s); one more independent move would harden it."
        else:
            readiness = "early"
            gap = "Single signal — could be noise until something repeats it."
        forming.append({
            "id": cid,
            "label": label,
            "count": len(members),
            "recent": recent,
            "distinctActors": len(actors),
            "distinctRegions": len(regions),
            "dominantTest": dominant,
            "readiness": readiness,
            "gap": gap,
            "whatFollows": PRECEDENCE.get(dominant, ""),
            "examples": [
                {"title": s.get("title"), "url": s.get("url"), "date": s.get("date")}
                for s, _ in sorted(members, key=lambda m: parse_date(m[0].get("date")) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)[:4]
            ],
        })
    order = {"close": 0, "building": 1, "early": 2}
    forming.sort(key=lambda f: (order[f["readiness"]], -f["distinctActors"], -f["count"]))

    # ── 3. where the evidence is concentrating right now ────────────────────
    theme_recent, theme_prior = Counter(), Counter()
    entity_recent = Counter()
    for row in ledger:
        when = parse_date(row.get("firstSeen") or row.get("signalDate"))
        if not when:
            continue
        theme = row.get("theme") or row.get("category") or "unclassified"
        if when >= recent_start:
            theme_recent[theme] += 1
            entity_recent.update(row.get("entities") or [])
        elif when >= prior_start:
            theme_prior[theme] += 1

    heat = []
    for theme in set(theme_recent) | set(theme_prior):
        trend, detail = trend_label(theme_recent[theme], theme_prior[theme])
        heat.append({"theme": theme, "recent": theme_recent[theme], "prior": theme_prior[theme],
                     "trend": trend, "detail": detail})
    heat.sort(key=lambda h: (-h["recent"], h["theme"]))

    out = {
        "generated": now.strftime("%Y-%m-%d"),
        "windowDays": WINDOW_DAYS,
        "ledgerRecords": len(ledger),
        "method": ("Trajectory compares the last %d days against the %d before it. A cluster is "
                   "called close only when several independent actors repeat the same structural "
                   "move. Counts are shown so a thin read stays visibly thin." % (WINDOW_DAYS, WINDOW_DAYS)),
        "trajectory": trajectory,
        "forming": forming,
        "heat": heat[:8],
        "movers": [{"entity": e, "count": c} for e, c in entity_recent.most_common(8)],
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"momentum: {len(trajectory)} directions, {len(forming)} forming clusters, "
          f"{len(heat)} themes -> {OUT.relative_to(REPO)}")
    for f in forming[:4]:
        print(f"  • [{f['readiness']}] {f['label']} — {f['count']} signals / {f['distinctActors']} actors")


if __name__ == "__main__":
    main()
