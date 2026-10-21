"""Offline web production assets: short IDs, working code, deterministic assembly.

Visual decisions come from assets.PROFILES / STYLES / EXEC. This module owns
reusable web mechanisms, not a competing aesthetic system. No network or model
is used by selection, preview generation, or export.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
from pathlib import Path

ASSETS: dict[str, dict] = {}
PACKS: dict[str, dict] = {}
SOURCES = {
    "backdrop": "https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/backdrop-filter",
    "scroll": "https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Scroll-driven_animations",
    "transition": "https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API/Using",
    "entry": "https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@starting-style",
    "color": "https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/color_value/color-mix",
    "container": "https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Conditional_rules/Container_scroll-state_queries",
}


def add(key, category, description, *, css="", markup="", js="", flags=(),
        controls=None, fallback="Static, readable content remains available.",
        cost="low", style="ultraviolet", source=()):
    ASSETS[key] = dict(id=key, category=category, description=description,
                       css=css.strip(), html=markup.strip(), js=js.strip(),
                       flags=list(flags), controls=controls or {}, fallback=fallback,
                       cost=cost, style=style, sources=[SOURCES[x] for x in source])


def knob(default, minimum, maximum, unit="", css=None):
    return dict(default=default, min=minimum, max=maximum, unit=unit, css=css)


CORE_CSS = r"""
:root { --uv-speed:1; --uv-intensity:1; --uv-alpha:.78; --uv-blur:20px; --uv-gap:24px; }
html { color-scheme:dark light; scroll-behavior:smooth; }
body { overflow-x:clip; }
button,input,select { font:inherit; }
button,a { -webkit-tap-highlight-color:transparent; }
.btn { display:inline-flex; align-items:center; justify-content:center; text-decoration:none; gap:10px; }
.uv-actions>a:not(.btn) { color:var(--text); text-decoration:none; padding-bottom:4px; border-bottom:1px solid var(--border); }
button { cursor:pointer; }
[hidden] { display:none !important; }
.uv-shell { width:min(1280px,calc(100% - 48px)); margin-inline:auto; }
.uv-nav { display:flex; align-items:center; justify-content:space-between; gap:24px;
  padding:24px 0; border-bottom:1px solid var(--border); }
.uv-nav a { color:var(--text); text-decoration:none; }
.uv-nav-links,.uv-actions,.uv-pills { display:flex; gap:16px; align-items:center; flex-wrap:wrap; }
.uv-brand { font-family:var(--font-display); font-weight:var(--weight-strong); letter-spacing:.05em; }
.uv-label { font-size:var(--size-sm); color:var(--muted); letter-spacing:.12em; text-transform:uppercase; }
.uv-hero { padding-block:clamp(64px,10vw,144px); position:relative; isolation:isolate; }
.uv-hero h1 { font-size:clamp(44px,7.7vw,112px); line-height:1.03; letter-spacing:-.055em;
  max-width:12ch; font-family:var(--font-display); font-weight:var(--weight-strong); }
.uv-lede { color:var(--muted); max-width:48ch; margin-block:28px; font-size:clamp(16px,1.6vw,21px); }
.uv-section { padding-block:clamp(44px,6vw,88px); scroll-margin-top:90px; }
.uv-section h2 { font-family:var(--font-display); font-size:clamp(26px,3vw,46px); line-height:1.15; }
.uv-section-head { display:flex; justify-content:space-between; align-items:end; gap:24px; margin-bottom:28px; }
.uv-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:var(--uv-gap); }
.uv-card { min-width:0; padding:28px; border:var(--border-width) solid var(--border);
  border-radius:var(--radius); background:var(--surface); position:relative; }
.uv-card h3 { font:var(--weight-strong) 22px/1.2 var(--font-display); margin-bottom:12px; }
.uv-card p { color:var(--muted); }
.uv-card-art { min-height:160px; display:grid; place-items:center; color:var(--accent); }
.uv-card-art svg { width:min(140px,70%); height:140px; }
.uv-scene{margin:0;min-width:0;}.uv-scene>svg{display:block;width:100%;height:auto;}.uv-scene figcaption{font-size:12px;line-height:1.5;color:var(--muted);padding-top:12px;}.uv-folio{color:var(--muted);font-size:14px;font-style:italic;}
.uv-visual { position:relative; aspect-ratio:1; min-height:240px; display:grid; place-items:center;
  color:var(--accent); isolation:isolate; }
.uv-visual svg { width:76%; height:76%; max-height:420px; }
.uv-visual::after { content:""; position:absolute; inset:8%; border:1px solid var(--border);
  border-radius:var(--radius); transform:rotate(-8deg); z-index:-1; }
.uv-metric { font:var(--weight-strong) clamp(32px,5vw,64px)/1 var(--font-display); margin-block:24px; }
.uv-foot { padding-block:44px; color:var(--muted); border-top:1px solid var(--border); }
.uv-demo { min-height:100svh; padding:clamp(24px,5vw,64px); position:relative; }
.uv-demo-stage { min-height:340px; display:grid; align-content:center; position:relative; isolation:isolate; }
.uv-demo h1 { font-family:var(--font-display); font-size:clamp(32px,5vw,64px); line-height:1.05; margin-block:16px 28px; }
.uv-demo .uv-card { max-width:720px; }
.uv-demo .uv-grid .uv-card { max-width:none; }
.uv-demo-note { margin-top:40px; color:var(--muted); max-width:70ch; font-size:var(--size-sm); }
.uv-demo-scroll { min-height:150svh; padding-top:32px; }
.uv-sr { position:absolute; width:1px; height:1px; overflow:hidden; clip-path:inset(50%); white-space:nowrap; }
.uv-tablist { display:flex; gap:8px; padding:8px; border:1px solid var(--border); border-radius:var(--radius); }
.uv-tablist button { padding:12px 20px; color:var(--muted); background:transparent; border:0; border-radius:var(--radius); }
.uv-tablist button[aria-selected=true] { color:var(--on-accent); background:var(--accent); }
.uv-panel { padding:32px; margin-top:16px; border:1px solid var(--border); background:var(--surface); border-radius:var(--radius); }
.uv-dialog { width:min(640px,calc(100% - 32px)); max-height:80svh; overflow:auto; margin:auto;
  background:var(--surface); color:var(--text); border:1px solid var(--border); border-radius:var(--radius); padding:28px; }
.uv-dialog::backdrop { background:rgba(0,0,0,.65); }
.uv-dialog header { display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; gap:20px; }
.uv-close { background:var(--surface); border:1px solid var(--border); color:var(--text); min-width:44px; min-height:44px; }
.uv-safe-ink { background:var(--surface); color:var(--text); padding:24px; border-radius:var(--radius); }
:where(a,button,input,select,summary,[tabindex]):focus-visible { outline:3px solid var(--accent); outline-offset:4px; }
@media(max-width:760px) { .uv-grid { grid-template-columns:1fr; } .uv-nav { align-items:start; }
  .uv-nav-links { gap:12px; } .uv-section-head { display:block; } }
@media(prefers-reduced-motion:reduce) { html { scroll-behavior:auto; }
  *,*::before,*::after { animation:none !important; transition:none !important; } }
[data-uv-paused] *,[data-uv-paused] *::before,[data-uv-paused] *::after { animation-play-state:paused !important; }
@media(prefers-reduced-transparency:reduce) { [data-uv-glass] { background:var(--surface) !important; backdrop-filter:none !important; } }
[data-uv-solid] [data-uv-glass] { background:var(--surface) !important; backdrop-filter:none !important; -webkit-backdrop-filter:none !important; }
"""

RUNTIME_JS = r"""
(function(){'use strict';
if(window.UltraWeb)return;
const registry=new Map(),live=new Map(),reduced=matchMedia('(prefers-reduced-motion: reduce)');
const errors=[];
function mount(root=document){
 const nodes=[...(root.matches&&root.matches('[data-uv]')?[root]:[]),...root.querySelectorAll('[data-uv]')];
 for(const el of nodes)for(const id of el.dataset.uv.split(/\s+/).filter(Boolean)){
  const item=registry.get(id);if(!item)continue;
  let own=live.get(el);if(!own){own=new Map();live.set(el,own);}if(own.has(id))continue;
  const cleanup=[];let data={};
  try{data=JSON.parse(el.dataset.uvConfig||'{}');if(!data||typeof data!=='object'||Array.isArray(data))data={};}catch(_){data={};}
  const opts={};for(const [key,rule]of Object.entries(item.controls)){
   const n=Number(data[key]??rule.default);opts[key]=Math.min(rule.max,Math.max(rule.min,Number.isFinite(n)?n:rule.default));
   if(rule.css){const old=el.style.getPropertyValue(rule.css);el.style.setProperty(rule.css,opts[key]+rule.unit);
    cleanup.push(()=>old?el.style.setProperty(rule.css,old):el.style.removeProperty(rule.css));}
  }
  const api={motion:!reduced.matches&&!document.documentElement.hasAttribute('data-uv-paused'),
   listen(target,event,fn,options){target.addEventListener(event,fn,options);cleanup.push(()=>target.removeEventListener(event,fn,options));},
   clean(fn){cleanup.push(fn);},
   animate(node,frames,options={}){if(!node.animate||!api.motion)return null;
    const a=node.animate(frames,{duration:500,easing:'cubic-bezier(.2,.8,.2,1)',...options});cleanup.push(()=>a.cancel());return a;},
   frame(fn){let raf=0;const run=(...args)=>{if(raf)return;raf=requestAnimationFrame(()=>{raf=0;fn(...args);});};
    cleanup.push(()=>cancelAnimationFrame(raf));return run;},
   loop(fn){let raf=0,inside=true,dead=false;
    function tick(t){raf=0;if(dead||!inside||document.hidden||!api.motion)return;fn(t);raf=requestAnimationFrame(tick);}
    function update(){if(dead)return;if(inside&&!document.hidden&&api.motion){if(!raf)raf=requestAnimationFrame(tick);}else{cancelAnimationFrame(raf);raf=0;}}
    const io='IntersectionObserver'in window?new IntersectionObserver(es=>{inside=es[0].isIntersecting;update();},{rootMargin:'100px'}):null;
    if(io)io.observe(el);api.listen(document,'visibilitychange',update);update();
    cleanup.push(()=>{dead=true;cancelAnimationFrame(raf);io?.disconnect();});},
   visible(fn){if(!('IntersectionObserver'in window)){fn(el);return;}
    const io=new IntersectionObserver(es=>{for(const e of es)if(e.isIntersecting){fn(e.target);io.unobserve(e.target);}},{threshold:.12});
    io.observe(el);cleanup.push(()=>io.disconnect());}
  };
  own.set(id,()=>{for(const fn of cleanup.reverse())try{fn();}catch(_){}});
  try{const stop=item.init(el,opts,api);if(typeof stop==='function')cleanup.push(stop);}
  catch(error){errors.push({id,message:String(error)});own.get(id)();own.delete(id);console.warn('UltraWeb '+id,error);}
 }
}
function unmount(root=document){for(const[el,own]of live)if(root===document||root===el||root.contains(el)){
 for(const stop of own.values())stop();live.delete(el);}}
window.UltraWeb={register(id,controls,init){registry.set(id,{controls,init});if(document.readyState!=='loading')queueMicrotask(()=>mount());},mount,unmount,errors,
 setMotion(paused){document.documentElement.toggleAttribute('data-uv-paused',!!paused);unmount();mount();},
 stats(){return{assets:registry.size,elements:live.size,instances:[...live.values()].reduce((n,m)=>n+m.size,0)};}};
reduced.addEventListener?.('change',()=>{unmount();mount();});
addEventListener('pagehide',()=>unmount());
if(document.readyState==='complete')queueMicrotask(()=>mount());else document.addEventListener('DOMContentLoaded',()=>mount(),{once:true});
})();
"""

CARD = '<article class="uv-card"><div class="uv-card-art">__MOTIF__</div><p class="uv-label">Built from the vault</p><h3>Designed to move.</h3><p>Local assets. Your identity.</p></article>'
TRIO = '<div class="uv-grid">'+CARD*3+'</div>'
ART = '<div class="uv-visual">__MOTIF__</div>'
TABS = '''<div data-uv="morph-tabs"><div class="uv-tablist" role="tablist" aria-label="Collection">
<button role="tab" aria-selected="true">Design</button><button role="tab" aria-selected="false" tabindex="-1">Motion</button><button role="tab" aria-selected="false" tabindex="-1">Build</button></div>
<section class="uv-panel" role="tabpanel"><h3>One visual language.</h3><p>Your profile determines the palette, type, shape and material.</p></section>
<section class="uv-panel" role="tabpanel" hidden><h3>Movement with intent.</h3><p>Responsive to the reader, the pointer and the scroll.</p></section>
<section class="uv-panel" role="tabpanel" hidden><h3>Ready to assemble.</h3><p>Reference the asset. Keep the code local.</p></section></div>'''

# Motion: every enhancement begins with visible content and respects reduced motion.
add('reveal-stagger','motion','Sequenced entrances with an observer fallback and no hidden content before JS.',
 markup='<div data-uv="reveal-stagger">'+TRIO+'</div>',
 controls={'distance':knob(28,0,80),'duration':knob(650,100,1600),'stagger':knob(100,0,300)},
 js="""if(!api.motion)return;api.visible(()=>{[...el.children].flatMap(n=>n.classList.contains('uv-grid')?[...n.children]:[n]).forEach((n,i)=>api.animate(n,[{opacity:0,transform:`translateY(${o.distance}px)`},{opacity:1,transform:'none'}],{duration:o.duration,delay:i*o.stagger,fill:'backwards'}));});""",flags=['motion'])
add('scroll-progress','motion','A reading-progress rail driven by native scroll timelines, with a measured fallback.',
 css='''.uv-progress{position:fixed;inset:0 0 auto;height:3px;background:var(--accent);transform:scaleX(0);transform-origin:left;z-index:80;}
@supports(animation-timeline:scroll()){.uv-progress{animation:uv-read linear both;animation-timeline:scroll(root block);}}
@keyframes uv-read{to{transform:scaleX(1);}}''',
 markup='<div data-uv="scroll-progress"><div class="uv-progress" aria-hidden="true"></div><h2>Keep moving.</h2><p>Scroll to watch the reading rail.</p><div class="uv-demo-scroll">'+TRIO+'</div></div>',
 js="""if(CSS.supports('animation-timeline:scroll()')&&api.motion)return;const bar=el.querySelector('.uv-progress');const update=api.frame(()=>{const d=document.documentElement;bar.style.transform=`scaleX(${d.scrollTop/Math.max(1,d.scrollHeight-d.clientHeight)})`;});api.listen(window,'scroll',update,{passive:true});api.listen(window,'resize',update);update();return()=>bar.style.removeProperty('transform');""",source=['scroll'])
add('scroll-depth','motion','A restrained depth shift with a scroll-linked timeline and JS fallback.',
 css='''.uv-depth{transform:translateY(var(--uv-depth-y,0px));}
@supports(animation-timeline:view()){.uv-depth{animation:uv-depth linear both;animation-timeline:view();animation-range:entry 0% exit 100%;}}
@keyframes uv-depth{from{translate:0 var(--uv-depth-distance,35px);}to{translate:0 calc(-1 * var(--uv-depth-distance,35px));}}''',
 markup='<section data-uv="scroll-depth"><h2>A different perspective.</h2><div class="uv-depth">'+ART+'</div><div class="uv-demo-scroll">'+TRIO+'</div></section>',
 controls={'distance':knob(35,0,90,'px',css='--uv-depth-distance')},flags=['motion'],source=['scroll'],
 js="""if(!api.motion||CSS.supports('animation-timeline:view()'))return;const n=el.querySelector('.uv-depth');const update=api.frame(()=>{const r=el.getBoundingClientRect();const f=(innerHeight/2-r.top-r.height/2)/innerHeight;n.style.setProperty('--uv-depth-y',Math.max(-o.distance,Math.min(o.distance,f*o.distance))+'px');});api.listen(window,'scroll',update,{passive:true});update();return()=>n.style.removeProperty('--uv-depth-y');""")
add('magnetic-button','motion','A pointer-responsive CTA with bounded travel and a still keyboard/touch state.',
 css='''.uv-magnetic{translate:var(--uv-mx,0px) var(--uv-my,0px);transition:translate .2s;display:inline-flex;align-items:center;justify-content:center;}''',
 markup='<button class="btn uv-magnetic" data-uv="magnetic-button">Explore the collection ↗</button>',
 controls={'strength':knob(.14,0,.3)},flags=['motion'],
 js="""if(!api.motion||!matchMedia('(pointer:fine)').matches)return;const move=api.frame(e=>{const r=el.getBoundingClientRect();el.style.setProperty('--uv-mx',((e.clientX-r.left-r.width/2)*o.strength)+'px');el.style.setProperty('--uv-my',((e.clientY-r.top-r.height/2)*o.strength)+'px');});const reset=()=>{el.style.removeProperty('--uv-mx');el.style.removeProperty('--uv-my');};api.listen(el,'pointermove',move);api.listen(el,'pointerleave',reset);api.listen(el,'blur',reset);return reset;""")
add('tilt-card','motion','A shallow, bounded 3D tilt that follows a fine pointer.',
 css='''.uv-tilt{transform:perspective(900px) rotateX(var(--uv-rx,0deg)) rotateY(var(--uv-ry,0deg));transition:transform .18s;transform-style:preserve-3d;}.uv-tilt .uv-card-art{transform:translateZ(24px);}''',
 markup='<div class="uv-tilt" data-uv="tilt-card">'+CARD+'</div>',controls={'angle':knob(7,0,14)},flags=['motion'],
 js="""if(!api.motion||!matchMedia('(pointer:fine)').matches)return;const move=api.frame(e=>{const r=el.getBoundingClientRect();el.style.setProperty('--uv-rx',((.5-(e.clientY-r.top)/r.height)*o.angle*2)+'deg');el.style.setProperty('--uv-ry',(((e.clientX-r.left)/r.width-.5)*o.angle*2)+'deg');});const reset=()=>{el.style.removeProperty('--uv-rx');el.style.removeProperty('--uv-ry');};api.listen(el,'pointermove',move);api.listen(el,'pointerleave',reset);return reset;""")
add('shared-transition','motion','Shared-element transitions between two real content states, with immediate fallback.',
 css='''.uv-shared-art{view-transition-name:uv-selected-art;}.uv-shared-expanded .uv-shared-art{max-width:540px;margin-inline:auto;}::view-transition-old(uv-selected-art),::view-transition-new(uv-selected-art){animation-duration:.5s;}''',
 markup='<div data-uv="shared-transition"><div class="uv-shared-art">'+ART+'</div><button class="btn" aria-expanded="false">Change perspective</button><p class="uv-shared-detail" hidden>One artifact, two perspectives. State changes remain immediate when animation is unavailable.</p></div>',
 flags=['motion'],source=['transition'],
 js="""const b=el.querySelector('button'),detail=el.querySelector('.uv-shared-detail');api.listen(b,'click',()=>{const update=()=>{const expanded=el.classList.toggle('uv-shared-expanded');b.setAttribute('aria-expanded',String(expanded));detail.hidden=!expanded;};if(api.motion&&document.startViewTransition)document.startViewTransition(update);else update();});""")
add('split-lines','motion','A clipped headline entrance with a single accessible label and readable static text.',
 css='''.uv-lines>span{display:block;overflow:clip;}.uv-lines em{display:block;font-style:normal;}''',
 markup='<h1 class="uv-lines" data-uv="split-lines" aria-label="Made to feel different."><span aria-hidden="true"><em>Made to feel</em></span><span aria-hidden="true"><em>different.</em></span></h1>',
 flags=['motion'],controls={'duration':knob(900,200,1800)},
 js="""if(!api.motion)return;api.visible(()=>el.querySelectorAll('em').forEach((n,i)=>api.animate(n,[{transform:'translateY(110%)'},{transform:'none'}],{duration:o.duration,delay:120*i,fill:'backwards'})));""")
add('ambient-marquee','motion','A looping text band with pause controls; duplicates are hidden from assistive technology.',
 css='''.uv-marquee{overflow:hidden;border-block:1px solid var(--border);padding-block:24px;}.uv-marquee-track{display:flex;gap:40px;width:max-content;animation:uv-marquee calc(26s / var(--uv-speed)) linear infinite;font:var(--weight-strong) clamp(28px,5vw,72px)/1.2 var(--font-display);}.uv-marquee-track>span{padding-right:40px;white-space:nowrap;}@keyframes uv-marquee{to{transform:translateX(-50%);}}.uv-marquee:hover .uv-marquee-track,.uv-marquee:focus-within .uv-marquee-track{animation-play-state:paused;}''',
 markup='<div data-uv="ambient-marquee"><div class="uv-marquee"><div class="uv-marquee-track"><span>LOCAL ASSETS · YOUR IDEAS · </span><span aria-hidden="true">LOCAL ASSETS · YOUR IDEAS · </span></div></div><button class="btn" aria-pressed="false">Pause motion</button></div>',
 flags=['motion'],controls={'speed':knob(1,.3,2,css='--uv-speed')},
 js="""const b=el.querySelector('button'),track=el.querySelector('.uv-marquee-track');if(!api.motion)track.style.animationPlayState='paused';api.listen(b,'click',()=>{const paused=b.getAttribute('aria-pressed')!=='true';b.setAttribute('aria-pressed',String(paused));b.textContent=paused?'Resume motion':'Pause motion';track.style.animationPlayState=paused||!api.motion?'paused':'';});""")
add('flip-grid','motion','Animated grid reordering using measured first/last positions rather than layout thrashing.',
 markup='<div data-uv="flip-grid"><button class="btn">Reorder the collection</button><div class="uv-grid" style="margin-top:24px">'+CARD*3+'</div></div>',flags=['motion'],
 js="""const g=el.querySelector('.uv-grid');api.listen(el.querySelector('button'),'click',()=>{const nodes=[...g.children],before=nodes.map(n=>n.getBoundingClientRect());g.append(nodes[0]);nodes.forEach((n,i)=>{const r=n.getBoundingClientRect();api.animate(n,[{transform:`translate(${before[i].left-r.left}px,${before[i].top-r.top}px)`},{transform:'none'}],{duration:500});});});""")
add('sticky-morph','motion','A navigation band that condenses while scrolling; scroll-state styling enhances a JS fallback.',
 css='''.uv-sticky-wrap{position:sticky;top:0;z-index:30;container-type:scroll-state;}.uv-sticky-bar{padding:24px;display:flex;justify-content:space-between;gap:16px;background:var(--surface);border-bottom:1px solid var(--border);transition:padding .25s;}.uv-is-stuck .uv-sticky-bar{padding-block:12px;}@supports(container-type:scroll-state){@container scroll-state(stuck:top){.uv-sticky-bar{padding-block:12px;}}}''',
 markup='<div data-uv="sticky-morph"><div class="uv-sticky-wrap"><nav class="uv-sticky-bar" aria-label="Demo"><strong>THE COLLECTION</strong><a href="#uv-sticky-end">Explore ↓</a></nav></div><div class="uv-demo-scroll">'+TRIO+'</div><p id="uv-sticky-end">At the end of the collection.</p></div>',
 js="""const n=el.querySelector('.uv-sticky-wrap');const update=api.frame(()=>{const r=n.getBoundingClientRect();n.classList.toggle('uv-is-stuck',r.top<=1&&scrollY>0);});api.listen(window,'scroll',update,{passive:true});update();""",source=['container'])

# Color and light: the hue always comes from the selected vault profile.
add('aurora-field','color','Three drifting light fields behind an opaque text plane; no animated blur repaint.',
 css='''.uv-aurora{position:relative;isolation:isolate;overflow:clip;min-height:420px;}.uv-aurora-lights{position:absolute;inset:-20%;z-index:-1;filter:blur(48px);opacity:calc(.24 * var(--uv-intensity));pointer-events:none;}.uv-aurora-lights i{position:absolute;width:55%;aspect-ratio:1;border-radius:50%;background:var(--accent);animation:uv-orbit calc(22s / var(--uv-speed)) ease-in-out infinite alternate;}.uv-aurora-lights i:nth-child(2){background:var(--accent2);left:50%;top:30%;animation-delay:-8s;}.uv-aurora-lights i:nth-child(3){background:var(--accent);left:30%;top:65%;animation-delay:-15s;}@keyframes uv-orbit{to{transform:translate(20%,-22%) scale(1.2);}}.uv-aurora-copy{padding:clamp(28px,5vw,64px);max-width:650px;}''',
 markup='<section class="uv-aurora" data-uv="aurora-field"><div class="uv-aurora-lights" aria-hidden="true"><i></i><i></i><i></i></div><div class="uv-aurora-copy"><p class="uv-label">A field of possibility</p><h1>Light, in motion.</h1><div class="uv-safe-ink"><p>Atmosphere behind the story. Readable text in front.</p></div></div></section>',
 controls={'speed':knob(1,.2,2,css='--uv-speed'),'intensity':knob(1,.2,1.4,css='--uv-intensity')},flags=['gradient','motion','organic'],cost='medium')
add('prism-border','color','A moving conic edge around a solid surface, with a static border fallback.',
 css='''@property --uv-prism-angle{syntax:"<angle>";initial-value:0deg;inherits:false;}.uv-prism{border:1px solid var(--accent);padding:32px;border-radius:var(--radius);background:var(--surface);}@supports(background:conic-gradient(from 0deg,red,blue)){.uv-prism{border:1px solid transparent;background:linear-gradient(var(--surface),var(--surface)) padding-box,conic-gradient(from var(--uv-prism-angle),var(--accent),var(--accent2),var(--border),var(--accent)) border-box;animation:uv-prism calc(8s / var(--uv-speed)) linear infinite;}}@keyframes uv-prism{to{--uv-prism-angle:360deg;}}''',
 markup='<article class="uv-prism" data-uv="prism-border"><p class="uv-label">The detail is the design</p><h2>A little edge.</h2><p>One moving border. A quiet surface within.</p></article>',
 controls={'speed':knob(1,.2,2,css='--uv-speed')},flags=['gradient','motion'])
add('iridescent-surface','color','A pointer-lit foil surface with a bounded, decorative sheen.',
 css='''.uv-foil{position:relative;isolation:isolate;overflow:hidden;padding:36px;border:1px solid var(--border);border-radius:var(--radius);background:var(--surface);}.uv-foil::before{content:"";position:absolute;inset:0;z-index:-1;opacity:.42;background:linear-gradient(var(--uv-foil-angle,115deg),transparent 12%,var(--accent) 35%,var(--accent2) 50%,var(--surface) 63%,transparent 85%);background-size:220% 220%;background-position:var(--uv-foil-x,50%) var(--uv-foil-y,50%);}.uv-foil .uv-safe-ink{max-width:45ch;}''',
 markup='<article class="uv-foil" data-uv="iridescent-surface">'+ART+'<div class="uv-safe-ink"><h2>Catch the light.</h2><p>A finish drawn from your profile’s accent family.</p></div></article>',flags=['gradient','glass'],style='y2k-chrome',
 js="""if(!api.motion||!matchMedia('(pointer:fine)').matches)return;api.listen(el,'pointermove',api.frame(e=>{const r=el.getBoundingClientRect(),x=(e.clientX-r.left)/r.width,y=(e.clientY-r.top)/r.height;el.style.setProperty('--uv-foil-angle',(80+x*100)+'deg');el.style.setProperty('--uv-foil-x',(x*100)+'%');el.style.setProperty('--uv-foil-y',(y*100)+'%');}));return()=>['--uv-foil-angle','--uv-foil-x','--uv-foil-y'].forEach(k=>el.style.removeProperty(k));""")
add('gradient-type','color','Perceptual gradient display type with solid readable fallback.',
 css='''.uv-gradient-type{color:var(--accent);}@supports(background-clip:text){.uv-gradient-type{background:linear-gradient(100deg,var(--accent),var(--accent2));background-clip:text;-webkit-background-clip:text;color:transparent;}}@supports(background:linear-gradient(90deg in oklch,red,blue)){.uv-gradient-type{background-image:linear-gradient(100deg in oklch,var(--accent),var(--accent2));}}''',
 markup='<h1 class="uv-gradient-type" data-uv="gradient-type">Color with<br>another dimension.</h1>',flags=['gradient'],source=['color'])
add('blend-spotlights','color','Local colored spotlights that follow a pointer behind an isolated content plane.',
 css='''.uv-blend{position:relative;isolation:isolate;overflow:hidden;padding:40px;min-height:400px;background:var(--bg);}.uv-blend::before,.uv-blend::after{content:"";position:absolute;inset:-10%;pointer-events:none;z-index:-1;opacity:.5;background:radial-gradient(circle at var(--uv-light-x,30%) var(--uv-light-y,35%),var(--accent),transparent 55%);}.uv-blend::after{background:radial-gradient(circle at 80% 70%,var(--accent2),transparent 50%);mix-blend-mode:screen;}''',
 markup='<div class="uv-blend" data-uv="blend-spotlights"><h1>Follow the light.</h1><div class="uv-safe-ink"><p>Move across this field to change the lighting.</p></div></div>',
 flags=['gradient'],cost='medium',
 js="""if(!api.motion||!matchMedia('(pointer:fine)').matches)return;api.listen(el,'pointermove',api.frame(e=>{const r=el.getBoundingClientRect();el.style.setProperty('--uv-light-x',((e.clientX-r.left)/r.width*100)+'%');el.style.setProperty('--uv-light-y',((e.clientY-r.top)/r.height*100)+'%');}));return()=>{el.style.removeProperty('--uv-light-x');el.style.removeProperty('--uv-light-y');};""")
add('shader-flow','color','A small original WebGL light-flow background with capped pixel density and no texture downloads.',
 css='''.uv-shader{position:relative;isolation:isolate;overflow:clip;min-height:460px;background:var(--bg2);}.uv-shader canvas{position:absolute;inset:0;width:100%;height:100%;z-index:-1;opacity:calc(.7 * var(--uv-intensity));}.uv-shader-copy{padding:clamp(28px,6vw,80px);}''',
 markup='<section class="uv-shader" data-uv="shader-flow"><canvas aria-hidden="true"></canvas><div class="uv-shader-copy"><p class="uv-label">Realtime · local · original</p><h1>A living field.</h1><div class="uv-safe-ink"><p>Light calculated on your GPU. The story remains readable without WebGL.</p></div></div></section>',
 controls={'speed':knob(.6,.1,1.5),'intensity':knob(1,.1,1,css='--uv-intensity')},flags=['gradient','organic','motion'],cost='high',fallback='A solid profile background; one still frame for reduced motion.',
 js=r"""const canvas=el.querySelector('canvas'),gl=canvas.getContext('webgl',{alpha:true,antialias:false,powerPreference:'low-power'});if(!gl)return;
