UltraWeb.register("scroll-depth",{"distance":{"default":35,"min":0,"max":90,"unit":"px","css":"--uv-depth-distance"}},function(el,o,api){
if(!api.motion||CSS.supports('animation-timeline:view()'))return;const n=el.querySelector('.uv-depth');const update=api.frame(()=>{const r=el.getBoundingClientRect();const f=(innerHeight/2-r.top-r.height/2)/innerHeight;n.style.setProperty('--uv-depth-y',Math.max(-o.distance,Math.min(o.distance,f*o.distance))+'px');});api.listen(window,'scroll',update,{passive:true});update();return()=>n.style.removeProperty('--uv-depth-y');
});
