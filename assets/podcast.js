(function () {
  const root = document.querySelector("[data-podcast-app]");
  const data = window.GAGANAI_PODCASTS;
  if (!root || !data) return;

  const episodes = data.episodes.slice().sort((a, b) => b.date.localeCompare(a.date));
  const filtersRoot = document.querySelector("[data-podcast-filters]");
  const feedRoot = document.querySelector("[data-episode-feed]");
  const showRoot = document.querySelector("[data-show-grid]");
  const themeRoot = document.querySelector("[data-theme-list]");
  const timelineRoot = document.querySelector("[data-podcast-timeline]");
  const lensRoot = document.querySelector("[data-lens-grid]");
  const search = document.querySelector("[data-podcast-search]");
  const themeTitle = document.querySelector("[data-theme-title]");
  const themeBody = document.querySelector("[data-theme-body]");
  let activeFilter = "All";
  let activeTheme = data.themes[0].id;

  const escape = (value) =>
    String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");

  const safeUrl = (value) => {
    try {
      const url = new URL(String(value || "").trim(), window.location.href);
      return url.protocol === "http:" || url.protocol === "https:" ? url.href : "#";
    } catch {
      return "#";
    }
  };

  const matches = (episode) => {
    const query = (search?.value || "").trim().toLowerCase();
    const filterMatch =
      activeFilter === "All" ||
      episode.category === activeFilter ||
      episode.tags.includes(activeFilter) ||
      episode.show === activeFilter;
    if (!query) return filterMatch;
    const haystack = [
      episode.show,
      episode.title,
      episode.guest,
      episode.category,
      episode.coreMessage,
      episode.keyPoints.join(" "),
      episode.governanceRead,
      episode.action,
      episode.tags.join(" ")
    ]
      .join(" ")
      .toLowerCase();
    return filterMatch && haystack.includes(query);
  };

  const renderMetrics = () => {
    document.querySelector("[data-reviewed]").textContent = data.reviewed;
    document.querySelector("[data-show-count]").textContent = data.shows.length;
    document.querySelector("[data-episode-count]").textContent = data.episodes.length;
    document.querySelector("[data-theme-count]").textContent = data.themes.length;
    document.querySelector("[data-youtube-count]").textContent = new Set([
      ...data.shows.map((show) => show.youtube),
      ...data.episodes.map((episode) => episode.youtube)
    ]).size;
  };

  const renderFilters = () => {
    filtersRoot.innerHTML = data.filters
      .map((filter) => `<button type="button" data-filter="${escape(filter)}" class="${filter === activeFilter ? "active" : ""}">${escape(filter)}</button>`)
      .join("");
  };

  const renderShows = () => {
    showRoot.innerHTML = data.shows
      .map(
        (show) => `
          <article class="show-card">
            <div class="show-topline"><span>${escape(show.lane)}</span><strong>${escape(show.signal)}</strong></div>
            <h3>${escape(show.name)}</h3>
            <p>${escape(show.why)}</p>
            <footer>
              <a href="${escape(safeUrl(show.youtube))}" target="_blank" rel="noreferrer">YouTube</a>
              <a href="${escape(safeUrl(show.source))}" target="_blank" rel="noreferrer">Show site</a>
            </footer>
          </article>
        `
      )
      .join("");
  };

  const episodeCard = (episode) => `
    <article class="episode-card" data-theme="${escape(episode.theme)}">
      <div class="episode-topline">
        <span>${escape(episode.date)}</span>
        <span>${escape(episode.show)} / ${escape(episode.category)}</span>
      </div>
      <h3>${escape(episode.title)}</h3>
      <p class="guest">${escape(episode.guest)}</p>
      <p>${escape(episode.coreMessage)}</p>
      <div class="message-block">
        <strong>Key things to remember</strong>
        <ul>${episode.keyPoints.map((point) => `<li>${escape(point)}</li>`).join("")}</ul>
      </div>
      <dl>
        <div><dt>Transcript status</dt><dd>${escape(episode.transcriptStatus)}</dd></div>
        <div><dt>Governance read</dt><dd>${escape(episode.governanceRead)}</dd></div>
        <div><dt>Action</dt><dd>${escape(episode.action)}</dd></div>
      </dl>
      <footer>
        <button type="button" data-theme-jump="${escape(episode.theme)}">Map theme</button>
        <a href="${escape(safeUrl(episode.youtube))}" target="_blank" rel="noreferrer">YouTube</a>
        <a href="${escape(safeUrl(episode.source))}" target="_blank" rel="noreferrer">Source notes</a>
      </footer>
    </article>
  `;

  const renderEpisodes = () => {
    const visible = episodes.filter(matches);
    feedRoot.innerHTML = visible.length
      ? visible.map(episodeCard).join("")
      : `<div class="empty-state"><strong>No matching episodes.</strong><p>Try another theme, show, or keyword.</p></div>`;
  };

  const renderThemes = () => {
    themeRoot.innerHTML = data.themes
      .map((theme) => {
        const count = episodes.filter((episode) => episode.theme === theme.id).length;
        return `
          <button type="button" data-theme-select="${escape(theme.id)}" class="${theme.id === activeTheme ? "active" : ""}">
            <strong>${escape(theme.label)}</strong>
            <span>${count} episodes</span>
          </button>
        `;
      })
      .join("");
    const theme = data.themes.find((item) => item.id === activeTheme) || data.themes[0];
    themeTitle.textContent = theme.label;
    themeBody.textContent = theme.body;
  };

  const renderLens = () => {
    lensRoot.innerHTML = data.lens
      .map(
        (item, index) => `
          <article>
            <span>${String(index + 1).padStart(2, "0")}</span>
            <h3>${escape(item.label)}</h3>
            <p>${escape(item.detail)}</p>
          </article>
        `
      )
      .join("");
  };

  const renderTimeline = () => {
    const visible = episodes.filter(matches);
    timelineRoot.innerHTML = visible
      .map(
        (episode) => `
          <article class="timeline-item" data-theme="${escape(episode.theme)}">
            <time>${escape(episode.date)}</time>
            <div>
              <span>${escape(episode.show)} / ${escape(episode.category)}</span>
              <h3>${escape(episode.title)}</h3>
              <p>${escape(episode.coreMessage)}</p>
            </div>
          </article>
        `
      )
      .join("");
  };

  const render = () => {
    renderFilters();
    renderEpisodes();
    renderThemes();
    renderTimeline();
  };

  filtersRoot.addEventListener("click", (event) => {
    const button = event.target.closest("[data-filter]");
    if (!button) return;
    activeFilter = button.dataset.filter;
    render();
  });

  root.addEventListener("click", (event) => {
    const button = event.target.closest("[data-theme-select], [data-theme-jump]");
    if (!button) return;
    activeTheme = button.dataset.themeSelect || button.dataset.themeJump;
    renderThemes();
    document.querySelectorAll("[data-theme]").forEach((node) => {
      node.classList.toggle("theme-active", node.dataset.theme === activeTheme);
    });
  });

  search?.addEventListener("input", () => {
    renderEpisodes();
    renderTimeline();
  });

  renderMetrics();
  renderShows();
  renderLens();
  render();
})();
