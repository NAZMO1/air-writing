// MediaPipe landmarks -> camera-independent game inputs. No OCR/classifier needed.
export const neutralInput = () => ({left:false,right:false,jump:false,boost:false,axisX:0,axisY:0,flight:true});
const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
const distance=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y,(a.z||0)-(b.z||0));
function angle(a,b,c){const u=[a.x-b.x,a.y-b.y,(a.z||0)-(b.z||0)],v=[c.x-b.x,c.y-b.y,(c.z||0)-(b.z||0)];return Math.acos(clamp(u.reduce((s,n,i)=>s+n*v[i],0)/(Math.hypot(...u)*Math.hypot(...v)||1),-1,1))*180/Math.PI;}
export function thumbExtended(lm,aspect=4/3){
 if(!lm||lm.length!==21)return false;
 // Correct normalized image aspect before comparing joint angles and distances.
 const p=lm.map(p=>({x:p.x*aspect,y:p.y,z:(p.z||0)*aspect}));
 const scale=distance(p[0],p[9]);
 return scale>.025 && angle(p[2],p[3],p[4])>150 && angle(p[1],p[2],p[3])>125 && distance(p[4],p[5])/scale>.56 && distance(p[4],p[0])>distance(p[3],p[0])*1.07;
}
function axis(d,range){const dead=.045;if(Math.abs(d)<=dead)return 0;return Math.sign(d)*clamp((Math.abs(d)-dead)/(range-dead),0,1);}
export class WristControls{
 constructor(){this.range=.24;this.reset();}
 reset(){this.origin=null;this.filtered=null;this.samples=[];this.calibrationStarted=null;this.lastSeen=-Infinity;this.lastTime=null;this.thumb=false;this.thumbCandidate=false;this.thumbSince=0;}
 recalibrate(){this.reset();}
 update(lm,now,aspect=4/3){
  if(!lm||lm.length!==21||!lm.every(p=>Number.isFinite(p.x)&&Number.isFinite(p.y))){this.filtered=null;this.thumb=false;this.thumbCandidate=false;this.thumbSince=now;this.samples=[];this.calibrationStarted=null;return {input:neutralInput(),status:this.origin?'lost':'searching',ready:false,progress:0,origin:this.origin};}
  const point={x:1-lm[0].x,y:lm[0].y}; // mirror so right on screen means right in game
  const dt=this.lastTime===null?1/30:clamp((now-this.lastTime)/1000,0,.1);this.lastTime=now;this.lastSeen=now;
  const alpha=1-Math.exp(-dt/.065);this.filtered=this.filtered?{x:this.filtered.x+(point.x-this.filtered.x)*alpha,y:this.filtered.y+(point.y-this.filtered.y)*alpha}:point;
  if(!this.origin){
   if(this.samples.length&&Math.hypot(point.x-this.samples[0].x,point.y-this.samples[0].y)>.075){this.samples=[];this.calibrationStarted=null;}
   if(this.calibrationStarted===null)this.calibrationStarted=now;
   this.samples.push(point);const progress=clamp((now-this.calibrationStarted)/900,0,1);
   if(progress<1||this.samples.length<8)return {input:neutralInput(),status:'calibrating',ready:false,progress,wrist:this.filtered};
   this.origin={x:this.samples.reduce((s,p)=>s+p.x,0)/this.samples.length,y:this.samples.reduce((s,p)=>s+p.y,0)/this.samples.length};this.filtered={...this.origin};
  }
  const rawThumb=thumbExtended(lm,aspect);
  if(rawThumb!==this.thumbCandidate){this.thumbCandidate=rawThumb;this.thumbSince=now;}
  if(now-this.thumbSince>=100)this.thumb=this.thumbCandidate;
  const axisX=axis(this.filtered.x-this.origin.x,this.range),axisY=axis(this.filtered.y-this.origin.y,this.range);
  return {input:{...neutralInput(),axisX,axisY,left:axisX<-.05,right:axisX>.05,boost:this.thumb},status:'tracking',ready:true,progress:1,wrist:this.filtered,origin:this.origin};
 }
}
