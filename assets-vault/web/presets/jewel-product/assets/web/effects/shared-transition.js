UltraWeb.register("shared-transition",{},function(el,o,api){
const b=el.querySelector('button'),detail=el.querySelector('.uv-shared-detail');api.listen(b,'click',()=>{const update=()=>{const expanded=el.classList.toggle('uv-shared-expanded');b.setAttribute('aria-expanded',String(expanded));detail.hidden=!expanded;};if(api.motion&&document.startViewTransition)document.startViewTransition(update);else update();});
});
