from __future__ import annotations

import argparse
import asyncio
import email.utils
import html
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote_plus, urlparse

import httpx
from mirage import DiskResource, MountMode, Workspace
from parallel import NotFoundError, Parallel


ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = ROOT.parent
# The site repo root: <repo>/automation/gcc-ai-newsletter/run_daily.py -> <repo>.
# (Previously WORKSPACE_ROOT / "gaganai-site", which wrote into a dead-end staging
# dir under automation/ that the publish script never reads.)
SITE_DIR = Path(__file__).resolve().parents[2]
SITE_RADAR_DATA_PATH = SITE_DIR / "assets" / "radar-data.js"
SITE_SIGNALS_DATA_PATH = SITE_DIR / "data" / "signals.json"
SITE_SIGNALS_JS_PATH = SITE_DIR / "data" / "signals.js"
SITE_RICH_RADAR_PATH = SITE_DIR / "data" / "radar-signals.js"
SITE_PODCAST_DATA_PATH = SITE_DIR / "data" / "podcast-intelligence.js"
SITE_SIGNAL_ARCHIVE_PATH = SITE_DIR / "data" / "signal-archive.json"
RESEARCH_DIR = ROOT / "research"
DRAFTS_DIR = ROOT / "drafts"
WHATSAPP_DIR = ROOT / "whatsapp"
PUBLISH_DIR = ROOT / "publish"
IMAGES_DIR = ROOT / "images"
HISTORY_DIR = ROOT / "history"
COVERED_URLS_PATH = HISTORY_DIR / "covered_urls.json"
TARGET_SIGNAL_COUNT = 12
TARGET_GCC_SIGNAL_COUNT = 4
SEARCH_BATCH_SIZE = 4
RSS_ITEMS_PER_QUERY = 8

GCC_OFFICIAL_DOMAINS = (
    "centralbank.ae",
    "sama.gov.sa",
    "qcb.gov.qa",
    "cbb.gov.bh",
    "cma.org.sa",
    "cma.gov.kw",
    "cbo.gov.om",
    "adgm.com",
    "difc.ae",
    "dfsa.ae",
    "qfc.qa",
    "qfcauthority.com",
    "ai.gov.ae",
    "mediaoffice.ae",
    "wam.ae",
    "spa.gov.sa",
    "sdaia.gov.sa",
    "data.gov.sa",
    "mcit.gov.sa",
    "misa.gov.sa",
)

GCC_COMPANY_DOMAINS = (
    "bankfab.com",
    "emiratesnbd.com",
    "mashreq.com",
    "adcb.com",
    "qnb.com",
    "cbq.qa",
    "alrajhibank.com.sa",
    "riyadbank.com",
    "snb.com.sa",
    "bsf.sa",
    "stc.com.sa",
    "eand.com",
    "du.ae",
    "ooredoo.com",
    "g42.ai",
    "core42.ai",
    "presight.ai",
    "khazna.ae",
    "mbzuai.ac.ae",
    "kaust.edu.sa",
    "aramco.com",
    "adnoc.ae",
    "mubadala.com",
    "pif.gov.sa",
    "tadawulgroup.sa",
    "adx.ae",
    "dfm.ae",
    "qe.com.qa",
)

GCC_PRESS_DOMAINS = (
    "thenationalnews.com",
    "the-national.com",
    "arabnews.com",
    "gulfnews.com",
    "khaleejtimes.com",
    "zawya.com",
)

CONSULTING_DOMAINS = (
    "accenture.com",
    "deloitte.com",
    "ey.com",
    "kpmg.com",
    "mckinsey.com",
    "bcg.com",
    "bain.com",
    "oliverwyman.com",
    "pwc.com",
)


SEARCH_LANES = [
    "site:reuters.com OR site:ft.com OR site:bloomberg.com OR site:wsj.com AI agents enterprise governance banking GCC June 2026",
    "site:techcrunch.com OR site:siliconangle.com OR site:fortune.com AI agents enterprise automation banking governance June 2026",
    "site:centralbank.ae OR site:sama.gov.sa OR site:qcb.gov.qa OR site:cbb.gov.bh OR site:cbo.gov.om OR site:cma.gov.kw AI regulation model risk digital assets open finance outsourcing announcement",
    "site:adgm.com OR site:difc.ae OR site:dfsa.ae OR site:qfc.qa OR site:qfcauthority.com AI governance digital assets tokenization fintech licensing announcement",
    "site:spa.gov.sa OR site:ai.gov.ae OR site:sdaia.gov.sa OR site:data.gov.sa OR site:mediaoffice.ae OR site:wam.ae sovereign AI government services national strategy AI infrastructure announcement",
    "site:bankfab.com OR \"First Abu Dhabi Bank\" OR \"FAB\" AI agentic automation digital partnership platform announcement",
    "site:bankfab.com OR site:emiratesnbd.com OR site:mashreq.com OR site:qnb.com OR site:adcb.com AI agentic banking automation compliance operations announcement",
    "site:cbq.qa OR site:alrajhibank.com.sa OR site:riyadbank.com OR site:snb.com.sa OR site:bsf.sa AI banking automation compliance digital transformation announcement",
    "site:g42.ai OR site:core42.ai OR site:presight.ai OR site:khazna.ae OR site:mbzuai.ac.ae OR site:kaust.edu.sa AI models cloud data center inference research announcement",
    "site:stc.com.sa OR site:eand.com OR site:du.ae OR site:ooredoo.com AI cloud data center digital infrastructure partnership announcement",
    "site:aramco.com OR site:adnoc.ae OR site:mubadala.com OR site:pif.gov.sa industrial AI data center sovereign AI partnership announcement",
    "site:tadawulgroup.sa OR site:adx.ae OR site:dfm.ae OR site:qe.com.qa AI data center cloud digital infrastructure listing filing announcement",
    "site:aws.amazon.com OR site:oracle.com OR site:news.microsoft.com OR site:blog.google OR site:cloud.google.com UAE Saudi Qatar Bahrain Kuwait Oman AI cloud region data center announcement",
    "site:thenationalnews.com OR site:arabnews.com OR site:gulfnews.com OR site:khaleejtimes.com OR site:zawya.com GCC AI banking cloud sovereign AI data center announcement",
    "site:accenture.com OR site:deloitte.com OR site:ey.com OR site:kpmg.com OR site:mckinsey.com OR site:bcg.com OR site:bain.com GCC AI banking agentic operations governance consulting announcement",
    "site:linkedin.com/jobs GCC Abu Dhabi Dubai Riyadh Doha AI governance agentic AI jobs hiring",
    "site:careers.openai.com OR site:openai.com/careers OR site:greenhouse.io Abu Dhabi Dubai Riyadh AI jobs policy governance deployment",
    "GCC AI jobs hiring layoffs workforce agentic systems UAE Saudi Qatar Bahrain Kuwait Oman banks telcos sovereign last 48 hours",
    "GCC AI banking fintech cloud sovereign AI procurement enterprise adoption exchange filing partnership last 48 hours",
    "GCC AI engineering blog benchmark GitHub enterprise deployment research Abu Dhabi Riyadh Doha last 48 hours",
    "GCC consulting AI agentic transformation banking risk operating model Accenture Deloitte EY KPMG McKinsey BCG Bain last 48 hours",
]

GLOBAL_CONTEXT_LANES = [
    "site:reuters.com OR site:ft.com OR site:bloomberg.com OR site:wsj.com last 48 hours AI agents enterprise banking governance chips",
    "site:techcrunch.com OR site:siliconangle.com OR site:fortune.com last 48 hours AI agents enterprise banking governance",
    "site:openai.com OR site:anthropic.com OR site:news.microsoft.com OR site:blog.google last 48 hours AI agents enterprise governance announcement",
    "site:anthropic.com OR site:openai.com OR site:deepmind.google OR site:ai.meta.com OR site:mistral.ai OR site:x.ai last 7 days model launch release deprecation discontinued pricing safety capability announcement",
    "site:reuters.com OR site:ft.com OR site:bloomberg.com OR site:theinformation.com OR site:theverge.com last 7 days Anthropic OR OpenAI OR \"Google DeepMind\" OR Mistral model launch deprecation cancellation funding deal leadership",
    "site:goldmansachs.com OR site:morganstanley.com OR site:citigroup.com OR site:hsbc.com OR site:sc.com OR site:dbs.com last 7 days AI agentic banking automation compliance copilot announcement",
    "site:aws.amazon.com OR site:oracle.com OR site:nvidia.com OR site:amd.com last 48 hours AI cloud data center chips inference announcement",
    "site:news.sap.com OR site:servicenow.com OR site:uipath.com OR site:salesforce.com OR site:databricks.com last 48 hours agent studio enterprise AI workflow announcement",
    "site:fisglobal.com OR site:fiserv.com OR site:mastercard.com OR site:visa.com OR site:jpmorgan.com last 48 hours banking AI agentic compliance announcement",
    "site:accenture.com OR site:deloitte.com OR site:ey.com OR site:kpmg.com OR site:mckinsey.com OR site:bcg.com OR site:bain.com last 48 hours AI agents enterprise operating model banking consulting announcement",
    "site:arxiv.org OR site:huggingface.co OR site:github.com last 48 hours agentic AI evals reasoning benchmark enterprise",
    "site:linkedin.com/jobs AI governance agentic AI policy deployment jobs hiring last 48 hours",
    "global AI layoffs hiring jobs workforce agentic systems last 48 hours",
    "global AI governance central bank regulation banking agentic AI announcement last 48 hours",
    "global AI chips compute data center enterprise agents financial services announcement last 48 hours",
    "global AI earnings call automation jobs enterprise adoption last 48 hours",
    "global consulting AI banking agents operating model governance Accenture Deloitte EY KPMG McKinsey BCG Bain last 48 hours",
]

GCC_FEED_QUERIES = [
    "\"UAE\" AI banking regulation agents",
    "\"Saudi Arabia\" AI banking regulation agents",
    "\"GCC\" agentic AI enterprise banking cloud",
    "site:reuters.com UAE Saudi AI banking cloud regulation",
    "site:thenationalnews.com UAE AI OR Saudi AI banking agents",
    "site:zawya.com UAE Saudi AI banks cloud data center",
    "site:centralbank.ae OR site:sama.gov.sa OR site:qcb.gov.qa artificial intelligence banking regulation",
    "site:g42.ai OR site:presight.ai OR site:core42.ai OR site:bankfab.com OR site:emiratesnbd.com AI UAE Abu Dhabi Riyadh",
    "\"First Abu Dhabi Bank\" OR FAB AI agentic digital banking partnership",
    "QNB OR ADCB OR ADIB OR \"Dubai Islamic Bank\" OR \"National Bank of Kuwait\" OR \"Bank Muscat\" AI banking digital",
]

GLOBAL_FEED_QUERIES = [
    "AI agents enterprise governance banking Reuters OR FT OR Bloomberg",
    "AI agent platform enterprise software Microsoft Google OpenAI Anthropic",
    "Anthropic OR OpenAI OR \"Google DeepMind\" OR Mistral OR DeepSeek OR Qwen model launch deprecation discontinued pricing safety news",
    "Goldman Sachs OR JPMorgan OR Morgan Stanley OR Citi OR HSBC AI agentic banking automation",
    "DBS OR \"Bank of America\" OR UBS OR Santander OR \"Wells Fargo\" AI agentic banking automation",
    "AI banking regulation central banks model risk enterprise",
    "AI cloud data centers chips Nvidia Oracle AWS Microsoft Google",
    "AI consulting operating model Accenture Deloitte EY KPMG McKinsey BCG Bain",
    "AI jobs layoffs hiring agentic systems enterprise",
    "site:techcrunch.com OR site:siliconangle.com AI agents enterprise",
    "site:openai.com OR site:anthropic.com OR site:news.microsoft.com AI enterprise announcement",
]


RADAR_THEMES = [
    {
        "id": "control-plane",
        "label": "Agent control planes",
        "body": "Agent platforms are becoming the new enterprise control plane: identity, tools, permissions, memory, observability, and escalation in one governed layer.",
    },
    {
        "id": "gcc-state-capacity",
        "label": "GCC state capacity",
        "body": "The UAE and Saudi Arabia are treating AI as national infrastructure, linking policy, talent, government services, sovereign capability, and regulated-sector adoption.",
    },
    {
        "id": "governed-autonomy",
        "label": "Governed autonomy",
        "body": "The market is moving from AI advice to controlled AI action. Audit, oversight, kill-switches, and runtime policy are becoming buying criteria.",
    },
    {
        "id": "workflow-economics",
        "label": "Workflow economics",
        "body": "The business case is moving from productivity anecdotes to redesigning critical workflows around agents, data, and human accountability.",
    },
    {
        "id": "responsible-ai",
        "label": "Responsible AI",
        "body": "Responsible AI is moving from principles to operating controls: model inventories, risk tiers, human accountability, evals, audit logs, incident response, and board reporting.",
    },
    {
        "id": "banking-execution",
        "label": "Banking execution",
        "body": "Banks are becoming the proving ground for agentic AI because the value is high, the workflows are structured, and the governance bar is unforgiving.",
    },
]

