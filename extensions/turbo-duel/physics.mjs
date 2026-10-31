export const W=1200,H=650,FLOOR=572,CEIL=70,GOAL=430;
export const blankInput=()=>({left:false,right:false,jump:false,boost:false});
const car=(i)=>({x:i?925:275,y:FLOOR-22,vx:0,vy:0,face:i?-1:1,boost:100,jumped:false,angle:0});
export function initialState(){return {cars:[car(0),car(1)],ball:{x:600,y:335,vx:0,vy:0},score:[0,0],time:120,phase:'waiting',countdown:0,message:'',goal:0,round:0};}
export function startMatch(s){Object.assign(s,initialState(),{phase:'countdown',countdown:3,round:s.round+1});}
function kickoff(s){s.cars=[car(0),car(1)];s.ball={x:600,y:335,vx:0,vy:0};s.phase='countdown';s.countdown=2;s.message='';}
const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
export function step(s,inputs,dt){
 dt=Math.min(dt,.025);if(s.phase==='waiting'||s.phase==='ended')return;
 if(s.phase==='countdown'){s.countdown-=dt;if(s.countdown<=0)s.phase='playing';return;}
 if(s.phase==='goal'){s.countdown-=dt;if(s.countdown<=0){if(s.score[0]>=5||s.score[1]>=5||s.time<=0&&s.score[0]!==s.score[1])s.phase='ended';else kickoff(s);}return;}
 s.time=Math.max(0,s.time-dt);if(s.time===0&&s.score[0]!==s.score[1]){s.phase='ended';return;}
 s.cars.forEach((c,i)=>{const input=inputs[i]||blankInput();const dir=input.flight?clamp(input.axisX||0,-1,1):Number(input.right)-Number(input.left);if(Math.abs(dir)>.05)c.face=Math.sign(dir);
 const grounded=c.y>=FLOOR-22-.5;let boosting=input.boost&&c.boost>0;if(boosting){c.boost=Math.max(0,c.boost-36*dt);c.vx+=c.face*1250*dt;if(!grounded)c.vy-=320*dt;}else c.boost=Math.min(100,c.boost+17*dt);
 c.vx+=dir*1050*dt;c.vx*=Math.exp(-(dir?1.8:4.3)*dt);c.vx=clamp(c.vx,-(boosting?640:390),boosting?640:390);
 if(input.flight){
 // Wrist joystick: neutral hovers; raising/lowering the wrist flies up/down.
 const vertical=clamp(input.axisY||0,-1,1);c.vy+=(vertical*(boosting?550:360)-c.vy)*(1-Math.exp(-7*dt));
 }else{if(input.jump&&!c.jumped&&grounded)c.vy=-650;c.vy+=1250*dt;}
 c.jumped=input.jump;c.x+=c.vx*dt;c.y+=c.vy*dt;
 if(c.y>FLOOR-22){c.y=FLOOR-22;c.vy=0;}if(c.y<CEIL+22){c.y=CEIL+22;c.vy=Math.abs(c.vy)*.3;}
 c.x=clamp(c.x,78,W-78);c.angle=grounded?0:clamp(c.vx/1800,-.32,.32);
 });
 const [a,c]=s.cars;if(Math.abs(a.x-c.x)<79&&Math.abs(a.y-c.y)<38){const dir=a.x<c.x?-1:1,overlap=79-Math.abs(a.x-c.x);a.x+=dir*overlap/2;c.x-=dir*overlap/2;const av=a.vx;a.vx=c.vx*.7;c.vx=av*.7;}
 const b=s.ball;b.vy+=760*dt;b.vx*=Math.exp(-.1*dt);b.x+=b.vx*dt;b.y+=b.vy*dt;
 if(b.y>FLOOR-23){b.y=FLOOR-23;b.vy=-Math.abs(b.vy)*.78;if(Math.abs(b.vy)<35)b.vy=0;b.vx*=.995;}
 if(b.y<CEIL+23){b.y=CEIL+23;b.vy=Math.abs(b.vy)*.85;}
 if(b.y<GOAL+23){if(b.x<83){b.x=83;b.vx=Math.abs(b.vx)*.85;}if(b.x>W-83){b.x=W-83;b.vx=-Math.abs(b.vx)*.85;}}
 for(const c of s.cars){const nx=clamp(b.x,c.x-39,c.x+39),ny=clamp(b.y,c.y-19,c.y+19);let dx=b.x-nx,dy=b.y-ny,d=Math.hypot(dx,dy);if(d<23){if(d<.001){dx=0;dy=-1;d=1;}const ux=dx/d,uy=dy/d;b.x+=ux*(23-d+1);b.y+=uy*(23-d+1);const dot=(b.vx-c.vx)*ux+(b.vy-c.vy)*uy;if(dot<0){b.vx-=1.65*dot*ux;b.vy-=1.65*dot*uy;}b.vx+=c.vx*.23;b.vy-=85;}}
 b.vx=clamp(b.vx,-1050,1050);b.vy=clamp(b.vy,-1000,1000);
 if(b.y>=GOAL&& (b.x<30||b.x>W-30)){const who=b.x<30?1:0;s.score[who]++;s.goal=who;s.phase='goal';s.countdown=2.3;s.message=who?'BUT ORANGE !':'BUT BLEU !';}
}
