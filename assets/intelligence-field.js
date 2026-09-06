/* Original perspective-projected 3D field and procedural ambient score.
   No libraries, audio downloads, autoplay, or external assets required. */
(() => {
  const canvas = document.getElementById('intelligence-canvas');
  const hero = document.querySelector('.hero');
  const motionButton = document.getElementById('motion-toggle');
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  const ctx = canvas?.getContext('2d');
  let paused = reduce.matches, visible = true, frame = 0, last = 0, time = 0;
  let width = 0, height = 0, pointerX = 0, pointerY = 0, aimX = 0, aimY = 0;
  const TAU = Math.PI*2;
  // Deterministic fragments distributed through a toroidal volume, with real z depth.
  const points = Array.from({length:900},(_,i)=>{
    const u = i*2.39996323, v = i*1.61803399;
    const ring = 1.15 + .36*Math.cos(v);
    return {x:ring*Math.cos(u),y:.36*Math.sin(v),z:ring*Math.sin(u),seed:i,
      gx:Math.cos(u)*Math.sqrt((i+.5)/900)*1.2,
      gy:Math.sin(u)*Math.sqrt((i+.5)/900)*1.2,
      gz:Math.sin(v)*.22};
  });
  function draw(now=0) {
    frame=0;
    if (!ctx || !width || !height) return;
    if (!paused && visible && !document.hidden) time += Math.min((now-last)/1000 || 0,.04);
    last=now;
    pointerX += (aimX-pointerX)*.04; pointerY += (aimY-pointerY)*.04;
    const progress = paused ? .15 : Math.max(0,Math.min(1,-hero.getBoundingClientRect().top/(hero.offsetHeight*.75)));
    const yaw = .25 + time*.085 + (paused?0:pointerX*.2);
    const tilt = .83 + (paused?0:pointerY*.1);
    const scale = Math.min(width*.29,height*.46);
    ctx.clearRect(0,0,width,height);
    const projected = points.map(p=>{
      const x = p.x*(1-progress)+p.gx*progress;
      const y = p.y*(1-progress)+p.gy*progress;
      const z = p.z*(1-progress)+p.gz*progress;
      const rx=x*Math.cos(yaw)-z*Math.sin(yaw), rz=x*Math.sin(yaw)+z*Math.cos(yaw);
      const ry=y*Math.cos(tilt)-rz*Math.sin(tilt), depth=y*Math.sin(tilt)+rz*Math.cos(tilt);
      const perspective=4/(4+depth);
      return {x:width*.53+rx*scale*perspective,y:height*.48+ry*scale*perspective,z:depth,p:perspective,seed:p.seed};
    });
    // Fine connections make the geometry readable without a heavy mesh.
    ctx.lineWidth=.55;
    for(let i=0;i<projected.length;i+=3){
      const a=projected[i], b=projected[(i+34)%projected.length];
      const dist=Math.hypot(a.x-b.x,a.y-b.y);
      if(dist<scale*.43){ctx.strokeStyle=`rgba(184,158,109,${.055+.07*(2-a.z)/4})`;ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();}
    }
    projected.sort((a,b)=>b.z-a.z);
    projected.forEach(p=>{
      const alpha=Math.max(.18,Math.min(.92,.55-p.z*.24));
      ctx.fillStyle=p.seed%7===0?`rgba(241,221,180,${alpha})`:`rgba(191,164,114,${alpha})`;
      const r=(p.seed%13===0?1.7:.8)*p.p;
      ctx.beginPath();ctx.arc(p.x,p.y,r,0,TAU);ctx.fill();
      if(p.seed%67===0){ctx.strokeStyle=`rgba(217,190,132,${alpha*.45})`;ctx.beginPath();ctx.arc(p.x,p.y,r+4,0,TAU);ctx.stroke();}
    });
    if(!paused && visible && !document.hidden) frame=requestAnimationFrame(draw);
  }
  function refresh(){if(frame)cancelAnimationFrame(frame);last=performance.now();draw(last);}
  function resize(){if(!ctx)return;const rect=canvas.getBoundingClientRect();width=rect.width;height=rect.height;const dpr=Math.min(devicePixelRatio||1,1.75);canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);refresh();}
  if(ctx){
    document.documentElement.classList.add('field-ready');
    motionButton.hidden=false;
    const label=()=>{motionButton.textContent=paused?'Play motion':'Pause motion';motionButton.setAttribute('aria-pressed',String(paused));};
    label(); motionButton.addEventListener('click',()=>{paused=!paused;label();refresh();});
    reduce.addEventListener('change',()=>{paused=reduce.matches;label();refresh();});
    hero.addEventListener('pointermove',e=>{const r=hero.getBoundingClientRect();aimX=(e.clientX-r.left)/r.width-.5;aimY=(e.clientY-r.top)/r.height-.5;},{passive:true});
    hero.addEventListener('pointerleave',()=>{aimX=aimY=0;});
    if('IntersectionObserver' in window)new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;refresh();},{rootMargin:'50px'}).observe(hero);
    window.addEventListener('resize',resize,{passive:true});
    document.addEventListener('visibilitychange',refresh);
    resize();
  }

  // A quiet, original D-major / B-minor ambient composition. User gesture only.
  const soundButton=document.getElementById('sound-toggle');
  const soundLabel=document.getElementById('sound-label');
  const Audio=window.AudioContext || window.webkitAudioContext;
  if(!Audio || !soundButton)return;
  soundButton.hidden=false;
  let audio,master,delay,feedback,timer,playing=false,step=0,next=0,busy=false;
  function voice(freq,start,duration,gain,soft=false){
    const osc=audio.createOscillator(),amp=audio.createGain();
    osc.type='sine';osc.frequency.value=freq;
    amp.gain.setValueAtTime(0,start);amp.gain.linearRampToValueAtTime(gain,start+(soft?1.5:.018));amp.gain.exponentialRampToValueAtTime(.0001,start+duration);
    osc.connect(amp);amp.connect(master);amp.connect(delay);osc.start(start);osc.stop(start+duration+.05);
  }
  const chords=[[146.832,184.997,220,277.183],[123.471,146.832,184.997,246.942],[97.999,146.832,184.997,246.942],[110,164.814,220,277.183]];
  function schedule(){
    if(!playing)return;
    while(next<audio.currentTime+.25){
      const chord=chords[Math.floor(step/16)%chords.length];
      if(step%16===0)chord.slice(0,3).forEach(f=>voice(f/2,next,10,.022,true));
      if(step%2===0)voice(chord[[0,2,1,3,2,1,3,2][Math.floor(step/2)%8]]*2,next,3.8,.047);
      next+=.72;step++;
    }
  }
  async function stop(){
    playing=false;clearInterval(timer);soundButton.setAttribute('aria-pressed','false');soundLabel.textContent='Sound off';
    if(audio){master.gain.cancelScheduledValues(audio.currentTime);master.gain.setTargetAtTime(0,audio.currentTime,.1);await new Promise(r=>setTimeout(r,350));await audio.close();audio=null;}
  }
  soundButton.addEventListener('click',async()=>{
    if(busy)return;busy=true;
    try{
      if(playing){await stop();return;}
      if(!audio){audio=new Audio();master=audio.createGain();master.gain.value=0;master.connect(audio.destination);delay=audio.createDelay(2);delay.delayTime.value=.54;feedback=audio.createGain();feedback.gain.value=.23;delay.connect(feedback);feedback.connect(delay);delay.connect(master);}
      await audio.resume();playing=true;master.gain.setTargetAtTime(.55,audio.currentTime,.6);next=audio.currentTime+.08;step=0;schedule();timer=setInterval(schedule,120);soundButton.setAttribute('aria-pressed','true');soundLabel.textContent='Sound on';
    }catch{soundLabel.textContent='Sound unavailable';}
    finally{busy=false;}
  });
  document.addEventListener('visibilitychange',()=>{if(document.hidden&&playing&&!busy){busy=true;stop().finally(()=>{busy=false;});}});
  window.addEventListener('pagehide',()=>{clearInterval(timer);if(audio)audio.close();});
})();