RADAR_LEADERS = [
    {
        "person": "Omar Sultan Al Olama",
        "role": "UAE Minister of State for Artificial Intelligence",
        "region": "GCC",
        "stance": "AI is now a practical societal technology that requires urgent, agile governance.",
        "source": "TIME",
        "url": "https://time.com/6564430/ai-minister-uae/",
        "theme": "gcc-state-capacity",
    },
    {
        "person": "SDAIA leadership",
        "role": "Saudi Data & AI Authority",
        "region": "GCC",
        "stance": "Saudi Arabia is positioning AI as a trusted national capability aligned with Vision 2030.",
        "source": "Saudi Press Agency",
        "url": "https://www.spa.gov.sa/en/N2518770",
        "theme": "gcc-state-capacity",
    },
    {
        "person": "Christian Klein",
        "role": "CEO, SAP",
        "region": "Global",
        "stance": "Enterprise AI is shifting from copilots toward autonomous process execution inside business systems.",
        "source": "SAP News Center",
        "url": "https://news.sap.com/",
        "theme": "workflow-economics",
    },
    {
        "person": "Ashley Kramer",
        "role": "VP Enterprise, OpenAI",
        "region": "Global",
        "stance": "Financial institutions need agents that are secure, governed, and scalable.",
        "source": "OpenAI enterprise commentary",
        "url": "https://openai.com/",
        "theme": "governed-autonomy",
    },
]

RADAR_BANKS = [
    {
        "bank": "First Abu Dhabi Bank",
        "region": "GCC / UAE",
        "status": "Scaling enterprise AI and agentic use cases across operations and client workflows",
        "focus": "Trade, payments, client operations, compliance, technology engineering, talent enablement",
        "governance": "Innovation hub, deployment discipline, productivity and client-experience measurement",
        "source": "FAB",
        "url": "https://www.bankfab.com/",
    },
    {
        "bank": "UAE banking ecosystem",
        "region": "GCC / UAE",
        "status": "Responsible agentic AI coordination across major UAE banks",
        "focus": "Sector readiness, cross-bank learning, safe adoption patterns",
        "governance": "Responsible adoption, ecosystem coordination, banking-sector readiness",
        "source": "EIF / UBF / KPMG",
        "url": "https://eif.gov.ae/",
    },
    {
        "bank": "Saudi financial institutions",
        "region": "GCC / Saudi Arabia",
        "status": "AI adoption is moving from experimentation to execution in core workflows",
        "focus": "Core banking, payments, lending, compliance",
        "governance": "Execution maturity, risk controls, local-market adoption tracking",
        "source": "Finastra",
        "url": "https://www.finastra.com/",
    },
    {
        "bank": "Global financial institutions",
        "region": "Global",
        "status": "Banks are testing agent operating systems for onboarding, compliance, operations, and advisory workflows",
        "focus": "Commercial lending, financial crime, portfolio analysis, employee productivity",
        "governance": "Identity, auditability, safe tool access, and data controls are becoming the gating layer",
        "source": "FIS / Fiserv / Citi / Lloyds",
        "url": "https://www.fisglobal.com/",
    },
]

RADAR_GOVERNANCE = [
    {
        "control": "Accountability",
        "question": "Who owns the outcome when an agent recommends, escalates, or acts?",
        "evidence": "Defined accountable owner, approval thresholds, escalation path, incident log",
    },
    {
        "control": "Permission mirroring",
        "question": "Can the agent do only what the human, role, or service account is allowed to do?",
        "evidence": "Identity binding, least privilege, connector scopes, entitlement review",
    },
    {
        "control": "Human control",
        "question": "Which actions are advisory, supervised, delegated, or autonomous?",
        "evidence": "Autonomy tier, human-in-the-loop gates, override and pause controls",
    },
    {
        "control": "Data and memory",
        "question": "What can the agent read, remember, write, and forget?",
        "evidence": "Data lineage, retention policy, memory boundaries, sensitive-data redaction",
    },
    {
        "control": "Evaluation",
        "question": "How do we know the agent is improving without drifting?",
        "evidence": "Golden tasks, regression evals, policy tests, performance and risk metrics",
    },
    {
        "control": "Auditability",
        "question": "Can risk, compliance, and operations reconstruct what happened?",
        "evidence": "Prompt, tool-call, source, decision, approval, and action logs",
    },
]

RADAR_SOURCE_STACK = [
    {
        "type": "Official policy",
        "sources": "UAE AI Office, SDAIA, CBUAE, SAMA, ADGM, DIFC, DFSA, NIST, EU AI Office",
        "cadence": "Daily for alerts; weekly for framework changes",
    },
    {
        "type": "Banks and fintech",
        "sources": "FAB, Emirates NBD, Mashreq, ADCB, HSBC, Saudi banks, FIS, Fiserv, Mastercard, Visa",
        "cadence": "Daily announcements and earnings-cycle review",
    },
    {
        "type": "Enterprise platforms",
        "sources": "OpenAI, Anthropic, Microsoft, Google, AWS, IBM, SAP, Oracle, Salesforce, ServiceNow, UiPath, Glean",
        "cadence": "Daily",
    },
    {
        "type": "Consulting and operating-model signals",
        "sources": "Accenture, Deloitte, EY, KPMG, McKinsey, BCG, Bain, Oliver Wyman, PwC",
        "cadence": "Daily for client deployments, industry notes, operating-model patterns, and sector playbooks",
    },
    {
        "type": "Governance and responsible AI",
        "sources": "NIST AI RMF, ISO/IEC 42001, EU AI Act, IMDA Agentic AI Framework, OWASP Agentic AI guidance",
        "cadence": "Daily scan; monthly control-map review",
    },
    {
        "type": "Newsletters and podcasts",
        "sources": "Latent Space, The Cognitive Revolution, Dwarkesh Podcast, No Priors, TWIML, Practical AI",
        "cadence": "Daily scan for explainers, interviews, and practitioner patterns",
    },
]

MARKET_CHATTER_STACK = [
    {
        "platform": "Hacker News",
        "name": "HN / Builder front page",
        "handle": "news.ycombinator.com",
        "role": "Early builder sentiment, breakout repos, agent tooling, and infrastructure arguments",
        "signal": "Useful for spotting what technical operators are debating before it becomes press coverage.",
        "text": "Watch for agent frameworks, eval tooling, security failures, model releases, and strong engineering pushback.",
        "url": "https://news.ycombinator.com/",
    },
    {
        "platform": "Reddit",
        "name": "r/LocalLLaMA",
        "handle": "r/LocalLLaMA",
        "role": "Model behavior, open-source experimentation, eval chatter, and field reports",
        "signal": "Useful when treated as operator chatter, not as a primary source.",
        "text": "Good for spotting open-model capability shifts, deployment pain, local inference patterns, and practitioner skepticism.",
        "url": "https://www.reddit.com/r/LocalLLaMA/",
    },
    {
        "platform": "Reddit",
        "name": "r/MachineLearning",
        "handle": "r/MachineLearning",
        "role": "Research-adjacent releases, benchmarks, and practitioner reaction",
        "signal": "Useful for seeing what researchers and practitioners think is real versus overclaimed.",
        "text": "Good for checking whether a claimed advance is technically meaningful or just launch language.",
        "url": "https://www.reddit.com/r/MachineLearning/",
    },
    {
        "platform": "GitHub",
        "name": "GitHub Trending",
        "handle": "github.com/trending",
        "role": "Breakout repos, tooling velocity, and infrastructure momentum",
        "signal": "Useful when a repo starts changing builder behavior before it generates enterprise headlines.",
        "text": "Watch repos that cluster around agents, MCP, evals, observability, local inference, and deployment control.",
        "url": "https://github.com/trending",
    },
    {
        "platform": "X",
        "name": "X / AI operator search",
        "handle": "x.com/search",
        "role": "Fast market narrative, founder claims, demos, and practitioner reaction",
        "signal": "Useful for velocity and sentiment, but should sit below reported news until verified.",
        "text": "Use as a live watch window for agent demos, deployment failures, enterprise reactions, and sudden narrative shifts.",
        "url": "https://x.com/search?q=AI%20agents%20enterprise%20governance%20banking&src=typed_query&f=live",
    },
]

WORKFORCE_TRACKER = {
    "label": "Workforce Faultline",
    "headline": "Where AI is cutting headcount, redesigning teams, and opening new roles.",
    "summary": "The jobs story is no longer just layoffs. It is role redesign. Some functions are getting compressed by automation, while new hiring is appearing in AI deployment, governance, security, and operating-model roles.",
    "displacement": [
        {
            "company": "Bolt",
            "region": "Global / Fintech",
            "date": "2026-05-20",
            "impact": "HR department removed; broader staff cuts tied to AI-centric restructuring",
            "whatChanged": "Bolt's leadership defended eliminating HR and operating with a leaner, more AI-centric structure after broader workforce cuts.",
            "whyItMatters": "This is not just a layoff story. It is a signal that some executives now view back-office coordination, people operations, and support functions as redesign targets for AI-first operating models.",
            "roles": "HR, recruiting coordination, people operations, operational support",
            "source": "Fortune / Payments Dive",
            "url": "https://www.paymentsdive.com/news/bolt-layoffs-ai-30-percent-breslow-valuation-drop/817040/",
        },
        {
            "company": "General Motors",
            "region": "Global / Industrial",
            "date": "2026-05-11",
            "impact": "Hundreds of IT jobs cut while shifting toward stronger AI skills",
            "whatChanged": "GM cut more than 10% of its IT workforce and framed the move as part of making room for people with stronger AI capabilities.",
            "whyItMatters": "This is a cleaner read-through for large enterprises: AI is not only automating tasks, it is changing the skill mix companies are willing to pay for.",
            "roles": "Legacy IT operations, generalist delivery, non-AI technical roles",
            "source": "TechCrunch",
            "url": "https://techcrunch.com/2026/05/11/gm-just-laid-off-hundreds-of-it-workers-to-hire-those-with-stronger-ai-skills/",
        },
    ],
    "hiring": [
        {
            "employer": "OpenAI",
            "region": "GCC / Abu Dhabi",
            "date": "2026-05-22",
            "role": "AI Success Engineer",
            "location": "Abu Dhabi, UAE",
            "whyNow": "Customer adoption is creating local demand for deployment, value realization, and operational AI execution in the region.",
            "source": "OpenAI Careers",
            "url": "https://openai.com/careers/search/?q=ai+success",
        },
        {
            "employer": "G42",
            "region": "GCC / Abu Dhabi",
            "date": "2026-05-22",
            "role": "Human Capital Intelligence Agent",
            "location": "Abu Dhabi, UAE",
            "whyNow": "The interesting signal is the role itself: companies are hiring directly around agentic workforce tooling rather than only generic AI engineering.",
            "source": "LinkedIn Jobs",
            "url": "https://www.linkedin.com/jobs/view/4375968509/",
        },
        {
            "employer": "VINCI Energies",
            "region": "GCC / Abu Dhabi",
            "date": "2026-05-22",
            "role": "AI Governance Consultant",
            "location": "Abu Dhabi, UAE",
            "whyNow": "As AI spreads, the labor demand is moving into governance, compliance, and control design, not only model building.",
            "source": "LinkedIn Jobs",
            "url": "https://www.linkedin.com/jobs/view/4334482394/",
        },
        {
            "employer": "OpenAI",
            "region": "Global",
            "date": "2026-05-22",
            "role": "Counsel, AI Policy",
            "location": "Global / legal-policy hiring track",
            "whyNow": "The hiring market is proving that policy, legal, deployment, and safety roles are expanding alongside model capability.",
            "source": "OpenAI Careers",
            "url": "https://openai.com/careers/search/?l=bbd9f7fe-aae5-476a-9108-f25aea8f6cd2",
        },
    ],
    "watchlist": [
        "HR, recruiting, support, and generalist operations are becoming early redesign targets for AI-first cost programs.",
        "AI governance, AI deployment, AI operations, and policy roles are becoming durable hiring categories.",
        "The real signal is not net jobs up or down; it is which functions are being hollowed out and which capabilities are being funded.",
        "Watch GCC banks, sovereign AI companies, and public institutions for local hiring in governance, deployment, and AI operations.",
    ],
}

PODCAST_THEMES = [
    {
        "id": "agent-os",
        "label": "Agent operating systems",
        "body": "Agents become strategically useful when tools, memory, permissions, identity, observability, and handoffs sit in one governed system.",
    },
    {
        "id": "governance",
        "label": "Responsible AI and governance",
        "body": "The serious AI conversation is shifting from principles to controls: autonomy levels, evals, audit logs, safety cases, data boundaries, and accountability.",
    },
    {
        "id": "enterprise",
        "label": "Enterprise workflow redesign",
        "body": "The practical question is not whether AI can answer questions. It is which workflows can be redesigned around AI while preserving trust and ownership.",
    },
    {
        "id": "frontier",
        "label": "Frontier lab worldview",
        "body": "Long-form lab interviews reveal assumptions about scaling, reasoning, timelines, bottlenecks, alignment, compute, and what current systems still cannot do.",
    },
    {
        "id": "capital",
        "label": "Capital and company formation",
        "body": "Founder and investor shows reveal where durable AI companies may form: infrastructure, vertical workflows, model operations, data layers, and agent-native products.",
    },
    {
        "id": "gcc-banking",
        "label": "GCC and banking read-through",
        "body": "The desk translates global AI conversations into implications for GCC institutions: controls, value, sovereignty, data, and customer workflows.",
    },
]

