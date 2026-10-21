UltraWeb.register("sticky-morph",{},function(el,o,api){
const n=el.querySelector('.uv-sticky-wrap');const update=api.frame(()=>{const r=n.getBoundingClientRect();n.classList.toggle('uv-is-stuck',r.top<=1&&scrollY>0);});api.listen(window,'scroll',update,{passive:true});update();
});
