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