const vertex='attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}';
const fragment='precision mediump float;uniform vec2 r;uniform float t;uniform vec3 a;uniform vec3 b;void main(){vec2 uv=gl_FragCoord.xy/r;uv.x*=r.x/r.y;float f=sin(uv.x*4.+t*.3+sin(uv.y*5.-t*.2))*cos(uv.y*4.-t*.25);float v=smoothstep(-.8,.9,f);vec3 c=mix(a,b,v);float light=.22+.55*smoothstep(.1,.85,v);gl_FragColor=vec4(c*light,1.);}';
function compile(type,src){const sh=gl.createShader(type);gl.shaderSource(sh,src);gl.compileShader(sh);if(!gl.getShaderParameter(sh,gl.COMPILE_STATUS)){gl.deleteShader(sh);return null;}return sh;}
const vs=compile(gl.VERTEX_SHADER,vertex),fs=compile(gl.FRAGMENT_SHADER,fragment);if(!vs||!fs){if(vs)gl.deleteShader(vs);if(fs)gl.deleteShader(fs);return;}
const prog=gl.createProgram();gl.attachShader(prog,vs);gl.attachShader(prog,fs);gl.linkProgram(prog);if(!gl.getProgramParameter(prog,gl.LINK_STATUS)){gl.deleteProgram(prog);gl.deleteShader(vs);gl.deleteShader(fs);return;}
const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);gl.useProgram(prog);const p=gl.getAttribLocation(prog,'p');gl.enableVertexAttribArray(p);gl.vertexAttribPointer(p,2,gl.FLOAT,false,0,0);
const time=gl.getUniformLocation(prog,'t'),res=gl.getUniformLocation(prog,'r');
function color(name){const h=getComputedStyle(el).getPropertyValue(name).trim().replace('#','');return [0,2,4].map(i=>parseInt(h.slice(i,i+2),16)/255);}
gl.uniform3fv(gl.getUniformLocation(prog,'a'),color('--accent'));gl.uniform3fv(gl.getUniformLocation(prog,'b'),color('--accent2'));
let lost=false;api.listen(canvas,'webglcontextlost',e=>{e.preventDefault();lost=true;});
function draw(t){if(lost)return;const dpr=Math.min(devicePixelRatio||1,1.5),w=Math.max(1,Math.round(el.clientWidth*dpr)),h=Math.max(1,Math.round(el.clientHeight*dpr));if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;gl.viewport(0,0,w,h);}gl.uniform2f(res,w,h);gl.uniform1f(time,t*.001*o.speed);gl.drawArrays(gl.TRIANGLES,0,6);}
draw(0);if(api.motion)api.loop(draw);else api.listen(window,'resize',()=>draw(0));return()=>{gl.deleteBuffer(buffer);gl.deleteProgram(prog);gl.deleteShader(vs);gl.deleteShader(fs);};""")
add('noise-film','color','A static, low-opacity film texture with an opaque fallback and no repeating paint loop.',
 css='''.uv-film{position:relative;isolation:isolate;}.uv-film::after{content:"";position:absolute;inset:0;pointer-events:none;opacity:var(--uv-noise,.055);z-index:2;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Cpath filter='url(%23n)' opacity='.7' d='M0 0h180v180H0z'/%3E%3C/svg%3E");}''',
 markup='<article class="uv-card uv-film" data-uv="noise-film">'+ART+'<h2>A little material.</h2><p>A static grain layer adds texture without a permanent animation.</p></article>',flags=['texture'],controls={'opacity':knob(.055,0,.16,css='--uv-noise')},style='golden-archive')
add('duotone-art','color','A two-color art treatment using profile accents and a composited SVG motif.',
 css='''.uv-duotone{background:var(--accent);isolation:isolate;position:relative;overflow:hidden;border-radius:var(--radius);}.uv-duotone .uv-visual{color:var(--accent2);mix-blend-mode:screen;}.uv-duotone::after{content:"";position:absolute;inset:0;pointer-events:none;background:var(--bg);mix-blend-mode:multiply;opacity:.3;}''',
 markup='<div class="uv-duotone" data-uv="duotone-art" role="img" aria-label="A decorative two-color motif from this profile">'+ART+'</div>',flags=['gradient'],fallback='Two solid profile colors; no external image is required.')
add('oklch-ramp','color','A perceptual accent ramp that upgrades from sRGB only when supported.',
 css='''.uv-ramp{display:grid;grid-template-columns:repeat(7,1fr);min-height:220px;overflow:hidden;border-radius:var(--radius);}.uv-ramp i{background:var(--accent);background:color-mix(in srgb,var(--accent) var(--uv-stop),var(--surface));}@supports(color:color-mix(in oklch,red,blue)){.uv-ramp i{background:var(--accent);background:color-mix(in oklch,var(--accent) var(--uv-stop),var(--surface));}}''',
 markup='<div class="uv-ramp" data-uv="oklch-ramp" role="img" aria-label="A perceptual seven-step accent ramp">'+''.join(f'<i style="--uv-stop:{v}%"></i>' for v in (10,25,40,55,70,85,100))+'</div>',source=['color'])

# Transparency: alpha applies to the surface, never to its text or children.
GLASS_CSS = '''[data-uv-glass]{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);position:relative;}
@supports((backdrop-filter:blur(1px)) or (-webkit-backdrop-filter:blur(1px))){[data-uv-glass]{background:color-mix(in srgb,var(--surface) calc(var(--uv-alpha)*100%),transparent);backdrop-filter:blur(var(--uv-blur)) saturate(140%);-webkit-backdrop-filter:blur(var(--uv-blur)) saturate(140%);}}
[data-uv-glass]::before{content:"";position:absolute;inset:0;border-radius:inherit;pointer-events:none;border:1px solid rgba(255,255,255,.16);}
'''
GLASS_CONTROLS={'opacity':knob(.8,.56,.98,css='--uv-alpha'),'blur':knob(20,0,32,'px',css='--uv-blur')}
add('glass-panel','transparency','A real frosted surface with readable inner text and a solid fallback.',css=GLASS_CSS,
 markup='<div class="uv-visual" style="padding:24px">__MOTIF__<article data-uv="glass-panel" data-uv-glass style="position:absolute;inset:18%;padding:28px"><div class="uv-safe-ink"><h2>Clarity, layered.</h2><p>Transparency belongs to the surface. Text keeps its contrast.</p></div></article></div>',
 controls=GLASS_CONTROLS,flags=['glass'],cost='medium',source=['backdrop'],fallback='Opaque profile surface when blur or transparency is unavailable.')
add('glass-dock','transparency','A compact, floating navigation dock with actual backdrop blur and explicit focus states.',
 css=GLASS_CSS+'''.uv-dock{position:sticky;top:18px;z-index:40;display:flex;align-items:center;justify-content:space-between;gap:16px;padding:14px 20px;}.uv-dock a{color:var(--text);text-decoration:none;padding:8px 12px;}.uv-dock a:hover,.uv-dock a:focus-visible{background:var(--surface);border-radius:var(--radius);}''',
 markup='<div data-uv="glass-dock"><nav class="uv-dock" data-uv-glass aria-label="Floating navigation"><a href="#uv-dock-story">Story</a><a href="#uv-dock-collection">Collection</a><a href="#uv-dock-contact">Contact</a></nav><section id="uv-dock-story" class="uv-demo-scroll">'+ART+'</section><section id="uv-dock-collection">'+TRIO+'</section><p id="uv-dock-contact">The collection is yours.</p></div>',
 controls=GLASS_CONTROLS,flags=['glass'],cost='medium',source=['backdrop'])
add('acrylic-card','transparency','Tinted acrylic, a thin specular edge, and a solid text scrim.',
 css=GLASS_CSS+'''.uv-acrylic{padding:32px;overflow:hidden;}.uv-acrylic::after{content:"";position:absolute;inset:0;z-index:-1;pointer-events:none;background:linear-gradient(135deg,transparent,var(--accent));opacity:.13;}''',
 markup='<div class="uv-visual">__MOTIF__<article class="uv-acrylic" data-uv="acrylic-card" data-uv-glass style="position:absolute;inset:16%"><p class="uv-label">Acrylic finish</p><div class="uv-safe-ink"><h2>A softer interface.</h2><p>Tinted by your palette, without lowering text opacity.</p></div></article></div>',
 flags=['glass','gradient'],controls=GLASS_CONTROLS,cost='medium',source=['backdrop'],style='frutiger-aero')
add('glass-stack','transparency','Three offset translucent sheets with one live blur layer to bound rendering cost.',
 css=GLASS_CSS+'''.uv-glass-stack{position:relative;padding:40px 24px 24px;margin:30px;}.uv-glass-stack::before,.uv-glass-stack::after{content:"";position:absolute;inset:0;border:1px solid var(--border);border-radius:var(--radius);background:var(--surface);opacity:.45;z-index:-1;transform:translate(18px,-18px) rotate(4deg);}.uv-glass-stack::after{transform:translate(34px,-34px) rotate(8deg);opacity:.2;}.uv-glass-stack>article{padding:32px;}''',
 markup='<div class="uv-glass-stack" data-uv="glass-stack"><article data-uv-glass>'+ART+'<div class="uv-safe-ink"><h2>Depth, with restraint.</h2><p>Three layers. One blur surface.</p></div></article></div>',
 flags=['glass'],controls=GLASS_CONTROLS,cost='medium',source=['backdrop'])
add('glass-popover','transparency','A frosted popover that opens by click or keyboard and closes with Escape.',
 css=GLASS_CSS+'''.uv-glass-popover{width:min(360px,calc(100vw - 32px));padding:24px;position:fixed;inset:auto;margin:12px;z-index:90;box-shadow:var(--shadow);}.uv-glass-popover h3{margin-bottom:12px;}''',
 markup='<div data-uv="glass-popover"><button class="btn" aria-expanded="false">Open quick panel</button><aside class="uv-glass-popover" data-uv-glass hidden><h3>Quick panel</h3><p>Layered controls without losing the context behind them.</p><button class="uv-close" aria-label="Close panel">×</button></aside></div>',
 flags=['glass'],controls=GLASS_CONTROLS,cost='medium',source=['backdrop','entry'],
 js="""const b=el.querySelector('.btn'),p=el.querySelector('aside'),close=p.querySelector('button');function hide(){p.hidden=true;b.setAttribute('aria-expanded','false');b.focus();}function place(){const r=b.getBoundingClientRect();p.style.left=Math.max(8,Math.min(innerWidth-p.offsetWidth-24,r.left))+'px';p.style.top=Math.min(innerHeight-p.offsetHeight-24,r.bottom+8)+'px';}api.listen(b,'click',()=>{p.hidden=!p.hidden;b.setAttribute('aria-expanded',String(!p.hidden));if(!p.hidden){place();close.focus();api.animate(p,[{opacity:0,translate:'0 -8px'},{opacity:1,translate:'0 0'}],{duration:180});}});api.listen(close,'click',hide);api.listen(document,'keydown',e=>{if(e.key==='Escape'&&!p.hidden)hide();});api.listen(document,'pointerdown',e=>{if(!p.hidden&&!el.contains(e.target))hide();});api.listen(window,'resize',place);api.listen(window,'scroll',()=>{if(!p.hidden)place();},{passive:true});""")
add('edge-fade','transparency','A content rail with soft masked edges and a non-masked fallback.',
 css='''.uv-edge-fade{overflow:auto;padding:24px;display:flex;gap:24px;scroll-snap-type:x mandatory;}.uv-edge-fade>.uv-card{min-width:min(320px,82vw);scroll-snap-align:center;}@supports(mask-image:linear-gradient(black,transparent)){.uv-edge-fade{mask-image:linear-gradient(90deg,transparent,#000 8%,#000 92%,transparent);}}''',
 markup='<div class="uv-edge-fade" data-uv="edge-fade" tabindex="0" role="region" aria-label="Scrollable collection">'+CARD*5+'</div>',flags=['gradient'],source=['backdrop'])

# Layouts: responsive, complete compositions with stable assembly slots.
HERO = '''<section class="uv-hero __HERO_CLASS__" __HERO_ATTRS__ id="story">__HERO_LAYERS__
<div class="uv-hero-copy"><p class="uv-label">__EYEBROW__</p><h1 class="__TITLE_CLASS__" __TITLE_ATTRS__>__TITLE__</h1>
<p class="uv-lede">__DESCRIPTION__</p><div class="uv-actions"><a class="btn __CTA_CLASS__" __CTA_ATTRS__ href="#collection">Explore the collection ↗</a><a href="#details">Discover the details ↓</a></div></div>
<div class="uv-visual __ART_CLASS__" __ART_ATTRS__>__HERO_ART__</div></section>'''
BUILD_CARD = CARD.replace('class="uv-card"','class="uv-card __CARD_CLASS__" __CARD_ATTRS__')
COLLECTION = '''<section class="uv-section" id="collection"><div class="uv-section-head"><div><p class="uv-label">The collection</p><h2>A language of your own.</h2></div><p>Considered down to the smallest detail.</p></div><div class="uv-grid __GRID_CLASS__" __GRID_ATTRS__>'''+BUILD_CARD*3+'</div></section>'
DETAILS = '''<section class="uv-section" id="details"><p class="uv-label">Made with intention</p><h2>Built here. Ready for anywhere.</h2><p class="uv-lede">A local library of motion, material and composition. The code stays close. Your ideas travel further.</p></section>'''
add('product-bento','layout','An asymmetric product hero and responsive bento collection with container-aware tiles.',
 css='''.uv-product .uv-hero{display:grid;grid-template-columns:1.12fr 1fr;align-items:center;gap:5vw;}.uv-product #collection>.uv-grid{grid-template-columns:1.3fr 1fr 1fr;}.uv-product #collection .uv-card:first-child{grid-row:span 2;}.uv-product .uv-card{container-type:inline-size;}@container(min-width:400px){.uv-product .uv-card-art{min-height:230px;}}@media(max-width:800px){.uv-product .uv-hero,.uv-product #collection>.uv-grid{grid-template-columns:1fr;}}''',
 markup='<main class="uv-product uv-shell">'+HERO+COLLECTION+DETAILS+'</main>')
add('editorial-split','layout','Large editorial typography, an offset motif and a boxless numbered reading sequence.',
 css='''.uv-editorial .uv-hero{display:grid;grid-template-columns:1.7fr 1fr;align-items:end;gap:6vw;border-bottom:1px solid var(--border);}.uv-editorial .uv-visual{aspect-ratio:3/4;}.uv-editorial .uv-visual::after{display:none;}.uv-editorial .uv-grid{display:block;counter-reset:edition;}.uv-editorial .uv-card{display:grid;grid-template-columns:90px 1fr 2fr;align-items:center;border:0;border-top:1px solid var(--border);border-radius:0;padding:32px 0;background:transparent;counter-increment:edition;}.uv-editorial .uv-card::before{content:"0" counter(edition);color:var(--muted);}.uv-editorial .uv-card-art,.uv-editorial .uv-card>.uv-label{display:none;}.uv-editorial .uv-hero h1{font-size:clamp(48px,9vw,144px);font-weight:400;letter-spacing:-.04em;}.uv-editorial .uv-hero-copy a:not(.btn){color:var(--text);}@media(max-width:800px){.uv-editorial .uv-hero{grid-template-columns:1fr;}.uv-editorial .uv-visual{max-height:300px;}.uv-editorial .uv-card{grid-template-columns:48px 1fr;gap:16px;}.uv-editorial .uv-card p{grid-column:2;}}''',
 markup='<main class="uv-editorial uv-shell">'+HERO+COLLECTION+DETAILS+'</main>',style='high-fashion')
add('story-rail','layout','A pinned exhibit opposite a long, numbered chapter rail; folds into a normal reading flow on mobile.',
 css='''.uv-story .uv-hero{display:grid;grid-template-columns:1fr 1fr;gap:6vw;align-items:center;}.uv-story #collection{display:grid;grid-template-columns:1fr 1fr;gap:8vw;align-items:start;}.uv-story .uv-section-head{position:sticky;top:120px;display:block;}.uv-story .uv-grid{display:block;}.uv-story .uv-card{margin-bottom:100px;min-height:320px;}.uv-story .uv-card:nth-child(even){margin-left:8%;}@media(max-width:800px){.uv-story .uv-hero,.uv-story #collection{grid-template-columns:1fr;}.uv-story .uv-section-head{position:static;}.uv-story .uv-card{margin-bottom:28px;}}''',
 markup='<main class="uv-story uv-shell">'+HERO+COLLECTION+DETAILS+'</main>',style='golden-archive')
add('overlap-gallery','layout','A dimensional hero followed by a horizontally snapped gallery that remains keyboard-scrollable.',
 css='''.uv-overlap .uv-hero{display:grid;grid-template-columns:1fr 1.1fr;gap:24px;align-items:center;}.uv-overlap .uv-hero-copy{position:relative;z-index:2;}.uv-overlap .uv-visual{margin-left:-8%;}.uv-overlap #collection>.uv-grid{display:flex;overflow:auto;scroll-snap-type:x mandatory;padding:24px 4px;}.uv-overlap #collection .uv-card{min-width:min(340px,82vw);scroll-snap-align:start;}.uv-overlap #collection .uv-card:nth-child(even){margin-top:30px;}@media(max-width:800px){.uv-overlap .uv-hero{grid-template-columns:1fr;}.uv-overlap .uv-visual{margin:0;}}''',
 markup='<main class="uv-overlap uv-shell">'+HERO+COLLECTION+DETAILS+'</main>',style='frutiger-aero')
add('product-focus','layout','One large product artifact, a sticky specification panel and clear comparison details.',
 css='''.uv-focus .uv-hero{display:grid;grid-template-columns:1fr 1.2fr;gap:8vw;align-items:center;}.uv-focus .uv-visual{grid-column:1;grid-row:1;min-height:450px;}.uv-focus .uv-hero-copy{grid-column:2;grid-row:1;}.uv-focus .uv-hero h1{font-size:clamp(42px,6vw,88px);}.uv-focus #details{max-width:760px;margin-left:auto;border-top:1px solid var(--border);}@media(max-width:800px){.uv-focus .uv-hero{display:flex;flex-direction:column-reverse;}.uv-focus .uv-visual{width:100%;min-height:280px;}}''',
 markup='<main class="uv-focus uv-shell">'+HERO+COLLECTION+DETAILS+'</main>',style='jewel')
add('app-panels','layout','A useful application shell with a sticky navigation column, compact hero and adaptive workspace tiles.',
 css='''.uv-app{display:grid;grid-template-columns:200px minmax(0,1fr);gap:40px;padding-block:40px;}.uv-app aside{position:sticky;top:32px;height:max-content;padding:20px;border:1px solid var(--border);border-radius:var(--radius);}.uv-app aside a{display:block;padding:12px 0;color:var(--muted);text-decoration:none;}.uv-app .uv-hero{display:grid;grid-template-columns:1.3fr 1fr;align-items:center;gap:24px;padding-block:32px;}.uv-app .uv-hero h1{font-size:clamp(34px,4vw,60px);}.uv-app .uv-visual{min-height:180px;}.uv-app .uv-grid{grid-template-columns:repeat(2,minmax(0,1fr));}.uv-app .uv-section{padding-block:32px;}@media(max-width:850px){.uv-app{grid-template-columns:1fr;}.uv-app aside{position:static;display:flex;gap:20px;flex-wrap:wrap;}.uv-app .uv-hero,.uv-app .uv-grid{grid-template-columns:1fr;}}''',
 markup='<main class="uv-app uv-shell"><aside aria-label="Workspace"><strong>WORKSPACE</strong><a href="#story">Overview</a><a href="#collection">Collection</a><a href="#details">Details</a></aside><div>'+HERO+COLLECTION+DETAILS+'</div></main>',style='neutral')
add('canvas-hero','layout','An immersive, centered canvas hero followed by an offset feature grid.',
 css='''.uv-canvas .uv-hero{min-height:80svh;display:grid;place-items:center;align-content:center;text-align:center;}.uv-canvas .uv-hero-copy{position:relative;z-index:2;}.uv-canvas .uv-hero h1{margin-inline:auto;max-width:13ch;}.uv-canvas .uv-lede{margin-inline:auto;}.uv-canvas .uv-actions{justify-content:center;}.uv-canvas .uv-visual{position:absolute;inset:4% 18%;z-index:-1;opacity:.13;}.uv-canvas .uv-visual::after{display:none;}.uv-canvas #collection .uv-card:nth-child(2){margin-top:48px;}.uv-canvas #collection .uv-card:nth-child(3){margin-top:96px;}@media(max-width:760px){.uv-canvas #collection .uv-card:nth-child(n){margin-top:0;}}''',
 markup='<main class="uv-canvas uv-shell">'+HERO+COLLECTION+DETAILS+'</main>',flags=['center'],style='vaporwave')
add('fluid-magazine','layout','An information-led magazine composition with a wide lead and aligned supporting columns.',
 css='''.uv-magazine .uv-hero{display:grid;grid-template-columns:1.5fr 1fr;align-items:end;gap:40px;border-bottom:2px solid var(--accent);}.uv-magazine .uv-visual::after{display:none;}.uv-magazine .uv-hero h1{font-size:clamp(44px,6vw,88px);max-width:14ch;letter-spacing:-.03em;}.uv-magazine #collection .uv-card{border:0;border-left:1px solid var(--border);border-radius:0;background:transparent;}.uv-magazine .uv-card:first-child{grid-column:span 2;}.uv-magazine #collection .uv-card-art{display:none;}@media(max-width:800px){.uv-magazine .uv-hero{grid-template-columns:1fr;}.uv-magazine .uv-card:first-child{grid-column:auto;}}''',
 markup='<main class="uv-magazine uv-shell">'+HERO+COLLECTION+DETAILS+'</main>',style='swiss-international')

# Interaction: real state, keyboard paths, focus handling and cleanup.
add('command-menu','interaction','A searchable command dialog with arrow keys, Enter, Escape and a scoped ⌘/Ctrl-K shortcut.',
 css='''.uv-command-input{width:100%;padding:16px;color:var(--text);background:var(--bg);border:1px solid var(--border);border-radius:var(--radius);}.uv-command-list{list-style:none;padding:0;margin-top:16px;}.uv-command-list button{width:100%;text-align:left;padding:16px;color:var(--text);background:transparent;border:0;}.uv-command-list button[aria-selected=true]{background:var(--accent);color:var(--on-accent);}.uv-command-empty{padding:16px;color:var(--muted);}''',
 markup='''<div data-uv="command-menu"><button class="btn">Quick actions <kbd>⌘ K</kbd></button><dialog class="uv-dialog"><header><h2>Quick actions</h2><button class="uv-close" aria-label="Close quick actions">×</button></header><label class="uv-sr">Search commands</label><input class="uv-command-input" type="search" aria-label="Search commands" placeholder="Find an action…" autocomplete="off"><ul class="uv-command-list"><li><button data-target="#story">Read the story</button></li><li><button data-target="#collection">Browse the collection</button></li><li><button data-target="#details">See the details</button></li></ul><p class="uv-command-empty" hidden>No matching actions.</p><p class="uv-label" aria-live="polite"></p></dialog></div>''',
 js="""const launch=el.querySelector('.btn'),d=el.querySelector('dialog'),input=d.querySelector('input'),all=[...d.querySelectorAll('li button')],empty=d.querySelector('.uv-command-empty'),live=d.querySelector('[aria-live]');let index=0;
