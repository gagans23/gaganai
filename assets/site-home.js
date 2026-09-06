// Live editorial data stays independent from the optional motion and sound layer.
(() => {
  const signal = document.querySelector('[data-live-signal]');
  const write = (root, key, value) => { const el = root.querySelector(`[data-${key}]`); if (el) el.textContent = value; };
  const get = async url => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 8000);
    try { const response = await fetch(url, {cache:'no-store', signal:controller.signal}); if (!response.ok) throw new Error('Unavailable'); return await response.json(); }
    finally { clearTimeout(timer); }
  };
  if (signal) Promise.all([get('data/signal-gate.json'), get('data/knowledge-graph.json')]).then(([gate,graph]) => {
    const lead = gate.attractors?.[0];
    if (!lead || !gate.generated) throw new Error('No edition');
    const date = new Date(`${gate.generated}T00:00:00Z`);
    if (!Number.isFinite(date.getTime())) throw new Error('Missing date');
    const age = Math.max(0, Math.floor((Date.now()-date.getTime())/86400000));
    const formatted = date.toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'});
    write(signal,'live-freshness',age>3 ? `Older edition · ${age} days old` : age===0 ? 'Updated today' : `Updated ${age} day${age===1?'':'s'} ago`);
    write(signal,'live-title',lead.title); write(signal,'live-thesis',lead.thesis);
    write(signal,'live-updated',`Edition published ${formatted}`);
    write(signal,'live-source',`Sources: signal-gate.json · knowledge-graph.json. Graph generated ${graph.generated || 'date unavailable'}.`);
    write(signal,'live-cadence',age>3 ? 'This edition is more than three days old. Read it as context, rather than a current update.' : 'Publication date reflects the signal pipeline. Individual evidence dates are shown in the full brief.');
    for (const [key,value,label] of [['stimuli',gate.stats?.stimuli,'stimuli'],['entities',graph.stats?.entities,'entities'],['signals',gate.stats?.signal,'passed'],['attractors',gate.stats?.attractors,'directions']]) write(signal,`live-${key}`,`${value ?? '—'} ${label}`);
  }).catch(() => {
    write(signal,'live-freshness','Latest edition unavailable');
    write(signal,'live-updated','Open the Situation Room for published editions.');
  });
  const card = document.querySelector('[data-writing-card]');
  if (card) get('data/writing.json').then(manifest => {
    const item = (manifest.items || []).filter(x=>x.title && /^writing\/[a-z0-9-]+\.html$/.test(x.href)).sort((a,b)=>String(b.date||'').localeCompare(String(a.date||'')))[0];
    if (!item) return;
    card.href=item.href;
    write(card,'writing-title',item.title); write(card,'writing-summary',item.summary);
    write(card,'writing-meta',[item.dateLabel,item.readTime,item.category].filter(Boolean).join(' · '));
  }).catch(()=>{});
})();
