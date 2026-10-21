UltraWeb.register("hover-preview",{},function(el,o,api){
const buttons=[...el.querySelectorAll('nav button')],art=el.querySelector('.uv-work-art'),label=art.querySelector('p');function select(i){buttons.forEach((b,j)=>b.setAttribute('aria-pressed',String(i===j)));label.textContent=buttons[i].textContent.slice(5);api.animate(art,[{opacity:.45,transform:'translateY(12px)'},{opacity:1,transform:'none'}],{duration:300});}buttons.forEach((b,i)=>{api.listen(b,'pointerenter',()=>select(i));api.listen(b,'focus',()=>select(i));api.listen(b,'click',()=>select(i));});
});