function visible(){return all.filter(b=>!b.parentElement.hidden);}function select(){visible().forEach((b,i)=>b.setAttribute('aria-selected',String(i===index)));}function close(){d.close();launch.focus();}function open(){if(d.open)return;if(!d.showModal)return;d.showModal();input.focus();input.value='';all.forEach(b=>b.parentElement.hidden=false);empty.hidden=true;index=0;select();}api.listen(launch,'click',open);api.listen(d.querySelector('.uv-close'),'click',close);api.listen(d,'cancel',()=>launch.focus());
api.listen(input,'input',()=>{const q=input.value.toLowerCase();all.forEach(b=>b.parentElement.hidden=!b.textContent.toLowerCase().includes(q));index=0;empty.hidden=visible().length>0;live.textContent=visible().length+' actions';select();});
api.listen(input,'keydown',e=>{if(e.key==='Escape'){e.preventDefault();close();return;}const items=visible();if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();index=(index+(e.key==='ArrowDown'?1:-1)+items.length)%Math.max(1,items.length);select();}if(e.key==='Enter'&&items[index]){e.preventDefault();items[index].click();}});
all.forEach(b=>api.listen(b,'click',()=>{close();document.querySelector(b.dataset.target)?.scrollIntoView({behavior:api.motion?'smooth':'auto'});}));
api.listen(document,'keydown',e=>{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'&&!/input|textarea|select/i.test(e.target.tagName)&&!e.target.isContentEditable){e.preventDefault();d.open?close():open();}});return()=>{if(d.open)d.close();};""")
add('morph-tabs','interaction','Keyboard-accessible tabs with measured content transitions and stable panel IDs.',
 markup=TABS,source=['transition'],
 js="""const tabs=[...el.querySelectorAll('[role=tab]')],panels=[...el.querySelectorAll('[role=tabpanel]')];const uid='uv-tabs-'+Math.random().toString(36).slice(2,8);tabs.forEach((t,i)=>{t.id=uid+'-tab-'+i;panels[i].id=uid+'-panel-'+i;t.setAttribute('aria-controls',panels[i].id);panels[i].setAttribute('aria-labelledby',t.id);});
function change(i,focus=false){const update=()=>{tabs.forEach((t,j)=>{t.setAttribute('aria-selected',String(i===j));t.tabIndex=i===j?0:-1;panels[j].hidden=i!==j;});if(focus)tabs[i].focus();};if(api.motion&&document.startViewTransition)document.startViewTransition(update);else update();}
tabs.forEach((t,i)=>{api.listen(t,'click',()=>change(i));api.listen(t,'keydown',e=>{let j=i;if(e.key==='ArrowRight')j=(i+1)%tabs.length;else if(e.key==='ArrowLeft')j=(i-1+tabs.length)%tabs.length;else if(e.key==='Home')j=0;else if(e.key==='End')j=tabs.length-1;else return;e.preventDefault();change(j,true);});});""")
add('hover-preview','interaction','A work list with a pointer/focus preview and click-to-select support for touch.',
 css='''.uv-hover-work{display:grid;grid-template-columns:1.2fr 1fr;gap:32px;align-items:center;}.uv-hover-work nav button{display:block;width:100%;text-align:left;color:var(--text);background:transparent;border:0;border-bottom:1px solid var(--border);padding:22px 4px;font-size:clamp(22px,3vw,42px);font-family:var(--font-display);}.uv-hover-work nav button[aria-pressed=true]{color:var(--accent);}.uv-work-art{transition:transform .3s;}@media(max-width:700px){.uv-hover-work{grid-template-columns:1fr;}}''',
 markup='<div class="uv-hover-work" data-uv="hover-preview"><nav aria-label="Selected work"><button aria-pressed="true">01 · Identity</button><button aria-pressed="false">02 · Atmosphere</button><button aria-pressed="false">03 · Interaction</button></nav><div class="uv-work-art">'+ART+'<p class="uv-label" aria-live="polite">Identity</p></div></div>',
 js="""const buttons=[...el.querySelectorAll('nav button')],art=el.querySelector('.uv-work-art'),label=art.querySelector('p');function select(i){buttons.forEach((b,j)=>b.setAttribute('aria-pressed',String(i===j)));label.textContent=buttons[i].textContent.slice(5);api.animate(art,[{opacity:.45,transform:'translateY(12px)'},{opacity:1,transform:'none'}],{duration:300});}buttons.forEach((b,i)=>{api.listen(b,'pointerenter',()=>select(i));api.listen(b,'focus',()=>select(i));api.listen(b,'click',()=>select(i));});""")
add('scrollspy','interaction','A section index that follows visible chapters and preserves normal anchor navigation.',
 css='''.uv-spy-nav{position:sticky;top:12px;display:flex;gap:12px;padding:12px;background:var(--surface);z-index:20;border-bottom:1px solid var(--border);}.uv-spy-nav a{color:var(--muted);padding:10px;text-decoration:none;}.uv-spy-nav a[aria-current=true]{color:var(--accent);text-decoration:underline;}.uv-chapter{min-height:75svh;scroll-margin-top:100px;padding-block:60px;}''',
 markup='<div data-uv="scrollspy"><nav class="uv-spy-nav" aria-label="Chapters"><a href="#chapter-one">Story</a><a href="#chapter-two">Collection</a><a href="#chapter-three">Details</a></nav><section class="uv-chapter" id="chapter-one"><h2>The story.</h2>'+ART+'</section><section class="uv-chapter" id="chapter-two"><h2>The collection.</h2>'+TRIO+'</section><section class="uv-chapter" id="chapter-three"><h2>The details.</h2><p>Every surface has a purpose.</p></section></div>',
 js="""if(!('IntersectionObserver'in window))return;const links=[...el.querySelectorAll('nav a')],sections=links.map(a=>document.getElementById(a.hash.slice(1))).filter(Boolean),visible=new Map();const io=new IntersectionObserver(es=>{es.forEach(e=>visible.set(e.target,e.intersectionRatio));const current=[...visible].sort((a,b)=>b[1]-a[1])[0];if(current&&current[1]>0)links.forEach(a=>a.setAttribute('aria-current',String(a.hash==='#'+current[0].id)));},{threshold:[0,.2,.5,.8]});sections.forEach(s=>io.observe(s));return()=>io.disconnect();""")
add('media-lightbox','interaction','An artifact lightbox with native modal focus management, Escape and a no-JS inline artifact.',
 css='''.uv-lightbox-launch{display:block;width:100%;padding:20px;color:var(--accent);background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);}.uv-lightbox-launch .uv-visual{min-height:240px;}.uv-lightbox-dialog{width:min(900px,calc(100% - 32px));}.uv-lightbox-dialog .uv-visual{max-height:65svh;}''',
 markup='<div data-uv="media-lightbox"><button class="uv-lightbox-launch" aria-label="Enlarge the artifact">'+ART+'<span>Explore the artifact ↗</span></button><dialog class="uv-dialog uv-lightbox-dialog"><header><h2>The artifact</h2><button class="uv-close" aria-label="Close artifact">×</button></header>'+ART+'<p>Drawn from your local profile’s motif collection.</p></dialog></div>',source=['entry'],
 js="""const b=el.querySelector('.uv-lightbox-launch'),d=el.querySelector('dialog');api.listen(b,'click',()=>{if(!d.showModal)return;d.showModal();api.animate(d,[{opacity:0,transform:'scale(.96)'},{opacity:1,transform:'none'}],{duration:320});});api.listen(d.querySelector('.uv-close'),'click',()=>d.close());api.listen(d,'click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close();}});api.listen(d,'close',()=>b.focus());return()=>{if(d.open)d.close();};""")
add('anchor-tip','interaction','An anchored contextual tip with focus, pointer and Escape paths, bounded inside the viewport.',
 css='''.uv-anchor-tip{position:relative;display:inline-block;}.uv-tip{position:fixed;z-index:100;max-width:min(300px,calc(100vw - 32px));padding:16px;background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:var(--radius);font-size:var(--size-sm);}''',
 markup='<span class="uv-anchor-tip" data-uv="anchor-tip"><button class="btn">A small detail ⓘ</button><span class="uv-tip" role="tooltip" hidden>Local code, meaningful defaults, and one stable asset ID.</span></span>',
 js="""const b=el.querySelector('button'),tip=el.querySelector('[role=tooltip]');tip.id='uv-tip-'+Math.random().toString(36).slice(2,8);b.setAttribute('aria-describedby',tip.id);let focused=false,hover=false;function update(){tip.hidden=!(focused||hover);if(tip.hidden)return;const r=b.getBoundingClientRect();tip.style.left=Math.max(8,Math.min(innerWidth-tip.offsetWidth-16,r.left))+'px';tip.style.top=Math.max(8,Math.min(innerHeight-tip.offsetHeight-8,r.bottom+10))+'px';}api.listen(b,'pointerenter',()=>{hover=true;update();});api.listen(el,'pointerleave',()=>{hover=false;update();});api.listen(b,'focus',()=>{focused=true;update();});api.listen(b,'blur',()=>{focused=false;update();});api.listen(b,'click',()=>{focused=true;update();});api.listen(b,'keydown',e=>{if(e.key==='Escape'){focused=hover=false;update();}});api.listen(window,'resize',update);api.listen(window,'scroll',update,{passive:true});""")
add('spotlight-grid','interaction','A soft pointer-following highlight across a responsive card grid.',
 css='''.uv-spot-grid .uv-card{isolation:isolate;overflow:hidden;}.uv-spot-grid .uv-card::after{content:"";position:absolute;inset:0;pointer-events:none;z-index:-1;opacity:var(--uv-spot-opacity,0);background:radial-gradient(240px circle at var(--uv-spot-x,50%) var(--uv-spot-y,50%),color-mix(in srgb,var(--accent) 16%,transparent),transparent 70%);transition:opacity .2s;}''',
 markup='<div class="uv-spot-grid" data-uv="spotlight-grid">'+TRIO+'</div>',flags=['gradient'],
 js="""if(!api.motion||!matchMedia('(pointer:fine)').matches)return;const cards=[...el.querySelectorAll('.uv-card')];api.listen(el,'pointermove',api.frame(e=>cards.forEach(n=>{const r=n.getBoundingClientRect();n.style.setProperty('--uv-spot-x',(e.clientX-r.left)+'px');n.style.setProperty('--uv-spot-y',(e.clientY-r.top)+'px');n.style.setProperty('--uv-spot-opacity','1');})));const reset=()=>cards.forEach(n=>n.style.removeProperty('--uv-spot-opacity'));api.listen(el,'pointerleave',reset);return reset;""")

PACKS.update({
    'luminous-product': dict(style='ultraviolet',layout='product-bento',effects=['aurora-field','prism-border','gradient-type','reveal-stagger','magnetic-button','tilt-card','glass-panel','scroll-progress','command-menu'],title='Make room for what’s next.',eyebrow='Ultraviolet · a luminous product language',description='A dimensional product experience: drifting light, precise interactions, and surfaces with just enough depth.'),
    'glass-command': dict(style='y2k-chrome',layout='app-panels',effects=['glass-dock','acrylic-card','iridescent-surface','reveal-stagger','morph-tabs','command-menu','anchor-tip'],title='A clearer kind of workspace.',eyebrow='Y2K Chrome · precision in layers',description='Translucent controls, chrome highlights, and an application shell that makes the work feel immediate.'),
    'aero-showcase': dict(style='frutiger-aero',layout='overlap-gallery',effects=['glass-panel','glass-dock','scroll-depth','reveal-stagger','magnetic-button','media-lightbox','edge-fade'],title='A brighter view of possibility.',eyebrow='Frutiger Aero · nature meets technology',description='Air, light, and transparent layers. An optimistic collection grounded in sky and grass.'),
    'kinetic-editorial': dict(style='high-fashion',layout='editorial-split',effects=['split-lines','reveal-stagger','hover-preview','shared-transition'],title='An uncommon point of view.',eyebrow='High Fashion · the considered collection',description='Scale, type, and open space. A deliberate visual story with movement that knows when to stop.'),
    'museum-scroll': dict(style='golden-archive',layout='story-rail',effects=['noise-film','scroll-depth','reveal-stagger','media-lightbox','scroll-progress','scrollspy'],title='A collection worth keeping.',eyebrow='Golden Archive · artifacts preserved locally',description='A quiet passage through objects, ideas, and discoveries. Framed in gold; connected by curiosity.'),
    'precision-saas': dict(style='neutral',layout='product-bento',effects=['reveal-stagger','morph-tabs','command-menu','sticky-morph','anchor-tip'],title='Less friction. More forward.',eyebrow='Neutral · clarity as a product decision',description='A clear product narrative with useful interactions, responsive structure, and a single action language.'),
    'chromatic-lab': dict(style='vaporwave',layout='canvas-hero',effects=['shader-flow','gradient-type','iridescent-surface','prism-border','ambient-marquee','magnetic-button','reveal-stagger'],title='Build outside the ordinary.',eyebrow='Vaporwave · a field of experiments',description='An immersive canvas of color, reflective material, and movement. All powered by assets stored here.'),
    'signal-publication': dict(style='swiss-international',layout='fluid-magazine',effects=['reveal-stagger','scroll-progress','sticky-morph','hover-preview'],title='Ideas, clearly expressed.',eyebrow='Swiss International · form follows information',description='A rigorous grid, direct typography, and deliberate transitions. Information takes the lead.'),
    'organic-studio': dict(style='organic-tech',layout='overlap-gallery',effects=['aurora-field','reveal-stagger','magnetic-button','tilt-card','morph-tabs'],title='Something with a life of its own.',eyebrow='Organic Tech · living forms, useful tools',description='Biomorphic shapes, softened edges, and calm color. A studio that feels connected to the world around it.'),
    'jewel-product': dict(style='jewel',layout='product-focus',effects=['prism-border','reveal-stagger','media-lightbox','shared-transition','magnetic-button'],title='A closer look changes everything.',eyebrow='Jewel · objects with presence',description='Deep color, fine details, and room around the object. An intentional stage for a distinctive collection.'),
})



# Profile compositions are reusable assets, not palette swaps of a product hero.
FOLIO_HERO = '''<section class="uv-hero __HERO_CLASS__" __HERO_ATTRS__ id="story">__HERO_LAYERS__<div class="uv-hero-copy"><p class="uv-label">__EYEBROW__</p><h1 class="__TITLE_CLASS__" __TITLE_ATTRS__>__TITLE__</h1><p class="uv-lede">__DESCRIPTION__</p><div class="uv-actions"><a class="btn __CTA_CLASS__" __CTA_ATTRS__ href="#collection">__ACTION__</a></div></div><figure class="uv-scene __ART_CLASS__" __ART_ATTRS__>__HERO_ART__<figcaption>__PLATE__</figcaption></figure></section>'''
add('scholar-folio','layout','A candlelit library frontispiece, annotated manuscript and double-ruled reading index.',
 style='dark-academia',css='''.uv-scholar{padding-top:28px;}.uv-scholar .uv-hero{display:grid;grid-template-columns:1.1fr 1fr;gap:6%;padding:48px 0 72px;align-items:center;border-block:3px double var(--accent);}.uv-scholar h1{font-size:clamp(50px,6.5vw,92px);font-weight:700;letter-spacing:-.045em;max-width:11ch;}.uv-scholar .uv-hero-copy{grid-column:2;grid-row:1;}.uv-scholar .uv-scene{grid-column:1;grid-row:1;padding:12px;border:3px double var(--accent);background:var(--bg2);}.uv-scholar .uv-lede{font-style:italic;}.uv-manuscript{display:grid;grid-template-columns:160px minmax(0,680px) 1fr;gap:40px;padding-block:70px;}.uv-manuscript .uv-margin{font-family:'Caveat',cursive;transform:rotate(-5deg);color:var(--accent);padding-top:60px;font-size:24px;}.uv-manuscript .uv-prose::first-letter{float:left;font-family:var(--font-display);font-size:4.4em;line-height:.8;padding:8px 12px 0 0;color:var(--accent);}.uv-reading-list{border-block:3px double var(--accent);}.uv-reading-list article{padding:26px 0;border-bottom:1px solid var(--border);display:grid;grid-template-columns:64px 1fr 150px;gap:24px;}.uv-reading-list h3{font-size:22px;}.uv-reading-list small{font-style:italic;color:var(--muted);}@media(max-width:800px){.uv-scholar .uv-hero{grid-template-columns:1fr;gap:40px;}.uv-scholar .uv-hero-copy,.uv-scholar .uv-scene{grid-column:auto;grid-row:auto;}.uv-manuscript{grid-template-columns:1fr;gap:20px;}.uv-manuscript .uv-margin{padding-top:0;}.uv-reading-list article{grid-template-columns:40px 1fr;}.uv-reading-list small{grid-column:2;}}''',
 markup='<main class="uv-scholar uv-shell">'+FOLIO_HERO+'<section id="collection" class="uv-section uv-manuscript"><aside class="uv-margin">A note in the margin:<br>keep asking better questions.</aside><article><p class="uv-label">From the commonplace book · I</p><h2>The quiet work of paying attention.</h2><p class="uv-prose">A library is a conversation across time. Open a volume, follow a footnote, leave a thought for the reader who comes after you.</p><p style="margin-top:24px">Collected essays, close readings and ideas worth returning to. Nothing here needs to hurry.</p></article><span class="uv-folio">Vol. I<br>Autumn edition</span></section><section class="uv-reading-list uv-section __GRID_CLASS__" __GRID_ATTRS__><article><span>I.</span><h3>On the art of observation</h3><small>Essay · 8 min</small></article><article><span>II.</span><h3>A room of collected thoughts</h3><small>Field notes · 6 min</small></article><article><span>III.</span><h3>The things we underline</h3><small>Reading list</small></article></section>'+DETAILS+'</main>')
add('signal-console','layout','A chamfered city-feed console with status rail, live-signal readouts and dense sector index.',
 style='cyberpunk',css='''.uv-console .uv-hero{display:grid;grid-template-columns:1fr 1.2fr;gap:5%;padding-block:36px;align-items:center;}.uv-console .uv-hero h1{font-size:clamp(36px,4.4vw,64px);letter-spacing:0;line-height:1.1;text-transform:uppercase;max-width:10ch;}.uv-console .uv-hero .uv-lede{font-size:15px;line-height:1.8;margin-block:20px;}.uv-console .uv-hero .uv-scene>svg{max-height:620px;}.uv-console .uv-inline-status{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;padding-top:24px;margin-top:24px;border-top:1px solid var(--border);font-size:11px;}.uv-inline-status strong{display:block;font:700 24px var(--font-display);color:var(--accent);}.uv-console .uv-scene{border:1px solid var(--accent);position:relative;}.uv-console .uv-scene::after{content:"";position:absolute;inset:0;pointer-events:none;background:repeating-linear-gradient(transparent 0 3px,rgba(0,0,0,.15) 3px 4px);}.uv-status-rail{display:flex;justify-content:space-between;gap:16px;padding:12px 0;border-block:1px solid var(--accent);color:var(--accent);font:14px var(--mono);flex-wrap:wrap;}.uv-console .uv-label{color:var(--accent2);}.uv-console .btn{clip-path:polygon(0 0,calc(100% - 13px) 0,100% 13px,100% 100%,13px 100%,0 calc(100% - 13px));border-radius:0;}.uv-telemetry{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));border:1px solid var(--border);}.uv-telemetry article{padding:24px;border-inline-end:1px solid var(--border);background:var(--bg2);}.uv-telemetry strong{display:block;font:700 40px var(--font-display);color:var(--accent);}.uv-sector-list{border-block:1px solid var(--accent);}.uv-sector-list p{display:grid;grid-template-columns:1fr 2fr 1fr;gap:20px;padding:18px;border-bottom:1px solid var(--border);font:14px var(--mono);}.uv-sector-list b{color:var(--accent2);}@media(max-width:800px){.uv-console .uv-hero{grid-template-columns:1fr;gap:36px;}.uv-telemetry{grid-template-columns:1fr;}.uv-telemetry article{border-block-end:1px solid var(--border);}.uv-sector-list p{grid-template-columns:1fr 1.5fr;}.uv-sector-list p>:last-child{grid-column:2;}}''',
 markup='<main class="uv-console uv-shell"><div class="uv-status-rail"><span>● UPLINK ESTABLISHED</span><span>SECTOR_07</span><span>LOCAL / ENCRYPTED</span></div>'+FOLIO_HERO+'<section id="collection" class="uv-section __GRID_CLASS__" __GRID_ATTRS__><div class="uv-telemetry"><article><span class="uv-label">Signal integrity</span><strong>98.4%</strong><p>Stable carrier</p></article><article><span class="uv-label">Nodes discovered</span><strong>024</strong><p>Mesh connected</p></article><article><span class="uv-label">Round trip</span><strong>12ms</strong><p>Local endpoint</p></article></div><div class="uv-sector-list"><p><b>CHANNEL_01</b><span>Optical feed / street level</span><span>ONLINE</span></p><p><b>CHANNEL_02</b><span>Relay station / rooftop</span><span>ONLINE</span></p><p><b>CHANNEL_03</b><span>Archive node / lower district</span><span>STANDBY</span></p></div></section>'+DETAILS+'</main>')
add('atelier-spread','layout','A fashion campaign spread with monumental Didone type, a portrait plate and minimal look index.',
 style='high-fashion',css='''.uv-atelier{max-width:1440px;}.uv-atelier .uv-hero{display:grid;grid-template-columns:1.1fr 1fr;gap:0;align-items:center;padding:40px 0 100px;min-height:85svh;}.uv-atelier .uv-hero-copy{position:relative;z-index:2;margin-right:-14%;padding-block:40px;}.uv-atelier .uv-hero h1{font-size:clamp(64px,10.5vw,158px);font-weight:700;letter-spacing:-.07em;max-width:7.5ch;line-height:.9;margin-block:36px;}.uv-atelier .uv-lede{font-size:18px;max-width:27ch;line-height:1.7;}.uv-atelier .uv-label{letter-spacing:.25em;font-family:var(--mono);font-size:12px;}.uv-atelier .uv-scene{margin-left:0;align-self:start;}.uv-atelier .uv-scene svg{aspect-ratio:3/4;object-fit:cover;}.uv-atelier .btn{color:var(--text);background:transparent;border:0;border-bottom:1px solid var(--text);border-radius:0;padding:12px 0;box-shadow:none;font-size:14px;letter-spacing:.15em;text-transform:uppercase;}.uv-look-index{border-top:1px solid var(--text);}.uv-look-index article{display:grid;grid-template-columns:70px 1fr 1fr;gap:36px;padding:36px 0;border-bottom:1px solid var(--border);align-items:baseline;}.uv-look-index h3{font-size:32px;font-weight:400;}.uv-look-index p{font-style:italic;color:var(--muted);}.uv-atelier #details{max-width:52ch;padding-block:100px;}@media(max-width:800px){.uv-atelier .uv-hero{grid-template-columns:1fr;padding-block:32px 60px;}.uv-atelier .uv-hero-copy{margin:0;}.uv-atelier .uv-hero h1{font-size:clamp(62px,16vw,100px);max-width:9ch;}.uv-atelier .uv-scene{max-width:100%;}.uv-look-index article{grid-template-columns:40px 1fr;gap:16px;}.uv-look-index p{grid-column:2;}}''',
 markup='<main class="uv-atelier uv-shell">'+FOLIO_HERO+'<section class="uv-look-index uv-section __GRID_CLASS__" __GRID_ATTRS__ id="collection"><p class="uv-label">Selected silhouettes / collection 01</p><article><span>01</span><h3>The sculpted coat.</h3><p>Structure. Volume. Restraint.</p></article><article><span>02</span><h3>A study in proportion.</h3><p>Cut with intention.</p></article><article><span>03</span><h3>Only what remains.</h3><p>The final edit.</p></article></section>'+DETAILS+'</main>')
add('nordic-catalog','layout','A daylight object catalogue, horizontal material index and practical product notes; polar-night mode remains available.',
 style='nordic',css='''.uv-nordic-page .uv-hero{display:grid;grid-template-columns:.9fr 1.3fr;gap:8%;align-items:center;padding-block:60px;}.uv-nordic-page h1{font-size:clamp(40px,5vw,68px);font-weight:600;letter-spacing:-.045em;max-width:12ch;line-height:1.12;}.uv-nordic-page .uv-lede{font-size:18px;max-width:33ch;}.uv-nordic-page .uv-label{font-size:12px;letter-spacing:.15em;}.uv-nordic-page .btn{border-radius:4px;padding:14px 24px;background:var(--accent);color:var(--on-accent);box-shadow:none;}.uv-material-index{display:grid;grid-template-columns:1.6fr 1fr 1fr;gap:8%;padding-block:64px;border-block:1px solid var(--border);}.uv-material-index h2{font-size:32px;font-weight:500;}.uv-material-index h3{font-size:18px;font-weight:500;margin-bottom:20px;}.uv-material-index p{color:var(--muted);}.uv-nordic-page #details{padding-block:80px;max-width:64ch;}.uv-nordic-page .uv-scene figcaption{font-size:12px;letter-spacing:.08em;}@media(max-width:800px){.uv-nordic-page .uv-hero{grid-template-columns:1fr;gap:36px;padding-block:40px;}.uv-material-index{grid-template-columns:1fr;gap:36px;}.uv-nordic-page h1{max-width:14ch;}}''',
 markup='<main class="uv-nordic-page uv-shell">'+FOLIO_HERO+'<section id="collection" class="uv-material-index __GRID_CLASS__" __GRID_ATTRS__><div><p class="uv-label">Considered objects</p><h2>Useful. Familiar.<br>Made to stay.</h2></div><article><h3>01 / Honest materials</h3><p>Timber, linen and matte ceramic. Each material does what it does best.</p></article><article><h3>02 / Everyday comfort</h3><p>Useful proportions. Soft light. Room for the way you live.</p></article></section>'+DETAILS+'</main>')
add('geometric-poster','layout','An asymmetric workshop poster with large functional numerals and a measured colour study.',
 style='bauhaus',css='''.uv-workshop .uv-hero{display:grid;grid-template-columns:1fr 1fr;gap:8%;padding-block:60px;align-items:center;border-bottom:2px solid var(--text);}.uv-workshop h1{font-size:clamp(48px,7vw,104px);line-height:.95;letter-spacing:-.065em;max-width:9ch;}.uv-workshop .uv-hero-copy::before{content:"01";display:block;font:700 72px var(--font-display);color:var(--accent);}.uv-workshop .uv-label{text-transform:uppercase;}.uv-workshop .btn{border-radius:0;}.uv-workshop .uv-grid{grid-template-columns:repeat(3,minmax(0,1fr));gap:0;}.uv-workshop .uv-card{border:0;border-right:1px solid var(--text);border-radius:0;background:transparent;box-shadow:none;}.uv-workshop .uv-card-art{display:none;}@media(max-width:800px){.uv-workshop .uv-hero,.uv-workshop .uv-grid{grid-template-columns:1fr;gap:36px;}.uv-workshop .uv-card{border-right:0;border-top:1px solid var(--text);}}''',
 markup='<main class="uv-workshop uv-shell">'+FOLIO_HERO+COLLECTION+DETAILS+'</main>')
add('botanical-plate','layout','A framed botanical exhibition poster whose border and lettering share a continuous organic line.',
 style='art-nouveau',css='''.uv-botanical{padding-top:36px;}.uv-botanical .uv-hero{display:grid;grid-template-columns:1fr 1fr;gap:3%;align-items:center;padding:54px 5%;border:3px double var(--accent);border-radius:48% 48% 0 0 / 6% 6% 0 0;}.uv-botanical .uv-hero h1{font-size:clamp(48px,6vw,84px);font-weight:600;line-height:1.05;max-width:9ch;letter-spacing:-.045em;}.uv-botanical .uv-label{font-size:12px;letter-spacing:.18em;}.uv-botanical .uv-lede{font-style:italic;max-width:31ch;}.uv-botanical .btn{border:1px solid var(--accent);border-radius:30px 0 30px 0;}.uv-botanical .uv-grid{gap:0;}.uv-botanical .uv-card{background:transparent;border:0;border-right:1px solid var(--border);border-radius:0;box-shadow:none;}.uv-botanical .uv-card-art{display:none;}.uv-botanical #details{max-width:64ch;margin:auto;}@media(max-width:800px){.uv-botanical .uv-hero,.uv-botanical .uv-grid{grid-template-columns:1fr;}.uv-botanical .uv-hero{padding:44px 24px;border-radius:0;}.uv-botanical .uv-scene{margin-top:32px;}.uv-botanical .uv-card{border-right:0;border-top:1px solid var(--border);}}''',
 markup='<main class="uv-botanical uv-shell">'+FOLIO_HERO+COLLECTION+DETAILS+'</main>')
PACKS['kinetic-editorial'].update(layout='atelier-spread',effects=['reveal-stagger','scroll-progress'],title='The shape of silence.',eyebrow='ATELIER / COLLECTION 01',description='A study in silhouette. Sculpted volume, deliberate proportion, and nothing without a purpose.')
PACKS.update({
 'candlelit-library':dict(style='dark-academia',layout='scholar-folio',effects=['noise-film','reveal-stagger','scroll-progress'],title='For the love of knowing.',eyebrow='THE COMMONPLACE / VOLUME I',description='Essays, observations and the quiet pleasure of following an idea a little further.'),
 'night-city-console':dict(style='cyberpunk',layout='signal-console',effects=['reveal-stagger','command-menu'],title='The city never disconnects.',eyebrow='NIGHT RELAY / SECTOR_07',description='Independent signals from the lower district. Open a channel. Read the network. Leave no trace.'),
 'nordic-daylight':dict(style='nordic',layout='nordic-catalog',effects=['reveal-stagger'],title='A little more room to live.',eyebrow='FORM / EVERYDAY OBJECTS',description='Considered objects for ordinary days. Honest materials, gentle light, and comfort that lasts.'),
 'workshop-modern':dict(style='bauhaus',layout='geometric-poster',effects=['reveal-stagger'],title='Form follows making.',eyebrow='WORKSHOP / FORM + MATERIAL',description='A practical study of colour, construction and useful objects. Learn by making.'),
 'botanical-exhibition':dict(style='art-nouveau',layout='botanical-plate',effects=['reveal-stagger'],title='The line comes to life.',eyebrow='BOTANICAL ARTS / EXHIBITION 01',description='An exhibition of growing forms, sinuous lines and the art of looking closely.')
})



# Explicitly distinguish visual languages from palette/accessibility registers.
STYLE_DESIGNS = {'dark-academia': {'kind': 'Visual style',
                   'layout': 'scholar-folio',
                   'title': 'For the love of knowing.',
                   'eyebrow': 'THE COMMONPLACE / VOLUME I',
                   'description': 'Essays, observations and the quiet pleasure of following an idea a little '
                                  'further.',
                   'brand': 'THE COMMONPLACE',
                   'action': 'Enter the reading room',
                   'plate': 'Plate I / a room for thought',
                   'recognition': 'Gothic library, double rules, manuscript drop cap, marginal notes; not a '
                                  'brown product grid.'},
 'cyberpunk': {'kind': 'Visual style',
               'layout': 'signal-console',
               'title': 'The city never disconnects.',
               'eyebrow': 'NIGHT RELAY / SECTOR_07',
               'description': 'Independent signals from the lower district. Open a channel. Read the '
                              'network. Leave no trace.',
               'brand': 'NIGHT RELAY_',
               'action': 'OPEN CHANNEL ↗',
               'plate': 'OPTICAL FEED / LOCAL VECTOR PLATE',
               'recognition': 'Chamfered controls, rain-lit city, dense telemetry and compressed mono '
                              'labels; not a neon product page.'},
 'high-fashion': {'kind': 'Visual style',
                  'layout': 'atelier-spread',
                  'title': 'The shape of silence.',
                  'eyebrow': 'ATELIER / COLLECTION 01',
                  'description': 'A study in silhouette. Sculpted volume, deliberate proportion, and nothing '
                                 'without a purpose.',
                  'brand': 'ATELIER',
                  'action': 'View the collection',
                  'plate': 'Look 01 / original fashion illustration',
                  'recognition': 'Monumental Didone, dominant portrait, asymmetry, tiny folios and a boxless '
                                 'look index; not a jewellery dashboard.'},
 'nordic': {'kind': 'Visual style',
            'layout': 'nordic-catalog',
            'title': 'A little more room to live.',
            'eyebrow': 'FORM / EVERYDAY OBJECTS',
            'description': 'Considered objects for ordinary days. Honest materials, gentle light, and '
                           'comfort that lasts.',
            'brand': 'FORM / OBJECTS',
            'action': 'Explore the objects',
            'plate': '01 / timber, ceramic and lateral light',
            'recognition': 'Useful horizontal catalogue, pale timber, layered lamp and quiet typography; not '
                           'just the Nord terminal palette.'},
 'bauhaus': {'kind': 'Visual style',
             'layout': 'geometric-poster',
             'title': 'Form follows making.',
             'eyebrow': 'WORKSHOP / FORM + MATERIAL',
             'description': 'A practical study of colour, construction and useful objects. Learn by making.',
             'brand': 'WORKSHOP 01',
             'action': 'Enter the workshop',
             'plate': 'Exercise 01 / original form study',
             'recognition': 'Asymmetric modular poster, functional oversized numerals and balanced geometric '
                            'masses; distinct from decorative Memphis.'},
 'art-nouveau': {'kind': 'Visual style',
                 'layout': 'botanical-plate',
                 'title': 'The line comes to life.',
                 'eyebrow': 'BOTANICAL ARTS / EXHIBITION 01',
                 'description': 'An exhibition of growing forms, sinuous lines and the art of looking '
                                'closely.',
                 'brand': 'BOTANICAL ARTS',
                 'action': 'Explore the exhibition',
                 'plate': 'Iris / original botanical plate',
                 'recognition': 'Whiplash stems extend into a continuous organic frame; distinct from '
                                'angular stepped Art Deco.'},
 'frutiger-aero': {'kind': 'Visual style',
                   'layout': 'overlap-gallery',
                   'title': 'A brighter way to connect.',
                   'eyebrow': 'AERO / NATURE + TECHNOLOGY',
                   'description': 'Optimistic tools in a world of sky, water and living things.',
                   'brand': 'AERO WORLD',
                   'action': 'Explore the world',
                   'plate': 'Sky, gloss and ecology',
                   'recognition': 'Wet glass, aqua spheres, sky/grass ecology and buoyant layered surfaces.'},
 'vaporwave': {'kind': 'Visual style',
               'layout': 'canvas-hero',
               'title': 'Wish you were here, again.',
               'eyebrow': 'AFTER HOURS / DIGITAL NOSTALGIA',
               'description': 'A memory of a future that never arrived. Sunset colour, synthetic objects and '
                              'a little interference.',
               'brand': 'AFTER HOURS',
               'action': 'Enter the archive',
               'plate': 'A synthetic memory',
               'recognition': 'A central retro object, checker horizon and spaced display type; leisure and '
                              'nostalgia rather than cyberpunk telemetry.'},
 'mono': {'kind': 'Visual style',
          'layout': 'app-panels',
          'title': 'NO FINISH. ALL STRUCTURE.',
          'eyebrow': 'INDEX / RAW WEB',
          'description': 'Exposed structure. Direct navigation. Content without camouflage.',
          'brand': 'INDEX_',
          'action': 'OPEN INDEX',
          'plate': 'Structure before surface',
          'recognition': 'Raw index, heavy rules, block typography, square controls and zero motion.'},
 'golden-archive': {'kind': 'Visual style',
                    'layout': 'story-rail',
                    'title': 'A record for another world.',
                    'eyebrow': 'THE GOLDEN ARCHIVE / RECORD 01',
                    'description': 'Objects, signals and stories kept with care. An exhibition across '
                                   'distance and time.',
                    'brand': 'GOLDEN ARCHIVE',
                    'action': 'Enter the exhibition',
                    'plate': 'Artifact 01 / transmission record',
                    'recognition': 'Pinned artifacts, museum plaques, gold discipline and a chapter rail; '
                                   'scholarship becomes an exhibit rather than a reading room.'},
 'avant-basic': {'kind': 'Visual style',
                 'layout': 'overlap-gallery',
                 'title': 'Less sensible. More alive.',
                 'eyebrow': 'PLAYHOUSE / COLOUR IN MOTION',
                 'description': 'A joyful collision of wavy shapes, clashing colours and unapologetic '
                                'objects.',
                 'brand': 'PLAYHOUSE',
                 'action': 'Meet the collection',
                 'plate': 'Memphis-influenced / original motifs',
                 'recognition': 'Oversized squiggles, checkerboard, flat clashing blocks and hard offsets; a '
                                'contemporary Memphis-influenced interpretation.'},
 'organic-tech': {'kind': 'Visual style',
                  'layout': 'overlap-gallery',
                  'title': 'Technology with room to grow.',
                  'eyebrow': 'LIVING SYSTEMS / STUDIO',
                  'description': 'Useful tools shaped by the rhythms of the living world.',
                  'brand': 'LIVING SYSTEMS',
                  'action': 'Explore the systems',
                  'plate': 'Cells, contours and softened structure',
                  'recognition': 'Biomorphic contours, asymmetric rounded fields and botanical interfaces; '
                                 'distinct from Nordic object functionalism.'},
 'skate-culture': {'kind': 'Visual style',
                   'layout': 'editorial-split',
                   'title': 'MADE TO GET MARKED.',
                   'eyebrow': 'STREET PRESS / ISSUE 01',
                   'description': 'Independent work from outside the lines. Worn in, written over, still '
                                  'moving.',
                   'brand': 'STREET PRESS',
                   'action': 'SEE THE DROP',
                   'plate': 'Sticker sheet / local vector graphics',
                   'recognition': 'Condensed shouting type, torn print edges, rotated stickers and an '
                                  'abrasive zine index.'},
 'mosaic': {'kind': 'Visual style',
            'layout': 'fluid-magazine',
            'title': 'Many pieces. One place.',
            'eyebrow': 'TESSERA / COLLECTED FRAGMENTS',
            'description': 'A collection built from fragments, each with a place in the whole.',
            'brand': 'TESSERA',
            'action': 'Explore the pieces',
            'plate': 'A field of tesserae',
            'recognition': 'Fragmented tile rhythm, irregular coloured chips and grout-like divisions; no '
                           'glass or fluid gradients.'},
 'art-deco': {'kind': 'Visual style',
              'layout': 'canvas-hero',
              'title': 'A grand entrance.',
              'eyebrow': 'THE SALON / EDITION 01',
              'description': 'An evening in measured geometry. Symmetry, stepped form and a little ceremony.',
              'brand': 'THE SALON',
              'action': 'Enter the salon',
              'plate': 'A geometric fan in gold',
              'recognition': 'Stepped portals, axial symmetry, fan geometry and tall lettering; distinct '
                             'from botanical Art Nouveau.'},
 'frutiger-metro': {'kind': 'Visual style',
                    'layout': 'overlap-gallery',
                    'title': 'A city in full bloom.',
                    'eyebrow': 'METRO / CULTURE IN COLOUR',
                    'description': 'Flat vectors, vivid places and an optimistic public rhythm.',
                    'brand': 'METRO BLOOM',
                    'action': 'Explore the programme',
                    'plate': 'Vector bloom / civic graphic',
                    'recognition': 'Flat flower bursts, dot clusters, swooshes and vivid civic colour; no '
                                   'Aero glass.'},
 'preppy-2000s': {'kind': 'Visual style',
                  'layout': 'product-bento',
                  'title': 'Meet you at the clubhouse.',
                  'eyebrow': 'THE CLUB / FALL EDITION',
                  'description': 'Collegiate colour, collected essentials and a little weekend spirit.',
                  'brand': 'THE CLUB',
                  'action': 'See the edit',
                  'plate': 'Argyle / crest / ribbon',
                  'recognition': 'Argyle panels, varsity slab, crest and ribbon hierarchy; brighter and more '
                                 'commercial than Dark Academia.'},
 'y2k-chrome': {'kind': 'Visual style',
                'layout': 'product-focus',
                'title': 'The future has a new finish.',
                'eyebrow': 'MILLENNIUM / OBJECT 001',
                'description': 'Liquid chrome, synthetic clarity and a confident new silhouette.',
                'brand': 'MILLENNIUM',
                'action': 'Discover the object',
                'plate': 'Chrome / orbital study',
                'recognition': 'Liquid-metal hero, stretched glossy controls and lens-flare accents; '
                               'distinct from vaporwave nostalgia.'},
 'swiss-international': {'kind': 'Visual style',
                         'layout': 'fluid-magazine',
                         'title': 'Information, in order.',
                         'eyebrow': 'DESIGN FORUM / PROGRAMME 01',
                         'description': 'Clear thinking made visible. A programme of talks, exhibitions and '
                                        'practical ideas.',
                         'brand': 'DESIGN FORUM',
                         'action': 'Read the programme',
                         'plate': 'Grid / signal / direction',
                         'recognition': 'Flush-left asymmetric grid, enormous functional numerals and one '
                                        'signal red; no centred hero or decorative frame.'},
 'editorial': {'kind': 'Visual style',
               'layout': 'editorial-split',
               'title': 'A point of view worth reading.',
               'eyebrow': 'THE REVIEW / ISSUE 01',
               'description': 'Independent essays and considered observations, published with care.',
               'brand': 'THE REVIEW',
               'action': 'Read the issue',
               'plate': 'Rules / columns / reading rhythm',
               'recognition': 'Magazine hierarchy, narrow reading columns, rules and numbered stories; less '
                              'theatrical than High Fashion.'},
 'neutral': {'kind': 'System / color register',
             'layout': 'product-bento',
             'title': 'A clearer working day.',
             'eyebrow': 'WORKSPACE / EVERYDAY TOOLS',
             'description': 'Practical tools with consistent spacing, useful hierarchy and familiar '
                            'controls.',
             'brand': 'WORKSPACE',
             'action': 'Open the workspace',
             'plate': 'System components',
             'recognition': 'A functional base system; choose for utility, not as a distinct historical '
                            'style.'},
 'hi-contrast': {'kind': 'System / color register',
                 'layout': 'app-panels',
                 'title': 'Clear at every step.',
                 'eyebrow': 'ACCESS / TASK INDEX',
                 'description': 'Large targets, explicit states and information you can find quickly.',
                 'brand': 'ACCESS',
                 'action': 'Start a task',
                 'plate': 'Visibility / structure / focus',
                 'recognition': 'An accessibility-oriented register with strong contrast and targets; not a '
                                'historical design movement.'},
 'pastel': {'kind': 'System / color register',
            'layout': 'product-bento',
            'title': 'A softer start.',
            'eyebrow': 'SMALL JOYS / DAILY EDIT',
            'description': 'Gentle colour and approachable objects for the little rituals of a day.',
            'brand': 'SMALL JOYS',
            'action': 'Find your ritual',
            'plate': 'Soft colour / rounded forms',
            'recognition': 'A soft colour/material register; combine with a deliberate layout rather than '
                           'calling colour a complete style.'},
 'earthy': {'kind': 'System / color register',
            'layout': 'product-focus',
            'title': 'Made by hand. Made to last.',
            'eyebrow': 'FIELDWORK / CRAFTED OBJECTS',
            'description': 'Clay, stone and practical things with a trace of the hands that made them.',
            'brand': 'FIELDWORK',
            'action': 'Meet the makers',
            'plate': 'Clay / grain / tactile form',
            'recognition': 'An earthy craft register; material texture and grounded product staging '
                           'distinguish it from a beige recolour.'},
 'jewel': {'kind': 'System / color register',
           'layout': 'product-focus',
           'title': 'Objects with presence.',
           'eyebrow': 'THE COLLECTION / OBJECT 01',
           'description': 'Deep colour, fine details and an object worth looking at closely.',
           'brand': 'THE COLLECTION',
           'action': 'View the object',
           'plate': 'Precious colour / display object',
           'recognition': 'A deep luxury colour register; choose High Fashion or Art Deco when a stronger '
                          'compositional language is needed.'},
 'ultraviolet': {'kind': 'System / color register',
                 'layout': 'product-bento',
                 'title': 'Make room for what’s next.',
                 'eyebrow': 'ULTRAVIOLET / PRODUCT STUDIO',
                 'description': 'A luminous product experience, built with considered depth and precise '
                                'interactions.',
                 'brand': 'ULTRAVIOLET',
                 'action': 'Explore the product',
                 'plate': 'Constellation / local motif',
                 'recognition': 'A luminous technology colour register; retain it for products that already '
                                'own this identity.'},
 'ember': {'kind': 'System / color register',
           'layout': 'app-panels',
           'title': 'Keep the work burning.',
           'eyebrow': 'FORGE / LOCAL WORKSPACE',
           'description': 'A warm working environment for making, testing and finishing what matters.',
           'brand': 'FORGE',
           'action': 'Open the forge',
           'plate': 'Heat / forged structure',
           'recognition': 'A warm-dark tool register; colour temperature is its distinction, not a separate '
                          'design movement.'}}


def _hero_artwork(style):
    a=_vault();p=a.profile_for(style)
    if p.get('hero_asset'):return a.SHAPES[p['hero_asset']]['svg']
    shapes=p['shapes'][:3]
    positions=[(45,70,570,570),(425,500,220,220),(30,590,230,200)]
    pieces=[]
    for key,(x,y,w,h) in zip(shapes,positions):
        art=a.SHAPES[key]['svg'].replace('<svg ',f'<svg x="{x}" y="{y}" width="{w}" height="{h}" ',1)
        pieces.append(art)
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 840" role="img" aria-label="'+html.escape(p['label']+' signature composition',quote=True)+'">'+''.join(pieces)+'</svg>'


def style_plan(style):
    d=STYLE_DESIGNS[style]
    return plan('luminous-product',style=style,layout=d['layout'],effects=[],copy={k:d[k] for k in ('title','eyebrow','description')})


def _identity_css(style):
    # These distinctions are structural and remain visible with colour hidden.
    return {
      'mono':'.uv-nav,.uv-app aside{border-width:3px;border-radius:0;}.uv-app .uv-hero h1{text-transform:uppercase;line-height:1;}.uv-app .uv-grid{display:block;}.uv-app .uv-card{border:0;border-top:3px solid var(--text);border-radius:0;background:transparent;}.uv-app .uv-card-art{display:none;}',
      'avant-basic':'.uv-hero{background:var(--bg2);border:3px solid var(--text);border-radius:32px 0 32px 0;padding:48px 32px!important;}.uv-hero h1{line-height:1;}.uv-overlap .uv-visual{transform:rotate(-5deg);}.uv-card:nth-child(even){transform:rotate(3deg);}.uv-card{box-shadow:6px 6px 0 var(--text);border:2px solid var(--text);}',
      'skate-culture':'.uv-hero h1{text-transform:uppercase;transform:rotate(-3deg);}.uv-hero .uv-visual{transform:rotate(8deg);}.uv-hero{border-bottom:5px solid var(--accent)!important;}.uv-card{border-block-width:3px!important;}.uv-label{font-family:"Permanent Marker",cursive;color:var(--accent);}',
      'art-deco':'.uv-canvas .uv-hero{border:4px double var(--accent);margin-top:32px;padding:70px 8%;}.uv-canvas .uv-visual{opacity:.24;inset:2% 8%;}.uv-canvas h1{font-family:"Poiret One",sans-serif;letter-spacing:.08em;text-transform:uppercase;}.uv-canvas .uv-hero-copy{background:var(--bg);padding:32px;}.uv-card{border:3px double var(--accent);border-radius:0;}',
      'swiss-international':'.uv-magazine .uv-hero h1{font-family:var(--font);font-weight:700;letter-spacing:-.065em;}.uv-magazine .uv-hero-copy::before{content:"01";display:block;font:700 clamp(80px,14vw,200px)/.85 var(--font);color:var(--accent);}.uv-magazine .uv-visual{display:none;}.uv-magazine .uv-hero{grid-template-columns:1fr;}.uv-magazine .uv-grid{gap:0;}.uv-magazine .uv-card{border-radius:0;border:0;border-top:1px solid var(--text);background:transparent;}',
      'preppy-2000s':'.uv-product .uv-hero{border-block:4px double var(--accent);margin-top:30px;padding:50px 24px;}.uv-product .uv-hero h1{font-family:"Alfa Slab One",serif;}.uv-product .uv-card{border:3px double var(--accent);}.uv-nav{border-block:3px solid var(--accent);}',
      'mosaic':'.uv-magazine .uv-hero{border:12px solid var(--border);padding:32px;}.uv-magazine .uv-grid{gap:8px;}.uv-magazine .uv-card:nth-child(2){background:var(--bg2);transform:translateY(20px);}.uv-magazine .uv-card{border:4px solid var(--border);border-radius:0;}.uv-visual::after{display:none;}',
      'frutiger-metro':'.uv-hero h1{font-weight:500;letter-spacing:-.05em;}.uv-overlap .uv-visual{transform:rotate(-8deg);}.uv-card{border:0;box-shadow:none;border-radius:0 44px 0 44px;}.uv-card:nth-child(2){border-radius:44px 0 44px 0;}.uv-nav{border-bottom:4px solid var(--accent);}',
      'vaporwave':'.uv-canvas .uv-visual{opacity:.32;inset:1% 16%;}.uv-canvas .uv-hero{border-bottom:2px solid var(--accent2);}.uv-canvas .uv-hero-copy{background:var(--surface);padding:36px;}.uv-canvas .uv-hero h1{text-transform:uppercase;letter-spacing:-.04em;}.uv-canvas .uv-label{letter-spacing:.3em;}',
      'organic-tech':'.uv-overlap .uv-visual{background:var(--bg2);border-radius:58% 42% 62% 38% / 42% 53% 47% 58%;}.uv-card{border:0;border-radius:38px 8px 38px 8px;}.uv-card:nth-child(2){border-radius:8px 38px 8px 38px;}.uv-hero h1{font-weight:500;}',
      'editorial':'.uv-editorial .uv-hero h1{font-size:clamp(48px,7vw,100px);max-width:11ch;}.uv-editorial .uv-visual{display:none;}.uv-editorial .uv-hero{grid-template-columns:1fr;}.uv-editorial .uv-hero-copy{max-width:760px;}.uv-editorial .uv-lede{font-family:var(--font-display);font-size:24px;}',
    }.get(style,'')




def style_context(style):
    a=_vault();d=STYLE_DESIGNS[style];p=a.profile_for(style)
    return dict(style=style,kind=d['kind'],recognition=d['recognition'],profile=f'profiles/{style}.md',layout=d['layout'],
                art=([p['hero_asset']] if p.get('hero_asset') else p['shapes'][:3]),
                preview=f'web/styles/{style}/index.html',tokens=f'css/tokens-{style}.css',
                composition=f'web/effects/{d["layout"]}.css',
                sources=p.get('sources',[]),
                guidance='Select the composition and art as well as the palette. Existing applications keep their established mode.')


def style_gallery(prefix='', fonts='../../fonts/fonts.css', vault='../index.html', research='../../STYLE-RESEARCH.md'):
    a=_vault()
    cards=[]
    for style,d in STYLE_DESIGNS.items():
        p=a.profile_for(style)
        cards.append('<article data-kind="'+html.escape(d['kind'],quote=True)+'" data-search="'+html.escape(style+' '+d['kind']+' '+d['recognition'],quote=True)+'"><header><div><p class="sg-kind">'+html.escape(d['kind'])+'</p><h2>'+html.escape(p['label'])+'</h2></div><a href="'+prefix+style+'/index.html">Open full style ↗</a></header><p class="sg-description">'+html.escape(d['recognition'])+'</p><a class="sg-frame" href="'+prefix+style+'/index.html" aria-label="Open '+html.escape(p['label'],quote=True)+' specimen"><iframe loading="lazy" title="'+html.escape(style,quote=True)+' design specimen" sandbox="allow-scripts allow-same-origin" src="'+prefix+style+'/index.html" tabindex="-1"></iframe></a><footer><code>'+style+'</code> · <code>'+d['layout']+'</code> · '+html.escape(p.get('hero_asset') or ', '.join(p['shapes'][:2]))+'</footer></article>')
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Ultra-PC / Distinct style atlas</title><link rel="stylesheet" href="'+fonts+'"><style>'+a._tokens_css('ultraviolet')+r'''
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.6 var(--font)}a{color:var(--accent2)}.sg-head{padding:36px clamp(20px,4vw,64px);border-bottom:1px solid var(--border)}.sg-head h1{font:600 clamp(32px,4vw,58px)/1.1 var(--font-display);margin:16px 0}.sg-head p{max-width:75ch;color:var(--muted)}.sg-tools{display:flex;flex-wrap:wrap;align-items:center;gap:18px;margin-top:24px}.sg-tools input[type=search],.sg-tools select{font:inherit;background:var(--surface);color:var(--text);border:1px solid var(--border);padding:12px;max-width:100%;border-radius:4px}.sg-tools label{display:flex;align-items:center;gap:8px}.sg-tools input[type=checkbox]{width:20px;height:20px;accent-color:var(--accent)}.sg-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:32px;padding:32px clamp(20px,4vw,64px)}article{border:1px solid var(--border);background:var(--surface);min-width:0;border-radius:8px;overflow:hidden}article header{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:22px 24px 0;min-height:110px}article h2{font:600 25px/1.2 var(--font-display);margin:6px 0}article header a{font-size:13px;white-space:nowrap}.sg-kind{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent2);margin:0}.sg-description{padding:0 24px;color:var(--muted);font-size:14px;min-height:68px}.sg-frame{display:block;position:relative;aspect-ratio:1280/900;overflow:hidden;background:var(--bg)}iframe{position:absolute;left:0;top:0;width:1280px;height:900px;border:0;transform:scale(var(--sg-scale,.45));transform-origin:top left;pointer-events:none}article footer{padding:16px 24px;font-size:12px;color:var(--muted);overflow-wrap:anywhere}.sg-mono iframe{filter:grayscale(1)}[hidden]{display:none!important}.sg-end{padding:0 4vw 50px;color:var(--muted);max-width:90ch}.sg-empty{padding:32px}:focus-visible{outline:3px solid var(--accent);outline-offset:4px}@media(max-width:900px){.sg-grid{grid-template-columns:1fr}article header{align-items:start;flex-direction:column;gap:6px}.sg-description{min-height:0}}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
</style></head><body><header class="sg-head"><a href="'''+vault+'">Modern web playground ↗</a><p>ULTRA-PC / LOCAL DESIGN ATLAS</p><h1>Style is more than a palette.</h1><p>'+str(len(STYLE_DESIGNS))+' directions: '+str(sum(d['kind']=='Visual style' for d in STYLE_DESIGNS.values()))+' visual styles and '+str(sum(d['kind']!='Visual style' for d in STYLE_DESIGNS.values()))+' system or color registers. Compare composition, type, material and imagery. Hide color to see which identities still hold. References come from your local Wikipedia and linked design institutions.</p><div class="sg-tools"><input id="sg-search" type="search" placeholder="Find a style or signature…" aria-label="Find a design style"><select id="sg-kind" aria-label="Filter design directions"><option value="focus">Requested four</option><option value="alternatives">New alternatives</option><option value="all">All directions</option><option>Visual style</option><option>System / color register</option></select><label><input id="sg-mono" type="checkbox">Hide color / inspect structure</label><span id="sg-count" aria-live="polite">27 directions</span></div></header><main class="sg-grid">'+''.join(cards)+'</main><p id="sg-empty" class="sg-empty" hidden>No directions match this filter.</p><footer class="sg-end">The larger illustrations are original local SVG assets. Fashion uses an original fashion plate; replace it with owned campaign photography when appropriate. Historical references are evidence for the interpretation, not artwork copied into the vault. <a href="'+research+'">Research and selection notes ↗</a></footer><script>'+r'''
const cards=[...document.querySelectorAll('main>article')],search=document.getElementById('sg-search'),kind=document.getElementById('sg-kind');function filter(){let n=0;for(const c of cards){c.hidden=!(c.dataset.search.toLowerCase().includes(search.value.toLowerCase())&&(kind.value==='all'||c.dataset.kind===kind.value||(kind.value==='focus'&&['dark-academia','cyberpunk','high-fashion','nordic'].some(k=>c.dataset.search.startsWith(k+' ')))||(kind.value==='alternatives'&&['bauhaus','art-nouveau'].some(k=>c.dataset.search.startsWith(k+' ')))));if(!c.hidden)n++;}document.getElementById('sg-count').textContent=n+' directions';document.getElementById('sg-empty').hidden=!!n;}search.addEventListener('input',filter);kind.addEventListener('change',filter);document.getElementById('sg-mono').addEventListener('change',e=>document.body.classList.toggle('sg-mono',e.target.checked));function resize(){document.querySelectorAll('.sg-frame').forEach(n=>n.style.setProperty('--sg-scale',n.clientWidth/1280));}if('ResizeObserver'in window){const ro=new ResizeObserver(resize);document.querySelectorAll('.sg-frame').forEach(n=>ro.observe(n));}else window.addEventListener('resize',resize);filter();resize();
'''+'</script></body></html>'


def _write_style_previews(root):
    (root/'styles').mkdir(exist_ok=True)
    for style in STYLE_DESIGNS:
        p=style_plan(style);dest=root/'styles'/style;dest.mkdir(exist_ok=True)
        (dest/'index.html').write_text(_document(p['copy']['title'],_compose(p),style,[p['layout']],theme=f'../../themes/{style}.css',fonts='../../../fonts/fonts.css',web='../../'),encoding='utf-8')
        (dest/'context.json').write_text(json.dumps(style_context(style),separators=(',',':')),encoding='utf-8')
    (root/'styles/index.html').write_text(style_gallery(),encoding='utf-8')
    lines=['# Distinct style selection','','Pick a visual language before choosing effects. Color registers are intentionally labelled.','']
    lines += ['- `'+k+'` — '+d['kind']+' / `'+d['layout']+'`: '+d['recognition'] for k,d in STYLE_DESIGNS.items()]
    lines += ['','Use `assets web context style/<id>` for compact paths and selected art IDs. Full evidence: `STYLE-RESEARCH.md` at the vault root.','']
    (root/'STYLE-INDEX.md').write_text('\n'.join(lines),encoding='utf-8')



STYLE_STORIES = {'frutiger-aero': [('A clearer connection.', 'Useful technology, with a little more air.'),
                   ('Room to grow.', 'Living colour and optimistic forms.'),
                   ('A world within reach.', 'Explore with clarity and confidence.')],
 'vaporwave': [('Lost signal.', 'A fragment of another future.'),
               ('Afterimage.', 'Some memories arrive in colour.'),
               ('Endless summer.', 'A synthetic horizon, held in place.')],
 'mono': [('01 / THE INDEX', 'A direct route to what matters.'),
          ('02 / THE CONTENT', 'Read it without distraction.'),
          ('03 / THE SOURCE', 'Show how the thing is made.')],
 'golden-archive': [('The record.', 'An artifact made to cross a great distance.'),
                    ('The signal.', 'A message held in a precise pattern.'),
                    ('The journey.', 'A collection with somewhere to go.')],
 'avant-basic': [('A little offbeat.', 'An object with a different rhythm.'),
                 ('More is more.', 'A colour collision worth keeping.'),
                 ('No straight answer.', 'Let the line take a detour.')],
 'organic-tech': [('Growing connections.', 'A network shaped by living systems.'),
                  ('Useful by nature.', 'Forms that soften the task.'),
                  ('A gentler rhythm.', 'Progress with room to breathe.')],
 'skate-culture': [('THE LATEST DROP', 'Independent graphics. Limited run.'),
                   ('MARK YOUR SPOT', 'Ink, grip and a point of view.'),
                   ('TAKE IT OUTSIDE', 'Made for use. Better with wear.')],
 'mosaic': [('The fragments.', 'Each piece keeps its own character.'),
            ('The pattern.', 'A rhythm built from differences.'),
            ('The whole.', 'Connections visible at every edge.')],
 'art-deco': [('The entrance.', 'A deliberate first impression.'),
              ('The salon.', 'An evening arranged in symmetry.'),
              ('The finishing detail.', 'Gold, geometry and restraint.')],
 'frutiger-metro': [('In full bloom.', 'A programme with room for everyone.'),
                    ('Across the city.', 'Find a new route through familiar places.'),
                    ('A shared rhythm.', 'Culture made visible in public.')],
 'preppy-2000s': [('The campus edit.', 'Everyday essentials, in club colours.'),
                  ('Weekend uniform.', 'A familiar stripe. A favourite layer.'),
                  ('The clubhouse.', 'Meet the people behind the collection.')],
 'y2k-chrome': [('Liquid form.', 'A new outline for a familiar object.'),
                ('Precision finish.', 'Light moves across a seamless surface.'),
                ('Beyond the ordinary.', 'A confident vision of what comes next.')],
 'swiss-international': [('Programme', 'Talks, workshops and public conversations.'),
                         ('Exhibitions', 'Objects and ideas, clearly presented.'),
                         ('Information', 'Times, places and practical details.')],
 'editorial': [('The lead essay.', 'A considered argument, given room.'),
               ('From the field.', 'Observations from outside the desk.'),
               ('The reading list.', 'Ideas to follow after the last page.')],
 'neutral': [('A useful overview.', 'Know what needs your attention.'),
             ('A clearer next step.', 'Keep the action close to the work.'),
             ('Everything in place.', 'Find the detail when you need it.')],
 'hi-contrast': [('Find a task.', 'Clear labels and familiar routes.'),
                 ('Choose an action.', 'Visible focus and generous targets.'),
                 ('Know the result.', 'Explicit states in plain language.')],
 'pastel': [('A morning ritual.', 'A small beginning, taken gently.'),
            ('A little company.', 'Friendly objects with familiar shapes.'),
            ('Time to unwind.', 'Room for a quieter end to the day.')],
 'earthy': [('From the earth.', 'Natural material, worked with care.'),
            ('From the hand.', 'Small differences tell the story.'),
            ('For the everyday.', 'Practical things, made to last.')],
 'jewel': [('The object.', 'A silhouette with quiet presence.'),
           ('The setting.', 'Depth of colour, carefully balanced.'),
           ('The detail.', 'A finish worth a closer look.')],
 'ultraviolet': [('A clearer overview.', 'See the work in a new light.'),
                 ('A precise interaction.', 'A useful response to every action.'),
                 ('Room for what’s next.', 'An adaptable foundation for the product.')],
 'ember': [('The workbench.', 'Keep the tools close to the task.'),
           ('The active project.', 'Build, test and return with clarity.'),
           ('The finished piece.', 'Make room for the work that remains.')],
 'bauhaus': [('Form study', 'Shape, scale and visual balance.'),
             ('Material study', 'Explore the properties of what you use.'),
             ('Construction', 'Bring the parts into a useful whole.')],
 'art-nouveau': [('The botanical plate.', 'Observe a line in the living world.'),
                 ('The continuous frame.', 'Let ornament shape the page.'),
                 ('The printed impression.', 'Colour, paper and an expressive contour.')]}


def _vault():
    from . import assets
    return assets


def compatible(style: str, effect: str) -> list[str]:
    a = _vault()
    if style not in a.STYLES:
        return ['unknown profile: '+style]
    if effect not in ASSETS:
        return ['unknown web asset: '+effect]
    flags = set(ASSETS[effect]['flags'])
    conflicts = flags.intersection(a.EXEC[style]['forbid'])
    if 'motion' in flags and a.EXEC[style]['dur'] == 0:
        conflicts.add('motion')
    return sorted(conflicts)


def compact(key: str) -> dict:
    v = ASSETS[key]
    return dict(id=key, category=v['category'], description=v['description'],
                files={ext:f'web/effects/{key}.{ext}' for ext in ('css','js')},
                markup=f'web/snippets/{key}.html', knobs={k:r['default'] for k,r in v['controls'].items()},
                flags=v['flags'], cost=v['cost'], fallback=v['fallback'])


def plan(name: str, *, style=None, layout=None, effects=None, settings=None, copy=None) -> dict:
    if name not in PACKS:
        raise ValueError('Unknown pack '+name+'. Choose: '+', '.join(PACKS))
    p = PACKS[name]
    style, layout = style or p['style'], layout or p['layout']
    ids = list(dict.fromkeys(effects if effects is not None else p['effects']))
    if layout not in ASSETS or ASSETS[layout]['category'] != 'layout':
        raise ValueError('Choose a layout asset ID.')
    for key in [layout,*ids]:
        if key in ids and ASSETS.get(key,{}).get('category') == 'layout':
            raise ValueError('Layout assets belong in --layout, not --effects.')
        conflict = compatible(style,key)
        if conflict:
            raise ValueError(f'{style} + {key}: incompatible ({", ".join(conflict)}). Choose a compatible asset or profile.')
    result = dict(schema=1, pack=name, style=style, layout=layout,
                  effects={key:{k:r['default'] for k,r in ASSETS[key]['controls'].items()} for key in ids},
                  copy={k:p[k] for k in ('title','eyebrow','description')})
    if copy:
        for key,value in copy.items():
            if key not in result['copy'] or not isinstance(value,str):
                raise ValueError('Copy must contain title, eyebrow or description strings.')
            result['copy'][key] = value
    for key,values in (settings or {}).items():
        if key not in result['effects'] or not isinstance(values,dict):
            raise ValueError('Settings name an unselected effect: '+key)
        for param,value in values.items():
            rule = ASSETS[key]['controls'].get(param)
            if not rule or isinstance(value,bool) or not isinstance(value,(int,float)) or not rule['min'] <= value <= rule['max']:
                raise ValueError(f'Invalid setting {key}.{param}: {value}')
            result['effects'][key][param] = value
    return result


def context(name: str, *, portable: bool = False) -> dict:
    """Cloud-facing metadata: identifiers, file paths, knobs; never source code."""
    if name.startswith('style/'):
        return style_context(name[6:])
    if name in ASSETS:
        return compact(name)
    p = plan(name)
    a = _vault()
    return dict(schema=1,pack=name,copy=p['copy'],style=p['style'],profile=f'profiles/{p["style"]}.md',
                layout=p['layout'],effects=p['effects'],
                art=([a.profile_for(p['style'])['hero_asset']] if a.profile_for(p['style']).get('hero_asset') else a.profile_for(p['style'])['shapes'][:3]),
                local_root="assets-vault" if portable else str(a.ASSETS_DIR),
                assemble=['python3','ultra.py' if portable else str(a.core.ROOT/'ultra.py'),'assets','web','build',name,'./my-site'],
                edit=['index.html','design.json'],
                reuse='Copy or reference the emitted assets. Keep their source outside model context unless changing that asset.')


def _motif(style: str) -> str:
    a = _vault()
    profile = a.profile_for(style)
    return a.SHAPES[profile['shapes'][0]]['svg']


def _js(key):
    v = ASSETS[key]
    return 'UltraWeb.register('+json.dumps(key)+','+json.dumps(v['controls'],separators=(',',':'))+',function(el,o,api){\n'+v['js']+'\n});\n'


# Attach effects to the real composition; more complex interactions become
# complete sections instead of half-wired placeholder attributes.
BINDINGS = {
    'aurora-field':('HERO','uv-aurora','<div class="uv-aurora-lights" aria-hidden="true"><i></i><i></i><i></i></div>'),
    'shader-flow':('HERO','uv-shader','<canvas aria-hidden="true"></canvas>'),
    'prism-border':('ART','uv-prism',''),
    'gradient-type':('TITLE','uv-gradient-type',''),
    'split-lines':('TITLE','uv-lines',''),
    'magnetic-button':('CTA','uv-magnetic',''),
    'tilt-card':('ART','uv-tilt',''),
    'iridescent-surface':('ART','uv-foil',''),
    'reveal-stagger':('GRID','',''),
    'spotlight-grid':('GRID','uv-spot-grid',''),
    'glass-panel':('CARD','',''),
    'acrylic-card':('CARD','uv-acrylic',''),
    'glass-dock':('NAV','uv-dock',''),
    'noise-film':('HERO','uv-film',''),
    'blend-spotlights':('HERO','uv-blend',''),
}


def _compose(p):
    slots = {s:dict(classes=[],effects=[],layers=[]) for s in ('HERO','ART','TITLE','CTA','GRID','CARD','NAV')}
    extras = []
    for key in p['effects']:
        if key in BINDINGS:
            slot,cls,layer = BINDINGS[key]
            slots[slot]['effects'].append(key)
            if cls: slots[slot]['classes'].append(cls)
            if layer: slots[slot]['layers'].append(layer)
        elif key == 'scroll-depth':
            slots['HERO']['effects'].append(key)
            slots['ART']['classes'].append('uv-depth')
        elif key == 'scroll-progress':
            slots['HERO']['effects'].append(key)
            slots['HERO']['layers'].append('<div class="uv-progress" aria-hidden="true"></div>')
        else:
            extra=ASSETS[key]['html']
            # Each separately mounted section owns the matching settings.
            cfg=html.escape(json.dumps(p['effects'][key],separators=(',',':')),quote=True)
            extra=extra.replace(f'data-uv="{key}"',f'data-uv="{key}" data-uv-config="{cfg}"')
            extras.append('<section class="uv-section uv-shell">'+extra+'</section>')
    nav='''<div class="uv-shell"><nav class="uv-nav __NAV_CLASS__" __NAV_ATTRS__ aria-label="Main navigation"><a class="uv-brand" href="#story">ULTRA / COLLECTION</a><div class="uv-nav-links"><a href="#collection">Collection</a><a href="#details">Details</a></div></nav></div>'''
    body=nav+ASSETS[p['layout']]['html']+''.join(extras)+'<footer class="uv-foot uv-shell">Made locally. Designed with intention.</footer>'
    for slot,values in slots.items():
        body=body.replace('__'+slot+'_CLASS__',' '.join(values['classes']))
        attrs=[]
        if values['effects']:
            attrs.append('data-uv="'+' '.join(values['effects'])+'"')
            merged={}
            for effect in values['effects']: merged.update(p['effects'][effect])
            attrs.append('data-uv-config="'+html.escape(json.dumps(merged,separators=(',',':')),quote=True)+'"')
        if set(values['effects']).intersection(('glass-panel','glass-dock','acrylic-card')):
            attrs.append('data-uv-glass')
        body=body.replace('__'+slot+'_ATTRS__',' '.join(attrs))
        body=body.replace('__'+slot+'_LAYERS__',''.join(values['layers']))
    for key,value in p['copy'].items(): body=body.replace('__'+key.upper()+'__',html.escape(value))
    if p['layout']=='signal-console':
        marker='</a></div></div><figure'
        telemetry='<div class="uv-inline-status"><span>INTEGRITY<strong>98.4%</strong></span><span>NODES<strong>024</strong></span><span>LATENCY<strong>12ms</strong></span></div>'
        body=body.replace(marker,'</a></div>'+telemetry+'</div><figure',1)
    body=body.replace('__HERO_ART__',_hero_artwork(p['style']))
    body=body.replace('__MOTIF__',_motif(p['style']))
    identity=STYLE_DESIGNS[p['style']]
    for title,description in STYLE_STORIES.get(p['style'],[]):
        body=body.replace('<h3>Designed to move.</h3><p>Local assets. Your identity.</p>','<h3>'+html.escape(title)+'</h3><p>'+html.escape(description)+'</p>',1)
    body=body.replace('Built from the vault',html.escape(identity['brand']))
    body=body.replace('A language of your own.',{'bauhaus':'Three practical studies.','art-nouveau':'The exhibition.','swiss-international':'Programme and information.'}.get(p['style'],'Selected work.'))
    details={
      'dark-academia':('Keep a commonplace book.','Record an observation. Follow a reference. Return to a thought when the room is quiet.'),
      'cyberpunk':('Own your connection.','Read the signal. Choose the channel. Keep the network in your hands.'),
      'high-fashion':('An exercise in restraint.','One silhouette. A precise proportion. Only what the final edit requires.'),
      'nordic':('Made for everyday use.','Good objects are easy to live with. Comfortable proportions, honest materials and details that do their work quietly.'),
      'bauhaus':('Learn by making.','Study the material, test the construction and let the useful form emerge.'),
      'art-nouveau':('A line through every art.','From botanical observation to printed page, the contour connects the image, the lettering and the frame.'),
    }.get(p['style'],(identity['title'],identity['description']))
    body=body.replace('Built here. Ready for anywhere.',html.escape(details[0]))
    body=body.replace('A local library of motion, material and composition. The code stays close. Your ideas travel further.',html.escape(details[1]))
    body=body.replace('Made locally. Designed with intention.',html.escape(identity['brand']+' / '+identity['plate']))

    for key,value in dict(ACTION=identity['action'],PLATE=identity['plate']).items():body=body.replace('__'+key+'__',html.escape(value))
    body=body.replace('ULTRA / COLLECTION',html.escape(identity['brand']))
    nav_labels={'dark-academia':('Catalogue','Notes'),'cyberpunk':('Channels','System'),'high-fashion':('Collection','Maison'),'nordic':('Objects','Materials')}
    if p['style'] in nav_labels:
        left,right=nav_labels[p['style']]
        body=body.replace('>Collection</a>','>'+left+'</a>').replace('>Details</a>','>'+right+'</a>')
    if 'split-lines' in p['effects']:
        title=html.escape(p['copy']['title'])
        body=body.replace('>'+title+'</h1>','><span><em>'+title+'</em></span></h1>')
    if re.search(r'__[A-Z_]+__',body):
        raise ValueError('Unresolved assembly slot.')
    return body


def _document(title, body, style, ids, *, theme, fonts, web, note=''):
    css=''.join(f'<link rel="stylesheet" href="{web}effects/{key}.css">' for key in ids if ASSETS[key]['css'])
    scripts=f'<script defer src="{web}runtime.js"></script>'+''.join(f'<script defer src="{web}effects/{key}.js"></script>' for key in ids)
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html.escape(title)}</title><link rel="stylesheet" href="{fonts}">'
            f'<link rel="stylesheet" href="{theme}"><link rel="stylesheet" href="{web}core.css">'+css+scripts+
            '</head><body data-uv-profile="'+html.escape(style,quote=True)+'"'+(' data-uv-mode="daylight"' if style=='nordic' and 'nordic-catalog' in ids else '')+'>'+body+note+'</body></html>')


def _brief(p):
    return f'''# Local design brief

