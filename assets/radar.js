(function () {
  const root = document.querySelector("[data-radar-app]");
  const data = window.GAGANAI_RADAR;
  if (!root || !data) return;

  const allSignals = (data.signals || []).slice().sort((a, b) => b.date.localeCompare(a.date));
  const leadStoryRoot = document.querySelector("[data-lead-story]");
  const storyListRoot = document.querySelector("[data-story-list]");
  const frontPageNoteRoot = document.querySelector("[data-front-page-note]");
  const thesisTitleRoot = document.querySelector("[data-sidebar-thesis-title]");
  const thesisBodyRoot = document.querySelector("[data-sidebar-thesis-body]");
  const joinTheDotsRoot = document.querySelector("[data-join-the-dots]");
  const predictionListRoot = document.querySelector("[data-prediction-list]");
  const sourceTrailRoot = document.querySelector("[data-source-trail]");
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
        <a href="${escape(signal.url)}" target="_blank" rel="noreferrer">Read original source</a>
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
        <a href="${escape(signal.url)}" target="_blank" rel="noreferrer">${escape(signal.source)}</a>
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

  const buildDeskSummary = (signals) => {
    const counts = {};
    signals.forEach((signal) => {
      const desk = signal.desk || "General";
      counts[desk] = (counts[desk] || 0) + 1;
    });
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3);
  };

  const renderThesis = (signals) => {
    if (!thesisTitleRoot || !thesisBodyRoot) return;
    const topDesk = buildDeskSummary(signals)[0];
    const currentCount = signals.filter(isCurrentStory).length;
    const lead = signals[0];

    if (!lead) {
      thesisTitleRoot.textContent = "The edition is thin.";
      thesisBodyRoot.textContent = "No credible stories cleared the page-one bar for this view.";
      return;
    }

    thesisTitleRoot.textContent =
      currentCount > 0
        ? `Today's news points toward ${String((topDesk && topDesk[0]) || lead.desk || "a new pressure point").toLowerCase()}.`
        : `The market is still leaning toward ${String((topDesk && topDesk[0]) || lead.desk || "the same pressure point").toLowerCase()}.`;
    thesisBodyRoot.textContent =
      currentCount > 0
        ? `The strongest source-backed stories in this edition suggest that ${lead.whyItMatters}`
        : `There is not enough verified current news on the page today, so the edition is leaning on the strongest recent stories. The pattern still worth watching is this: ${lead.whyItMatters}`;
  };

  const renderJoinTheDots = (signals) => {
    if (!joinTheDotsRoot) return;
    const currentSignals = signals.filter(isCurrentStory);
    const items = currentSignals.slice(0, 3).map(
      (signal) => `
        <article>
          <h4>${escape(signal.title)}</h4>
          <p>${escape(signal.whyItMatters)}</p>
        </article>
      `
    );
    joinTheDotsRoot.innerHTML = items.length
      ? items.join("")
      : `<article><h4>No strong story chain yet.</h4><p>Until fresher stories clear the bar, the edition will not pretend there is a clear narrative arc to connect.</p></article>`;
  };

  const renderPredictions = (signals) => {
    if (!predictionListRoot) return;
    const top = signals.filter(isCurrentStory).slice(0, 3);
    const predictions = top.map((signal) => ({
      title: signal.title,
      body: signal.readThrough || signal.whyItMatters
    }));
    predictionListRoot.innerHTML = predictions.length
      ? predictions
      .map(
        (item) => `
          <article>
            <h4>${escape(item.title)}</h4>
            <p>${escape(item.body)}</p>
          </article>
        `
      )
      .join("")
      : `<article><h4>No credible short-term call yet.</h4><p>The right move today is to wait for stronger reported developments rather than over-predict from stale context.</p></article>`;
  };

  const renderSources = (signals) => {
    if (!sourceTrailRoot) return;
    sourceTrailRoot.innerHTML = signals
      .slice(0, 6)
      .map(
        (signal) => `
          <article>
            <h4>${escape(signal.source)}</h4>
            <p>${escape(signal.title)}</p>
            <p>${sourceQualityBadge(signal)}</p>
            <a href="${escape(signal.url)}" target="_blank" rel="noreferrer">Open source</a>
          </article>
        `
      )
      .join("");
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
              <a href="${escape(item.url)}" target="_blank" rel="noreferrer">Open thread</a>
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
    renderThesis(signals);
    renderJoinTheDots(signals);
    renderPredictions(signals);
    renderSources(signals);
    renderMarketChatter();
  };

  render();
})();
