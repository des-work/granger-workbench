UltraWeb.register("spotlight-grid",{},function(el,o,api){
if(!api.motion||!matchMedia('(pointer:fine)').matches)return;const cards=[...el.querySelectorAll('.uv-card')];api.listen(el,'pointermove',api.frame(e=>cards.forEach(n=>{const r=n.getBoundingClientRect();n.style.setProperty('--uv-spot-x',(e.clientX-r.left)+'px');n.style.setProperty('--uv-spot-y',(e.clientY-r.top)+'px');n.style.setProperty('--uv-spot-opacity','1');})));const reset=()=>cards.forEach(n=>n.style.removeProperty('--uv-spot-opacity'));api.listen(el,'pointerleave',reset);return reset;
});
