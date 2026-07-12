// Related reading — renders "Keep reading" cards at the bottom of every essay.
// Driven by data/writing.json (the same manifest as the homepage latest-card),
// so new essays appear everywhere automatically. Scoring: same category first,
// then recency. Fails silently: no manifest, no block.
(function () {
  var slot = document.querySelector("[data-related-essays]");
  if (!slot) return;
  fetch("../data/writing.json", { cache: "no-store" })
    .then(function (r) { return r.json(); })
    .then(function (d) {
      var items = (d && d.items) || [];
      if (items.length < 2) return;
      var here = location.pathname.split("/").pop();
      var slugOf = function (e) { return (e.href || "").split("/").pop(); };
      var cur = null;
      var pool = [];
      items.forEach(function (e) {
        if (slugOf(e) === here) cur = e; else pool.push(e);
      });
      pool.sort(function (a, b) {
        var score = function (e) { return cur && e.category === cur.category ? 1 : 0; };
        return (score(b) - score(a)) || String(b.date || "").localeCompare(String(a.date || ""));
      });
      var top = pool.slice(0, 3);
      if (!top.length) return;
      var esc = function (s) {
        return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
          return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
        });
      };
      var css =
        ".related-essays-slot{max-width:760px;margin:2.6rem auto 1.2rem;padding:0 24px;box-sizing:border-box}" +
        ".rel-h{font-family:'IBM Plex Mono',ui-monospace,monospace;font-size:.68rem;font-weight:600;letter-spacing:.18em;text-transform:uppercase;color:#b3661f;margin:0 0 .9rem}" +
        ".rel-grid{display:grid;gap:10px;margin:0}" +
        ".rel-card{display:block;text-decoration:none;color:inherit;border:1px solid rgba(90,80,60,.28);border-left:3px solid #b3661f;border-radius:0 8px 8px 0;background:rgba(179,102,31,.05);padding:14px 18px;transition:background .15s ease,transform .15s ease}" +
        ".rel-card:hover{background:rgba(179,102,31,.10);transform:translateY(-1px)}" +
        ".rel-card strong{display:block;font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:1.08rem;line-height:1.3}" +
        ".rel-card small{display:block;margin-top:4px;font-family:'IBM Plex Mono',ui-monospace,monospace;font-size:.6rem;letter-spacing:.1em;text-transform:uppercase;opacity:.62}" +
        ".rel-card p{margin:.45rem 0 0;font-size:.92rem;line-height:1.5;opacity:.75;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}";
      slot.innerHTML =
        "<style>" + css + "</style>" +
        '<h2 class="rel-h">Keep reading</h2>' +
        '<div class="rel-grid">' +
        top.map(function (e) {
          return '<a class="rel-card" href="' + esc(slugOf(e)) + '">' +
            "<strong>" + esc(e.title) + "</strong>" +
            "<small>" + esc(e.dateLabel || "") + (e.readTime ? " · " + esc(e.readTime) : "") + (e.category ? " · " + esc(e.category) : "") + "</small>" +
            "<p>" + esc(e.summary || "") + "</p></a>";
        }).join("") +
        "</div>";
    })
    .catch(function () {});
})();
