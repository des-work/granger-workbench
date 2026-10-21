UltraWeb.register("reveal-stagger",{"distance":{"default":28,"min":0,"max":80,"unit":"","css":null},"duration":{"default":650,"min":100,"max":1600,"unit":"","css":null},"stagger":{"default":100,"min":0,"max":300,"unit":"","css":null}},function(el,o,api){
if(!api.motion)return;api.visible(()=>{[...el.children].flatMap(n=>n.classList.contains('uv-grid')?[...n.children]:[n]).forEach((n,i)=>api.animate(n,[{opacity:0,transform:`translateY(${o.distance}px)`},{opacity:1,transform:'none'}],{duration:o.duration,delay:i*o.stagger,fill:'backwards'}));});
});
