/** Native WebView — same cinematic engine as web canvas (in-place stars, delta time). */
export const GALAXY_CINEMATIC_HTML = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
<style>html,body{margin:0;padding:0;overflow:hidden;background:#000;width:100%;height:100%}canvas{display:block;width:100%;height:100%}</style>
</head>
<body><canvas id="c"></canvas>
<script>
(function(){
var canvas=document.getElementById("c");
var ctx=canvas.getContext("2d",{alpha:true});
if(!ctx)return;
var FLY=0.2,STEP=1/120,stars=[],w=0,h=0,dpr=1,cx=0,cy=0,last=0,accum=0;

function setTint(s){
  if(s.tint===1){s.cr=255;s.cg=228;s.cb=175;s.gr=255;s.gg=200;s.gb=120;return;}
  if(s.tint===2){s.cr=220;s.cg=195;s.cb=255;s.gr=160;s.gg=120;s.gb=255;return;}
  s.cr=255;s.cg=255;s.cb=255;s.gr=175;s.gg=210;s.gb=255;
}
function respawn(s){
  var a=Math.random()*6.28318,d=Math.pow(Math.random(),0.7);
  s.bx=Math.cos(a)*d;s.by=Math.sin(a)*d;s.z=1;s.pz=1;
  s.phase=Math.random()*6.28318;s.bright=Math.random();
  var r=Math.random();s.tint=r<0.9?0:r<0.95?1:2;setTint(s);
}
function initStars(n){
  stars.length=n;
  for(var i=0;i<n;i++){
    var s=stars[i]||{};
    s.bx=0;s.by=0;s.z=1;s.pz=1;s.phase=0;s.bright=0;s.tint=0;
    respawn(s);s.z=0.15+Math.random()*0.85;s.pz=s.z;stars[i]=s;
  }
}
function project(s,z){
  var inv=1/Math.max(z,0.045);
  return{x:cx+s.bx*w*0.5*inv,y:cy+s.by*h*0.5*inv,inv:inv};
}
function step(s){s.pz=s.z;s.z-=FLY*STEP;if(s.z<=0.035)respawn(s);}
function bg(){ctx.fillStyle="#000000";ctx.fillRect(0,0,w,h);}
function draw(blend,t){
  for(var i=0;i<stars.length;i++){
    var s=stars[i],zd=s.pz+(s.z-s.pz)*blend;
    var p1=project(s,zd),p0=project(s,Math.min(1,zd+0.06));
    var rad=Math.min(3.8,(0.18+s.bright*0.95)*p1.inv*0.34);
    var tw=0.88+0.12*Math.sin(t*(1.1+s.bright*1.4)+s.phase);
    var al=Math.min(1,(0.12+(1-zd)*0.82)*(0.55+s.bright*0.45)*tw);
    if(al<0.04||rad<0.1)continue;
    var dx=p1.x-p0.x,dy=p1.y-p0.y,seg=Math.sqrt(dx*dx+dy*dy);
    if(zd<0.5&&seg>1.1){
      var ang=Math.atan2(dy,dx),len=Math.min(seg*0.9,rad*7);
      ctx.save();ctx.translate(p1.x,p1.y);ctx.rotate(ang);
      ctx.globalAlpha=al*0.32*(0.5-zd)*2;
      var st=ctx.createLinearGradient(-len,0,rad*0.3,0);
      st.addColorStop(0,"rgba("+s.gr+","+s.gg+","+s.gb+",0)");
      st.addColorStop(0.45,"rgba("+s.cr+","+s.cg+","+s.cb+","+(al*0.35)+")");
      st.addColorStop(1,"rgba("+s.cr+","+s.cg+","+s.cb+","+(al*0.75)+")");
      ctx.fillStyle=st;ctx.beginPath();
      ctx.ellipse(-len*0.35,0,len*0.45,rad*0.5,0,0,6.28318);ctx.fill();ctx.restore();
    }
    if(rad<1.1){
      ctx.fillStyle="rgba("+s.cr+","+s.cg+","+s.cb+","+(al*0.85)+")";
      ctx.beginPath();ctx.arc(p1.x,p1.y,Math.max(0.35,rad*0.45),0,6.28318);ctx.fill();continue;
    }
    var g=ctx.createRadialGradient(p1.x,p1.y,0,p1.x,p1.y,rad*5);
    g.addColorStop(0,"rgba("+s.cr+","+s.cg+","+s.cb+","+al+")");
    g.addColorStop(0.12,"rgba("+s.gr+","+s.gg+","+s.gb+","+(al*0.55)+")");
    g.addColorStop(0.4,"rgba("+s.gr+","+s.gg+","+s.gb+","+(al*0.12)+")");
    g.addColorStop(1,"rgba(0,0,0,0)");
    ctx.fillStyle=g;ctx.beginPath();ctx.arc(p1.x,p1.y,rad*5,0,6.28318);ctx.fill();
    ctx.fillStyle="rgba("+s.cr+","+s.cg+","+s.cb+","+Math.min(1,al*1.08)+")";
    ctx.beginPath();ctx.arc(p1.x,p1.y,Math.max(0.38,rad*0.4),0,6.28318);ctx.fill();
  }
}
function resize(){
  w=window.innerWidth||360;h=window.innerHeight||640;
  cx=w*0.5;cy=h*0.5;dpr=Math.min(window.devicePixelRatio||1,2);
  canvas.width=Math.floor(w*dpr);canvas.height=Math.floor(h*dpr);
  canvas.style.width=w+"px";canvas.style.height=h+"px";
  ctx.setTransform(dpr,0,0,dpr,0,0);
  initStars(Math.min(5200,Math.floor((w*h)/115)));accum=0;
}
function frame(now){
  if(!last)last=now;
  var dt=Math.min(0.05,Math.max(0.001,(now-last)/1000));last=now;
  accum+=dt;var g=0;
  while(accum>=STEP&&g<10){for(var i=0;i<stars.length;i++)step(stars[i]);accum-=STEP;g++;}
  var blend=accum/STEP;
  ctx.clearRect(0,0,w,h);nebula();draw(blend,now/1000);
  requestAnimationFrame(frame);
}
resize();window.addEventListener("resize",resize);
document.addEventListener("visibilitychange",function(){if(!document.hidden)last=0;});
requestAnimationFrame(frame);
})();
</script>
</body>
</html>`;
