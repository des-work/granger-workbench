/* starfield-js — Warp starfield flying toward the viewer on <canvas id='stars'>.  [style: vaporwave] */
// <canvas id="stars" style="position:fixed;inset:0;z-index:-1;background:var(--bg)"></canvas>
const c = document.getElementById('stars'), x = c.getContext('2d');
let W, H, stars = [];
function resize(){ W = c.width = innerWidth; H = c.height = innerHeight; }
resize(); addEventListener('resize', resize);
for (let i = 0; i < 300; i++) stars.push({ x:(Math.random()-0.5)*W, y:(Math.random()-0.5)*H, z:Math.random()*W });
(function loop(){
  // trail colour from the page background, so stars sit on the real field
  const root = getComputedStyle(document.documentElement);
  const bg = root.getPropertyValue('--bg').trim() || '#0f1b3d';
  const star = root.getPropertyValue('--accent').trim();
  x.fillStyle = bg + '66'; x.fillRect(0,0,W,H);
  for (const s of stars){
    s.z -= 6; if (s.z <= 0){ s.z = W; s.x = (Math.random()-0.5)*W; s.y = (Math.random()-0.5)*H; }
    const k = 128/s.z, sx = s.x*k + W/2, sy = s.y*k + H/2, r = (1-s.z/W)*2.5;
    x.fillStyle = star || '#01cdfe'; x.fillRect(sx, sy, r, r);
  }
  requestAnimationFrame(loop);
})();