Use the Ultra-PC `{p['style']}` profile and `{p['layout']}` layout.
Selected effects: {', '.join(p['effects'])}.

The site is already assembled. Edit the words, links, and content in `index.html`.
Reuse the CSS/JS files under `assets/web/`; do not regenerate those effects or
paste their full source into model context. `design.json` records IDs and knob
values. To change motion or material, use the selected asset's documented knobs.
Preserve the project's identity and the profile's constraints.

Fonts and licenses are local. No package install, CDN, API call, or bundler is
needed to run this output. Use `assets/web/manifest.json` to discover additional
local modules; read only the files needed for a real code change. Module controls
are set in `data-uv-config`. Motion honors the reader's preferences; use
`UltraWeb.setMotion(true)` to pause it. Add `data-uv-solid` on `<html>` for opaque
surfaces. User content must remain readable with either preference.
'''


def build(name, destination, *, style=None, layout=None, effects=None, settings=None, copy=None, prepared=None):
    a=_vault()
    p=prepared or plan(name,style=style,layout=layout,effects=effects,settings=settings,copy=copy)
    # Revalidate caller-supplied plans rather than trusting a config file.
    p=plan(p['pack'],style=p['style'],layout=p['layout'],effects=list(p['effects']),settings=p['effects'],copy=p['copy'])
    out=Path(destination).expanduser()
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError('Destination must be empty; existing work is never overwritten: '+str(out))
    css,kit=a._kit_css(p['style'])
    body=_compose(p)  # Validate everything before creating output files.
    ids=[p['layout'],*p['effects']]
    profile=a.profile_for(p['style'])
    missing=[f for f in profile['fonts']['files'] if not (a.FONT_DIR/f).exists()]
    if missing: raise ValueError('Restore local fonts first: '+', '.join(missing))
    slugs={f.rsplit('-',1)[0] for f in profile['fonts']['files']}
    missing_licenses=[s for s in slugs if not (a.ASSETS_DIR/'licenses'/('fontsource-'+s)).is_dir()]
    if missing_licenses: raise ValueError('Restore local font licenses first: '+', '.join(missing_licenses))
    (out/'assets/web/effects').mkdir(parents=True)
    (out/'assets/theme.css').write_text(css+'\n'+_identity_css(p['style']),encoding='utf-8')
    (out/'assets/web/core.css').write_text(CORE_CSS,encoding='utf-8')
    (out/'assets/web/runtime.js').write_text(RUNTIME_JS,encoding='utf-8')
    for key in ids:
        (out/f'assets/web/effects/{key}.css').write_text(ASSETS[key]['css']+'\n',encoding='utf-8')
        (out/f'assets/web/effects/{key}.js').write_text(_js(key),encoding='utf-8')
    fonts=out/'fonts';fonts.mkdir()
    blocks=[]
    for file in a.profile_for(p['style'])['fonts']['files']:
        shutil.copy2(a.FONT_DIR/file,fonts/file)
        family,weight,_=a.FONT_MAP[file.removesuffix('.woff2')]
        blocks.append("@font-face{font-family:'"+family+"';font-weight:"+str(weight)+";font-style:normal;font-display:swap;src:url('./"+file+"') format('woff2');}")
    (fonts/'fonts.css').write_text('\n'.join(blocks),encoding='utf-8')
    # Keep the font license alongside every portable copy.
    for slug in slugs:
        source=a.ASSETS_DIR/'licenses'/('fontsource-'+slug)
        shutil.copytree(source,out/'licenses'/source.name)
    (out/'index.html').write_text(_document(p['copy']['title'],body,p['style'],ids,
        theme='assets/theme.css',fonts='fonts/fonts.css',web='assets/web/'),encoding='utf-8')
    (out/'design.json').write_text(json.dumps(p,indent=2)+'\n',encoding='utf-8')
    (out/'AI-BRIEF.md').write_text(_brief(p),encoding='utf-8')
    portable=[]
    for key in ids:
        item=compact(key)
        item['files']={ext:f'assets/web/effects/{key}.{ext}' for ext in ('css','js')}
        item['markup']='index.html'  # The selected modules are already composed here.
        portable.append(item)
    (out/'assets/web/manifest.json').write_text(json.dumps(portable,separators=(',',':')),encoding='utf-8')
    return p


def audit():
    a=_vault();issues=[]
    for name in PACKS:
        try:plan(name)
        except ValueError as exc:issues.append(('FAIL','web pack',str(exc)))
    for key,v in ASSETS.items():
        if not v['css'] and not v['js']:
            issues.append(('FAIL','web asset',key+' has no implementation'))
        if not v['html']:issues.append(('FAIL','web asset',key+' has no markup'))
        if 'fetch(' in v['js'] or re.search(r'(?:src|href)=["\']https?://',v['html']):
            issues.append(('FAIL','offline web asset',key+' requires a remote resource'))
        for param,rule in v['controls'].items():
            if not rule['min']<=rule['default']<=rule['max']:
                issues.append(('FAIL','web control',key+'.'+param))
    web=a.ASSETS_DIR/'web'
    for path in ('index.html','core.css','runtime.js','manifest.json','MODEL-INDEX.md'):
        if not (web/path).exists():issues.append(('FAIL','web vault','missing '+path))
    return issues


def sync():
    """Generate the library, live demos, presets and compact model index."""
    a=_vault();root=a.ASSETS_DIR/'web'
    for folder in ('effects','snippets','recipes','demos','themes','presets'):
        (root/folder).mkdir(parents=True,exist_ok=True)
    (root/'core.css').write_text(CORE_CSS,encoding='utf-8')
    (root/'runtime.js').write_text(RUNTIME_JS,encoding='utf-8')
    for style in a.STYLES:
        (root/f'themes/{style}.css').write_text(a._kit_css(style)[0]+'\n'+_identity_css(style),encoding='utf-8')
    inventory=[]
    for key,v in ASSETS.items():
        record=compact(key)
        record['controls']=v['controls'];record['sources']=v['sources']
        record['bytes']=len((v['css']+_js(key)+v['html']).encode())
        inventory.append(record)
        (root/f'effects/{key}.css').write_text(v['css']+'\n',encoding='utf-8')
        (root/f'effects/{key}.js').write_text(_js(key),encoding='utf-8')
        if v['category']=='layout':
            example=plan('luminous-product',style=v['style'],layout=key,effects=[])
            snippet=_compose(example)
        else:snippet=v['html'].replace('__MOTIF__',_motif(v['style']))
        (root/f'snippets/{key}.html').write_text(snippet,encoding='utf-8')
        demo=root/f'demos/{key}';demo.mkdir(exist_ok=True)
        body=('<main class="uv-demo"><p class="uv-label" id="story">ULTRA-PC / '+v['category'].upper()+'</p>'
              '<h1>'+html.escape(key.replace('-',' '))+'</h1><div class="uv-demo-stage" id="collection">'+snippet+'</div>'
              '<p class="uv-demo-note" id="details">'+html.escape(v['description'])+' '+html.escape(v['fallback'])+'</p></main>')
        (demo/'index.html').write_text(_document(key,body,v['style'],[key],theme=f'../../themes/{v["style"]}.css',
           fonts='../../../fonts/fonts.css',web='../../'),encoding='utf-8')
        usage=f'''# {key}

