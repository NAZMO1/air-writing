import {W,H,FLOOR,GOAL,initialState,step,startMatch,blankInput} from './physics.mjs';
const blue='#63d9ff',orange='#ff925b';
function round(ctx,x,y,w,h,r,fill){ctx.fillStyle=fill;ctx.beginPath();ctx.roundRect(x,y,w,h,r);ctx.fill();}
export function draw(ctx,s,t,local=0,demo=false){
 ctx.clearRect(0,0,W,H);const bg=ctx.createLinearGradient(0,0,0,H);bg.addColorStop(0,'#0d1827');bg.addColorStop(1,'#152b3a');ctx.fillStyle=bg;ctx.fillRect(0,0,W,H);
 // Stadium structure and atmospheric lights.
 ctx.strokeStyle='#284150';ctx.lineWidth=1;for(let x=60;x<=1140;x+=60){ctx.beginPath();ctx.moveTo(x,70);ctx.lineTo(x,FLOOR);ctx.stroke();}for(let y=90;y<FLOOR;y+=60){ctx.beginPath();ctx.moveTo(60,y);ctx.lineTo(1140,y);ctx.stroke();}
 ctx.fillStyle='#142331';for(let i=0;i<15;i++){ctx.fillRect(i*90,75+(i%3)*12,65,85);ctx.fillRect(i*90+10,200,40,55);}
 for(let i=0;i<80;i++){ctx.fillStyle=i%3===0?'#85c5d64d':'#aaccc51a';ctx.fillRect(70+(i*157)%1060,100+(i*43)%130,3,3);}
 ctx.strokeStyle='#7cacba25';ctx.setLineDash([8,12]);ctx.beginPath();ctx.moveTo(600,80);ctx.lineTo(600,FLOOR);ctx.stroke();ctx.setLineDash([]);ctx.beginPath();ctx.arc(600,FLOOR,150,Math.PI,0);ctx.stroke();
 // Goals, including mesh.
 for(const [x,color] of [[4,blue],[1140,orange]]){ctx.fillStyle=color+'12';ctx.fillRect(x,GOAL,56,FLOOR-GOAL);ctx.strokeStyle=color+'35';for(let k=0;k<=56;k+=14){ctx.beginPath();ctx.moveTo(x+k,GOAL);ctx.lineTo(x+k,FLOOR);ctx.stroke();}for(let k=0;k<145;k+=16){ctx.beginPath();ctx.moveTo(x,GOAL+k);ctx.lineTo(x+56,GOAL+k);ctx.stroke();}ctx.strokeStyle=color;ctx.lineWidth=5;ctx.beginPath();ctx.moveTo(x,GOAL);ctx.lineTo(x+56,GOAL);ctx.stroke();}
 ctx.lineWidth=4;ctx.strokeStyle='#7c9eab';ctx.beginPath();ctx.moveTo(60,GOAL);ctx.lineTo(60,70);ctx.quadraticCurveTo(60,50,80,50);ctx.lineTo(1120,50);ctx.quadraticCurveTo(1140,50,1140,70);ctx.lineTo(1140,GOAL);ctx.stroke();
 ctx.fillStyle='#203a45';ctx.fillRect(0,FLOOR,W,78);ctx.fillStyle='#8aa5a5';ctx.fillRect(0,FLOOR,W,4);ctx.fillStyle='#d5ff62';for(let i=0;i<40;i++)ctx.fillRect(i*35+5,FLOOR+13,15,3);
 ctx.font='bold 12px monospace';ctx.fillStyle='#7796a1';ctx.fillText('TURBO DUEL  /  ARENA 01',62,620);ctx.textAlign='right';ctx.fillText('BOOST. JUMP. SCORE.',1138,620);ctx.textAlign='left';
 const b=s.ball;ctx.save();ctx.translate(b.x,b.y);ctx.shadowColor='#eaffbf';ctx.shadowBlur=20;ctx.fillStyle='#f2f5df';ctx.beginPath();ctx.arc(0,0,23,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;ctx.rotate((b.x+b.y)/55);ctx.strokeStyle='#30454a';ctx.lineWidth=3;ctx.beginPath();for(let i=0;i<6;i++){let a=i*Math.PI/3;let x=Math.cos(a)*10,y=Math.sin(a)*10;if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);}ctx.closePath();ctx.stroke();for(let i=0;i<3;i++){let a=i*2*Math.PI/3;ctx.beginPath();ctx.moveTo(Math.cos(a)*10,Math.sin(a)*10);ctx.lineTo(Math.cos(a)*23,Math.sin(a)*23);ctx.stroke();}ctx.restore();
 s.cars.forEach((c,i)=>{ctx.save();ctx.translate(c.x,c.y);ctx.rotate(c.angle);ctx.scale(c.face,1);const color=i?orange:blue;
 if(Math.abs(c.vx)>390){ctx.fillStyle='#d8ff64';ctx.beginPath();ctx.moveTo(-40,-4);ctx.lineTo(-75-Math.sin(t*30)*16,3);ctx.lineTo(-40,12);ctx.fill();ctx.fillStyle='#fff6ca';ctx.fillRect(-55,0,15,7);}
 ctx.shadowColor=color;ctx.shadowBlur=12;round(ctx,-42,-16,84,31,9,color);ctx.shadowBlur=0;round(ctx,-23,-31,48,22,7,color);round(ctx,-15,-27,31,15,4,'#1d3447');round(ctx,32,-10,10,7,2,'#ffffdd');round(ctx,-43,-9,6,8,2,'#ff5f5f');ctx.fillStyle='#17232c';ctx.fillRect(-35,9,70,5);
 for(const x of [-26,27]){ctx.fillStyle='#080f19';ctx.beginPath();ctx.arc(x,16,12,0,Math.PI*2);ctx.fill();ctx.strokeStyle='#93a6b0';ctx.lineWidth=3;ctx.beginPath();ctx.arc(x,16,6,0,Math.PI*2);ctx.stroke();}
 ctx.restore();if(!demo){ctx.font='bold 12px monospace';ctx.fillStyle=color;ctx.textAlign='center';ctx.fillText(i===local?'VOUS':i?'ORANGE':'BLEU',c.x,c.y-52);ctx.textAlign='left';}
 });
 if(!demo&&['countdown','goal','ended','waiting'].includes(s.phase)){let text=s.phase==='countdown'?String(Math.ceil(s.countdown)):s.phase==='goal'?s.message:s.phase==='waiting'?'EN ATTENTE DU 2E PILOTE':s.score[0]===s.score[1]?'ÉGALITÉ':`${s.score[0]>s.score[1]?'BLEU':'ORANGE'} REMPORTE LE MATCH`;
 ctx.textAlign='center';ctx.font=s.phase==='countdown'?'900 110px sans-serif':'900 37px sans-serif';ctx.shadowColor='#050e1a';ctx.shadowBlur=25;ctx.fillStyle=s.phase==='goal'?(s.goal?orange:blue):'#e9f3de';ctx.fillText(text,600,265);ctx.shadowBlur=0;ctx.textAlign='left';}
}
export class Engine{
 constructor(canvas,notify){this.canvas=canvas;this.ctx=canvas.getContext('2d');this.notify=notify;this.s=initialState();this.input=blankInput();this.mode='demo';this.role=0;this.paused=false;this.stop=false;this.lastFrame=performance.now();this.lastUI=0;this.s.phase='playing';this.s.time=9999;this.tick=this.tick.bind(this);this.frame=requestAnimationFrame(this.tick);}
 emit(){this.notify({score:[...this.s.score],time:this.s.time,phase:this.s.phase,boost:this.s.cars[0].boost,mode:this.mode,paused:this.paused});}
 tick(now){if(this.stop)return;let dt=Math.min((now-this.lastFrame)/1000,.05);this.lastFrame=now;
 if(!this.paused){const opponent=this.bot(1),mine=this.mode==='demo'?this.bot(0):this.input;while(dt>0){const d=Math.min(dt,1/120);step(this.s,[mine,opponent],d);dt-=d;}if(this.mode==='demo'&&(this.s.phase==='ended'||this.s.time<500)){this.s=initialState();this.s.phase='playing';this.s.time=9999;}}
 draw(this.ctx,this.s,now/1000,0,this.mode==='demo');if(now-this.lastUI>100){this.emit();this.lastUI=now;}this.frame=requestAnimationFrame(this.tick);}
 bot(i){const c=this.s.cars[i],b=this.s.ball;const aim=b.x+(i?44:-44),diff=aim-c.x;return {left:diff<-18,right:diff>18,jump:Math.abs(diff)<135&&b.y<480&&c.y>540&&Math.sin(performance.now()/190)>0,boost:Math.abs(diff)>240&&c.boost>35};}
 training(){this.mode='training';this.role=0;this.input=blankInput();this.paused=false;startMatch(this.s);this.emit();}
 setPaused(value){this.paused=value;this.lastFrame=performance.now();this.emit();}
 replay(){startMatch(this.s);this.emit();}
 leave(){this.mode='demo';this.paused=false;this.input=blankInput();this.s=initialState();this.s.phase='playing';this.s.time=9999;this.emit();}
 destroy(){this.stop=true;cancelAnimationFrame(this.frame);}
}
