UltraWeb.register("morph-tabs",{},function(el,o,api){
const tabs=[...el.querySelectorAll('[role=tab]')],panels=[...el.querySelectorAll('[role=tabpanel]')];const uid='uv-tabs-'+Math.random().toString(36).slice(2,8);tabs.forEach((t,i)=>{t.id=uid+'-tab-'+i;panels[i].id=uid+'-panel-'+i;t.setAttribute('aria-controls',panels[i].id);panels[i].setAttribute('aria-labelledby',t.id);});
function change(i,focus=false){const update=()=>{tabs.forEach((t,j)=>{t.setAttribute('aria-selected',String(i===j));t.tabIndex=i===j?0:-1;panels[j].hidden=i!==j;});if(focus)tabs[i].focus();};if(api.motion&&document.startViewTransition)document.startViewTransition(update);else update();}
tabs.forEach((t,i)=>{api.listen(t,'click',()=>change(i));api.listen(t,'keydown',e=>{let j=i;if(e.key==='ArrowRight')j=(i+1)%tabs.length;else if(e.key==='ArrowLeft')j=(i-1+tabs.length)%tabs.length;else if(e.key==='Home')j=0;else if(e.key==='End')j=tabs.length-1;else return;e.preventDefault();change(j,true);});});
});
