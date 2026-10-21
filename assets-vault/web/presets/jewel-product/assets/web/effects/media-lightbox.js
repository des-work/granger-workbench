UltraWeb.register("media-lightbox",{},function(el,o,api){
const b=el.querySelector('.uv-lightbox-launch'),d=el.querySelector('dialog');api.listen(b,'click',()=>{if(!d.showModal)return;d.showModal();api.animate(d,[{opacity:0,transform:'scale(.96)'},{opacity:1,transform:'none'}],{duration:320});});api.listen(d.querySelector('.uv-close'),'click',()=>d.close());api.listen(d,'click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close();}});api.listen(d,'close',()=>b.focus());return()=>{if(d.open)d.close();};
});
