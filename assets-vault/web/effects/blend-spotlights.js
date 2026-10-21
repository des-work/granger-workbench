UltraWeb.register("blend-spotlights",{},function(el,o,api){
if(!api.motion||!matchMedia('(pointer:fine)').matches)return;api.listen(el,'pointermove',api.frame(e=>{const r=el.getBoundingClientRect();el.style.setProperty('--uv-light-x',((e.clientX-r.left)/r.width*100)+'%');el.style.setProperty('--uv-light-y',((e.clientY-r.top)/r.height*100)+'%');}));return()=>{el.style.removeProperty('--uv-light-x');el.style.removeProperty('--uv-light-y');};
});
