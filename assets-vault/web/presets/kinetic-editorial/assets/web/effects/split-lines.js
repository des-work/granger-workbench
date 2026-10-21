UltraWeb.register("split-lines",{"duration":{"default":900,"min":200,"max":1800,"unit":"","css":null}},function(el,o,api){
if(!api.motion)return;api.visible(()=>el.querySelectorAll('em').forEach((n,i)=>api.animate(n,[{transform:'translateY(110%)'},{transform:'none'}],{duration:o.duration,delay:120*i,fill:'backwards'})));
});
