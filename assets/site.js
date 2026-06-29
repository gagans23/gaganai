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

  const escapeInline = (value) =>
    String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");

  const safeUrl = (value) => {
    const url = String(value || "").trim();
    return /^https?:\/\//i.test(url) ? url : "#";
  };

  const hydratePodcastPage = () => {
    const podcastData = window.GAGANAI_PODCASTS;
    const hero = document.querySelector(".podcast-hero");
    if (!hero || !podcastData) return;

    const shows = (podcastData.shows || []).filter((show) => show && show.name);
    const episodes = (podcastData.episodes || [])
      .filter((episode) => episode && episode.title)
      .sort((a, b) => String(b.date || "").localeCompare(String(a.date || "")));

    const consoleCount = document.querySelector(".listening-console strong");
    const consoleCopy = document.querySelector(".listening-console p");
    if (consoleCount) consoleCount.textContent = String(shows.length || 0);
    if (consoleCopy) {
      consoleCopy.textContent = shows.length
        ? `${shows.length} shows monitored / reviewed ${podcastData.reviewed || "today"}`
        : `Reviewed ${podcastData.reviewed || "today"}`;
    }

    const grid = document.querySelector(".podcast-grid");
    if (grid && shows.length) {
      grid.innerHTML = shows
        .map((show, index) => {
          const rank = String(index + 1).padStart(2, "0");
          const signal = Math.max(0, Math.min(100, Number(show.signal) || 70));
          return `
            <article class="podcast-card">
              <div class="podcast-rank"><b>${rank}</b><span>${escapeInline(show.lane || "AI signal")}</span></div>
              <h2>${escapeInline(show.name)}</h2>
              <div class="signal-meter" style="--signal: ${signal}%"><i></i><span>${escapeInline(show.lane || "Signal")} signal</span></div>
              <p>${escapeInline(show.why || "A useful source for tracking how AI narratives are forming.")}</p>
              <dl>
                <div><dt>Source</dt><dd><a href="${escapeInline(safeUrl(show.source))}" target="_blank" rel="noreferrer">Official feed</a></dd></div>
                <div><dt>YouTube</dt><dd><a href="${escapeInline(safeUrl(show.youtube))}" target="_blank" rel="noreferrer">Channel</a></dd></div>
              </dl>
            </article>
          `;
        })
        .join("");
    }

    const thesisCopy = document.querySelector(".podcast-thesis > p");
    if (thesisCopy && episodes.length) {
      thesisCopy.textContent =
        `Reviewed ${podcastData.reviewed || "today"}. This page tracks recurring claims across long-form AI conversations and connects them back to agentic systems, governance, infrastructure, capital, and enterprise execution.`;
    }

    const trendlineTitle = document.querySelector(".trendline-panel h2");
    const trendlineCopy = document.querySelector(".trendline-panel div > p:not(.eyebrow)");
    const trendlineList = document.querySelector(".trendline-list");
    if (trendlineTitle && episodes.length) {
      trendlineTitle.textContent = "The current listening thread.";
    }
    if (trendlineCopy && episodes.length) {
      trendlineCopy.textContent =
        "The latest monitored episodes are useful when they explain why a radar story matters, contradict the market narrative, or expose a governance issue before it becomes a board problem.";
    }
    if (trendlineList && episodes.length) {
      trendlineList.innerHTML = episodes
        .slice(0, 6)
        .map((episode) => {
          const label = [episode.date, episode.show].filter(Boolean).join(" / ");
          return `<span>${escapeInline(label)}: ${escapeInline(episode.title)}</span>`;
        })
        .join("");
    }
  };

  const hydrateBooks = () => {
    const links = new Map([
      ["The Beginning of Infinity", "https://www.amazon.com/Beginning-Infinity-Explanations-Transform-World/dp/0143121359"],
      ["The Lessons of History", "https://www.amazon.com/Lessons-History-Will-Durant/dp/143914995X"],
      ["Poor Charlie's Almanack", "https://www.stripe.press/poor-charlies-almanack"],
      ["Superintelligence", "https://www.amazon.com/Superintelligence-Dangers-Strategies-Nick-Bostrom/dp/0198739834"],
      ["Breakneck", "https://www.amazon.com/Breakneck-Chinas-Quest-Engineer-Future/dp/1324106034"]
    ]);
    const coverFor = (title, author) => {
      const lines = [];
      String(title || "Book")
        .split(/\s+/)
        .forEach((word) => {
          const current = lines[lines.length - 1] || "";
          if (!current || `${current} ${word}`.length > 18) {
            lines.push(word);
          } else {
            lines[lines.length - 1] = `${current} ${word}`;
          }
        });
      const titleLines = lines.slice(0, 4)
        .map((line, index) => `<text x="48" y="${160 + index * 48}" font-family="Georgia, serif" font-size="36" font-weight="700" fill="#1b1713">${escapeInline(line)}</text>`)
        .join("");

      return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(`
        <svg xmlns="http://www.w3.org/2000/svg" width="480" height="720" viewBox="0 0 480 720">
          <rect width="480" height="720" fill="#efe4d2"/>
          <rect x="36" y="36" width="408" height="648" fill="none" stroke="#9a641b" stroke-width="10"/>
          <text x="48" y="86" font-family="Arial, sans-serif" font-size="20" font-weight="800" fill="#9a641b" letter-spacing="3">THE LEDGER SHELF</text>
          ${titleLines}
          <text x="48" y="618" font-family="Arial, sans-serif" font-size="24" font-weight="700" fill="#6f6258">${escapeInline(author || "")}</text>
        </svg>
      `)}`;
    };

    document.querySelectorAll(".book-card").forEach((card) => {
      const title = card.querySelector("h3")?.textContent?.trim();
      const author = card.querySelector("p")?.textContent?.trim();
      const url = links.get(title);
      const image = card.querySelector("img");
      if (image) {
        const originalSrc = image.currentSrc || image.src;
        const fallbackCover = coverFor(title, author);
        image.loading = "eager";
        image.src = fallbackCover;
        if (/^https?:\/\//i.test(originalSrc)) {
          const probe = new Image();
          probe.addEventListener("load", () => {
            if (probe.naturalWidth > 24 && probe.naturalHeight > 24) {
              image.src = originalSrc;
            }
          }, { once: true });
          probe.src = originalSrc;
        }
      }
      if (!url) return;

      card.setAttribute("role", "link");
      card.setAttribute("tabindex", "0");
      card.setAttribute("aria-label", `Open ${title}`);
      if (!card.querySelector("small")) {
        const action = document.createElement("small");
        action.textContent = "Open book";
        card.appendChild(action);
      }

      const openBook = () => window.open(url, "_blank", "noopener,noreferrer");
      card.addEventListener("click", (event) => {
        if (!event.target.closest("a")) openBook();
      });
      card.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openBook();
        }
      });
    });
  };

  hydratePodcastPage();
  hydrateBooks();

  const knowledgeCanvas = document.querySelector("[data-knowledge-field]");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (knowledgeCanvas && !reduceMotion) {
    const ctx = knowledgeCanvas.getContext("2d");
    const concepts = [
      "AI",
      "Judgment",
      "Trust",
      "Capital",
      "Risk",
      "Agents",
      "Memory",
      "Governance",
      "Institutions",
      "Knowledge",
      "Workflows",
      "Leadership"
    ];
    let width = 0;
    let height = 0;
    let dpr = 1;
    let nodes = [];
    let frame = 0;

    const resizeKnowledgeField = () => {
      const rect = knowledgeCanvas.getBoundingClientRect();
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = rect.width;
      height = rect.height;
      knowledgeCanvas.width = Math.floor(width * dpr);
      knowledgeCanvas.height = Math.floor(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      nodes = concepts.map((label, index) => {
        const band = index / Math.max(concepts.length - 1, 1);
        return {
          label,
          x: width * (0.38 + 0.55 * ((Math.sin(index * 2.18) + 1) / 2)),
          y: height * (0.12 + 0.76 * band),
          vx: (Math.cos(index * 1.7) * 0.18),
          vy: (Math.sin(index * 1.31) * 0.14),
          r: 2.2 + (index % 4) * 0.55,
          phase: index * 0.8
        };
      });
    };

    const drawKnowledgeField = () => {
      frame += 0.008;
      ctx.clearRect(0, 0, width, height);

      const gradient = ctx.createRadialGradient(width * 0.72, height * 0.46, 20, width * 0.72, height * 0.46, width * 0.64);
      gradient.addColorStop(0, "rgba(82, 194, 185, 0.11)");
      gradient.addColorStop(0.48, "rgba(154, 100, 27, 0.055)");
      gradient.addColorStop(1, "rgba(0, 0, 0, 0)");
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, width, height);

      nodes.forEach((node) => {
        node.x += node.vx + Math.sin(frame + node.phase) * 0.045;
        node.y += node.vy + Math.cos(frame + node.phase) * 0.035;
        if (node.x < width * 0.34 || node.x > width * 0.96) node.vx *= -1;
        if (node.y < height * 0.08 || node.y > height * 0.92) node.vy *= -1;
      });

      for (let i = 0; i < nodes.length; i += 1) {
        for (let j = i + 1; j < nodes.length; j += 1) {
          const a = nodes[i];
          const b = nodes[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          const limit = Math.min(width, 520) * 0.36;
          if (distance < limit) {
            const alpha = (1 - distance / limit) * 0.22;
            ctx.strokeStyle = `rgba(183, 226, 219, ${alpha})`;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }

      nodes.forEach((node, index) => {
        const pulse = 0.65 + Math.sin(frame * 2 + node.phase) * 0.35;
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.r + pulse * 1.2, 0, Math.PI * 2);
        ctx.fillStyle = index % 3 === 0 ? "rgba(240, 201, 120, .86)" : "rgba(137, 218, 209, .82)";
        ctx.fill();
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.r * 5.2, 0, Math.PI * 2);
        ctx.fillStyle = index % 3 === 0 ? "rgba(240, 201, 120, .055)" : "rgba(137, 218, 209, .055)";
        ctx.fill();
      });

      requestAnimationFrame(drawKnowledgeField);
    };

    resizeKnowledgeField();
    drawKnowledgeField();
    window.addEventListener("resize", resizeKnowledgeField);
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
    ".home-section, .subscribe-panel, .thought-card, .book-card, .article h2, .stat-card, .argument-grid article, .levels-grid article, .case-file, .reader-response, .challenge-panel, .situation-teaser, .radar-card, .heatmap-row, .radar-metrics article"
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


// Reading progress + auto TOC for essays [codex 2026-06-30]
(function () {
  var main = document.querySelector("main.article-site, main.body");
  if (!main) return;
  var bar = document.createElement("div");
  bar.className = "read-progress";
  bar.setAttribute("aria-hidden", "true");
  document.body.appendChild(bar);
  var target = document.querySelector("article.article") || main;
  function update() {
    var r = target.getBoundingClientRect();
    var total = Math.max(r.height - window.innerHeight, 1);
    var scrolled = Math.min(Math.max(-r.top, 0), total);
    bar.style.width = (scrolled / total * 100) + "%";
  }
  update();
  window.addEventListener("scroll", update, { passive: true });
  window.addEventListener("resize", update);
  var art = document.querySelector("article.article");
  if (art) {
    var heads = Array.prototype.slice.call(art.querySelectorAll(":scope > h2")).filter(function (h) { return !h.closest("header"); });
    if (heads.length >= 4) {
      heads.forEach(function (h, i) {
        if (!h.id) {
          h.id = "s-" + (h.textContent.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || ("sec" + i));
        }
      });
      var nav = document.createElement("nav");
      nav.className = "essay-toc";
      nav.setAttribute("aria-label", "On this page");
      nav.innerHTML = '<span class="toc-label">On this page</span><ol>' + heads.map(function (h) { return '<li><a href="#' + h.id + '">' + h.textContent.trim() + "</a></li>"; }).join("") + "</ol>";
      var hdr = art.querySelector(":scope > header");
      if (hdr) hdr.after(nav); else art.prepend(nav);
    }
  }
})();
