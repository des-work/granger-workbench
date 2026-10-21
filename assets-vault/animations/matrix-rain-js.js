/* matrix-rain-js — Falling green code rain on a <canvas id='matrix'>.  [style: cyberpunk] */
// <canvas id="matrix" style="position:fixed;inset:0;z-index:-1;background:#000"></canvas>
const c = document.getElementById('matrix'), x = c.getContext('2d');
let W = c.width = innerWidth, H = c.height = innerHeight;
addEventListener('resize', () => { W = c.width = innerWidth; H = c.height = innerHeight; });
const cols = Math.floor(W / 14), drops = Array(cols).fill(0);
const chars = 'ｱｲｳｴｵｶ01<>=/*-+アカサタナ'.split('');
setInterval(() => {
  x.fillStyle = 'rgba(0,0,0,0.06)'; x.fillRect(0,0,W,H);
  // the glyph colour comes from the page, with matrix green as the fallback
  const accent = getComputedStyle(document.documentElement)
                   .getPropertyValue('--accent').trim() || '#00ff41';
  x.fillStyle = accent; x.font = '14px monospace';
  drops.forEach((y, i) => {
    x.fillText(chars[Math.random()*chars.length|0], i*14, y*14);
    drops[i] = (y*14 > H && Math.random() > 0.975) ? 0 : y + 1;
  });
}, 55);