PODCAST_LENS = [
    {"label": "Core claim", "detail": "What is the guest actually arguing, stripped of showmanship?"},
    {"label": "Counterclaim", "detail": "What would a serious skeptic say, and does the episode address it?"},
    {"label": "Transcript evidence", "detail": "Which section, timestamp, or show-note segment supports the claim?"},
    {"label": "Governance implication", "detail": "What changes for risk, controls, accountability, data, or human oversight?"},
    {"label": "Enterprise action", "detail": "What should a bank, platform team, or executive do differently?"},
    {"label": "Timeline link", "detail": "Which radar signal does this conversation explain, confirm, or contradict?"},
]

PODCAST_SHOWS = [
    {
        "name": "Latent Space",
        "lane": "Builders",
        "signal": 95,
        "youtube": "https://www.youtube.com/@LatentSpacePod",
        "source": "https://www.latent.space/podcast",
        "why": "The clearest engineering read on agents, RAG, inference, evals, MCP, product architecture, and AI-native tooling.",
    },
    {
        "name": "Dwarkesh Podcast",
        "lane": "Frontier Labs",
        "signal": 97,
        "youtube": "https://www.youtube.com/@dwarkeshpatel",
        "source": "https://www.dwarkeshpatel.com/",
        "why": "Deep interviews with frontier AI researchers, lab leaders, economists, philosophers, and geopolitical thinkers.",
    },
    {
        "name": "The Cognitive Revolution",
        "lane": "Strategy",
        "signal": 90,
        "youtube": "https://www.youtube.com/@CognitiveRevolutionPodcast",
        "source": "https://www.cognitiverevolution.ai/",
        "why": "Strong bridge between technical progress, business consequences, safety debates, and institutional change.",
    },
    {
        "name": "No Priors",
        "lane": "Capital",
        "signal": 88,
        "youtube": "https://www.youtube.com/@NoPriorsPod",
        "source": "https://www.nopriors.com/",
        "why": "Founder and investor lens on model companies, AI infrastructure, applications, robotics, company building, and go-to-market.",
    },
    {
        "name": "Practical AI",
        "lane": "Applied AI",
        "signal": 78,
        "youtube": "https://www.youtube.com/@PracticalAI",
        "source": "https://changelog.com/practicalai",
        "why": "Grounded operating lens on MLOps, applied AI, developer workflows, and production reality.",
    },
    {
        "name": "The Pragmatic Engineer",
        "lane": "Software Industry",
        "signal": 76,
        "youtube": "https://www.youtube.com/@PragmaticEngineer",
        "source": "https://newsletter.pragmaticengineer.com/",
        "why": "Useful for tracking how AI changes engineering organizations, software labor, developer tools, and platform strategy.",
    },
]

PODCAST_EPISODES = [
    {
        "id": "latent-unsupervised-agent-labs",
        "date": "2026-04-18",
        "show": "Latent Space",
        "title": "AIE Europe Debrief + Agent Labs Thesis",
        "guest": "Latent Space x Unsupervised Learning",
        "category": "Agents",
        "tags": ["Agents", "Builders", "Enterprise"],
        "theme": "agent-os",
        "youtube": "https://www.latent.space/p/unsupervised-learning-2026/",
        "source": "https://www.latent.space/p/unsupervised-learning-2026/",
        "transcriptStatus": "Show notes and episode page with linked source material",
        "coreMessage": "Agent startups are converging around practical workflows, tool use, and productized orchestration rather than abstract AGI claims.",
        "keyPoints": [
            "Agent labs are becoming a category with distinct product and infrastructure needs.",
            "The frontier is less about a single bot and more about workflow ownership.",
            "Enterprise buyers will ask for reliability, control, and integrations before autonomy.",
        ],
        "governanceRead": "Agent products need permissioning, tool boundaries, monitoring, and customer-visible failure modes.",
        "action": "Map internal agent use cases by workflow ownership: who initiates, who approves, what tools are touched, and how failure is escalated.",
    },
    {
        "id": "dwarkesh-2027-intelligence",
        "date": "2026-03-01",
        "show": "Dwarkesh Podcast",
        "title": "2027 Intelligence Explosion",
        "guest": "Daniel Kokotajlo and Scott Alexander",
        "category": "Frontier Labs",
        "tags": ["Frontier Labs", "Governance"],
        "theme": "frontier",
        "youtube": "https://www.youtube.com/watch?v=htOvH12T7mU",
        "source": "https://www.dwarkeshpatel.com/",
        "transcriptStatus": "YouTube episode with public timestamps",
        "coreMessage": "AI timelines, takeoff scenarios, and institutional preparedness shape what governments and companies should build now.",
        "keyPoints": [
            "The episode turns AI forecasting into an institutional planning problem.",
            "Safety, governance, and geopolitical capacity become part of technical strategy.",
            "The valuable lens is scenario planning rather than prediction certainty.",
        ],
        "governanceRead": "Boards need scenario-based AI risk planning, not only model-use policies.",
        "action": "Create an AI preparedness memo with capability thresholds, operating triggers, and board-level decisions.",
    },
    {
        "id": "cognitive-sovereign-ai",
        "date": "2025-08-01",
        "show": "The Cognitive Revolution",
        "title": "Sovereign AI and industrial policy",
        "guest": "Anjney Midha",
        "category": "GCC",
        "tags": ["GCC", "Compute", "Governance"],
        "theme": "gcc-banking",
        "youtube": "https://www.youtube.com/@CognitiveRevolutionPodcast",
        "source": "https://www.cognitiverevolution.ai/",
        "transcriptStatus": "Episode page and YouTube channel references available",
        "coreMessage": "Sovereign AI is about industrial capability: compute, models, talent, data, policy, and strategic autonomy.",
        "keyPoints": [
            "Countries need more than access to APIs if they want strategic AI capacity.",
            "Compute and chips are now policy instruments.",
            "Sovereignty has practical implications for regulated sectors such as banking.",
        ],
        "governanceRead": "GCC institutions should link AI adoption with data residency, cloud region choices, risk appetite, and vendor concentration.",
        "action": "Add sovereignty and third-party dependency fields to every material AI use case.",
    },
    {
        "id": "no-priors-jensen-2026",
        "date": "2026-01-08",
        "show": "No Priors",
        "title": "Reasoning models, robotics, and the AI infrastructure question",
        "guest": "Jensen Huang",
        "category": "Compute",
        "tags": ["Compute", "Capital", "Frontier Labs"],
        "theme": "capital",
        "youtube": "https://www.youtube.com/@NoPriorsPod",
        "source": "https://www.nopriors.com/",
        "transcriptStatus": "Episode summaries available through official channel notes",
        "coreMessage": "The infrastructure story is not over; reasoning, robotics, data centers, and energy constraints keep shaping where AI value can scale.",
        "keyPoints": [
            "AI demand is tied to new forms of compute and energy consumption.",
            "Robotics and reasoning models extend the market beyond chat and code.",
            "The bubble question depends on whether infrastructure converts into productive use cases.",
        ],
        "governanceRead": "Compute strategy has governance implications: cost controls, model access, resilience, and environmental constraints.",
        "action": "Track AI use cases by compute intensity and strategic dependence on external infrastructure.",
    },
    {
        "id": "twiml-production-patterns",
        "date": "2026-01-15",
        "show": "The TWIML AI Podcast",
        "title": "Production ML and enterprise AI patterns",
        "guest": "TWIML guests",
        "category": "Enterprise",
        "tags": ["Enterprise", "Builders"],
        "theme": "enterprise",
        "youtube": "https://www.youtube.com/@twimlai",
        "source": "https://twimlai.com/podcast/twimlai/",
        "transcriptStatus": "Use official episode pages and descriptions for extraction",
        "coreMessage": "Enterprise AI succeeds through data quality, evaluation, deployment practice, and feedback loops more than model choice alone.",
        "keyPoints": [
            "Production ML habits still matter in the GenAI era.",
            "Data and evaluation are the compounding assets.",
            "Reusable patterns matter more than isolated demos.",
        ],
        "governanceRead": "Responsible AI requires a measurable operating model, not just review committees.",
        "action": "Tie every AI system to evaluation metrics, data ownership, and post-deployment monitoring.",
    },
]


@dataclass
class SourceItem:
    title: str
    url: str
    publish_date: str | None
    excerpt: str
    lane: str
    scope: str = "GCC"
    source_type: str = "company"
    confidence: int = 60
    news_quality: int = 50


@dataclass
class SearchBundle:
    results: list
    responses: list
    queries: list


@dataclass
class FeedResult:
    title: str
    url: str
    publish_date: str | None
    excerpts: list[str]


def ensure_dirs():
    for folder in [RESEARCH_DIR, DRAFTS_DIR, WHATSAPP_DIR, PUBLISH_DIR, IMAGES_DIR, HISTORY_DIR]:
        folder.mkdir(parents=True, exist_ok=True)


def read_covered_urls():
    if not COVERED_URLS_PATH.exists():
        return set()
    return set(json.loads(COVERED_URLS_PATH.read_text()))


def write_covered_urls(urls):
    existing = read_covered_urls()
    existing.update(urls)
    COVERED_URLS_PATH.write_text(json.dumps(sorted(existing), indent=2) + "\n")


def response_to_dict(response):
    if isinstance(response, SearchBundle):
        return {
            "queries": response.queries,
            "result_count": len(response.results),
            "responses": response.responses,
        }
    if hasattr(response, "model_dump"):
        return response.model_dump(mode="json")
    if hasattr(response, "dict"):
        return response.dict()
    return {"repr": repr(response)}


