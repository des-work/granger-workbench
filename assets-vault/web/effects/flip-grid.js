UltraWeb.register("flip-grid",{},function(el,o,api){
const g=el.querySelector('.uv-grid');api.listen(el.querySelector('button'),'click',()=>{const nodes=[...g.children],before=nodes.map(n=>n.getBoundingClientRect());g.append(nodes[0]);nodes.forEach((n,i)=>{const r=n.getBoundingClientRect();api.animate(n,[{transform:`translate(${before[i].left-r.left}px,${before[i].top-r.top}px)`},{transform:'none'}],{duration:500});});});
});
