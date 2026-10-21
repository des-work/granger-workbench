
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
