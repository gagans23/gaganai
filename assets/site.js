(function () {
  const config = window.GAGANAI_SITE_CONFIG || {};
  const username = config.buttondownUsername || "gaganai";
  const forms = document.querySelectorAll("[data-subscribe-form]");

  forms.forEach((form) => {
    form.action = `https://buttondown.email/api/emails/embed-subscribe/${encodeURIComponent(username)}`;
    form.addEventListener("submit", () => {
      const button = form.querySelector("button");
      if (button) button.textContent = "Opening signup...";
    });
  });

  if (config.cloudflareAnalyticsToken) {
    const script = document.createElement("script");
    script.defer = true;
    script.src = "https://static.cloudflareinsights.com/beacon.min.js";
    script.dataset.cfBeacon = JSON.stringify({ token: config.cloudflareAnalyticsToken });
    document.head.appendChild(script);
  }

  if (document.querySelector(".article")) {
    const progress = document.createElement("div");
    progress.className = "reading-progress";
    progress.setAttribute("aria-hidden", "true");
    document.body.appendChild(progress);

    const updateProgress = () => {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      const ratio = max > 0 ? window.scrollY / max : 0;
      progress.style.transform = `scaleX(${Math.min(1, Math.max(0, ratio))})`;
    };

    updateProgress();
    window.addEventListener("scroll", updateProgress, { passive: true });
    window.addEventListener("resize", updateProgress);
  }

  const revealItems = document.querySelectorAll(
    ".home-section, .subscribe-panel, .thought-card, .book-card, .article h2, .stat-card, .argument-grid article, .levels-grid article, .case-file, .reader-response, .challenge-panel"
  );

  if ("IntersectionObserver" in window) {
    revealItems.forEach((item) => item.classList.add("reveal"));
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );

    revealItems.forEach((item) => observer.observe(item));
  }
})();
