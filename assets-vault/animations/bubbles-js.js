/* bubbles-js — Rising translucent bubbles on a <canvas id='bubbles'> — Frutiger Aero.  [style: frutiger-aero] */
// <canvas id="bubbles" style="position:fixed;inset:0;z-index:-1"></canvas>
const c = document.getElementById('bubbles'), x = c.getContext('2d');
let W, H, bubbles = [];
function resize(){ W = c.width = innerWidth; H = c.height = innerHeight; }
resize(); addEventListener('resize', resize);
for (let i = 0; i < 40; i++) bubbles.push({
  x: Math.random()*W, y: Math.random()*H, r: 6+Math.random()*26,
  s: 0.3+Math.random()*0.9
});
(function loop(){
  x.clearRect(0,0,W,H);
  for (const b of bubbles){
    b.y -= b.s; if (b.y + b.r < 0){ b.y = H + b.r; b.x = Math.random()*W; }
    const g = x.createRadialGradient(b.x-b.r*0.3, b.y-b.r*0.3, 1, b.x, b.y, b.r);
    // the bubble's rim picks up the page accent; the core stays specular white
    const tint = getComputedStyle(document.documentElement)
                   .getPropertyValue('--accent').trim() || '#60b2f0';
    g.addColorStop(0,'rgba(255,255,255,0.9)'); g.addColorStop(1, tint + '26');
    x.beginPath(); x.arc(b.x,b.y,b.r,0,7); x.fillStyle=g; x.fill();
  }
  requestAnimationFrame(loop);
})();