{v['description']}

Category: {v['category']} · Cost: {v['cost']} · Default profile: {v['style']}
Flags: {', '.join(v['flags']) or 'none'}

Load `web/core.css`, `web/runtime.js`, and `web/effects/{key}.css` / `.js`.
Use `web/snippets/{key}.html` as the markup. Preview: `web/demos/{key}/index.html`.
All visual tokens come from the chosen vault profile. `data-uv-config` accepts:

```json
{json.dumps({k:r['default'] for k,r in v['controls'].items()},indent=2)}
```

Bounds: {json.dumps(v['controls'],separators=(',',':'))}
Fallback: {v['fallback']}
The runtime mounts once per element, cleans listeners/observers on unmount, and
pauses continuous JS work off screen or when the page is hidden. Reduced motion
keeps content visible. Read this recipe only when tuning the asset; use its ID
and file paths in cloud prompts.
'''
        if v['sources']:usage+='\nImplementation references: '+', '.join(v['sources'])+'\n'
        (root/f'recipes/{key}.md').write_text(usage,encoding='utf-8')
    # Rebuild only generated preset directories. User work is exported elsewhere.
    for name in PACKS:
        dest=root/'presets'/name
        if dest.exists():
            import tempfile
            with tempfile.TemporaryDirectory(prefix='ultra-web-') as temporary:
                draft=Path(temporary)/name
                build(name,draft)
                shutil.copytree(draft,dest,dirs_exist_ok=True)
        else:
            build(name,dest)
    manifest=dict(schema=1,assets=inventory,packs={k:{field:v[field] for field in ('style','layout','effects')} for k,v in PACKS.items()})
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    index=['# Compact web asset index','',
           'Start with `web/STYLE-INDEX.md` when choosing a visual language. Pick IDs; assemble locally.','',
           '`ultra assets web packs` · `ultra assets web search glass` · `ultra assets web context luminous-product`',
           '`ultra assets web build luminous-product ./site`','',
           '| ID | Category | What it does |','|---|---|---|']
    index += [f'| {k} | {v["category"]} | {v["description"]} |' for k,v in ASSETS.items()]
    index += ['','## Complete page packs','']+[f'- `{k}`: {v["style"]} / {v["layout"]}' for k,v in PACKS.items()]
    index += ['','The context command returns IDs, paths, parameters and an assembly command. It does not include source code.',
              'A model needs filesystem tools or the exported folder to use local files; pasting full code into a chat loses that benefit.']
    (root/'MODEL-INDEX.md').write_text('\n'.join(index)+'\n',encoding='utf-8')
    _write_style_previews(root)
    _gallery(root,manifest)
    return dict(assets=len(ASSETS),packs=len(PACKS),categories=sorted({v['category'] for v in ASSETS.values()}),
                index='web/MODEL-INDEX.md',gallery='web/index.html')


def _gallery(root,manifest):
    a=_vault()
    data=dict(assets=[{**compact(k),'controls':v['controls'],'style':v['style']} for k,v in ASSETS.items()],
              packs=[dict(id=k,**v,context=context(k,portable=True)) for k,v in PACKS.items()])
    payload=json.dumps(data,separators=(',',':')).replace('<','\\u003c')
    css=r'''
