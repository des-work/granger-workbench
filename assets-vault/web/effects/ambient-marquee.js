UltraWeb.register("ambient-marquee",{"speed":{"default":1,"min":0.3,"max":2,"unit":"","css":"--uv-speed"}},function(el,o,api){
const b=el.querySelector('button'),track=el.querySelector('.uv-marquee-track');if(!api.motion)track.style.animationPlayState='paused';api.listen(b,'click',()=>{const paused=b.getAttribute('aria-pressed')!=='true';b.setAttribute('aria-pressed',String(paused));b.textContent=paused?'Resume motion':'Pause motion';track.style.animationPlayState=paused||!api.motion?'paused':'';});
});
