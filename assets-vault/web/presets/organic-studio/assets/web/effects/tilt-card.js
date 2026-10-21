UltraWeb.register("tilt-card",{"angle":{"default":7,"min":0,"max":14,"unit":"","css":null}},function(el,o,api){
if(!api.motion||!matchMedia('(pointer:fine)').matches)return;const move=api.frame(e=>{const r=el.getBoundingClientRect();el.style.setProperty('--uv-rx',((.5-(e.clientY-r.top)/r.height)*o.angle*2)+'deg');el.style.setProperty('--uv-ry',(((e.clientX-r.left)/r.width-.5)*o.angle*2)+'deg');});const reset=()=>{el.style.removeProperty('--uv-rx');el.style.removeProperty('--uv-ry');};api.listen(el,'pointermove',move);api.listen(el,'pointerleave',reset);return reset;
});