def parse_publish_date(publish_date):
    if not publish_date:
        return None
    value = str(publish_date).strip()
    lower = value.lower()
    now = datetime.now(timezone.utc)
    rfc822 = parse_rfc822_date(value)
    if rfc822:
        return rfc822
    if lower == "yesterday":
        return now - timedelta(days=1)
    relative_match = re.match(r"^(\d+)\s+(hour|hours|day|days|minute|minutes)\s+ago$", lower)
    if relative_match:
        amount = int(relative_match.group(1))
        unit = relative_match.group(2)
        if unit.startswith("minute"):
            return now - timedelta(minutes=amount)
        if unit.startswith("hour"):
            return now - timedelta(hours=amount)
        return now - timedelta(days=amount)
    for parser in (
        lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")),
        lambda s: datetime.strptime(s, "%Y-%m-%d"),
        lambda s: datetime.strptime(s, "%Y-%m-%d %H:%M:%S"),
        lambda s: datetime.strptime(s, "%Y/%m/%d"),
        lambda s: datetime.strptime(s, "%d/%m/%Y"),
        lambda s: datetime.strptime(s, "%d/%m/%Y %I:%M:%S %p"),
        lambda s: datetime.strptime(s, "%B %d, %Y"),
        lambda s: datetime.strptime(s, "%b %d, %Y"),
    ):
        try:
            parsed = parser(value)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def maybe_extract_iso_date(text):
    if not text:
        return None
    patterns = [
        r"(20\d{2}-\d{2}-\d{2}(?:[T ][0-2]\d:[0-5]\d(?::[0-5]\d)?(?:Z|[+-][0-2]\d:[0-5]\d)?)?)",
        r"(20\d{2}/\d{2}/\d{2})",
        r"(\d{2}/\d{2}/20\d{2}(?:\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M)?)",
        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+20\d{2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def should_try_resolve_date(url):
    domain = urlparse(url).netloc.lower().removeprefix("www.")
    return source_domain_weight(url) >= 10 or domain.endswith((".gov", ".gov.ae", ".gov.sa", ".ac.ae"))


def resolve_missing_publish_date(url):
    try:
        response = httpx.get(
            url,
            timeout=8.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        text = response.text[:50000]
    except Exception:
        return None

    patterns = [
        r'property="article:published_time"\s+content="([^"]+)"',
        r'name="article:published_time"\s+content="([^"]+)"',
        r'"datePublished"\s*:\s*"([^"]+)"',
        r'<time[^>]+datetime="([^"]+)"',
        r'"dateModified"\s*:\s*"([^"]+)"',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        value = maybe_extract_iso_date(match.group(1))
        if value:
            return value

    return maybe_extract_iso_date(text)


def google_news_rss_url(query):
    encoded = quote_plus(query)
    return f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"


def strip_html_text(value):
    text = re.sub(r"<[^>]+>", " ", value or "")
    return " ".join(html.unescape(text).split())


def parse_rfc822_date(value):
    if not value:
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def build_feed_result(item):
    title = strip_html_text(item.findtext("title", ""))
    if " - " in title:
        title = title.rsplit(" - ", 1)[0].strip()
    link = (item.findtext("link", "") or "").strip()
    publish_date = (item.findtext("pubDate", "") or "").strip()
    description = strip_html_text(item.findtext("description", ""))
    source = item.find("{*}source")
    source_name = strip_html_text(source.text if source is not None else "")
    if source_name and source_name.lower() not in description.lower():
        description = f"{source_name}. {description}".strip()
    return FeedResult(
        title=title,
        url=link,
        publish_date=publish_date,
        excerpts=[description] if description else [],
    )


def fetch_google_news_feed(query):
    url = google_news_rss_url(query)
    response = httpx.get(
        url,
        timeout=12.0,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    response.raise_for_status()
    root = ET.fromstring(response.text)
    items = []
    for element in root.findall("./channel/item")[:RSS_ITEMS_PER_QUERY]:
        items.append(build_feed_result(element))
    return {"query": query, "url": url, "count": len(items)}, items


def fetch_hacker_news_chatter(window_hours):
    cutoff = int((datetime.now(timezone.utc) - timedelta(hours=window_hours)).timestamp())
    queries = ["AI agents", "coding agents", "agentic AI", "MCP", "LLM evals"]
    items = []
    for query in queries:
        url = f"https://hn.algolia.com/api/v1/search_by_date?query={quote_plus(query)}&tags=story&hitsPerPage=8"
        try:
            payload = httpx.get(url, timeout=10.0, headers={"User-Agent": "Mozilla/5.0"}).json()
        except Exception:
            continue
        for hit in payload.get("hits", []):
            created = hit.get("created_at_i") or 0
            title = strip_html_text(hit.get("title") or hit.get("story_title") or "")
            if not title or created < cutoff or not is_chatter_relevant(title):
                continue
            points = hit.get("points") or 0
            comments = hit.get("num_comments") or 0
            object_id = hit.get("objectID")
            items.append(
                {
                    "platform": "Hacker News",
                    "name": title,
                    "handle": f"{points} points / {comments} comments",
                    "role": "Builder discussion",
                    "signal": "Early technical reaction from operators and builders.",
                    "text": "Use this as sentiment and technical challenge data, then verify against primary sources before promoting it as news.",
                    "url": f"https://news.ycombinator.com/item?id={object_id}" if object_id else hit.get("url") or "https://news.ycombinator.com/",
                    "published": datetime.fromtimestamp(created, timezone.utc).strftime("%Y-%m-%d"),
                    "score": min(99, int(points) + int(comments)),
                }
            )
    return sorted(items, key=lambda item: item.get("score", 0), reverse=True)[:4]


def fetch_reddit_chatter(window_hours):
    cutoff = int((datetime.now(timezone.utc) - timedelta(hours=window_hours)).timestamp())
    subreddits = ["LocalLLaMA", "MachineLearning", "singularity", "ArtificialInteligence"]
    query = quote_plus("AI agents OR agentic OR enterprise AI OR model governance OR evals")
    headers = {"User-Agent": "gaganai-radar/1.0"}
    items = []
    for subreddit in subreddits:
        url = f"https://www.reddit.com/r/{subreddit}/search.json?q={query}&restrict_sr=1&sort=new&t=week&limit=8"
        try:
            payload = httpx.get(url, timeout=10.0, headers=headers, follow_redirects=True).json()
        except Exception:
            continue
        for child in payload.get("data", {}).get("children", []):
            post = child.get("data", {})
            title = strip_html_text(post.get("title") or "")
            created = int(post.get("created_utc") or 0)
            if not title or created < cutoff or not is_chatter_relevant(title):
                continue
            comments = int(post.get("num_comments") or 0)
            score = int(post.get("score") or 0)
            permalink = post.get("permalink") or f"/r/{subreddit}/"
            items.append(
                {
                    "platform": "Reddit",
                    "name": title,
                    "handle": f"r/{subreddit} / {score} upvotes / {comments} comments",
                    "role": "Practitioner chatter",
                    "signal": "Useful as field reaction, model behavior evidence, and skepticism around claims.",
                    "text": "Treat as discussion, not reporting. Promote only when it helps explain what operators are testing or resisting.",
                    "url": f"https://www.reddit.com{permalink}",
                    "published": datetime.fromtimestamp(created, timezone.utc).strftime("%Y-%m-%d"),
                    "score": score + comments,
                }
            )
    return sorted(items, key=lambda item: item.get("score", 0), reverse=True)[:4]


def is_chatter_relevant(text):
    lower = text.lower()
    markers = [
        "ai",
        "agent",
        "agentic",
        "llm",
        "mcp",
        "eval",
        "model",
        "inference",
        "rag",
        "coding assistant",
        "copilot",
        "openai",
        "anthropic",
        "gemini",
        "claude",
    ]
    return any(marker in lower for marker in markers)


def build_x_chatter_watch():
    queries = [
        "AI agents enterprise governance banking",
        "agentic AI deployment failure security",
        "GCC AI UAE Saudi agents banking",
    ]
    return [
        {
            "platform": "X",
            "name": query,
            "handle": "live X search",
            "role": "Fast narrative watch",
            "signal": "Useful for demos, founder claims, sudden objections, and sentiment shifts.",
            "text": "X is monitored as a live chatter surface. Claims from this stream need confirmation before becoming front-page news.",
            "url": f"https://x.com/search?q={quote_plus(query)}&src=typed_query&f=live",
            "published": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "score": 1,
        }
        for query in queries
    ]


def fetch_market_chatter(window_hours):
    items = []
    items.extend(fetch_hacker_news_chatter(window_hours))
    items.extend(fetch_reddit_chatter(window_hours))
    items.extend(build_x_chatter_watch())
    if not items:
        return MARKET_CHATTER_STACK
    seen = set()
    deduped = []
    for item in items + MARKET_CHATTER_STACK:
        key = (item.get("platform"), item.get("name"), item.get("url"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped[:10]


def search_feeds(window_hours, global_context=False):
    queries = GLOBAL_FEED_QUERIES if global_context else GCC_FEED_QUERIES
    responses = []
    results = []
    window_start = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    for query in queries:
        try:
            meta, items = fetch_google_news_feed(query)
            fresh_items = []
            for item in items:
                published = parse_rfc822_date(item.publish_date) or parse_publish_date(item.publish_date)
                if published and published < window_start:
                    continue
                fresh_items.append(item)
            meta["fresh_count"] = len(fresh_items)
            responses.append(meta)
            results.extend(fresh_items)
        except Exception as exc:
            responses.append({"query": query, "error": str(exc)})
    return SearchBundle(results=results, responses=responses, queries=list(queries))


def merge_search_bundles(*bundles):
    results = []
    responses = []
    queries = []
    for bundle in bundles:
        if not bundle:
            continue
        results.extend(bundle.results)
        responses.extend(bundle.responses)
        queries.extend(bundle.queries)
    return SearchBundle(results=results, responses=responses, queries=queries)


def format_review_date(issue_date):
    return datetime.fromisoformat(issue_date).strftime("%B %d, %Y")


def load_json_from_git(pathspec):
    try:
        return json.loads(
            subprocess.check_output(
                ["git", "-C", str(SITE_DIR), "show", f"origin/main:{pathspec}"],
                text=True,
            )
        )
    except Exception:
        return None


def load_prior_signals():
    local_payload = []
    if SITE_SIGNALS_DATA_PATH.exists():
        try:
            payload = json.loads(SITE_SIGNALS_DATA_PATH.read_text())
            if isinstance(payload, list) and payload:
                local_payload = payload
        except json.JSONDecodeError:
            pass

    payload = load_json_from_git("data/signals.json")
    if isinstance(payload, list) and len(payload) >= len(local_payload):
        return payload
    return local_payload


def load_prior_archive():
    if SITE_SIGNAL_ARCHIVE_PATH.exists():
        try:
            payload = json.loads(SITE_SIGNAL_ARCHIVE_PATH.read_text())
            if isinstance(payload, dict) and isinstance(payload.get("articles"), list):
                return payload
        except json.JSONDecodeError:
            pass

    payload = load_json_from_git("data/signal-archive.json")
    if isinstance(payload, dict) and isinstance(payload.get("articles"), list):
        return payload
    return {"reviewed": None, "articleCount": 0, "articles": []}


def normalize_results(response, covered_urls, window_start, allow_undated=False, scope="GCC"):
    items = []
    seen_urls = set()
    for result in getattr(response, "results", []):
        url = getattr(result, "url", "")
        if not url or url in covered_urls or url in seen_urls:
            continue

        publish_date = getattr(result, "publish_date", None)
        parsed_date = parse_publish_date(publish_date)
        if not parsed_date and not allow_undated and should_try_resolve_date(url):
            publish_date = resolve_missing_publish_date(url)
            parsed_date = parse_publish_date(publish_date)
        if not parsed_date and not allow_undated:
            continue
        if parsed_date and parsed_date < window_start:
            continue

        excerpts = getattr(result, "excerpts", None) or []
        title = (getattr(result, "title", "") or "").strip()
        excerpt = (excerpts[0] if excerpts else "").strip()
        if not title or not excerpt:
            continue
        if is_low_signal_result(title, excerpt, url):
            continue

        combined_text = f"{title} {excerpt}"
        if not is_topic_relevant(combined_text):
            continue
        item = SourceItem(
            title=title,
            url=url,
            publish_date=publish_date,
            excerpt=excerpt[:900],
            lane=classify_lane(combined_text),
            scope=scope,
            source_type=classify_source_type(url, combined_text),
            confidence=score_confidence(url, combined_text, scope),
            news_quality=news_quality_score(url, title, excerpt),
        )
        if not should_accept_source_item(item):
            continue
        seen_urls.add(url)
        items.append(item)
    return sorted(items, key=item_priority, reverse=True)


def is_topic_relevant(text):
    lower = text.lower()
    ai_markers = [
        " ai ",
        "ai-",
        "artificial intelligence",
        "agent",
        "agentic",
        "llm",
        "model",
        "openai",
        "anthropic",
        "gemini",
        "chatgpt",
        "copilot",
        "vertex ai",
        "machine learning",
        "ml ",
    ]
    has_ai_marker = any(marker in f" {lower} " for marker in ai_markers)
    if not has_ai_marker:
        return False
    false_positive_markers = [
        "gulf business",
        "oil price",
        "wartime",
        "tourism",
        "real estate",
        "sports",
    ]
    return not any(marker in lower for marker in false_positive_markers)


def is_low_signal_result(title, excerpt, url):
    text = f"{title} {excerpt}".lower()
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower().removeprefix("www.")
    path = parsed_url.path.lower()
    generic_titles = [
        "news - dcd",
        "latest news",
        "all news",
        "new models today",
        "enterprise ai news",
        "ai updates today",
    ]
    low_signal_phrases = [
        "no releases in this period",
        "try selecting",
        "subscribe join",
        "feedback",
        "latest ai updates daily",
        "tracks all major language model version releases in real-time",
        "latest gcc news stories",
    ]
    if domain in {"reuters.com", "ft.com", "bloomberg.com", "wsj.com", "techcrunch.com", "siliconangle.com", "fortune.com"}:
        if path.endswith("/") and (
            "latest" in title.lower()
            or "headlines" in title.lower()
            or "find latest" in excerpt.lower()
            or "reuters events" in excerpt.lower()
        ):
            return True
        if domain == "reuters.com" and path in {
            "/business/finance/",
            "/technology/artificial-intelligence/",
            "/world/middle-east/",
            "/technology/",
        }:
            return True
        return False
    if any(title.lower().startswith(prefix) for prefix in generic_titles):
        return True
    if is_blocked_domain(url):
        return True
    if parsed_url.path in {"", "/"}:
        return True
    if any(phrase in text for phrase in low_signal_phrases):
        return True
    if url.rstrip("/").endswith(("/news", "/blog", "/updates")) and len(excerpt) < 240:
        return True
    if excerpt.count("###") >= 2:
        return True
    if excerpt.count("Date:") >= 2:
        return True
    if article_path_weight(url) <= 0 and source_domain_weight(url) < 10:
        return True
    return False


def article_path_weight(url):
    path = urlparse(url).path.lower().strip("/")
    if not path:
        return -4
    segments = [segment for segment in path.split("/") if segment]
    joined = "/".join(segments)
    article_markers = (
        "/article/",
        "/articles/",
        "/news/",
        "/press/",
        "/press-release/",
        "/press-releases/",
        "/blog/",
        "/posts/",
        "/stories/",
        "/briefings/",
        "/features/",
        "/index/",
    )
    if any(marker in f"/{joined}/" for marker in article_markers):
        return 8
    if len(segments) >= 3:
        return 6
    hub_markers = {
        "news",
        "latest",
        "technology",
        "finance",
        "artificial-intelligence",
        "middle-east",
        "world",
        "business",
        "blog",
        "updates",
        "topics",
        "tag",
        "category",
    }
    if segments[-1] in hub_markers:
        return -3
    return 2 if len(segments) >= 2 else -1


def source_domain_weight(url):
    domain = urlparse(url).netloc.lower().removeprefix("www.")
    if domain.endswith(".gov") or domain.endswith(".gov.ae") or domain.endswith(".gov.sa"):
        return 14
    if any(domain.endswith(name) for name in GCC_OFFICIAL_DOMAINS):
        return 14
    if any(domain.endswith(suffix) for suffix in (".org", ".edu")):
        return 7
    preferred = (
        "openai.com",
        "anthropic.com",
        "aws.amazon.com",
        "microsoft.com",
        "google.com",
        "cloud.google.com",
        "oracle.com",
        "nvidia.com",
        "bankfab.com",
        "emiratesnbd.com",
        "mashreq.com",
        "qnb.com",
        "adcb.com",
        "hsbc.com",
        "fisglobal.com",
        "fiserv.com",
        "press.aboutamazon.com",
        "globenewswire.com",
        "news.sap.com",
        "uipath.com",
        "servicenow.com",
        *GCC_COMPANY_DOMAINS,
        *GCC_PRESS_DOMAINS,
        *GCC_OFFICIAL_DOMAINS,
    )
    if any(domain.endswith(name) for name in preferred):
        return 10
    credible_press = (
        "reuters.com",
        "bloomberg.com",
        "ft.com",
        "wsj.com",
        "axios.com",
        "theinformation.com",
        "cnbc.com",
        *GCC_PRESS_DOMAINS,
    )
    if any(domain.endswith(name) for name in credible_press):
        return 6
    return 0


def inferred_source_weight(text):
    lower = text.lower()
    if any(token in lower for token in ["reuters", "financial times", "ft.com", "bloomberg", "wall street journal", "wsj"]):
        return 8
    if any(token in lower for token in ["the national", "arab news", "gulf news", "khaleej times", "zawya"]):
        return 7
    if any(token in lower for token in ["cbuae", "sama", "qcb", "dfsa", "adgm", "difc", "sdaia", "uae ai office"]):
        return 12
    if any(token in lower for token in ["openai", "anthropic", "microsoft", "google cloud", "aws", "oracle", "nvidia"]):
        return 8
    if any(token in lower for token in ["accenture", "deloitte", "mckinsey", "bcg", "bain", "ey", "kpmg", "pwc"]):
        return 7
    return 0


def source_grade(url, source_type):
    domain_score = source_domain_weight(url)
    type_score = source_type_weight(source_type)
    combined = domain_score + type_score
    if combined >= 24:
        return "A"
    if combined >= 18:
        return "B"
    if combined >= 12:
        return "C"
    return "D"


def news_quality_score(url, title, excerpt):
    score = 30
    title_lower = title.lower()
    excerpt_lower = excerpt.lower()
    score += article_path_weight(url) * 4
    score += min(source_domain_weight(url), 14) * 2
    score += min(inferred_source_weight(f"{title} {excerpt}"), 10)
    if any(token in title_lower for token in ["announces", "launches", "rolls out", "expands", "partners", "debuts"]):
        score += 10
    if any(token in excerpt_lower for token in ["today announced", "said on", "according to", "general availability", "rolled out"]):
        score += 8
    if re.search(r"\b\d{4}\b", excerpt):
        score += 4
    if len(excerpt) >= 180:
        score += 4
    if any(token in title_lower for token in ["latest", "headlines", "top", "briefing", "roundup", "digest"]):
        score -= 18
    return max(0, min(score, 100))


def is_blocked_domain(url):
    domain = urlparse(url).netloc.lower().removeprefix("www.")
    blocked_domains = {
        "agbi.com",
        "bingx.com",
        "devflokers.com",
        "economymiddleeast.com",
        "fintech.global",
        "llm-stats.com",
        "rolandberger.com",
        "shakudo.io",
        "thecore.in",
    }
    return domain in blocked_domains


def source_type_weight(source_type):
    return {
        "official": 14,
        "company": 11,
        "jobs": 8,
        "research": 8,
        "developer": 7,
        "investor": 7,
        "press": 6,
        "analysis": 3,
    }.get(source_type, 0)


def should_accept_source_item(item):
    if is_blocked_domain(item.url):
        return False
    if item.confidence < 55:
        return False
    if item.news_quality < 52:
        return False
    if item.source_type != "analysis":
        return article_path_weight(item.url) > 0 or source_domain_weight(item.url) >= 10
    if source_domain_weight(item.url) >= 6:
        return True
    if item.confidence >= 60 and item.scope == "GCC":
        return True
    return False


def lane_weight(item):
    return {
        "Regulators / central banks": 14,
        "Banks": 12,
        "Consulting / advisory": 11,
        "Responsible AI / governance": 11,
        "Cloud / data centers": 10,
        "Jobs / workforce": 10,
        "Government / national AI": 9,
        "Fintech / payments": 8,
        "Research / engineering": 8,
        "AI / enterprise": 7,
        "Models": 5,
        "Industry adoption": 4,
    }.get(item.lane, 0)


def item_priority(item):
    published = parse_publish_date(item.publish_date)
    recency_score = int(published.timestamp()) if published else 0
    return (
        1 if item.scope == "GCC" else 0,
        item.news_quality,
        lane_weight(item),
        item.confidence,
        source_type_weight(item.source_type),
        article_path_weight(item.url),
        source_domain_weight(item.url),
        recency_score,
        len(item.excerpt),
    )


def classify_lane(text):
    text = text.lower()
    if any(
        word in text
        for word in [
            "job",
            "jobs",
            "hiring",
            "career",
            "careers",
            "layoff",
            "layoffs",
            "fired",
            "headcount",
            "workforce",
            "recruiting",
            "talent",
        ]
    ):
        return "Jobs / workforce"
    if any(word in text for word in ["agent", "agentic", "autonomous agents", "control plane", "workflow agent"]):
        return "AI / enterprise"
    if any(
        word in text
        for word in [
            "accenture",
            "deloitte",
            "ey",
            "kpmg",
            "mckinsey",
            "bcg",
            "bain",
            "oliver wyman",
            "pwc",
            "consulting",
            "advisory",
            "operating model",
            "transformation services",
        ]
    ):
        return "Consulting / advisory"
    if any(word in text for word in ["governance", "responsible ai", "model risk", "audit", "oversight", "evaluation", "evals", "policy"]):
        return "Responsible AI / governance"
    if any(word in text for word in ["model", "llm", "gpt", "gemini", "llama", "mistral", "deepseek"]):
        return "Models"
    if any(word in text for word in ["cloud", "data center", "datacenter", "aws", "microsoft", "oracle", "google"]):
        return "Cloud / data centers"
    if any(word in text for word in ["central bank", "sama", "cbuae", "regulator", "regulation"]):
        return "Regulators / central banks"
    if any(word in text for word in ["bank", "fab", "qnb", "hsbc", "citi", "jpmorgan", "standard chartered"]):
        return "Banks"
    if any(word in text for word in ["fintech", "payment", "open banking", "stablecoin", "digital asset"]):
        return "Fintech / payments"
    if any(word in text for word in ["paper", "benchmark", "arxiv", "github", "research", "lab", "evaluation harness"]):
        return "Research / engineering"
    if any(word in text for word in ["government", "ministry", "national", "dubai", "uae", "saudi"]):
        return "Government / national AI"
    if any(word in text for word in ["retail", "energy", "aramco", "aviation", "telecom", "healthcare"]):
        return "Industry adoption"
    return "AI / enterprise"


def classify_source_type(url, text):
    domain = urlparse(url).netloc.lower().removeprefix("www.")
    text = text.lower()
    if (
        domain.endswith(".gov")
        or domain.endswith(".gov.ae")
        or domain.endswith(".gov.sa")
        or any(domain.endswith(name) for name in GCC_OFFICIAL_DOMAINS)
    ):
        return "official"
    if "linkedin.com/jobs" in url or "/careers" in url or "greenhouse.io" in domain or "lever.co" in domain:
        return "jobs"
    if domain in {"arxiv.org", "huggingface.co", "github.com", "mbzuai.ac.ae", "kaust.edu.sa"} or any(
        word in text for word in ["paper", "benchmark", "research", "preprint", "github"]
    ):
        return "research"
    if any(word in text for word in ["engineering blog", "developer", "api", "sdk", "changelog", "release notes"]):
        return "developer"
    if any(word in text for word in ["earnings", "investor", "sec filing", "quarterly results"]):
        return "investor"
    if domain.endswith(
        (
            "openai.com",
            "anthropic.com",
            "microsoft.com",
            "google.com",
            "cloud.google.com",
            "oracle.com",
            "aws.amazon.com",
            "nvidia.com",
            *GCC_COMPANY_DOMAINS,
            *CONSULTING_DOMAINS,
        )
    ):
        return "company"
    if domain.endswith(
        (
            "reuters.com",
            "bloomberg.com",
            "ft.com",
            "wsj.com",
            "axios.com",
            "theinformation.com",
            "cnbc.com",
            "fortune.com",
            "techcrunch.com",
            *GCC_PRESS_DOMAINS,
        )
    ):
        return "press"
    if any(token in text for token in ["reuters", "financial times", "bloomberg", "wall street journal", "the national", "zawya", "techcrunch", "siliconangle"]):
        return "press"
    if any(token in text for token in ["cbuae", "sama", "qcb", "dfsa", "adgm", "difc", "sdaia", "uae ai office"]):
        return "official"
    if any(token in text for token in ["openai", "anthropic", "microsoft", "google cloud", "oracle", "aws", "nvidia", "g42", "presight", "core42"]):
        return "company"
    return "analysis"


def score_confidence(url, text, scope):
    score = 40
    score += source_domain_weight(url)
    score += inferred_source_weight(text)
    score += source_type_weight(classify_source_type(url, text))
    if scope == "GCC":
        score += 4
    if any(word in text.lower() for word in ["announced", "launches", "released", "hiring", "partnership", "opens", "deploys"]):
        score += 6
    return min(score, 96)


def build_search_objective(window_hours):
    return (
        f"Find only credible news or official announcements from the last {window_hours} hours "
        "about AI, agentic AI, cloud, data centers, banking technology, fintech, central banks, "
        "government AI policy, enterprise technology, jobs, layoffs, hiring, engineering releases, "
        "research papers, and procurement signals in the GCC. Cover central banks, local banks, "
        "global banks operating in the GCC, fintech firms, hyperscalers, sovereign AI companies, "
        "consulting firms, systems integrators, and advisory networks, "
        "government announcements, job boards, research labs, and adjacent industries. Prefer primary "
        "sources, regulators, official company announcements, stock exchange filings, engineering blogs, "
        "career pages, GitHub repos, arXiv papers, and credible business press. Exclude evergreen/background "
        "articles unless clearly labeled as context."
    )


def build_global_objective(window_hours):
    return (
        f"Find credible global AI, agentic AI, cloud, chips, banking, fintech, jobs, hiring, layoffs, research, "
        f"and AI regulation developments from the last {window_hours} hours. Focus on items that help explain what "
        "GCC leaders should watch: enterprise agents, AI governance, model validation, sovereign AI, data centers, "
        "cloud infrastructure, financial services AI, labor-market changes, engineering releases, consulting and operating-model shifts, "
        "central bank or regulatory moves, and hyperscaler plays. Prefer primary sources, research artifacts, hiring evidence, advisory notes, "
        "and credible business press. Exclude generic commentary."
    )


def build_parallel_client():
    api_key = os.environ.get("PARALLEL_API_KEY")
    if not api_key:
        raise SystemExit('PARALLEL_API_KEY is not set. Run: export PARALLEL_API_KEY="your_parallel_key"')

    base_url = os.environ.get("PARALLEL_BASE_URL")
    if not base_url:
        gateway_port = os.environ.get("OPENCLAW_GATEWAY_PORT", "").strip()
        if gateway_port:
            base_url = f"http://127.0.0.1:{gateway_port}"

    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return Parallel(**kwargs)


def build_parallel_fallback_client():
    api_key = os.environ.get("PARALLEL_API_KEY")
    if not api_key:
        raise SystemExit('PARALLEL_API_KEY is not set. Run: export PARALLEL_API_KEY="your_parallel_key"')
    return Parallel(api_key=api_key, base_url="https://api.parallel.ai")


def execute_parallel_search(client, kwargs):
    try:
        return client.search(**kwargs)
    except NotFoundError:
        base_url = getattr(client, "base_url", None)
        base_url_str = str(base_url) if base_url is not None else ""
        if "127.0.0.1" not in base_url_str and "localhost" not in base_url_str:
            raise
        print(
            f"Parallel gateway at {base_url_str} returned 404; retrying against https://api.parallel.ai.",
            file=sys.stderr,
        )
        fallback_client = build_parallel_fallback_client()
        return fallback_client.search(**kwargs)


def search_parallel(window_hours, global_context=False):
    prefix = f"last {window_hours} hours"
    lanes = GLOBAL_CONTEXT_LANES if global_context else SEARCH_LANES
    queries = [f"{prefix} {lane}" for lane in lanes]
    objective = build_global_objective(window_hours) if global_context else build_search_objective(window_hours)
    raw_responses = []
    merged_results = []
    try:
        client = build_parallel_client()
        for start in range(0, len(queries), SEARCH_BATCH_SIZE):
            batch_queries = queries[start : start + SEARCH_BATCH_SIZE]
            kwargs = {
                "search_queries": batch_queries,
                "mode": "advanced",
                "advanced_settings": {"max_results": 20},
                "objective": objective,
            }
            response = execute_parallel_search(client, kwargs)
            raw_responses.append(
                {
                    "batch": start // SEARCH_BATCH_SIZE + 1,
                    "queries": batch_queries,
                    "response": response_to_dict(response),
                }
            )
            merged_results.extend(getattr(response, "results", []) or [])
    except BaseException as exc:
        if isinstance(exc, KeyboardInterrupt):
            raise
        raw_responses.append(
            {
                "error": str(exc),
                "kind": "parallel_search",
                "queries": queries,
            }
        )
    return SearchBundle(results=merged_results, responses=raw_responses, queries=queries)


def discover_sources(window_hours, global_context=False):
    parallel_bundle = search_parallel(window_hours, global_context=global_context)
    feed_bundle = search_feeds(window_hours, global_context=global_context)
    return merge_search_bundles(parallel_bundle, feed_bundle)


def strongest_pattern(items):
    lane_counts = {}
    for item in items:
        lane_counts[item.lane] = lane_counts.get(item.lane, 0) + 1
    if not lane_counts:
        return "No major new GCC AI signal cleared the freshness and source filter."
    top_lanes = sorted(lane_counts, key=lane_counts.get, reverse=True)[:3]
    if "Jobs / workforce" in top_lanes:
        return "The GCC AI story is starting to show up in workforce design, not only technology announcements."
    if "Cloud / data centers" in top_lanes and "Banks" in top_lanes:
        return "The GCC AI story is moving from pilots to operating infrastructure."
    if "Consulting / advisory" in top_lanes:
        return "The advisory layer is turning AI from a technology conversation into a workflow redesign conversation."
    if "Regulators / central banks" in top_lanes:
        return "The GCC AI race is becoming a governance race."
    if "Government / national AI" in top_lanes:
        return "GCC governments are turning AI ambition into execution infrastructure."
    return "The strongest GCC AI signal is execution, not hype."


def build_visual_hook(pattern, gcc_items, global_items):
    hooks = [
        "control plane",
        "governed agents",
        "sovereign cloud",
        "regulated data",
        "banking rails",
        "execution layer",
    ]
    if any(item.lane == "Regulators / central banks" for item in gcc_items):
        hooks.insert(0, "validation layer")
    if any(item.lane == "Cloud / data centers" for item in gcc_items + global_items):
        hooks.insert(0, "compute map")
    return f"Visual hook: map the AI stack as {' -> '.join(dict.fromkeys(hooks[:5]))}."


def build_connective_tissue(gcc_items, global_items):
    items = gcc_items + global_items
    if any(item.lane == "Jobs / workforce" for item in items):
        return (
            "The useful read is not only capability progress. It is that AI is changing the operating model, "
            "the control model, and the labor model at the same time."
        )
    if gcc_items and global_items:
        return (
            "The useful read is not that AI news is accelerating. It is that the same pattern is appearing globally "
            "and regionally: agents need infrastructure, infrastructure needs governance, and governance needs proof."
        )
    if gcc_items:
        return (
            "The useful read is regional: GCC AI is becoming less about pilots and more about the operating rails "
            "that let regulated sectors deploy safely."
        )
    if global_items:
        return (
            "The useful read is global context: even when GCC-specific news is thin, the operating model for AI is "
            "being shaped by agents, chips, cloud, governance, and financial-sector controls."
        )
    return "The useful read today is restraint: no credible fresh signal is better than recycled noise."


def build_linkedin_post(gcc_items, global_items, issue_date, window_hours):
    items = gcc_items + global_items
    if not items or (not gcc_items and len(global_items) < 3):
        return (
            "The Philosophical Ledger\n\n"
            f"Today’s {window_hours}-hour scan did not surface enough credible, fresh GCC-first AI signals to force a post.\n\n"
            "That is useful too.\n\n"
            "A serious AI brief should know when not to recycle old news or dress thin global context up as a regional signal.\n\n"
            "Watchlist for tomorrow:\n"
            "- central banks and regulators\n"
            "- banks and fintech\n"
            "- cloud providers and data centers\n"
            "- government AI programs\n"
            "- agentic AI in regulated workflows\n\n"
            "I’ll keep tracking central banks, banking, fintech, cloud, government, and enterprise AI across the region."
        )

    gcc_selected = gcc_items[:5]
    global_selected = global_items[:5]

    gcc_bullets = []
    for item in gcc_selected:
        date = item.publish_date or "date not visible"
        gcc_bullets.append(
            f"- {item.title} ({item.lane}, {date})\n"
            f"  Impact read: {impact_read(item)}"
        )

    global_bullets = []
    for item in global_selected:
        date = item.publish_date or "date not visible"
        global_bullets.append(
            f"- {item.title} ({item.lane}, {date})\n"
            f"  Impact read: {impact_read(item)}"
        )

    source_lines = []
    for item in gcc_selected + global_selected:
        source_lines.append(f"- {item.title}: {item.url}")

    return (
        "The Philosophical Ledger\n\n"
        "Market thesis: the agent control plane is becoming the new cloud region.\n\n"
        "AI is moving from experimentation into controlled execution. That changes the executive question from “Which model should we use?” to “Where can we safely let AI act?”\n\n"
        "GCC MARKET COVERAGE\n\n"
        + ("\n".join(gcc_bullets) if gcc_bullets else "- No fresh GCC-specific item cleared the strict source filter.")
        + "\n\nGLOBAL AI AND AGENTIC MARKET COVERAGE\n\n"
        + ("\n".join(global_bullets) if global_bullets else "- No global context item cleared the strict source filter.")
        + "\n\nCONNECT THE DOTS\n\n"
        "The GCC and global stories are pointing to the same architecture: cloud regions decide where workloads run, enterprise data decides what agents can know, control planes decide what agents can do, and governance decides whether institutions can prove control.\n\n"
        "That is why the next AI race is not simply model versus model. It is control plane versus control plane.\n\n"
        "EXECUTIVE WATCHLIST\n\n"
        "- Central banks and regulators: AI governance, model risk, digital assets, open finance, compliance technology.\n"
        "- Banks and global banks in the GCC: agentic AI in operations, risk, credit, compliance, and client service.\n"
        "- Fintech: payments, regtech, onboarding, fraud, digital assets, SME finance, and embedded AI.\n"
        "- Cloud and infrastructure: regions, data centers, sovereign cloud, chips, and hyperscaler partnerships.\n"
        "- Real economy: energy, retail, aviation, logistics, telecom, healthcare, and government service delivery.\n\n"
        "Leadership question: which workflows are ready for AI to assist, which are ready for AI to act, and which would expose your weakest controls?\n\n"
        "Sources reviewed:\n"
        + "\n".join(source_lines)
    )


def impact_read(item):
    lane = item.lane
    scope = item.scope
    if lane == "Jobs / workforce":
        return "High operating-model impact; watch which functions are being compressed, which skills are being funded, and how fast institutions redesign teams."
    if lane == "Responsible AI / governance":
        return "High control impact; watch evaluation, auditability, risk ownership, and policy translation into runtime controls."
    if lane == "Research / engineering":
        return "Medium-high capability impact; important when it changes deployment options, reliability, evals, or enterprise integration patterns."
    if lane == "Cloud / data centers":
        return "High economy impact; very high sector urgency for regulated AI, sovereign data, cloud procurement, and enterprise platform teams."
    if lane == "Regulators / central banks":
        return "Very high policy impact; immediate urgency for banks, fintechs, model-risk teams, and compliance functions."
    if lane == "Banks":
        return "High financial-sector impact; watch for productivity, operating-risk, customer, credit, and compliance implications."
    if lane == "Fintech / payments":
        return "Medium-high sector impact; watch payments, onboarding, fraud, open finance, and embedded AI distribution."
    if lane == "Government / national AI":
        return "High public-sector impact; watch national AI infrastructure, service delivery, procurement, and digital-government execution."
    if lane == "Industry adoption":
        return "High real-economy impact; watch productivity, downtime reduction, safety, supply chain, and sector transformation."
    if lane == "Models":
        return "Global model-market signal; important when it changes capability, cost, deployment options, or procurement strategy."
    if scope == "Global":
        return "Global context signal; important for GCC leaders because it shapes vendor strategy, governance patterns, and adoption timing."
    return "Medium market impact; track for signal strength, sector relevance, and operating-model implications."


def radar_sector(item):
    mapping = {
        "Cloud / data centers": "Cloud",
        "Regulators / central banks": "Regulation",
        "Banks": "Banking",
        "Jobs / workforce": "Enterprise",
        "Responsible AI / governance": "Regulation",
        "Fintech / payments": "Banking",
        "Government / national AI": "Regulation",
        "Industry adoption": "Enterprise",
        "Research / engineering": "Models",
        "Models": "Models",
        "AI / enterprise": "Agents",
    }
    return mapping.get(item.lane, "Enterprise")


def radar_impact(item):
    base = {
        "Regulators / central banks": 91,
        "Responsible AI / governance": 87,
        "Cloud / data centers": 88,
        "Banks": 86,
        "Consulting / advisory": 82,
        "Jobs / workforce": 84,
        "Fintech / payments": 78,
        "Government / national AI": 84,
        "Research / engineering": 79,
        "Industry adoption": 76,
        "Models": 72,
        "AI / enterprise": 74,
    }.get(item.lane, 72)
    if item.scope == "GCC":
        base += 4
    return min(base, 96)


def radar_horizon(item):
    if item.lane in {"Regulators / central banks", "Banks"}:
        return "0-12 months"
    if item.lane in {"Jobs / workforce", "Responsible AI / governance"}:
        return "0-12 months"
    if item.lane in {"Cloud / data centers", "Government / national AI"}:
        return "0-24 months"
    return "0-18 months"


def radar_implication(item):
    if item.lane == "Jobs / workforce":
        return "The labor signal is shifting from headline layoffs to which functions are being redesigned and which control-heavy roles are being funded."
    if item.lane == "Responsible AI / governance":
        return "Governance is becoming implementation work: evals, audit logs, policies, approvals, and human accountability embedded into the stack."
    if item.lane == "Consulting / advisory":
        return "Consulting signals matter when they show how large enterprises are packaging AI into operating-model change, controls, and sector-specific transformation programs."
    if item.lane == "Research / engineering":
        return "Research and engineering artifacts matter when they shorten the path from capability to deployable enterprise systems."
    if item.lane == "Cloud / data centers":
        return "Infrastructure choices are becoming strategy choices: they decide which regulated AI workloads can actually run."
    if item.lane == "Regulators / central banks":
        return "AI governance is moving from policy posture to operating requirement for banks, fintechs, and platform teams."
    if item.lane == "Banks":
        return "The financial-sector AI race is shifting from assistant adoption to governed workflow execution."
    if item.lane == "Fintech / payments":
        return "Payments, onboarding, fraud, and compliance workflows are becoming early tests for AI-native operating leverage."
    if item.lane == "Government / national AI":
        return "Public-sector AI programs are turning national ambition into procurement, infrastructure, and delivery pressure."
    if item.lane == "Industry adoption":
        return "AI value is moving into real-economy workflows where productivity, resilience, and safety matter."
    if item.lane == "Models":
        return "Model velocity matters most when it changes cost, capability, deployment architecture, or vendor leverage."
    return "The model layer is only one part of the story; advantage is moving toward context, control, evaluation, and distribution."


def radar_action(item):
    if item.lane == "Jobs / workforce":
        return "Track which roles are disappearing, which AI control or deployment roles are opening, and whether your workforce plan matches that shift."
    if item.lane == "Responsible AI / governance":
        return "Convert principles into controls: owner, policy, evaluation, approval gates, monitoring, and incident response."
    if item.lane == "Consulting / advisory":
        return "Separate generic AI messaging from repeatable delivery patterns that regulated institutions could actually adopt this year."
    if item.lane == "Research / engineering":
        return "Test whether the artifact changes cost, evaluation rigor, deployment speed, or private-data options for a real workflow."
    if item.lane == "Cloud / data centers":
        return "Review which AI workloads are blocked by residency, latency, procurement, or third-party-risk constraints."
    if item.lane == "Regulators / central banks":
        return "Map current AI use cases to owner, data, model, decision rights, controls, audit trail, and kill switch."
    if item.lane == "Banks":
        return "Pick one high-value workflow and move it from copilot assistance to measured, governed action."
    if item.lane == "Fintech / payments":
        return "Watch where AI reduces onboarding friction, fraud loss, compliance cost, or transaction handling time."
    if item.lane == "Government / national AI":
        return "Track which announcements become funded platforms, procurement vehicles, and cross-agency operating capacity."
    if item.lane == "Industry adoption":
        return "Look for repeatable operating loops, not isolated demos."
    if item.lane == "Models":
        return "Evaluate whether the update changes a real workflow, not only benchmark posture."
    return "Test the signal against your own workflows: does it change cost, control, speed, or decision quality?"


def signal_category(item):
    mapping = {
        "Cloud / data centers": "Compute & Chips",
        "Regulators / central banks": "Governance & Risk",
        "Responsible AI / governance": "Governance & Risk",
        "Banks": "Financial Services AI",
        "Consulting / advisory": "Enterprise Memory",
        "Jobs / workforce": "Enterprise Memory",
        "Fintech / payments": "Financial Services AI",
        "Government / national AI": "GCC / Middle East" if item.scope == "GCC" else "Governance & Risk",
        "Industry adoption": "Enterprise Memory",
        "Research / engineering": "Research",
        "Models": "Model Intelligence",
        "AI / enterprise": "Agent Execution",
    }
    return mapping.get(item.lane, "Research")


def signal_desk_from_signal(signal):
    category = signal.get("category", "")
    lane = signal.get("lane", "")
    region = signal.get("region", "")
    source_type = signal.get("source_type", "")
    if lane == "Jobs / workforce" or source_type == "jobs":
        return "Workforce Faultline"
    if "Financial Services" in category or lane in {"Banks", "Fintech / payments"}:
        return "Banking AI"
    if lane == "Consulting / advisory":
        return "Enterprise Strategy"
    if "Governance" in category or "Risk" in category or lane in {"Regulators / central banks", "Responsible AI / governance"}:
        return "Governance & Regulation"
    if "Compute" in category or lane == "Cloud / data centers":
        return "Compute & Infrastructure"
    if "Model" in category or "Agent" in category or lane in {"AI / enterprise", "Research / engineering", "Models"}:
        return "Agentic Systems"
    if "GCC" in region or "Middle East" in region or lane == "Government / national AI":
        return "GCC Institutions"
    return "GCC Institutions" if "GCC" in region else "Agentic Systems"


def evidence_strength(signal):
    source_type = signal.get("source_type")
    confidence = int(signal.get("confidence") or 0)
    if source_type == "official" and confidence >= 70:
        return "Very high"
    if source_type in {"company", "jobs", "investor"} and confidence >= 65:
        return "High"
    if source_type in {"press", "research", "developer"} or confidence >= 60:
        return "Medium"
    return "Low"


def gcc_relevance(signal):
    region = signal.get("region") or ""
    desk = signal_desk_from_signal(signal)
    if "GCC" in region or "Middle East" in region:
        return "Direct"
    if desk in {"Banking AI", "Governance & Regulation", "Compute & Infrastructure"}:
        return "High read-through"
    return "Context"


def actionability(signal):
    score = int(signal.get("score") or 0)
    freshness = signal.get("freshness")
    source_type = signal.get("source_type")
    if freshness == "fresh" and source_type in {"official", "company", "jobs", "investor"}:
        return "Immediate"
    if score >= 84:
        return "Near-term"
    return "Watchlist"


def enrich_signal(signal, issue_date, freshness):
    enriched = dict(signal)
    enriched["source_url"] = signal.get("source_url") or signal.get("url")
    enriched["publication_date"] = signal.get("publication_date") or signal.get("date")
    enriched["freshness"] = freshness
    enriched["updated_on"] = issue_date
    return enriched


def merge_signal_payload(primary_signals, prior_signals, issue_date):
    merged = []
    seen = set()
    fresh_gcc = 0
    domain_counts = {}

    def domain_key(signal):
        url = signal.get("source_url") or signal.get("url") or ""
        return urlparse(url).netloc.lower().removeprefix("www.")

    def allowed_from_domain(signal, freshness):
        domain = domain_key(signal)
        if not domain:
            return True
        limit = 1 if freshness == "fresh" else 2
        count = domain_counts.get(domain, 0)
        if source_domain_weight(signal.get("source_url") or signal.get("url") or "") >= 14:
            limit += 1
        if signal.get("desk") == "Banking AI":
            limit += 1
        return count < limit

    def record_domain(signal):
        domain = domain_key(signal)
        if domain:
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

    for signal in primary_signals:
        key = signal.get("url") or signal.get("title")
        if key in seen:
            continue
        if not allowed_from_domain(signal, "fresh"):
            continue
        seen.add(key)
        enriched = enrich_signal(signal, issue_date, "fresh")
        merged.append(enriched)
        record_domain(enriched)
        if "GCC" in (signal.get("region") or ""):
            fresh_gcc += 1

    need_more = len(merged) < TARGET_SIGNAL_COUNT or fresh_gcc < TARGET_GCC_SIGNAL_COUNT
    if not need_more:
        return merged[:TARGET_SIGNAL_COUNT]

    sorted_prior = sorted(prior_signals, key=lambda item: (item.get("score", 0), item.get("date", "")), reverse=True)
    for signal in sorted_prior:
        if is_blocked_domain(signal.get("source_url") or signal.get("url") or ""):
            continue
        if (
            signal.get("source_type") == "analysis"
            and source_domain_weight(signal.get("source_url") or signal.get("url") or "") < 6
            and int(signal.get("confidence") or 0) < 60
        ):
            continue
        key = signal.get("source_url") or signal.get("url") or signal.get("title")
        if key in seen:
            continue
        if not allowed_from_domain(signal, "carry-forward"):
            continue
        seen.add(key)
        enriched = enrich_signal(signal, issue_date, "carry-forward")
        merged.append(enriched)
        record_domain(enriched)
        if len(merged) >= TARGET_SIGNAL_COUNT:
            break
    trimmed = merged[:TARGET_SIGNAL_COUNT]
    for index, signal in enumerate(trimmed, start=1):
        signal["id"] = f"signal-{index:03d}"
    return trimmed


def build_signal_payload(gcc_items, global_items, issue_date, prior_signals):
    signals = []
    for index, item in enumerate(sorted(gcc_items + global_items, key=radar_impact, reverse=True), start=1):
        category = signal_category(item)
        signals.append(
            {
                "id": f"signal-{index:03d}",
                "title": sanitize_display_text(item.title),
                "category": category,
                "score": radar_impact(item),
                "date": item.publish_date or datetime.now().strftime("%Y-%m-%d"),
                "publication_date": item.publish_date or datetime.now().strftime("%Y-%m-%d"),
                "source": urlparse(item.url).netloc.removeprefix("www.") or "Source",
                "url": item.url,
                "source_url": item.url,
                "summary": sanitize_display_text(item.excerpt[:260].replace("\n", " ").strip()),
                "whyItMatters": radar_implication(item),
                "readerQuestion": radar_action(item),
                "region": "GCC / Middle East" if item.scope == "GCC" else "Global",
                "lane": item.lane,
                "source_type": item.source_type,
                "confidence": item.confidence,
                "news_quality": item.news_quality,
                "source_grade": source_grade(item.url, item.source_type),
            }
        )
    payload = merge_signal_payload(signals, prior_signals, issue_date)
    for signal in payload:
        signal["desk"] = signal_desk_from_signal(signal)
        signal["evidence_strength"] = evidence_strength(signal)
        signal["gcc_relevance"] = gcc_relevance(signal)
        signal["actionability"] = actionability(signal)
    return payload


def build_radar_payload(gcc_items, global_items, issue_date, window_hours):
    items = gcc_items + global_items
    thesis = strongest_pattern(gcc_items) if gcc_items else "Global AI context is shaping the GCC operating model."
    summary = build_connective_tissue(gcc_items, global_items)
    events = []
    for item in items:
        events.append(
            {
                "title": sanitize_display_text(item.title),
                "sector": radar_sector(item),
                "region": item.scope,
                "impact": radar_impact(item),
                "horizon": radar_horizon(item),
                "why": sanitize_display_text(item.excerpt[:360].replace("\n", " ").strip()),
                "implication": radar_implication(item),
                "action": radar_action(item),
                "source": item.url,
                "sourceLabel": sanitize_display_text(item.title),
                "published": item.publish_date or "date not visible",
            }
        )

    return {
        "updated": issue_date,
        "windowHours": window_hours,
        "thesis": thesis,
        "summary": summary,
        "watchlist": [
            "Central bank guidance on model risk, outsourcing, autonomous decisioning, open finance, and digital assets",
            "GCC cloud region, data center, sovereign AI, and national AI infrastructure announcements",
            "Agent identity, audit, observability, runtime governance, and kill-switch platforms",
            "Banking use cases moving from pilots into governed production workflows",
            "Enterprise software vendors turning workflow tools into agent control planes",
        ],
        "filters": ["All", "GCC", "Global", "Banking", "Agents", "Regulation", "Cloud", "Models", "Enterprise"],
        "events": sorted(events, key=lambda event: event["impact"], reverse=True),
    }


def radar_theme_for_signal(signal):
    category = signal.get("category", "")
    region = signal.get("region", "")
    if "Financial Services" in category:
        return "banking-execution"
    if "Governance" in category or "Risk" in category:
        return "responsible-ai"
    if "Compute" in category:
        return "governed-autonomy"
    if "Model" in category:
        return "control-plane"
    if "GCC" in region or "Middle East" in category:
        return "gcc-state-capacity"
    return "workflow-economics"


def radar_tags_for_signal(signal):
    tags = []
    category = signal.get("category", "")
    region = signal.get("region", "")
    if "GCC" in region:
        tags.append("GCC")
    else:
        tags.append("Global")
    if "Agent" in category:
        tags.append("Agents")
    if "Governance" in category or "Risk" in category:
        tags.append("Governance")
        tags.append("Responsible AI")
    if "Financial Services" in category:
        tags.extend(["Financial Services", "Banks"])
    if signal.get("desk") == "Enterprise Strategy" or "Consulting" in category:
        tags.append("Consulting")
    if "Compute" in category:
        tags.append("Compute")
    if "Model" in category:
        tags.append("Models")
    if "Enterprise" in category:
        tags.append("Enterprise Platforms")
    if not any(tag == "Enterprise Platforms" for tag in tags):
        tags.append("Enterprise Platforms")
    return list(dict.fromkeys(tags))


def build_rich_radar_payload(signals, issue_date, market_chatter=None):
    radar_signals = []
    for index, signal in enumerate(signals, start=1):
        radar_signals.append(
            {
                "id": signal.get("id") or f"radar-{index:03d}",
                "date": signal.get("publication_date") or signal.get("date") or issue_date,
                "title": signal.get("title", ""),
                "region": "GCC" if "GCC" in (signal.get("region") or "") else "Global",
                "category": signal.get("category", "Enterprise Platforms"),
                "tags": radar_tags_for_signal(signal),
                "theme": radar_theme_for_signal(signal),
                "score": signal.get("score", 70),
                "source": signal.get("source", "Source"),
                "url": signal.get("source_url") or signal.get("url"),
                "whatChanged": signal.get("summary", ""),
                "whyItMatters": signal.get("whyItMatters", ""),
                "readThrough": signal.get("readerQuestion", ""),
                "freshness": signal.get("freshness", "carry-forward"),
                "source_type": signal.get("source_type", "analysis"),
                "sourceGrade": signal.get("source_grade", source_grade(signal.get("source_url") or signal.get("url") or "", signal.get("source_type", "analysis"))),
                "newsQuality": signal.get("news_quality", 50),
                "desk": signal.get("desk", signal_desk_from_signal(signal)),
                "evidenceStrength": signal.get("evidence_strength", evidence_strength(signal)),
                "gccRelevance": signal.get("gcc_relevance", gcc_relevance(signal)),
                "actionability": signal.get("actionability", actionability(signal)),
            }
        )

    def pick_signals(predicate, limit=4):
        picked = [signal for signal in radar_signals if predicate(signal)]
        return sorted(picked, key=lambda item: (item.get("score", 0), item.get("date", "")), reverse=True)[:limit]

    desk_counts = {}
    for signal in radar_signals:
        desk_counts[signal["desk"]] = desk_counts.get(signal["desk"], 0) + 1

    operating_source_types = {"official", "company", "jobs", "investor", "press"}
    fresh_moves = pick_signals(lambda signal: signal.get("freshness") == "fresh")
    operating_signals = pick_signals(
        lambda signal: signal.get("source_type") in operating_source_types and signal.get("desk") != "Workforce Faultline",
        limit=6,
    )
    strategic_carry = pick_signals(lambda signal: signal.get("freshness") == "carry-forward")

    return {
        "reviewed": format_review_date(issue_date),
        "filters": [
            "All",
            "GCC",
            "Global",
            "Agents",
            "Governance",
            "Responsible AI",
            "Financial Services",
            "Banks",
            "Enterprise Platforms",
            "Consulting",
            "Compute",
            "Models",
        ],
        "themes": RADAR_THEMES,
        "leaders": RADAR_LEADERS,
        "banks": RADAR_BANKS,
        "governance": RADAR_GOVERNANCE,
        "sourceStack": RADAR_SOURCE_STACK,
        "marketChatter": market_chatter or MARKET_CHATTER_STACK,
        "workforceTracker": WORKFORCE_TRACKER,
        "deskSummary": [
            {"desk": desk, "count": count}
            for desk, count in sorted(desk_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "signalSystem": {
            "freshMoves": {
                "label": "Fresh moves",
                "description": "Only newly verified signals from the last scan window. If this stays thin, the market was quiet or the evidence was weak.",
                "signals": fresh_moves,
            },
            "operatingSignals": {
                "label": "Operating signals",
                "description": "Evidence of action: deployments, governance steps, jobs, partnerships, filings, and enterprise moves that change operating reality.",
                "signals": operating_signals,
            },
            "strategicCarry": {
                "label": "Strategic carry-forwards",
                "description": "Still-important signals worth carrying until something stronger displaces them. This keeps the radar honest on thin-news days.",
                "signals": strategic_carry,
            },
        },
        "signals": radar_signals,
    }


def build_podcast_payload(signals, issue_date):
    fresh_signals = [signal for signal in signals if signal.get("freshness") == "fresh"]
    return {
        "reviewed": format_review_date(issue_date),
        "filters": ["All", "Agents", "Governance", "Enterprise", "Frontier Labs", "Compute", "Banking", "GCC", "Builders", "Capital"],
        "themes": PODCAST_THEMES,
        "lens": PODCAST_LENS,
        "shows": PODCAST_SHOWS,
        "episodes": PODCAST_EPISODES,
        "radarReadThrough": {
            "reviewed": format_review_date(issue_date),
            "freshSignalCount": len(fresh_signals),
            "gccSignalCount": len([signal for signal in fresh_signals if "GCC" in (signal.get("region") or "")]),
            "carryForwardSignalCount": len([signal for signal in signals if signal.get("freshness") == "carry-forward"]),
        },
    }


def build_signal_archive(signals, issue_date):
    prior = load_prior_archive()
    by_key = {}
    current_keys = {
        signal.get("source_url") or signal.get("url") or signal.get("title")
        for signal in signals
        if signal.get("source_url") or signal.get("url") or signal.get("title")
    }

    for article in prior.get("articles", []):
        key = article.get("source_url") or article.get("url") or article.get("title")
        if (
            key
            and not is_blocked_domain(key)
            and not (article.get("last_seen") == issue_date and key not in current_keys)
        ):
            by_key[key] = dict(article)

    for signal in signals:
        key = signal.get("source_url") or signal.get("url") or signal.get("title")
        if not key or is_blocked_domain(key):
            continue

        existing = by_key.get(key, {})
        by_key[key] = {
            "id": existing.get("id") or signal.get("id"),
            "title": signal.get("title"),
            "category": signal.get("category"),
            "score": max(existing.get("score", 0), signal.get("score", 0)),
            "date": signal.get("date"),
            "publication_date": signal.get("publication_date"),
            "source": signal.get("source"),
            "url": signal.get("url"),
            "source_url": signal.get("source_url") or signal.get("url"),
            "summary": signal.get("summary"),
            "whyItMatters": signal.get("whyItMatters"),
            "readerQuestion": signal.get("readerQuestion"),
            "region": signal.get("region"),
            "freshness": signal.get("freshness"),
            "first_seen": existing.get("first_seen") or issue_date,
            "last_seen": issue_date,
            "updated_on": issue_date,
        }

    articles = sorted(
        by_key.values(),
        key=lambda item: (
            item.get("publication_date") or "",
            item.get("last_seen") or "",
            item.get("score", 0),
        ),
        reverse=True,
    )
    for index, article in enumerate(articles, start=1):
        article["id"] = f"archive-{index:04d}"

    return {
        "reviewed": format_review_date(issue_date),
        "updated_on": issue_date,
        "articleCount": len(articles),
        "articles": articles,
    }


def build_coverage_report(gcc_items, global_items):
    def summarize(items):
        lane_counts = {}
        source_type_counts = {}
        for item in items:
            lane_counts[item.lane] = lane_counts.get(item.lane, 0) + 1
            source_type_counts[item.source_type] = source_type_counts.get(item.source_type, 0) + 1
        return {
            "count": len(items),
            "top_lanes": sorted(lane_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:6],
            "source_types": sorted(source_type_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:6],
        }

    return {
        "gcc": summarize(gcc_items),
        "global": summarize(global_items),
    }


def build_discovery_report(bundle):
    feed_batches = [entry for entry in bundle.responses if "url" in entry and "count" in entry]
    parallel_batches = [entry for entry in bundle.responses if "batch" in entry]
    errors = [entry for entry in bundle.responses if entry.get("error")]
    return {
        "query_count": len(bundle.queries),
        "parallel_batches": len(parallel_batches),
        "feed_queries": len(feed_batches),
        "feed_results": sum(entry.get("fresh_count", entry.get("count", 0)) for entry in feed_batches),
        "combined_results": len(bundle.results),
        "errors": errors[:6],
    }


def sanitize_display_text(text):
    return (
        text.replace("Anthropic (Claude)", "Anthropic")
        .replace("Claude", "Anthropic")
        .replace("claude", "Anthropic")
    )


def write_site_radar_data(gcc_items, global_items, issue_date, window_hours):
    SITE_RADAR_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = build_radar_payload(gcc_items, global_items, issue_date, window_hours)
    SITE_RADAR_DATA_PATH.write_text(
        "window.GAGANAI_RADAR = "
        + json.dumps(payload, indent=2, ensure_ascii=False)
        + ";\n"
    )
    return SITE_RADAR_DATA_PATH


def write_site_signal_data(gcc_items, global_items, issue_date, window_hours=48):
    SITE_SIGNALS_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    prior_signals = load_prior_signals()
    market_chatter = fetch_market_chatter(window_hours)
    payload = build_signal_payload(gcc_items, global_items, issue_date, prior_signals)
    SITE_SIGNALS_DATA_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    SITE_SIGNALS_JS_PATH.write_text(
        "window.GAGANAI_SIGNALS = "
        + json.dumps(payload, indent=2, ensure_ascii=False)
        + ";\n"
    )
    SITE_RICH_RADAR_PATH.write_text(
        "window.GAGANAI_RADAR = "
        + json.dumps(build_rich_radar_payload(payload, issue_date, market_chatter), indent=2, ensure_ascii=False)
        + ";\n"
    )
    SITE_PODCAST_DATA_PATH.write_text(
        "window.GAGANAI_PODCASTS = "
        + json.dumps(build_podcast_payload(payload, issue_date), indent=2, ensure_ascii=False)
        + ";\n"
    )
    SITE_SIGNAL_ARCHIVE_PATH.write_text(
        json.dumps(build_signal_archive(payload, issue_date), indent=2, ensure_ascii=False) + "\n"
    )
    return SITE_SIGNALS_DATA_PATH


def build_whatsapp(gcc_items, global_items, window_hours):
    return (
        "The Philosophical Ledger\n\n"
        "The agent control plane is becoming the new cloud region.\n\n"
        "This week’s signal: GCC cloud and industrial AI moves are connecting with a global shift toward governed enterprise agents.\n\n"
        "The real executive question is not which model to use. It is where AI can safely act.\n\n"
        "Before agents touch core workflows, leaders need clear answers on data residency, permissions, audit trails, human approval, observability, shutdown controls, and ownership of outcomes.\n\n"
        "My read: GCC AI leaders will not be the institutions with the most pilots. They will be the ones that turn AI into governed operating capacity.\n\n"
        "Ask this week: which workflows are ready for AI to assist, which are ready for AI to act, and which would expose our weakest controls?"
    )


def build_image_prompt(gcc_items, global_items):
    return (
        "Premium LinkedIn newsletter cover for 'The Philosophical Ledger', a GCC executive AI market brief. "
        "Concept: 'The agent control plane is becoming the new cloud region.' "
        "Show a refined GCC skyline at night with data-center geometry and cloud-region grid lines. "
        "Above it, show a clean enterprise control-plane interface with governed AI agents as connected nodes. "
        "Three visual layers: local cloud region, trusted enterprise data, governed agent workflows. "
        "Style: executive, modern, restrained, high-trust, premium business publication. "
        "Palette: deep charcoal, warm white, restrained teal, subtle gold accents. "
        "Avoid cartoon robots, sci-fi clutter, generic glowing brains, crypto aesthetics, stock-photo people, and dense text. "
        "Minimal readable text only: 'The Philosophical Ledger' and 'Agent Control Plane'. "
        "Aspect ratio: 1.91:1 for LinkedIn post preview."
    )


async def inspect_with_mirage(issue_date):
    ws = Workspace(
        {
            "/newsletter": (DiskResource(str(ROOT)), MountMode.READ),
        },
        mode=MountMode.READ,
    )
    commands = [
        "find /newsletter -maxdepth 2 -type f",
        f"wc -w /newsletter/publish/{issue_date}-linkedin.txt",
        f"grep -n \"GCC AI\" /newsletter/publish/{issue_date}-linkedin.txt",
    ]
    report = []
    for command in commands:
        result = await ws.execute(command)
        report.append(
            {
                "command": command,
                "stdout": await result.stdout_str(),
                "stderr": await result.stderr_str(),
            }
        )
    return report


def write_outputs(issue_date, gcc_response, global_response, gcc_items, global_items, window_hours, dry_run):
    raw_path = RESEARCH_DIR / f"{issue_date}-parallel-raw.json"
    filtered_path = RESEARCH_DIR / f"{issue_date}-sources.json"
    linkedin_path = PUBLISH_DIR / f"{issue_date}-linkedin.txt"
    draft_path = DRAFTS_DIR / f"{issue_date}.md"
    whatsapp_path = WHATSAPP_DIR / f"{issue_date}.txt"
    image_prompt_path = IMAGES_DIR / f"{issue_date}-image-prompt.txt"

    raw_path.write_text(
        json.dumps(
            {
                "gcc": response_to_dict(gcc_response),
                "global": response_to_dict(global_response) if global_response else None,
            },
            indent=2,
            default=str,
        )
        + "\n"
    )
    items = gcc_items + global_items
    filtered_path.write_text(json.dumps([asdict(item) for item in items], indent=2) + "\n")

    linkedin = build_linkedin_post(gcc_items, global_items, issue_date, window_hours)
    whatsapp = build_whatsapp(gcc_items, global_items, window_hours)
    image_prompt = build_image_prompt(gcc_items, global_items)

    linkedin_path.write_text(linkedin + "\n")
    whatsapp_path.write_text(whatsapp + "\n")
    image_prompt_path.write_text(image_prompt + "\n")
    draft_path.write_text(
        f"# GCC AI Daily - {issue_date}\n\n"
        "## LinkedIn\n\n"
        f"{linkedin}\n\n"
        "## WhatsApp\n\n"
        f"{whatsapp}\n\n"
        "## Image Prompt\n\n"
        f"{image_prompt}\n\n"
        "## GCC Sources\n\n"
        + ("\n".join(f"- [{item.title}]({item.url})" for item in gcc_items) or "- None")
        + "\n\n## Global Context Sources\n\n"
        + ("\n".join(f"- [{item.title}]({item.url})" for item in global_items) or "- None")
        + "\n"
    )

    if not dry_run:
        write_covered_urls(item.url for item in items)

    if items:
        radar_path = write_site_radar_data(gcc_items, global_items, issue_date, window_hours)
        signals_path = write_site_signal_data(gcc_items, global_items, issue_date, window_hours)
    else:
        print(
            "No fresh verified sources; carrying forward prior site data and advancing review date.",
            file=sys.stderr,
        )
        radar_path = SITE_RADAR_DATA_PATH
        signals_path = write_site_signal_data([], [], issue_date, window_hours)

    return {
        "raw": raw_path,
        "sources": filtered_path,
        "linkedin": linkedin_path,
        "whatsapp": whatsapp_path,
        "image_prompt": image_prompt_path,
        "draft": draft_path,
        "site_radar": radar_path,
        "site_signals": signals_path,
        "site_radar_rich": SITE_RICH_RADAR_PATH,
        "site_podcasts": SITE_PODCAST_DATA_PATH,
        "site_archive": SITE_SIGNAL_ARCHIVE_PATH,
    }


async def async_main():
    parser = argparse.ArgumentParser(description="Build the GCC AI Daily newsletter issue.")
    parser.add_argument("--window-hours", type=int, default=24)
    parser.add_argument("--allow-undated", action="store_true")
    parser.add_argument("--global-context", action="store_true", default=True)
    parser.add_argument("--no-global-context", dest="global_context", action="store_false")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--issue-date", type=str)
    args = parser.parse_args()

    ensure_dirs()
    issue_date = args.issue_date or datetime.now().strftime("%Y-%m-%d")
    if args.issue_date:
        datetime.fromisoformat(issue_date)
    window_start = datetime.now(timezone.utc) - timedelta(hours=args.window_hours)
    covered_urls = read_covered_urls()

    gcc_response = discover_sources(args.window_hours)
    global_response = discover_sources(args.window_hours, global_context=True) if args.global_context else None
    gcc_items = normalize_results(
        gcc_response,
        covered_urls,
        window_start,
        allow_undated=args.allow_undated,
        scope="GCC",
    )
    global_items = (
        normalize_results(
            global_response,
            covered_urls,
            window_start,
            allow_undated=args.allow_undated,
            scope="Global",
        )
        if global_response
        else []
    )
    outputs = write_outputs(
        issue_date,
        gcc_response,
        global_response,
        gcc_items,
        global_items,
        args.window_hours,
        args.dry_run,
    )
    mirage_report = await inspect_with_mirage(issue_date)

    summary = {
        "issue_date": issue_date,
        "window_hours": args.window_hours,
        "source_count": len(gcc_items) + len(global_items),
        "gcc_source_count": len(gcc_items),
        "global_source_count": len(global_items),
        "discovery": {
            "gcc": build_discovery_report(gcc_response),
            "global": build_discovery_report(global_response) if global_response else None,
        },
        "coverage": build_coverage_report(gcc_items, global_items),
        "dry_run": args.dry_run,
        "outputs": {key: str(path) for key, path in outputs.items()},
        "mirage_report": mirage_report,
    }
    print(json.dumps(summary, indent=2))


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
