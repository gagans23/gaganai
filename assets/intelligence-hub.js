/* One evidence-driven surface. No generated answers or simulated live activity. */
(() => {
 'use strict';
 const $=id=>document.getElementById(id);
 const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const safe=value=>{try{const u=new URL(value,location.href);return /^https?:$/.test(u.protocol)?u.href:'#';}catch{return '#';}};
 const date=value=>{const d=new Date(value);return Number.isFinite(d.getTime())?d:null;};
 const labelDate=value=>date(value)?.toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'})||'Date not recorded';
 const get=async(path,text=false)=>{const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),12000);try{const r=await fetch(path,{cache:'no-store',signal:controller.signal});if(!r.ok)throw Error(path);return text?await r.text():await r.json();}finally{clearTimeout(timer);}};
 let records=[],graph={nodes:[],edges:[]},statuses=new Map(),entity='',limit=12,mapRefresh=()=>{},filterReady=false;
 $('map-entity').value='';
 const values=()=>({q:$('feed-query').value.trim().toLowerCase(),desk:$('feed-desk').value,days:Number($('feed-window').value),status:$('feed-status').value});
 const makeOptions=(el,items)=>items.forEach(item=>{const opt=document.createElement('option');opt.value=item;opt.textContent=item;el.append(opt);});
 function chooseEntity(value){entity=value;$('map-entity').value=value;limit=12;const node=graph.nodes.find(n=>n.id===value);$('map-selection').textContent=node?`${node.id} · ${node.count} source mentions. The evidence feed is filtered to this entity.`:'Drag to rotate. Select a point to explore its evidence.';mapRefresh();renderFeed();}
 function renderFeed(){
  if(!filterReady)return;
  const f=values(),cutoff=Date.now()-f.days*86400000;
  const matchingRecords=records.filter(r=>(!entity||(r.entities||[]).includes(entity))&&(!f.desk||r.desk===f.desk)&&(!f.status||(f.status==='passed'?['mapped','unbound'].includes(r.state):r.state===f.status))&&(!f.days||(r.time&&r.time>=cutoff))&&(!f.q||r.search.includes(f.q)));
  const groups=new Map();matchingRecords.forEach(r=>{const key=r.title.toLowerCase().replace(/\s+/g,' ').trim();if(groups.has(key))groups.get(key).copies.push(r);else groups.set(key,{...r,copies:[r]});});
  const matched=[...groups.values()];
  $('feed-count').textContent=`${matched.length} stories from ${matchingRecords.length} matching records · ${records.length} in the ledger`;
  $('entity-chips').replaceChildren();if(entity){const b=document.createElement('button');b.className='entity-chip';b.type='button';b.textContent=`${entity} ×`;b.setAttribute('aria-label',`Remove ${entity} filter`);b.addEventListener('click',()=>chooseEntity(''));$('entity-chips').append(b);}
  const statusNames={mapped:'Supports a direction',unbound:'Passed · not yet bound',noise:'Rejected by the gate',unclassified:'Not yet classified'};
  $('feed-results').innerHTML=matched.length?matched.slice(0,limit).map(r=>`<article class="feed-item"><div class="record-meta"><time>${esc(labelDate(r.signalDate||r.date||r.firstSeen))}</time><span>${esc(r.desk||r.category||'Uncategorised')}</span></div><div><h3><a href="${esc(safe(r.url))}" target="_blank" rel="noopener noreferrer">${esc(r.title)}</a></h3>${r.whatChanged?`<p>${esc(r.whatChanged)}</p>`:''}<p class="record-tags">${esc(statusNames[r.state])} · ${esc(r.source)}${r.region?' · '+esc(r.region):''}</p>${r.copies.length>1?`<details><summary>${r.copies.length} source records for this story</summary>${r.copies.map(c=>`<p><a href="${esc(safe(c.url))}" target="_blank" rel="noopener noreferrer">${esc(c.source)} · ${esc(labelDate(c.signalDate||c.firstSeen))} ↗</a></p>`).join('')}</details>`:''}${r.whyItMatters?`<details><summary>Why this was collected</summary><p>${esc(r.whyItMatters)}</p><p class="record-tags">Collection note, not an independently verified prediction.</p></details>`:''}</div><a class="source-arrow" href="${esc(safe(r.url))}" target="_blank" rel="noopener noreferrer" aria-label="Open source: ${esc(r.title)}">↗</a></article>`).join(''):'<div class="hub-empty"><h3>No matching records.</h3><p>Try a wider date range or reset the filters. We do not fill gaps with invented stories.</p></div>';
  $('feed-more').hidden=matched.length<=limit;
  $('feed-more').textContent=`Show more evidence (${Math.min(12,Math.max(0,matched.length-limit))}) ↓`;
 }
 $('feed-filters').addEventListener('submit',e=>e.preventDefault());
 for(const id of ['feed-query','feed-desk','feed-window','feed-status'])$(id).addEventListener(id==='feed-query'?'input':'change',()=>{limit=12;renderFeed();});
 $('feed-clear').addEventListener('click',()=>{$('feed-filters').reset();chooseEntity('');});
 $('feed-more').addEventListener('click',()=>{limit+=12;renderFeed();});
 $('map-entity').addEventListener('change',e=>chooseEntity(e.target.value));
 $('show-rejected').addEventListener('click',()=>{$('feed-filters').reset();$('feed-status').value='noise';chooseEntity('');});
 $('hub-print').addEventListener('click',()=>window.print());
 const list=items=>'<ul>'+(items||[]).map(x=>`<li>${esc(x)}</li>`).join('')+'</ul>';
 function renderDirections(gate,momentum){
  $('hub-directions').innerHTML=(gate.attractors||[]).map((a,i)=>{
   const trend=momentum?.trajectory?.find(t=>t.id===a.id),max=Math.max(trend?.recent||0,trend?.prior||0,1);
   const trendHTML=trend?`<div class="trend-row"><div><strong>${esc(trend.trend)}</strong><p>${esc(trend.detail)}<br>Window ending ${esc(labelDate(momentum.generated))}</p></div><div class="trend-bars" role="img" aria-label="Prior period ${esc(trend.prior)} records; recent period ${esc(trend.recent)} records"><i style="height:${Math.max(2,32*trend.prior/max)}px"></i><i style="height:${Math.max(2,32*trend.recent/max)}px"></i></div></div>`:'';
   return `<article class="direction-card" id="${esc(a.id)}"><div class="direction-meta"><span>0${i+1} / EDITORIAL DIRECTION</span><span>${esc(a.strengthLabel||'Published')}</span></div><h3>${esc(a.title)}</h3><p class="decision">${esc(a.decision||a.thesis)}</p>${trendHTML}<details><summary>Open the decision brief</summary><div class="brief-body"><h4>The read</h4><p>${esc(a.why||a.thesis)}</p><h4>What to do now</h4>${list(a.actNow)}<h4>What to watch</h4>${list(a.watchNext)}<h4>What would change this view</h4><p>${esc(a.disconfirming||'No falsification criteria recorded.')}</p><h4>Supporting evidence</h4><div class="brief-source-list">${(a.signals||[]).map(s=>`<a href="${esc(safe(s.url))}" target="_blank" rel="noopener noreferrer">${esc(s.title)} ↗<br><small>${esc(labelDate(s.date))}</small></a>`).join('')}</div></div></details></article>`;
  }).join('')||'<p>No editorial directions have been published for this edition.</p>';
 }
 function renderForming(m){
  if(!m){$('hub-forming').innerHTML='<p>Emerging-pattern data is unavailable for this edition. The source feed remains available.</p>';return;}
  $('momentum-period').textContent=`Analysis as of ${labelDate(m.generated)} · ${m.windowDays}-day comparison windows · ${m.ledgerRecords} ledger records`;
  $('momentum-method').textContent=m.method||'Momentum compares recorded activity, not the whole market.';
  $('hub-forming').innerHTML=(m.forming||[]).map(c=>`<article class="forming-card"><p class="hub-kicker">${esc(c.readiness==='close'?'Ready for editorial review':c.readiness||'Developing')}</p><h3>${esc(c.label)}</h3><div class="forming-counts"><div><strong>${esc(c.count)}</strong><span>signals</span></div><div><strong>${esc(c.distinctActors)}</strong><span>actors</span></div></div><p>${esc(c.gap)}</p><details><summary>Inspect this pattern</summary><p><strong>Heuristic implication:</strong> ${esc(c.whatFollows)}</p><ul>${(c.examples||[]).map(e=>`<li><a href="${esc(safe(e.url))}" target="_blank" rel="noopener noreferrer">${esc(e.title)} ↗</a><br><small>${esc(labelDate(e.date))}</small></li>`).join('')}</ul></details></article>`).join('')||'<p>No clusters currently meet the published evidence threshold.</p>';
 }
 function initialiseMap(){
  const canvas=$('evidence-map'),ctx=canvas.getContext('2d');if(!ctx||!graph.nodes.length)return;
  $('map-fallback').hidden=true;const control=$('map-motion');control.hidden=false;
  const reduce=matchMedia('(prefers-reduced-motion: reduce)');let paused=reduce.matches,visible=true,width=0,height=0,frame=0,last=0,angle=.3,tilt=.15,drag=null,projected=[];
  const hash=s=>[...s].reduce((h,c)=>(h*31+c.charCodeAt(0))>>>0,0);
  const nodes=[...graph.nodes].sort((a,b)=>hash(a.id)-hash(b.id)).map((n,i)=>{const y=1-2*(i+.5)/graph.nodes.length,rad=Math.sqrt(1-y*y),a=i*2.39996323;return {...n,x:Math.cos(a)*rad,y,z:Math.sin(a)*rad};});
  const byId=new Map(nodes.map(n=>[n.id,n]));
  const edges=graph.edges.filter(e=>byId.has(e.source)&&byId.has(e.target));
  const label=()=>{control.textContent=paused?'Play motion':'Pause motion';control.setAttribute('aria-pressed',String(paused));};label();
  const project=n=>{const x=n.x*Math.cos(angle)-n.z*Math.sin(angle),z=n.x*Math.sin(angle)+n.z*Math.cos(angle),y=n.y*Math.cos(tilt)-z*Math.sin(tilt),depth=n.y*Math.sin(tilt)+z*Math.cos(tilt),p=3.5/(3.5+depth);return {x:width/2+x*Math.min(width*.33,height*.37)*p,y:height/2+y*Math.min(width*.33,height*.37)*p,z:depth,p};};
  function draw(now){frame=0;if(!width||!height)return;if(!paused&&!drag&&visible&&!document.hidden)angle+=Math.min(.04,(now-last)/1000||0)*.1;last=now;ctx.clearRect(0,0,width,height);
   // Reference meridians show the 3D volume; they are not evidence edges.
   ctx.strokeStyle='rgba(178,185,145,.13)';ctx.lineWidth=.6;
   for(let ring=0;ring<3;ring++){ctx.beginPath();for(let k=0;k<=96;k++){const t=k*Math.PI*2/96;const point=project(ring===0?{x:Math.cos(t)*1.12,y:Math.sin(t)*1.12,z:0}:ring===1?{x:Math.cos(t)*1.12,y:0,z:Math.sin(t)*1.12}:{x:0,y:Math.cos(t)*1.12,z:Math.sin(t)*1.12});if(k===0)ctx.moveTo(point.x,point.y);else ctx.lineTo(point.x,point.y);}ctx.stroke();}
   const neighbours=new Set(edges.filter(e=>e.source===entity||e.target===entity).flatMap(e=>[e.source,e.target]));
   edges.forEach(e=>{const a=project(byId.get(e.source)),b=project(byId.get(e.target)),focused=!entity||e.source===entity||e.target===entity;ctx.strokeStyle=focused?`rgba(205,176,120,${entity?.65:.19+Math.min(e.weight,15)*.018})`:'rgba(130,150,114,.07)';ctx.lineWidth=focused?Math.min(2,.4+e.weight*.08):.4;ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.quadraticCurveTo((a.x+b.x)/2+(width/2-(a.x+b.x)/2)*.18,(a.y+b.y)/2+(height/2-(a.y+b.y)/2)*.18,b.x,b.y);ctx.stroke();});
   projected=nodes.map(n=>({...n,...project(n)})).sort((a,b)=>b.z-a.z);
   const occupied=[];
   projected.forEach(n=>{const focus=!entity||neighbours.has(n.id),r=(2+Math.sqrt(n.count)*.55)*n.p;ctx.globalAlpha=focus?Math.max(.35,.76-n.z*.2):.16;ctx.fillStyle=n.id===entity?'#fff5d4':n.type==='concept'?'#b3c19a':'#d2b181';ctx.beginPath();ctx.arc(n.x,n.y,r,0,Math.PI*2);ctx.fill();ctx.strokeStyle='#d2b18155';ctx.beginPath();ctx.arc(n.x,n.y,r+5,0,Math.PI*2);ctx.stroke();if((n.count>=6&&n.z<.7)||n.id===entity){ctx.globalAlpha=focus?.95:.18;ctx.fillStyle='#e5e8d9';ctx.font='12px "IBM Plex Mono", monospace';const textWidth=ctx.measureText(n.id).width;const x=Math.max(3,Math.min(width-textWidth-3,n.x+r+8));const y=Math.max(14,Math.min(height-5,n.y+4));if(n.id===entity||!occupied.some(b=>x<b.x+b.w+5&&x+textWidth+5>b.x&&Math.abs(y-b.y)<17)){ctx.fillText(n.id,x,y);occupied.push({x,y,w:textWidth});}}ctx.globalAlpha=1;});
   if(!paused&&visible&&!document.hidden)frame=requestAnimationFrame(draw);
  }
  function refresh(){if(frame)cancelAnimationFrame(frame);last=performance.now();draw(last);}mapRefresh=refresh;
  function resize(){const r=canvas.getBoundingClientRect();width=r.width;height=r.height;const dpr=Math.min(devicePixelRatio||1,2);canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);refresh();}
  control.addEventListener('click',()=>{paused=!paused;label();refresh();});reduce.addEventListener('change',()=>{paused=reduce.matches;label();refresh();});
  canvas.addEventListener('pointerdown',e=>{drag={id:e.pointerId,x:e.clientX,y:e.clientY,startX:e.clientX,startY:e.clientY,moved:false};canvas.setPointerCapture(e.pointerId);});
  canvas.addEventListener('pointermove',e=>{if(!drag||e.pointerId!==drag.id)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;angle+=dx*.008;tilt=Math.max(-1,Math.min(1,tilt+dy*.005));drag.moved ||= Math.hypot(e.clientX-drag.startX,e.clientY-drag.startY)>6;drag.x=e.clientX;drag.y=e.clientY;refresh();});
  canvas.addEventListener('pointerup',e=>{if(!drag)return;const moved=drag.moved;drag=null;if(!moved){const r=canvas.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;const n=[...projected].reverse().find(n=>Math.hypot(n.x-x,n.y-y)<Math.max(14,Math.sqrt(n.count)+7));if(n)chooseEntity(entity===n.id?'':n.id);}refresh();});
  canvas.addEventListener('pointercancel',()=>{drag=null;refresh();});
  if('IntersectionObserver'in window)new IntersectionObserver(es=>{visible=es[0].isIntersecting;refresh();}).observe(canvas);
  document.addEventListener('visibilitychange',refresh);window.addEventListener('resize',resize,{passive:true});resize();
 }
 Promise.allSettled([get('data/signal-gate.json'),get('data/knowledge-graph.json'),get('data/momentum.json'),get('data/signal-ledger.jsonl',true)]).then(results=>{
  const [gate,g,m,text]=results.map(r=>r.status==='fulfilled'?r.value:null);
  if(gate){
   $('stat-records').textContent=gate.stats.stimuli;$('stat-signals').textContent=gate.stats.signal;$('stat-directions').textContent=gate.attractors.length;
   const age=date(gate.generated)?Math.max(0,Math.floor((Date.now()-date(gate.generated))/86400000)):null;
   $('hub-freshness').textContent=`Edition ${labelDate(gate.generated)}${age!==null&&age>3?' · Older edition — '+age+' days old':''}`;
   $('hub-freshness').classList.toggle('is-stale',age!==null&&age>3);
   $('freshness-method').textContent=`Edition generated ${labelDate(gate.generated)}. Evidence window: ${gate.window?.from||'unavailable'} to ${gate.window?.to||'unavailable'}. Collection dates and source publication dates are different.`;
   $('gate-accounting').textContent=`${gate.stats.mapped} mapped + ${gate.stats.unresolved} unbound + ${gate.stats.noise} rejected = ${gate.stats.stimuli} source records.`;
   (gate.attractors||[]).forEach(a=>(a.signals||[]).forEach(s=>statuses.set(s.url,'mapped')));(gate.other||[]).forEach(s=>statuses.set(s.url,'unbound'));(gate.noise||[]).forEach(s=>statuses.set(s.url,'noise'));
   renderDirections(gate,m);
  }else{$('hub-freshness').textContent='Decision data unavailable · source records may still be explored below.';$('hub-directions').innerHTML='<p class="hub-empty">The decision briefs could not be loaded. Please try again later or explore the published source editions.</p>';}
  renderForming(m);
  if(g){graph=g;$('stat-entities').textContent=graph.nodes.length;makeOptions($('map-entity'),graph.nodes.map(n=>n.id).sort());initialiseMap();}
  if(text){
   let invalid=0;records=text.trim().split(/\r?\n/).flatMap(line=>{try{return [JSON.parse(line)];}catch{invalid++;return [];}}).filter(r=>r.title&&r.url).map(r=>{
    let source=r.source_domain||r.sourceName;try{source ||= new URL(r.url).hostname.replace(/^www\./,'');}catch{source='Source link';}
    if(source==='news.google.com')source='Google News source link';
    return {...r,time:date(r.signalDate||r.date||r.firstSeen)?.getTime()||0,state:statuses.get(r.url)||'unclassified',source,search:[r.title,r.whatChanged,r.whyItMatters,r.desk,r.category,r.region,...(r.entities||[]),...(r.tags||[])].join(' ').toLowerCase()};
   }).sort((a,b)=>b.time-a.time);
   makeOptions($('feed-desk'),[...new Set(records.map(r=>r.desk).filter(Boolean))].sort());filterReady=true;renderFeed();if(!gate)$('stat-records').textContent=records.length;
   if(invalid){const note=document.createElement('p');note.className='hub-meta';note.textContent=`${invalid} malformed record${invalid===1?' was':'s were'} omitted from this view.`;$('feed-results').before(note);}
  }else{$('feed-count').textContent='Evidence ledger unavailable';$('feed-results').innerHTML='<p class="hub-empty">The source ledger could not be loaded. <a href="radar/index.html">Browse the published editions instead ↗</a></p>';}
  if(location.hash){const target=document.getElementById(decodeURIComponent(location.hash.slice(1)));if(target){if(target.classList.contains('direction-card'))target.querySelector('details').open=true;target.scrollIntoView({behavior:'instant',block:'start'});}}
 }).catch(()=>{$('hub-freshness').textContent='Some intelligence could not be displayed. Please reload or browse the source editions.';});
})();
