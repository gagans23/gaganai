(() => {
  const map = document.querySelector('.journey-map');
  if (!map) return;
  const links = [...map.querySelectorAll('.journey-step')];
  const chapters = links.map(a => document.querySelector(a.getAttribute('href')));
  const motion = document.querySelector('#journey-motion');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let paused = reduced.matches, queued = false;
  function setMotion() {
    map.classList.toggle('motion-paused', paused);
    motion.textContent = paused ? 'Enable motion' : 'Pause motion';
    motion.setAttribute('aria-pressed', String(paused));
    map.style.setProperty('--tilt', '0deg');
  }
  function select(index) {
    links.forEach((a,i) => {
      a.classList.toggle('is-active', i === index);
      if (i === index) a.setAttribute('aria-current','step');
      else a.removeAttribute('aria-current');
    });
    document.querySelector('#journey-position').textContent = String(index+1).padStart(2,'0')+' / 06';
    document.querySelector('#journey-lesson').textContent = chapters[index].dataset.lesson;
  }
  function track() {
    queued = false;
    let best = 0, distance = Infinity;
    chapters.forEach((c,i) => {
      const d = Math.abs(c.getBoundingClientRect().top - innerHeight * .3);
      if (d < distance) { distance = d; best = i; }
    });
    select(best);
  }
  addEventListener('scroll', () => {
    if (!queued) { queued = true; requestAnimationFrame(track); }
  }, {passive:true});
  links.forEach((a,i) => a.addEventListener('click', () => {
    const details = chapters[i].querySelector('details');
    if (details) details.open = true;
    select(i);
  }));
  motion.addEventListener('click', () => { paused = !paused; setMotion(); });
  reduced.addEventListener('change', () => { paused = reduced.matches; setMotion(); });
  map.addEventListener('pointermove', e => {
    if (paused || e.pointerType !== 'mouse') return;
    const r = map.getBoundingClientRect();
    map.style.setProperty('--tilt', ((e.clientX-r.left)/r.width-.5)*9+'deg');
  });
  map.addEventListener('pointerleave', () => map.style.setProperty('--tilt','0deg'));
  setMotion(); track();
})();
