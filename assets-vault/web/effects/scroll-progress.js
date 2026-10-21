UltraWeb.register("scroll-progress",{},function(el,o,api){
if(CSS.supports('animation-timeline:scroll()')&&api.motion)return;const bar=el.querySelector('.uv-progress');const update=api.frame(()=>{const d=document.documentElement;bar.style.transform=`scaleX(${d.scrollTop/Math.max(1,d.scrollHeight-d.clientHeight)})`;});api.listen(window,'scroll',update,{passive:true});api.listen(window,'resize',update);update();return()=>bar.style.removeProperty('transform');
});