body{margin:0} .wb-top{padding:22px 28px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;gap:24px;}
.wb-logo{font:var(--weight-strong) 22px var(--font-display);letter-spacing:-.02em}.wb-logo small{font:12px var(--mono);color:var(--muted);display:block;margin-top:6px;letter-spacing:.14em;}
.wb-top>a{color:var(--accent);text-decoration:none;font-size:14px}.wb-shell{display:grid;grid-template-columns:260px minmax(0,1fr);min-height:calc(100svh - 93px)}
.wb-side{padding:24px 18px;border-right:1px solid var(--border);position:sticky;top:0;height:100svh;overflow:auto;}
.wb-side input{width:100%;padding:12px;color:var(--text);background:var(--surface);border:1px solid var(--border);border-radius:8px;margin-bottom:18px;}
.wb-modes{display:flex;gap:8px;margin-bottom:16px}.wb-modes button{flex:1}.wb-side button,.wb-toolbar button,.wb-copy{font:inherit;color:var(--muted);background:transparent;border:1px solid var(--border);padding:10px 12px;border-radius:8px;cursor:pointer;}
.wb-side button[aria-pressed=true],.wb-toolbar button[aria-pressed=true]{background:var(--accent);color:var(--on-accent);border-color:var(--accent);}
.wb-cats{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:22px}.wb-cats button{font-size:11px;padding:7px 9px;text-transform:uppercase;letter-spacing:.04em;}
.wb-list button{display:block;width:100%;text-align:left;padding:13px 10px;margin-bottom:5px;border-color:transparent;font-size:13px}.wb-list button small{display:block;font-size:10px;color:var(--muted);margin-top:3px;text-transform:uppercase;letter-spacing:.06em;}
.wb-list button[aria-current=true]{border-color:var(--accent);color:var(--text);background:var(--surface)}
.wb-main{padding:30px;min-width:0}.wb-intro{display:flex;justify-content:space-between;gap:24px;align-items:end;margin-bottom:24px}.wb-intro h1{font:var(--weight-strong) clamp(28px,3vw,44px)/1.1 var(--font-display);letter-spacing:-.035em;margin:9px 0;}
.wb-intro p{color:var(--muted);font-size:14px;max-width:65ch}.wb-count{font:12px var(--mono);color:var(--accent);white-space:nowrap;padding-bottom:8px;}
.wb-toolbar{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:14px}.wb-toolbar div{display:flex;gap:8px;align-items:center}.wb-toolbar button{font-size:12px;}
.wb-toolbar a{color:var(--accent);font-size:13px;text-decoration:none}.wb-preview{width:100%;height:650px;border:1px solid var(--border);border-radius:12px;background:var(--bg2);display:block;}
.wb-controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:20px;padding:22px 0;border-bottom:1px solid var(--border)}
.wb-controls label{display:block;font-size:12px;color:var(--muted)}.wb-controls input{display:block;width:100%;accent-color:var(--accent);margin-top:10px}.wb-controls output{float:right;color:var(--text)}
.wb-controls select{width:100%;padding:8px;background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:6px;margin-top:6px;}
.wb-info{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-top:24px}.wb-info h2{font-size:16px;margin-bottom:12px}.wb-info p{font-size:13px;color:var(--muted);line-height:1.7}.wb-info pre{font:12px/1.6 var(--mono);white-space:pre-wrap;overflow-wrap:anywhere;padding:20px;background:var(--surface);border:1px solid var(--border);border-radius:8px;max-height:240px;overflow:auto;}
.wb-stats{font-size:12px;color:var(--accent);margin-bottom:10px}.wb-copy{font-size:12px;margin-top:10px}.wb-empty{font-size:13px;color:var(--muted);padding:20px 4px}
@media(max-width:900px){.wb-shell{grid-template-columns:1fr}.wb-side{position:static;height:auto;border-right:0;border-bottom:1px solid var(--border)}.wb-list{max-height:180px;overflow:auto}.wb-list button{display:inline-block;width:220px}.wb-main{padding:20px}.wb-preview{height:610px}.wb-info{grid-template-columns:1fr}.wb-count{display:none}}
'''
    markup='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Ultra-PC · Modern Web Vault</title><link rel="stylesheet" href="../fonts/fonts.css"><link rel="stylesheet" href="themes/ultraviolet.css"><link rel="stylesheet" href="core.css"><style>'''+css+'''</style></head><body>
<header class="wb-top"><div class="wb-logo">Ultra-PC / Web Vault<small>LOCAL MATERIALS FOR EXCEPTIONAL WEBSITES</small></div><a href="styles/index.html">Compare distinct styles ↗</a><a href="../demo.html">Full design vault ↗</a></header>
<div class="wb-shell"><aside class="wb-side"><input id="wb-search" type="search" placeholder="Find an effect or layout…" aria-label="Search local web assets"><div class="wb-modes"><button id="wb-pages" aria-pressed="true">Complete pages</button><button id="wb-assets" aria-pressed="false">Assets</button></div><div class="wb-cats" id="wb-categories"></div><nav class="wb-list" id="wb-list" aria-label="Local asset collection"></nav></aside>
<main class="wb-main"><div class="wb-intro"><div><p class="uv-label">MOTION / COLOR / MATERIAL / COMPOSITION</p><h1 id="wb-title">Luminous product</h1><p id="wb-description"></p></div><span class="wb-count">{len(ASSETS)} ASSETS · {len(PACKS)} PAGE PACKS</span></div>
<div class="wb-toolbar"><div><button id="wb-motion" aria-pressed="false">Pause motion</button><button id="wb-solid" aria-pressed="false">Solid surfaces</button></div><a id="wb-open" href="presets/luminous-product/index.html" target="_blank" rel="noopener">Open full preview ↗</a></div>
<iframe class="wb-preview" id="wb-preview" title="Live local web asset preview" src="presets/luminous-product/index.html"></iframe>
<div class="wb-controls" id="wb-controls"></div><div class="wb-info"><section><h2>Pick it. Tune it. Keep the code local.</h2><p id="wb-fallback"></p><p>Copy a compact brief for your cloud model. It names the profile, layout, effects and assembly command. The implementation stays in these local files.</p><p id="wb-files"></p></section><section><h2>Model context</h2><div class="wb-stats" id="wb-stats"></div><pre id="wb-context"></pre><button class="wb-copy" id="wb-copy">Copy compact brief</button><p id="wb-copy-status" aria-live="polite"></p></section></div></main></div>
<script id="wb-data" type="application/json">'''+payload+r'''</script><script>
(function(){'use strict';const data=JSON.parse(document.getElementById('wb-data').textContent),byId=new Map(data.assets.map(a=>[a.id,a]));let mode='pages',category='all',current='luminous-product',paused=false,solid=false,tune='',brief='',edits={};const $=id=>document.getElementById('wb-'+id),frame=$('preview');
function list(){const q=$('search').value.toLowerCase(),items=mode==='pages'?data.packs:data.assets;const filtered=items.filter(v=>(category==='all'||v.category===category)&&(v.id+' '+(v.description||'')+' '+(v.category||'')+' '+(v.flags||[]).join(' ')).includes(q));$('list').replaceChildren();for(const item of filtered){const b=document.createElement('button');b.textContent=item.id;b.setAttribute('aria-current',String(item.id===current));const small=document.createElement('small');small.textContent=mode==='pages'?item.style+' / '+item.layout:item.category+' / '+item.cost;b.append(small);b.addEventListener('click',()=>select(item.id));$('list').append(b);}if(!filtered.length){const p=document.createElement('p');p.className='wb-empty';p.textContent='No local assets match this search.';$('list').append(p);}}
function categories(){const holder=$('categories');holder.replaceChildren();if(mode==='pages')return;for(const id of ['all','motion','color','transparency','layout','interaction']){const b=document.createElement('button');b.textContent=id;b.setAttribute('aria-pressed',String(category===id));b.addEventListener('click',()=>{category=id;categories();list();});holder.append(b);}}
function controls(){const holder=$('controls');holder.replaceChildren();let asset=byId.get(current);if(mode==='pages'){const pack=data.packs.find(p=>p.id===current),label=document.createElement('label'),sel=document.createElement('select');label.textContent='Tune an effect';label.append(sel);for(const id of pack.effects){const option=document.createElement('option');option.value=id;option.textContent=id;sel.append(option);}if(!pack.effects.includes(tune))tune=pack.effects[0];sel.value=tune;sel.setAttribute('aria-label','Tune an effect');sel.addEventListener('change',()=>{tune=sel.value;controls();});holder.append(label);asset=byId.get(tune);}if(!asset)return;
for(const [key,rule]of Object.entries(asset.controls)){const label=document.createElement('label'),out=document.createElement('output'),input=document.createElement('input');label.textContent=key;out.textContent=rule.default+rule.unit;label.append(out);input.type='range';input.min=rule.min;input.max=rule.max;input.step=(rule.max-rule.min)>10?1:.01;input.value=edits[asset.id]?.[key]??rule.default;out.textContent=input.value+rule.unit;input.setAttribute('aria-label',asset.id+' '+key);input.addEventListener('input',()=>{out.textContent=input.value+rule.unit;edits[asset.id]??={};edits[asset.id][key]=Number(input.value);refreshBrief();const doc=frame.contentDocument;if(!doc?.defaultView.UltraWeb)return;for(const root of doc.querySelectorAll('[data-uv]'))if(root.dataset.uv.split(/\s+/).includes(asset.id)){let cfg={};try{cfg=JSON.parse(root.dataset.uvConfig||'{}');}catch(_){}cfg[key]=Number(input.value);root.dataset.uvConfig=JSON.stringify(cfg);}doc.defaultView.UltraWeb.unmount();doc.defaultView.UltraWeb.mount();if(paused)doc.defaultView.UltraWeb.setMotion(true);});label.append(input);holder.append(label);}}
function refreshBrief(){const item=mode==='pages'?data.packs.find(v=>v.id===current):byId.get(current);const ctx=mode==='pages'?JSON.parse(JSON.stringify(item.context)):{id:item.id,profile:'profiles/'+item.style+'.md',files:item.files,markup:item.markup,knobs:{...item.knobs}};if(mode==='pages'){for(const[id,values]of Object.entries(edits))if(ctx.effects[id])Object.assign(ctx.effects[id],values);}else Object.assign(ctx.knobs,edits[item.id]||{});brief=JSON.stringify(ctx,null,2);$('context').textContent=brief;const bytes=new TextEncoder().encode(brief).length;const ids=mode==='pages'?[item.layout,...item.effects]:[item.id];const sourceBytes=ids.reduce((sum,id)=>sum+byId.get(id).bytes,0);$('stats').textContent='Brief: '+(bytes/1024).toFixed(1)+' KB · module implementation: '+(sourceBytes/1024).toFixed(1)+' KB kept local';}
function select(id){if(current!==id)edits={};current=id;const item=mode==='pages'?data.packs.find(v=>v.id===id):byId.get(id);$('title').textContent=id.replaceAll('-',' ');$('description').textContent=item.description;const path=mode==='pages'?'presets/'+id+'/index.html':'demos/'+id+'/index.html';frame.src=path;$('open').href=path;const ctx=mode==='pages'?item.context:{id:item.id,profile:'profiles/'+item.style+'.md',files:item.files,markup:item.markup,knobs:item.knobs};brief=JSON.stringify(ctx,null,2);$('context').textContent=brief;const contextBytes=new TextEncoder().encode(brief).length;const assetIds=mode==='pages'?[item.layout,...item.effects]:[id];const bytes=assetIds.reduce((sum,id)=>sum+byId.get(id).bytes,0);$('stats').textContent='Brief: '+(contextBytes/1024).toFixed(1)+' KB · module implementation: '+(bytes/1024).toFixed(1)+' KB kept local';$('fallback').textContent=mode==='pages'?'A complete, responsive page from the '+item.style+' profile. Effects are selected together and checked against the profile.':item.fallback;$('files').textContent=mode==='pages'?'Build locally: ultra assets web build '+id+' ./my-site':'Files: '+Object.values(item.files).join(' · ');refreshBrief();controls();list();}
frame.addEventListener('load',()=>{const doc=frame.contentDocument;if(!doc)return;doc.documentElement.toggleAttribute('data-uv-solid',solid);doc.defaultView.UltraWeb?.setMotion(paused);});$('motion').addEventListener('click',()=>{paused=!paused;$('motion').setAttribute('aria-pressed',String(paused));$('motion').textContent=paused?'Resume motion':'Pause motion';frame.contentWindow.UltraWeb?.setMotion(paused);});$('solid').addEventListener('click',()=>{solid=!solid;$('solid').setAttribute('aria-pressed',String(solid));frame.contentDocument?.documentElement.toggleAttribute('data-uv-solid',solid);});
for(const name of ['pages','assets'])$(name).addEventListener('click',()=>{mode=name;category='all';$('pages').setAttribute('aria-pressed',String(mode==='pages'));$('assets').setAttribute('aria-pressed',String(mode==='assets'));current=mode==='pages'?'luminous-product':'aurora-field';categories();select(current);});$('search').addEventListener('input',list);$('copy').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(brief);$('copy-status').textContent='Compact brief copied.';}catch(_){$('copy-status').textContent='Select and copy the brief above.';}});categories();select(current);
})();</script></body></html>'''
    # Include byte counts without embedding implementation code into the brief.
    sizes={r['id']:r['bytes'] for r in manifest['assets']}
    data['assets']=[dict(v,bytes=sizes[v['id']]) for v in data['assets']]
    new_payload=json.dumps(data,separators=(',',':')).replace('<','\\u003c')
    markup=markup.replace(payload,new_payload)
    markup=markup.replace('{len(ASSETS)}',str(len(ASSETS))).replace('{len(PACKS)}',str(len(PACKS)))
    (root/'index.html').write_text(markup,encoding='utf-8')


