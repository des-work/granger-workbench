UltraWeb.register("scrollspy",{},function(el,o,api){
if(!('IntersectionObserver'in window))return;const links=[...el.querySelectorAll('nav a')],sections=links.map(a=>document.getElementById(a.hash.slice(1))).filter(Boolean),visible=new Map();const io=new IntersectionObserver(es=>{es.forEach(e=>visible.set(e.target,e.intersectionRatio));const current=[...visible].sort((a,b)=>b[1]-a[1])[0];if(current&&current[1]>0)links.forEach(a=>a.setAttribute('aria-current',String(a.hash==='#'+current[0].id)));},{threshold:[0,.2,.5,.8]});sections.forEach(s=>io.observe(s));return()=>io.disconnect();
});
