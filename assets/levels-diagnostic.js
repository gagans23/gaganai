(function () {
  var mount = document.getElementById("levels-diagnostic");
  if (!mount) return;

  if (!document.getElementById("lvld-fonts")) {
    var f = document.createElement("link");
    f.id = "lvld-fonts";
    f.rel = "stylesheet";
    f.href = "https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Spectral:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap";
    document.head.appendChild(f);
  }

  var css = "" +
    ".lvld{font-family:'Spectral',Georgia,serif;background:#f2efe6;color:#1c1712;border:1px solid #ddd8c9;border-radius:12px;padding:clamp(22px,4vw,34px);max-width:760px;margin:0 auto}" +
    ".lvld .kick{font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#b3661f;margin:0 0 12px}" +
    ".lvld h3{font-family:'Fraunces',serif;font-weight:700;font-size:clamp(24px,3.2vw,30px);line-height:1.1;margin:0 0 10px;color:#1c1712}" +
    ".lvld .lede{color:#6f6459;font-size:15px;line-height:1.55;margin:0 0 6px}" +
    ".lvld .qs{margin-top:20px}" +
    ".lvld .q{margin-bottom:20px}" +
    ".lvld .qlab{font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.12em;text-transform:uppercase;margin:0 0 6px}" +
    ".lvld .qt{font-family:'Fraunces',serif;font-weight:600;font-size:18px;margin:0 0 10px;color:#1c1712}" +
    ".lvld label{display:flex;gap:10px;align-items:flex-start;padding:10px 12px;border:1px solid #ddd8c9;background:#fff;margin-bottom:6px;cursor:pointer;font-size:14px;line-height:1.4;color:#1c1712;transition:border-color .12s,background .12s}" +
    ".lvld label input{margin-top:3px;accent-color:#b3661f}" +
    ".lvld .go{font-family:'IBM Plex Mono',monospace;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#f2efe6;background:#1c1712;border:0;padding:13px 24px;cursor:pointer;border-radius:0;margin-top:6px}" +
    ".lvld .go:hover{background:#b3661f}" +
    ".lvld .warn{color:#b3661f;font-size:13px;margin:10px 0 0;display:none}" +
    ".lvld .out{display:none;margin-top:24px;border-top:1px solid #ddd8c9;padding-top:24px}" +
    ".lvld .res-grid{display:grid;grid-template-columns:240px 1fr;gap:24px;align-items:center}" +
    "@media(max-width:560px){.lvld .res-grid{grid-template-columns:1fr;gap:14px}}" +
    ".lvld .lv{font-family:'Fraunces',serif;font-weight:700;font-size:30px;line-height:1.05;margin:0 0 6px;color:#1c1712}" +
    ".lvld .lvsub{color:#6f6459;font-size:15px;line-height:1.55;margin:0 0 16px}" +
    ".lvld .bn{background:#fff;border:1px solid #ddd8c9;padding:16px 18px}" +
    ".lvld .bn .bl{font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:#8a8f9c;margin:0 0 6px}" +
    ".lvld .bn .bt{font-size:14.5px;line-height:1.5;margin:0;color:#1c1712}" +
    ".lvld .share{display:flex;flex-wrap:wrap;gap:10px;margin-top:20px;align-items:center}" +
    ".lvld .sb{font-family:'IBM Plex Mono',monospace;font-size:12px;letter-spacing:.1em;text-transform:uppercase;text-decoration:none;color:#1c1712;background:none;border:1px solid #1c1712;padding:10px 16px;cursor:pointer;border-radius:0}" +
    ".lvld .sb:hover{background:#1c1712;color:#f2efe6}" +
    ".lvld .sub{margin-top:20px;border-top:1px dashed #ddd8c9;padding-top:18px}" +
    ".lvld .sub p{color:#6f6459;font-size:14px;margin:0 0 10px}" +
    ".lvld .subf{display:flex;gap:8px;flex-wrap:wrap}" +
    ".lvld .subf input[type=email]{flex:1;min-width:200px;border:1px solid #ddd8c9;background:#fff;padding:12px 14px;font-family:'Spectral',serif;font-size:14px;color:#1c1712}" +
    ".lvld .subf input[type=email]:focus{outline:2px solid #b3661f;outline-offset:1px}" +
    ".lvld .subf button{font-family:'IBM Plex Mono',monospace;font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:#f2efe6;background:#b3661f;border:0;padding:12px 18px;cursor:pointer}" +
    ".lvld .agentic{color:#b3661f}.lvld .org{color:#8a8f9c}";
  if (!document.getElementById("lvld-css")) {
    var st = document.createElement("style");
    st.id = "lvld-css";
    st.textContent = css;
    document.head.appendChild(st);
  }

  var Q = [
    { ax: "Substrate", tag: "Org", q: "What can AI see?", o: [
      ["Work lives in people's heads, meetings, and tools AI can't read", 0],
      ["Some docs are accessible; the important context is still tribal", 2],
      ["Most systems of record are queryable by AI", 4],
      ["The company is machine-legible by default", 5]] },
    { ax: "Authority", tag: "Org", q: "What can AI do?", o: [
      ["It can only summarise what humans already wrote", 1],
      ["It drafts and suggests; humans execute everything", 2],
      ["It acts on systems of record, behind approval gates", 4],
      ["It takes bounded action and propagates across teams", 5]] },
    { ax: "Trust", tag: "Agentic", q: "Would you let it act unwatched?", o: [
      ["No — we don't trust it to act on its own", 0],
      ["A human reviews every action before it lands", 2],
      ["It acts within bounded scope; we audit the traces after", 4],
      ["It acts unsupervised because we can prove how it behaved — traces, evals, kill-switch", 5]] },
    { ax: "Memory", tag: "Agentic", q: "Does it compound, or start cold?", o: [
      ["Every run starts from zero", 1],
      ["It remembers within a task, forgets after", 2],
      ["It carries context across tasks and time", 4],
      ["It learns from outcomes and improves its own loops", 5]] },
    { ax: "Extensibility", tag: "Org", q: "Who can extend the system?", o: [
      ["A few power users hold everything together", 1],
      ["Engineering ships it all; the business waits in line", 2],
      ["Non-engineers ship internal tools with guardrails", 4],
      ["Extending the system is how everyone works", 5]] },
    { ax: "Structure", tag: "Org", q: "How has the organisation changed?", o: [
      ["Same 2023 org chart with better autocomplete", 0],
      ["New AI roles bolted on; the structure is unchanged", 2],
      ["Teams and workflows redesigned around agents", 4],
      ["The operating model itself is agent-native", 5]] }
  ];
  var LV = [
    ["L0", "Theater", "AI is in the press release, not the workflow."],
    ["L1", "Productivity", "Individuals are faster. The company is not."],
    ["L2", "Team workflow", "Pockets work; nothing propagates beyond them."],
    ["L3", "Infrastructure", "The substrate is being built; trust is catching up."],
    ["L4", "Compounding OS", "The system improves itself across teams."],
    ["L5", "Self-driving", "The org notices, decides, acts, and learns without a human starting it."]
  ];
  var MOVE = {
    Substrate: "Make your work legible to a machine before you ask it to act.",
    Authority: "Give the system permission to act on systems of record, behind gates.",
    Trust: "You can't grant authority you can't verify. Build the trace and eval layer before you widen autonomy.",
    Memory: "A system that forgets can't compound. Give it durable memory and a learning loop.",
    Extensibility: "Let non-engineers ship tools, or you stall at a few power users.",
    Structure: "Redesign the org around the work, not the 2023 chart with autocomplete."
  };
  var ESC = function (s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); };

  function radar(scores, minIdx) {
    var cx = 210, cy = 150, R = 100, n = 6;
    function pt(i, r) {
      var a = (-90 + i * 60) * Math.PI / 180;
      return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
    }
    var s = '<svg viewBox="0 0 420 300" width="100%" role="img" aria-label="Your maturity profile across the six axes">';
    var k, i;
    for (k = 1; k <= 5; k++) {
      var ring = "";
      for (i = 0; i < n; i++) { var p = pt(i, R * k / 5); ring += (i ? "L" : "M") + p[0].toFixed(1) + "," + p[1].toFixed(1) + " "; }
      s += '<path d="' + ring + 'Z" fill="none" stroke="#ddd8c9" stroke-width="1"/>';
    }
    for (i = 0; i < n; i++) { var e = pt(i, R); s += '<line x1="' + cx + '" y1="' + cy + '" x2="' + e[0].toFixed(1) + '" y2="' + e[1].toFixed(1) + '" stroke="#ddd8c9" stroke-width="1"/>'; }
    var poly = "";
    for (i = 0; i < n; i++) { var sp = pt(i, R * Math.max(scores[i], 0.15) / 5); poly += (i ? "L" : "M") + sp[0].toFixed(1) + "," + sp[1].toFixed(1) + " "; }
    s += '<path d="' + poly + 'Z" fill="rgba(179,102,31,0.16)" stroke="#b3661f" stroke-width="2"/>';
    for (i = 0; i < n; i++) {
      var vp = pt(i, R * Math.max(scores[i], 0.15) / 5);
      var hot = i === minIdx;
      s += '<circle cx="' + vp[0].toFixed(1) + '" cy="' + vp[1].toFixed(1) + '" r="' + (hot ? 5 : 3) + '" fill="' + (hot ? "#b3661f" : "#1c1712") + '"/>';
    }
    for (i = 0; i < n; i++) {
      var lp = pt(i, R + 16), a = -90 + i * 60, anchor = "middle";
      if (Math.cos(a * Math.PI / 180) > 0.3) anchor = "start";
      else if (Math.cos(a * Math.PI / 180) < -0.3) anchor = "end";
      var col = i === minIdx ? "#b3661f" : "#6f6459";
      var wt = i === minIdx ? "700" : "500";
      s += '<text x="' + lp[0].toFixed(1) + '" y="' + (lp[1] + 4).toFixed(1) + '" text-anchor="' + anchor + '" font-family="IBM Plex Mono,monospace" font-size="11" font-weight="' + wt + '" fill="' + col + '">' + Q[i].ax + "</text>";
    }
    return s + "</svg>";
  }

  var wrap = document.createElement("div");
  wrap.className = "lvld";
  var qh = "";
  Q.forEach(function (it, qi) {
    qh += '<div class="q"><p class="qlab ' + (it.tag === "Agentic" ? "agentic" : "org") + '">Q' + (qi + 1) + " · " + it.ax + " · " + it.tag + '</p><p class="qt">' + ESC(it.q) + "</p>";
    it.o.forEach(function (op) {
      qh += '<label><input type="radio" name="lq' + qi + '" value="' + op[1] + '" data-ax="' + it.ax + '"><span>' + ESC(op[0]) + "</span></label>";
    });
    qh += "</div>";
  });
  wrap.innerHTML =
    '<p class="kick">The Philosophical Ledger · Self-Diagnostic</p>' +
    '<h3>Which level is your organisation?</h3>' +
    '<p class="lede">Six questions — four about your organisation, two about your agents. Your real level is your <em>weakest</em> answer. The asymmetry is the diagnostic.</p>' +
    '<div class="qs">' + qh + "</div>" +
    '<button class="go" type="button">Show my level</button>' +
    '<p class="warn">Answer all six to see where you stand.</p>' +
    '<div class="out"></div>';
  mount.appendChild(wrap);

  wrap.addEventListener("change", function (e) {
    if (e.target && e.target.type === "radio") {
      var box = e.target.closest(".q");
      box.querySelectorAll("label").forEach(function (l) { l.style.borderColor = "#ddd8c9"; l.style.background = "#fff"; });
      var lab = e.target.closest("label");
      lab.style.borderColor = "#b3661f"; lab.style.background = "#faf3e8";
    }
  });
  wrap.addEventListener("mouseover", function (e) { var l = e.target.closest && e.target.closest("label"); if (l && l.parentNode.classList.contains("q")) l.style.borderColor = "#b3661f"; });
  wrap.addEventListener("mouseout", function (e) { var l = e.target.closest && e.target.closest("label"); if (l && l.parentNode.classList.contains("q") && !l.querySelector("input").checked) l.style.borderColor = "#ddd8c9"; });

  wrap.querySelector(".go").addEventListener("click", function () {
    var vals = [], axes = [], ok = true, i;
    for (i = 0; i < 6; i++) {
      var sel = wrap.querySelector('input[name="lq' + i + '"]:checked');
      if (!sel) { ok = false; break; }
      vals.push(+sel.value); axes.push(sel.getAttribute("data-ax"));
    }
    var warn = wrap.querySelector(".warn");
    if (!ok) { warn.style.display = "block"; return; }
    warn.style.display = "none";
    var min = Math.min.apply(null, vals), bi = vals.indexOf(min), ax = axes[bi], lv = LV[min];
    var shareText = "My AI-org level: " + lv[0] + " · " + lv[1] + ". Bottleneck: " + ax + ". Where do you stand? — The Philosophical Ledger";
    var shareUrl = "https://gagansachdeva.com/writing/levels-revisited-for-agents.html";
    var profile = Q.map(function (q, i) {
      return "  " + (q.ax + " ..............").slice(0, 15) + " " + vals[i] + "/5" + (i === bi ? "  <- bottleneck" : "");
    }).join("\n");
    var emailBody =
      "Your AI-org diagnostic — The Philosophical Ledger\n\n" +
      "LEVEL: " + lv[0] + " · " + lv[1] + "\n" + lv[2] + "\n\n" +
      "BOTTLENECK: " + ax + "\n" + MOVE[ax] + "\n\n" +
      "YOUR PROFILE (weakest axis = your real level):\n" + profile + "\n\n" +
      "Read the framework and find where you stand:\n" + shareUrl;
    var out = wrap.querySelector(".out");
    out.innerHTML =
      '<div class="res-grid"><div>' + radar(vals, bi) + "</div><div>" +
      '<p class="kick">Your level</p>' +
      '<p class="lv">' + lv[0] + " · " + lv[1] + "</p>" +
      '<p class="lvsub">' + ESC(lv[2]) + "</p>" +
      '<div class="bn"><p class="bl">Your bottleneck · ' + ax + '</p><p class="bt">' + ESC(MOVE[ax]) + "</p></div>" +
      "</div></div>" +
      '<div class="share">' +
      '<button class="sb" data-share type="button">Share my result</button>' +
      '<a class="sb" target="_blank" rel="noreferrer" href="https://wa.me/?text=' + encodeURIComponent(shareText + " " + shareUrl) + '">WhatsApp</a>' +
      '<a class="sb" href="mailto:?subject=' + encodeURIComponent("My AI-org scorecard: " + lv[0] + " · " + lv[1]) + "&body=" + encodeURIComponent(emailBody) + '">Email my scorecard</a>' +
      "</div>" +
      '<div class="sub"><p>Get the climb playbook for ' + lv[0] + " — the specific moves to clear your " + ax + ' bottleneck. No filler between issues.</p>' +
      '<form class="subf" action="https://buttondown.email/api/emails/embed-subscribe/gagan" method="post" target="popupwindow">' +
      '<input type="email" name="email" placeholder="you@example.com" aria-label="Email address" required>' +
      '<input type="hidden" name="tag" value="levels-diagnostic-' + lv[0].toLowerCase() + '">' +
      '<input type="hidden" name="metadata__bottleneck" value="' + ax + '">' +
      '<input type="hidden" name="metadata__source" value="levels-diagnostic">' +
      '<input type="hidden" name="redirect" value="https://gagansachdeva.com/thanks.html">' +
      '<button type="submit">Send me the playbook</button></form></div>';
    out.style.display = "block";
    var btn = out.querySelector("[data-share]");
    btn.addEventListener("click", function () {
      if (navigator.share) {
        navigator.share({ title: "AI-org diagnostic", text: shareText, url: shareUrl }).catch(function () {});
      } else if (navigator.clipboard) {
        navigator.clipboard.writeText(shareText + " " + shareUrl).then(function () { btn.textContent = "Copied"; });
      }
    });
    out.scrollIntoView({ behavior: "smooth", block: "nearest" });
  });
})();
