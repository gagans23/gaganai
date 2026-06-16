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
