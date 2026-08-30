const canvas = document.querySelector("[data-context-field]");
const context = canvas?.getContext("2d");
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

if (canvas && context) {
  const points = Array.from({ length: 72 }, (_, index) => ({
    angle: (Math.PI * 2 * index) / 72,
    radius: 0.18 + ((index * 17) % 41) / 100,
    speed: 0.00018 + ((index % 7) * 0.000035),
    drift: (index % 5) * 0.17,
  }));

  let width = 0;
  let height = 0;
  let animationFrame = 0;

  const resize = () => {
    const ratio = window.devicePixelRatio || 1;
    width = canvas.clientWidth;
    height = canvas.clientHeight;
    canvas.width = Math.max(1, Math.floor(width * ratio));
    canvas.height = Math.max(1, Math.floor(height * ratio));
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
  };

  const draw = (time = 0) => {
    context.clearRect(0, 0, width, height);
    const cx = width * 0.66;
    const cy = height * 0.47;
    const scale = Math.min(width, height) * 0.82;

    context.lineWidth = 1;
    points.forEach((point, index) => {
      const theta = point.angle + time * point.speed;
      const wobble = Math.sin(time * 0.0004 + point.drift) * 0.026;
      const radius = (point.radius + wobble) * scale;
      const x = cx + Math.cos(theta) * radius * 0.78;
      const y = cy + Math.sin(theta) * radius * 0.46;

      if (index % 3 === 0) {
        context.beginPath();
        context.moveTo(cx, cy);
        context.lineTo(x, y);
        context.strokeStyle = "rgba(246,239,228,0.045)";
        context.stroke();
      }

      context.beginPath();
      context.arc(x, y, index % 9 === 0 ? 2.4 : 1.4, 0, Math.PI * 2);
      context.fillStyle = index % 11 === 0 ? "rgba(53,198,181,0.58)" : "rgba(246,239,228,0.26)";
      context.fill();
    });

    if (!prefersReducedMotion) {
      animationFrame = window.requestAnimationFrame(draw);
    }
  };

  resize();
  draw(0);
  window.addEventListener("resize", resize);

  if (!prefersReducedMotion) {
    animationFrame = window.requestAnimationFrame(draw);
  }

  window.addEventListener("pagehide", () => window.cancelAnimationFrame(animationFrame));
}
