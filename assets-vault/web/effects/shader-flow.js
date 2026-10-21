UltraWeb.register("shader-flow",{"speed":{"default":0.6,"min":0.1,"max":1.5,"unit":"","css":null},"intensity":{"default":1,"min":0.1,"max":1,"unit":"","css":"--uv-intensity"}},function(el,o,api){
const canvas=el.querySelector('canvas'),gl=canvas.getContext('webgl',{alpha:true,antialias:false,powerPreference:'low-power'});if(!gl)return;
const vertex='attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}';
const fragment='precision mediump float;uniform vec2 r;uniform float t;uniform vec3 a;uniform vec3 b;void main(){vec2 uv=gl_FragCoord.xy/r;uv.x*=r.x/r.y;float f=sin(uv.x*4.+t*.3+sin(uv.y*5.-t*.2))*cos(uv.y*4.-t*.25);float v=smoothstep(-.8,.9,f);vec3 c=mix(a,b,v);float light=.22+.55*smoothstep(.1,.85,v);gl_FragColor=vec4(c*light,1.);}';
function compile(type,src){const sh=gl.createShader(type);gl.shaderSource(sh,src);gl.compileShader(sh);if(!gl.getShaderParameter(sh,gl.COMPILE_STATUS)){gl.deleteShader(sh);return null;}return sh;}
const vs=compile(gl.VERTEX_SHADER,vertex),fs=compile(gl.FRAGMENT_SHADER,fragment);if(!vs||!fs){if(vs)gl.deleteShader(vs);if(fs)gl.deleteShader(fs);return;}
const prog=gl.createProgram();gl.attachShader(prog,vs);gl.attachShader(prog,fs);gl.linkProgram(prog);if(!gl.getProgramParameter(prog,gl.LINK_STATUS)){gl.deleteProgram(prog);gl.deleteShader(vs);gl.deleteShader(fs);return;}
const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);gl.useProgram(prog);const p=gl.getAttribLocation(prog,'p');gl.enableVertexAttribArray(p);gl.vertexAttribPointer(p,2,gl.FLOAT,false,0,0);
const time=gl.getUniformLocation(prog,'t'),res=gl.getUniformLocation(prog,'r');
function color(name){const h=getComputedStyle(el).getPropertyValue(name).trim().replace('#','');return [0,2,4].map(i=>parseInt(h.slice(i,i+2),16)/255);}
gl.uniform3fv(gl.getUniformLocation(prog,'a'),color('--accent'));gl.uniform3fv(gl.getUniformLocation(prog,'b'),color('--accent2'));
let lost=false;api.listen(canvas,'webglcontextlost',e=>{e.preventDefault();lost=true;});
function draw(t){if(lost)return;const dpr=Math.min(devicePixelRatio||1,1.5),w=Math.max(1,Math.round(el.clientWidth*dpr)),h=Math.max(1,Math.round(el.clientHeight*dpr));if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;gl.viewport(0,0,w,h);}gl.uniform2f(res,w,h);gl.uniform1f(time,t*.001*o.speed);gl.drawArrays(gl.TRIANGLES,0,6);}
draw(0);if(api.motion)api.loop(draw);else api.listen(window,'resize',()=>draw(0));return()=>{gl.deleteBuffer(buffer);gl.deleteProgram(prog);gl.deleteShader(vs);gl.deleteShader(fs);};
});
