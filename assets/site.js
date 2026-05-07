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
})();
