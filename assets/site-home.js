// Motion is opt-in: no JS or prefers-reduced-motion => fully static page.
const MOTION_OK = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
if (MOTION_OK) document.documentElement.classList.add("js-anim");

// Reveal-on-scroll for [data-reveal] blocks (staggered within a viewport batch).
if (MOTION_OK && "IntersectionObserver" in window) {
  const revealer = new IntersectionObserver((entries) => {
    let order = 0;
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.style.transitionDelay = `${order * 90}ms`;
      entry.target.classList.add("is-in");
      revealer.unobserve(entry.target);
      order += 1;
    });
  }, { rootMargin: "0px 0px -8% 0px", threshold: 0.15 });
  document.querySelectorAll("[data-reveal]").forEach((el) => revealer.observe(el));
  // Safety net: if the observer is throttled, never leave in-viewport content hidden.
  setInterval(() => {
    document.querySelectorAll("[data-reveal]:not(.is-in)").forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.top < window.innerHeight && r.bottom > 0) el.classList.add("is-in");
    });
  }, 1500);
}

// Count-up for the provenance-machine stats once they are on screen.
const pendingCounts = [];
let machineSeen = false;
function runCount(el, target, suffix) {
  el.__counted = true;
  const t0 = performance.now();
  const dur = 950;
  function frame(now) {
    const p = Math.min(1, (now - t0) / dur);
    const eased = 1 - Math.pow(1 - p, 3);
    el.textContent = `${Math.round(target * eased)} ${suffix}`;
    if (p < 1) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
  // rAF can be throttled to zero (hidden tab, battery saver): guarantee the final value.
  setTimeout(() => { el.textContent = `${target} ${suffix}`; }, dur + 150);
}
function setStat(el, target, suffix) {
  if (!el) return;
  const n = Number(target);
  if (!MOTION_OK || !Number.isFinite(n)) { el.textContent = `${target} ${suffix}`; return; }
  if (machineSeen) runCount(el, n, suffix);
  else {
    pendingCounts.push([el, n, suffix]);
    // If the observer never fires (throttled surface), never leave a placeholder.
    setTimeout(() => { if (!el.__counted) el.textContent = `${target} ${suffix}`; }, 2600);
  }
}
if (MOTION_OK && "IntersectionObserver" in window) {
  const machineEl = document.querySelector(".provenance-machine");
  if (machineEl) {
    const counter = new IntersectionObserver((entries, obs) => {
      if (!entries.some((e) => e.isIntersecting)) return;
      machineSeen = true;
      pendingCounts.splice(0).forEach(([el, n, suffix]) => runCount(el, n, suffix));
      obs.disconnect();
    }, { threshold: 0.3 });
    counter.observe(machineEl);
  }
} else {
  machineSeen = true;
}

const video = document.querySelector(".hero-video");
const toggle = document.querySelector("[data-video-toggle]");

if (video && toggle) {
  toggle.addEventListener("click", () => {
    if (video.paused) {
      video.play();
      toggle.classList.add("is-paused-icon");
      toggle.classList.remove("is-play-icon");
      toggle.setAttribute("aria-label", "Pause video");
      return;
    }

    video.pause();
    toggle.classList.add("is-play-icon");
    toggle.classList.remove("is-paused-icon");
    toggle.setAttribute("aria-label", "Play video");
  });
}

const liveSignal = document.querySelector("[data-live-signal]");

function generatedAgeInDays(dateValue) {
  if (!dateValue) return null;

  const generated = new Date(`${dateValue}T00:00:00Z`);
  if (Number.isNaN(generated.getTime())) return null;

  return Math.max(0, Math.floor((Date.now() - generated.getTime()) / 86400000));
}

function liveFreshnessCopy(dateValue) {
  const age = generatedAgeInDays(dateValue);
  if (age === null) return { label: "Live data", cadence: "Updated daily from the signal pipeline." };
  if (age === 0) return { label: "Fresh today", cadence: "Updated today from the 06:00 GST signal pipeline." };
  if (age === 1) return { label: "Fresh yesterday", cadence: "Updated yesterday from the daily signal pipeline." };
  if (age <= 3) return { label: `${age} days old`, cadence: "Recently updated by the daily signal pipeline." };
  return { label: `Stale · ${age} days old`, cadence: "Pipeline attention needed — this signal is older than three days." };
}

if (liveSignal) {
  Promise.all([
    fetch("data/signal-gate.json", { cache: "no-store" }).then((response) => {
      if (!response.ok) throw new Error("Signal gate unavailable");
      return response.json();
    }),
    fetch("data/knowledge-graph.json", { cache: "no-store" }).then((response) => {
      if (!response.ok) throw new Error("Knowledge graph unavailable");
      return response.json();
    }),
  ])
    .then(([gate, graph]) => {
      const lead = gate.attractors?.[0];
      if (!lead) return;

      const freshness = liveFreshnessCopy(gate.generated);
      liveSignal.querySelector("[data-live-freshness]").textContent = freshness.label;
      liveSignal.querySelector("[data-live-updated]").textContent = `Ledger rebuilt ${gate.generated}`;
      liveSignal.querySelector("[data-live-source]").textContent = `Source: signal-gate.json + knowledge-graph.json · graph ${graph.generated || "ready"}`;
      liveSignal.querySelector("[data-live-cadence]").textContent = freshness.cadence;
      liveSignal.querySelector("[data-live-index]").textContent = "01";
      liveSignal.querySelector("[data-live-title]").textContent = lead.title;
      liveSignal.querySelector("[data-live-thesis]").textContent = lead.thesis;
      setStat(liveSignal.querySelector("[data-live-stimuli]"), gate.stats.stimuli, "stimuli");
      setStat(liveSignal.querySelector("[data-live-entities]"), graph.stats.entities, "entities");
      setStat(liveSignal.querySelector("[data-live-signals]"), gate.stats.signal, "passed");
      setStat(liveSignal.querySelector("[data-live-attractors]"), gate.stats.attractors, "directions");
      liveSignal.classList.add("is-resolved");
      if ((generatedAgeInDays(gate.generated) || 0) > 3) liveSignal.classList.add("is-stale");
    })
    .catch(() => {
      liveSignal.querySelector("[data-live-freshness]").textContent = "Pipeline pending";
      liveSignal.querySelector("[data-live-updated]").textContent = "Next ledger update pending";
      liveSignal.querySelector("[data-live-source]").textContent = "Could not load generated source files";
      liveSignal.querySelector("[data-live-cadence]").textContent = "Live data is temporarily unavailable.";
      liveSignal.classList.add("is-stale");
    });
}

const writingCard = document.querySelector("[data-writing-card]");

function formatWritingFreshness(dateValue) {
  if (!dateValue) return "Synced from Writing archive";

  const published = new Date(`${dateValue}T00:00:00Z`);
  if (Number.isNaN(published.getTime())) return "Synced from Writing archive";

  const now = new Date();
  const ageDays = Math.max(0, Math.floor((now - published) / 86400000));
  if (ageDays <= 45) return "Fresh this month";
  if (ageDays <= 90) return "Latest in the archive";
  return `Archive quiet for ${Math.round(ageDays / 30)} months`;
}

function applyWritingLead(item) {
  if (!writingCard || !item) return;

  const status = writingCard.querySelector("[data-writing-status]");
  const freshness = writingCard.querySelector("[data-writing-freshness]");
  const meta = writingCard.querySelector("[data-writing-meta]");
  const title = writingCard.querySelector("[data-writing-title]");
  const summary = writingCard.querySelector("[data-writing-summary]");
  const readTime = writingCard.querySelector("[data-writing-read-time]");
  const cta = writingCard.querySelector("[data-writing-cta]");
  const readingLatest = document.querySelector("[data-reading-latest]");

  writingCard.href = item.href;
  if (status) status.textContent = "Latest field note";
  if (freshness) freshness.textContent = formatWritingFreshness(item.date);
  if (meta) {
    meta.textContent = [item.dateLabel, item.readTime, item.category].filter(Boolean).join(" · ");
  }
  if (title) title.textContent = item.title;
  if (summary) summary.textContent = item.summary;
  if (readTime) readTime.textContent = item.readTime;
  if (cta) cta.textContent = item.cta || "Read the newest field note →";

  if (readingLatest) {
    readingLatest.href = item.href;
    const label = readingLatest.querySelector("span");
    if (label) label.textContent = "Newest";
    readingLatest.lastChild.textContent = item.title;
  }
}

if (writingCard) {
  fetch("data/writing.json", { cache: "no-store" })
    .then((response) => {
      if (!response.ok) throw new Error("Writing manifest unavailable");
      return response.json();
    })
    .then((manifest) => {
      const items = Array.isArray(manifest.items) ? manifest.items : [];
      const latest = items
        .filter((item) => item && item.title && item.href)
        .sort((a, b) => String(b.date || "").localeCompare(String(a.date || "")))[0];
      applyWritingLead(latest);
    })
    .catch(() => {
      const freshness = writingCard.querySelector("[data-writing-freshness]");
      if (freshness) freshness.textContent = "Using page fallback";
    });
}


// SpaceX-inspired: scroll-driven provenance machine — steps light up in sequence as you scroll [codex 2026-06-30]
(function () {
  const machine = document.querySelector(".provenance-machine");
  if (!machine) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    machine.querySelectorAll(".machine-step").forEach((s) => s.classList.add("is-active"));
    return;
  }
  const section = machine.closest("section") || machine;
  const steps = machine.querySelectorAll(".machine-step");
  let ticking = false;
  function update() {
    ticking = false;
    const r = section.getBoundingClientRect();
    const vh = window.innerHeight;
    const progress = Math.max(0, Math.min(1, (vh - r.top) / (vh + r.height * 0.6)));
    const n = steps.length;
    steps.forEach((s, i) => {
      if (progress >= (i / n) * 0.82) s.classList.add("is-active");
    });
  }
  function onScroll() {
    if (!ticking) { ticking = true; requestAnimationFrame(update); }
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll);
  update();
})();
