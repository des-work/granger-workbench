UltraWeb.register("iridescent-surface",{},function(el,o,api){
if(!api.motion||!matchMedia('(pointer:fine)').matches)return;api.listen(el,'pointermove',api.frame(e=>{const r=el.getBoundingClientRect(),x=(e.clientX-r.left)/r.width,y=(e.clientY-r.top)/r.height;el.style.setProperty('--uv-foil-angle',(80+x*100)+'deg');el.style.setProperty('--uv-foil-x',(x*100)+'%');el.style.setProperty('--uv-foil-y',(y*100)+'%');}));return()=>['--uv-foil-angle','--uv-foil-x','--uv-foil-y'].forEach(k=>el.style.removeProperty(k));
});