def handle(argv):
    parser=argparse.ArgumentParser(prog='ultra assets web',description='Local motion, color, transparency, layouts and interactions; no model or CDN required.')
    commands=parser.add_subparsers(dest='command')
    listing=commands.add_parser('list');listing.add_argument('category',nargs='?');listing.add_argument('--style');listing.add_argument('--json',action='store_true')
    searching=commands.add_parser('search');searching.add_argument('query');searching.add_argument('--style');searching.add_argument('--limit',type=int,default=8);searching.add_argument('--json',action='store_true')
    commands.add_parser('packs')
    styles=commands.add_parser('styles');styles.add_argument('--json',action='store_true')
    ctx=commands.add_parser('context');ctx.add_argument('id')
    show=commands.add_parser('show');show.add_argument('id');show.add_argument('--code',choices=['html','css','js'])
    building=commands.add_parser('build');building.add_argument('pack');building.add_argument('destination');building.add_argument('--style');building.add_argument('--layout');building.add_argument('--effects');building.add_argument('--config',type=Path);building.add_argument('--zip',action='store_true')
    commands.add_parser('check');commands.add_parser('gallery')
    try:args=parser.parse_args(argv)
    except SystemExit as exc:return int(exc.code)
    try:
        if args.command in ('list','search'):
            keys=list(ASSETS)
            if args.command=='list' and args.category:keys=[k for k in keys if ASSETS[k]['category']==args.category]
            if args.style:keys=[k for k in keys if not compatible(args.style,k)]
            if args.command=='search':
                words=set(re.findall(r'[a-z0-9]+',args.query.lower()))
                def rank(key):
                    v=ASSETS[key];text=(key+' '+v['category']+' '+v['description']+' '+' '.join(v['flags'])).lower()
                    return sum(3 if word in key else 1 for word in words if word in text)
                keys=sorted((k for k in keys if rank(k)),key=lambda k:-rank(k))[:max(1,args.limit)]
            if args.json:print(json.dumps([compact(k) for k in keys],separators=(',',':')))
            else:
                for key in keys:print(f'{key:24} {ASSETS[key]["category"]:13} {ASSETS[key]["description"]}')
                print(f'{len(keys)} local assets. Use context <id> for paths and knobs; show <id> --code css only when editing code.')
            return 0
        if args.command=='styles':
            if args.json:print(json.dumps([style_context(k) for k in STYLE_DESIGNS],separators=(',',':')))
            else:
                for key,d in STYLE_DESIGNS.items():print(f'{key:23} {d["kind"]:25} {d["recognition"]}')
            return 0
        if args.command=='packs':
            for key,v in PACKS.items():print(f'{key:24} {v["style"]:20} {v["layout"]:20} {len(v["effects"])} effects')
            return 0
        if args.command in ('context','show'):
            if getattr(args,'code',None):
                if args.id not in ASSETS:raise ValueError('Choose an asset ID for --code.')
                print(_js(args.id) if args.code=='js' else ASSETS[args.id][args.code])
            else:print(json.dumps(context(args.id),separators=(',',':')))
            return 0
        if args.command=='build':
            prepared=None
            if args.config:prepared=json.loads(args.config.read_text(encoding='utf-8'))
            p=build(args.pack,args.destination,style=args.style,layout=args.layout,effects=args.effects.split(',') if args.effects else None,prepared=prepared)
            if args.zip:
                archive=Path(args.destination).expanduser().resolve()
                if Path(str(archive)+'.zip').exists():raise ValueError('ZIP already exists; exported folder was kept.')
                shutil.make_archive(str(archive),'zip',archive)
            print(json.dumps(dict(output=str(Path(args.destination).expanduser().resolve()),profile=p['style'],layout=p['layout'],effects=list(p['effects']),brief='AI-BRIEF.md'),separators=(',',':')))
            return 0
        if args.command=='check':
            issues=audit()
            for level,rule,detail in issues:print(f'{level} {rule}: {detail}')
            print(f'{len(ASSETS)} web assets · {len(PACKS)} packs · {len(issues)} issues')
            return int(bool(issues))
        if args.command=='gallery':
            path=_vault().ASSETS_DIR/'web/index.html'
            print(path);_vault().core.open_in_os(path);return 0
        parser.print_help();return 0
    except (ValueError,KeyError,OSError,TypeError) as exc:
        print('Web assets: '+str(exc));return 2
