(function () {
  const root = document.querySelector("[data-radar-app]");
  const data = window.GAGANAI_RADAR;
  if (!root || !data) return;

  const allSignals = (data.signals || []).slice().sort((a, b) => b.date.localeCompare(a.date));
  const leadStoryRoot = document.querySelector("[data-lead-story]");
  const storyListRoot = document.querySelector("[data-story-list]");
  const frontPageNoteRoot = document.querySelector("[data-front-page-note]");
  const layerCakeRoot = document.querySelector("[data-layer-cake]");
  const cakeNoteRoot = document.querySelector("[data-cake-note]");
  const marketChatterRoot = document.querySelector("[data-market-chatter]");
  const lastReviewedRoot = document.querySelector("[data-last-reviewed]");
  const lastReviewedCardRoot = document.querySelector("[data-last-reviewed-card]");
  const primaryDeskRoot = document.querySelector("[data-primary-desk]");
  const primaryRegionRoot = document.querySelector("[data-primary-region]");

  const escape = (value) =>
    String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");

  // Allow only http(s) in hrefs — blocks javascript:/data: if data is ever polluted.
  const safeUrl = (value) => {
    const s = String(value || "").trim();
    return /^https?:\/\//i.test(s) ? escape(s) : "#";
  };

  const deskPriority = {
    "GCC Institutions": 7,
    "Banking AI": 6,
    "Governance & Regulation": 5,
    "Agentic Systems": 4,
    "Enterprise Strategy": 3,
    "Compute & Infrastructure": 2,
    "Workforce Faultline": 1
  };

  const sourcePriority = {
    official: 6,
    company: 5,
    investor: 4,
    press: 4,
    jobs: 3,
    research: 3,
    developer: 2,
    analysis: 1
  };

  const ageInDays = (value) => {
    if (!value) return 999;
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return 999;
    return Math.max(0, Math.floor((Date.now() - parsed.getTime()) / 86400000));
  };

  const isCurrentStory = (signal) =>
    signal?.freshness === "fresh" ||
    ageInDays(signal?.date || signal?.publication_date || "") <= 21;

  const isGenericRoundup = (signal) => {
    const text = `${signal.title || ""} ${signal.source || ""}`.toLowerCase();
    return /top\s*\d+|weekly briefing|trend reports?|competitors|roundup|digest/.test(text);
  };

  const shouldShow = (signal) => {
    if (isGenericRoundup(signal) && signal.freshness === "carry-forward") return false;
    if (signal.freshness === "carry-forward" && ageInDays(signal.date || signal.publication_date || "") > 35) {
      return false;
    }
    if ((signal.newsQuality || 50) < 50) return false;
    return true;
  };

  const scoreStory = (signal) => {
    const desk = deskPriority[signal.desk] || 0;
    const source = sourcePriority[String(signal.source_type || "").toLowerCase()] || 0;
    const freshness = signal.freshness === "fresh" ? 80 : signal.freshness === "carry-forward" ? 0 : 20;
    const recency = Math.max(0, 60 - Math.min(ageInDays(signal.date || signal.publication_date || ""), 60));
    const gccBoost = signal.region === "GCC" ? 35 : signal.gccRelevance === "High read-through" ? 20 : 0;
    return desk * 100 + source * 40 + freshness + recency + gccBoost + Number(signal.score || 0);
  };

  const visibleSignals = () =>
    allSignals
      .filter(shouldShow)
      .sort((a, b) => scoreStory(b) - scoreStory(a));

  const sourceBadge = (signal) =>
    [signal.region, signal.desk, signal.source].filter(Boolean).map(escape).join(" / ");

  const sourceQualityBadge = (signal) => {
    const grade = signal.sourceGrade || "C";
    const quality = signal.newsQuality || 50;
    return `${escape(grade)} source / ${escape(quality)} quality`;
  };

  const renderLead = (signal, signals) => {
    if (!leadStoryRoot) return;
    if (!signal) {
      leadStoryRoot.innerHTML = `<div class="empty-state"><strong>No current stories are ready for the front page.</strong><p>The feed needs fresher reported news before this edition should lead with a headline.</p></div>`;
      return false;
    }

    leadStoryRoot.innerHTML = `
      <div class="lead-story-topline">
        <span>${escape(signal.date)}</span>
        <span>${sourceBadge(signal)}</span>
        <span>${sourceQualityBadge(signal)}</span>
      </div>
      <h3>${escape(signal.title)}</h3>
      <p class="lead-story-summary">${escape(signal.whatChanged)}</p>
      <div class="lead-story-analysis">
        <article>
          <span>Why this matters</span>
          <p>${escape(signal.whyItMatters)}</p>
        </article>
        <article>
          <span>What to watch</span>
          <p>${escape(signal.readThrough)}</p>
        </article>
      </div>
      <div class="lead-story-actions">
        <a href="${safeUrl(signal.url)}" target="_blank" rel="noreferrer">Read original source</a>
      </div>
    `;
    return true;
  };

  const storyCard = (signal) => `
    <article class="story-card">
      <div class="story-card-topline">
        <span>${escape(signal.date)}</span>
        <span>${sourceBadge(signal)}</span>
        <span>${sourceQualityBadge(signal)}</span>
      </div>
      <h4>${escape(signal.title)}</h4>
      <p>${escape(signal.whatChanged)}</p>
      <div class="story-card-footer">
        <strong>${escape(signal.whyItMatters)}</strong>
        <a href="${safeUrl(signal.url)}" target="_blank" rel="noreferrer">${escape(signal.source)}</a>
      </div>
    </article>
  `;

  const renderStoryList = (signals, hasLeadStory) => {
    if (!storyListRoot) return;
    const currentSignals = signals.filter(isCurrentStory);
    const rest = hasLeadStory ? currentSignals.slice(1, 9) : currentSignals.slice(0, 8);
    storyListRoot.innerHTML = rest.length
      ? rest.map(storyCard).join("")
      : `<div class="empty-state"><strong>No current supporting stories are ready.</strong><p>The edition needs fresher reported stories before it should look like a full front page.</p></div>`;
  };

  // Gagan's read: the five-layer cake (after Jensen Huang's stack).
  // Keep LAYERS and classifyLayer in lockstep with automation/render_radar.py.
  const LAYERS = [
    [5, "Agents & Applications", "Where AI meets work — agents in production, banking, government, enterprise, people."],
    [4, "Models & Intelligence", "Frontier labs, model releases, training, open weights, evals."],
    [3, "AI Factories & Cloud", "Data centres, sovereign compute, cloud capacity."],
    [2, "Silicon & Networks", "Chips, accelerators, fabs, export controls."],
    [1, "Energy & Power", "The watts underneath it all — grid, generation, power deals."]
  ];
  const LAYER_RE = {
    1: /\b(energy|power plants?|gigawatts?|megawatts?|nuclear|electricity|grid)\b/,
    2: /\b(chips?|semiconductors?|gpus?|silicon|tsmc|chip fabs?|fabrication|foundr(?:y|ies)|wafers?|ai accelerators?|export controls?)\b/,
    3: /\b(data cent(?:re|er)s?|datacenters?|ai factor(?:y|ies)|hyperscalers?|cloud regions?|compute capacity|sovereign compute|colocation|ai infrastructure|infrastructure buildouts?)\b/,
    4: /\b(models?|frontier labs?|open[- ]weights?|training runs?|benchmarks?|reasoning|fine[- ]tun\w*|inference)\b/
  };

  const classifyLayer = (signal) => {
    const text = `${signal.title || ""} ${signal.whatChanged || ""} ${signal.desk || ""}`.toLowerCase();
    for (const layer of [1, 2, 3]) {
      if (LAYER_RE[layer].test(text)) return layer;
    }
    if (signal.desk === "Compute & Infrastructure") return 3;
    if (/\b(agents?|agentic)\b/.test(text)) return 5;
    if (LAYER_RE[4].test(text)) return 4;
    return 5;
  };

  const renderLayerCake = (signals) => {
    if (!layerCakeRoot) return;
    const current = signals.filter(isCurrentStory);
    const groups = { 1: [], 2: [], 3: [], 4: [], 5: [] };
    current.forEach((signal) => groups[classifyLayer(signal)].push(signal));
    const hot = current.length
      ? [5, 4, 3, 2, 1].reduce((a, b) => (groups[b].length > groups[a].length ? b : a))
      : null;

    layerCakeRoot.innerHTML = LAYERS.map(([n, name, desc]) => {
      const stories = groups[n];
      const moves = stories
        .slice(0, 2)
        .map((s) => `<article><h4>${escape(s.title)}</h4><p>${escape(s.readThrough || s.whyItMatters)}</p></article>`)
        .join("");
      const movesHtml = moves ? `<div class="cake-moves">${moves}</div>` : "";
      const count = stories.length
        ? `<span class="cake-count">${stories.length} moving</span>`
        : `<span class="cake-count cake-count-quiet">quiet</span>`;
      const hotCls = n === hot && stories.length ? " is-hot" : "";
      const quietCls = stories.length ? "" : " is-quiet";
      return `<article class="cake-layer cake-l${n}${hotCls}${quietCls}">
        <div class="cake-head"><span class="cake-num">L${n}</span><h3>${escape(name)}</h3>${count}</div>
        <p class="cake-desc">${escape(desc)}</p>${movesHtml}</article>`;
    }).join("");

    if (cakeNoteRoot) {
      if (hot && groups[hot].length) {
        const hotName = LAYERS.find(([n]) => n === hot)[1];
        cakeNoteRoot.textContent = `Today the pressure is on L${hot} — ${hotName.toLowerCase()}: ${groups[hot].length} of ${current.length} verified stories move that layer.`;
      } else {
        cakeNoteRoot.textContent = "No verified current stories cleared the bar today, so every layer reads quiet.";
      }
    }
  };

  const renderMarketChatter = () => {
    if (!marketChatterRoot) return;
    marketChatterRoot.innerHTML = (data.marketChatter || [])
      .slice(0, 8)
      .map((item, index) => {
        const platform = item.platform || item.name || "Market";
        const handle = item.handle || item.role || "watch stream";
        const text = item.text || item.role || item.signal || "";
        return `
          <details class="chatter-card" ${index === 0 ? "open" : ""}>
            <summary>
              <span class="chatter-platform">${escape(platform)}</span>
              <strong>${escape(item.name)}</strong>
              <small>${escape(handle)}</small>
            </summary>
            <p>${escape(text)}</p>
            <div class="chatter-read">
              <span>${escape(item.signal || "Market discussion, not primary reporting.")}</span>
              <a href="${safeUrl(item.url)}" target="_blank" rel="noreferrer">Open thread</a>
            </div>
          </details>
        `
      })
      .join("");
  };

  const renderEditionNote = (signals) => {
    if (!frontPageNoteRoot) return;
    const fresh = signals.filter((signal) => signal.freshness === "fresh").length;
    const current = signals.filter(isCurrentStory).length;
    const gcc = signals.filter((signal) => signal.region === "GCC").length;
    frontPageNoteRoot.textContent =
      fresh > 0
        ? `${fresh} fresh stories and ${gcc} GCC-relevant stories are on today's page.`
        : current > 0
          ? `${current} source-backed current stories and ${gcc} GCC-relevant stories are on today's page.`
          : `The edition is using archived source-backed context until the next current story clears the page-one bar.`;
  };

  const renderMeta = (signals) => {
    if (lastReviewedRoot) lastReviewedRoot.textContent = data.reviewed || "";
    if (lastReviewedCardRoot) lastReviewedCardRoot.textContent = data.reviewed || "";
    if (primaryDeskRoot) primaryDeskRoot.textContent = signals[0]?.desk || "Agentic Systems";
    if (primaryRegionRoot) primaryRegionRoot.textContent = signals[0]?.region || "Global";
  };

  const render = () => {
    const signals = visibleSignals();
    renderMeta(signals);
    renderEditionNote(signals);
    const hasLeadStory = renderLead(signals[0], signals);
    renderStoryList(signals, hasLeadStory);
    renderLayerCake(signals);
    renderMarketChatter();
  };

  render();
})();
