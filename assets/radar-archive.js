(function () {
  const root = document.querySelector("[data-radar-archive]");
  if (!root) return;

  const listRoot = document.querySelector("[data-archive-list]");
  const filtersRoot = document.querySelector("[data-archive-filters]");
  const search = document.querySelector("[data-archive-search]");
  const reviewedRoot = document.querySelector("[data-archive-reviewed]");
  const countRoot = document.querySelector("[data-archive-count]");
  let activeFilter = "All";
  let archive = { reviewed: "Unknown", articleCount: 0, articles: [] };

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

  const categories = () => {
    const found = new Set(["All"]);
    archive.articles.forEach((article) => found.add(article.category || "Uncategorized"));
    return Array.from(found);
  };

  const matches = (article) => {
    const query = (search?.value || "").trim().toLowerCase();
    const filterMatch = activeFilter === "All" || article.category === activeFilter;
    if (!query) return filterMatch;
    const haystack = [
      article.title,
      article.category,
      article.region,
      article.source,
      article.summary,
      article.whyItMatters,
      article.readerQuestion,
    ]
      .join(" ")
      .toLowerCase();
    return filterMatch && haystack.includes(query);
  };

  const renderFilters = () => {
    filtersRoot.innerHTML = categories()
      .map(
        (category) =>
          `<button type="button" data-archive-filter="${escape(category)}" class="${category === activeFilter ? "active" : ""}">${escape(category)}</button>`
      )
      .join("");
  };

  const card = (article) => `
    <article class="archive-card">
      <div class="archive-card-topline">
        <span>${escape(article.publication_date || article.date || "Unknown date")}</span>
        <span>${escape(article.region || "Global")} / ${escape(article.category || "Uncategorized")}</span>
        <strong>${escape(article.score || "n/a")}</strong>
      </div>
      <h2>${escape(article.title)}</h2>
      <p>${escape(article.summary || "")}</p>
      <dl>
        <div><dt>Why it mattered</dt><dd>${escape(article.whyItMatters || "")}</dd></div>
        <div><dt>Reader question</dt><dd>${escape(article.readerQuestion || "")}</dd></div>
        <div><dt>First seen</dt><dd>${escape(article.first_seen || "Unknown")}</dd></div>
        <div><dt>Last seen</dt><dd>${escape(article.last_seen || "Unknown")}</dd></div>
        <div><dt>Freshness</dt><dd>${escape(article.freshness || "Unknown")}</dd></div>
      </dl>
      <footer>
        <span>${escape(article.source || "Source")}</span>
        <a href="${escape(safeUrl(article.source_url || article.url))}" target="_blank" rel="noreferrer">Open source</a>
      </footer>
    </article>
  `;

  const renderList = () => {
    const visible = archive.articles.filter(matches);
    countRoot.textContent = String(archive.articleCount || archive.articles.length || 0);
    listRoot.innerHTML = visible.length
      ? visible.map(card).join("")
      : `<div class="archive-empty"><strong>No matching archived articles.</strong><p>Try a broader category or clear the search.</p></div>`;
  };

  const render = () => {
    reviewedRoot.textContent = archive.reviewed || "Unknown";
    renderFilters();
    renderList();
  };

  filtersRoot.addEventListener("click", (event) => {
    const button = event.target.closest("[data-archive-filter]");
    if (!button) return;
    activeFilter = button.dataset.archiveFilter;
    render();
  });

  search?.addEventListener("input", renderList);

  fetch("data/signal-archive.json", { cache: "no-store" })
    .then((response) => {
      if (!response.ok) throw new Error(`Archive fetch failed: ${response.status}`);
      return response.json();
    })
    .then((payload) => {
      archive = payload;
      render();
    })
    .catch(() => {
      listRoot.innerHTML = `<div class="archive-empty"><strong>Archive unavailable.</strong><p>The daily pipeline has not written archive data yet.</p></div>`;
    });
})();
