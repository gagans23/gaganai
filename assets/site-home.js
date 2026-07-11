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

      liveSignal.querySelector("[data-live-updated]").textContent = `Ledger rebuilt ${gate.generated}`;
      liveSignal.querySelector("[data-live-index]").textContent = "01";
      liveSignal.querySelector("[data-live-title]").textContent = lead.title;
      liveSignal.querySelector("[data-live-thesis]").textContent = lead.thesis;
      liveSignal.querySelector("[data-live-stimuli]").textContent = `${gate.stats.stimuli} stimuli`;
      liveSignal.querySelector("[data-live-entities]").textContent = `${graph.stats.entities} entities`;
      liveSignal.querySelector("[data-live-signals]").textContent = `${gate.stats.signal} passed`;
      liveSignal.querySelector("[data-live-attractors]").textContent = `${gate.stats.attractors} directions`;
      liveSignal.classList.add("is-resolved");
    })
    .catch(() => {
      liveSignal.querySelector("[data-live-updated]").textContent = "Next ledger update pending";
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
      if (progress >= i / n) s.classList.add("is-active");
    });
  }
  function onScroll() {
    if (!ticking) { ticking = true; requestAnimationFrame(update); }
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll);
  update();
})();
