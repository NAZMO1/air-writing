import {WristControls,neutralInput} from './wrist-controls.mjs';
const CDN='https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.21';
const MODEL='https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task';
const connections=[[0,1],[1,2],[2,3],[3,4],[0,5],[5,6],[6,7],[7,8],[5,9],[9,10],[10,11],[11,12],[9,13],[13,14],[14,15],[15,16],[13,17],[0,17],[17,18],[18,19],[19,20]];
export class CameraController{
 constructor(video,canvas,onUpdate){this.video=video;this.canvas=canvas;this.onUpdate=onUpdate;this.controls=new WristControls();this.generation=0;this.running=false;this.frame=0;this.lastVideo=-1;this.lastFrame=0;this.lastUI=0;}
 async start(){
  this.stop();const gen=this.generation;this.onUpdate({status:'loading',input:neutralInput(),ready:false,progress:0});
  let stream,detector;
  try{
   if(!navigator.mediaDevices?.getUserMedia)throw Object.assign(new Error('La caméra nécessite un navigateur récent et une page HTTPS (ou localhost).'),{name:'BrowserUnavailableError'});
   if(typeof document!=='undefined'){const probe=document.createElement('canvas');const gl=probe.getContext('webgl2')||probe.getContext('webgl');if(!gl)throw Object.assign(new Error('WebGL est indisponible. Active l’accélération graphique du navigateur ou essaie Chrome/Edge récent.'),{name:'BrowserUnavailableError'});gl.getExtension('WEBGL_lose_context')?.loseContext();}
   stream=await navigator.mediaDevices.getUserMedia({audio:false,video:{facingMode:'user',width:{ideal:640},height:{ideal:480},frameRate:{ideal:30,max:30}}});
   if(gen!==this.generation){stream.getTracks().forEach(t=>t.stop());return;}
   this.stream=stream;this.video.srcObject=stream;await this.video.play();
   this.onUpdate({status:'model',input:neutralInput(),ready:false,progress:0});
   const {FilesetResolver,HandLandmarker}=await import(/* @vite-ignore */ `${CDN}/vision_bundle.mjs`);
   const files=await FilesetResolver.forVisionTasks(`${CDN}/wasm`);
   const options={baseOptions:{modelAssetPath:MODEL,delegate:'GPU'},runningMode:'VIDEO',numHands:1,minHandDetectionConfidence:.6,minHandPresenceConfidence:.6,minTrackingConfidence:.6};
   try{detector=await HandLandmarker.createFromOptions(files,options);}catch{options.baseOptions.delegate='CPU';detector=await HandLandmarker.createFromOptions(files,options);}
   if(gen!==this.generation){detector.close();stream.getTracks().forEach(t=>t.stop());return;}
   this.detector=detector;this.running=true;this.lastVideo=-1;this.lastFrame=0;this.lastUI=0;
   stream.getVideoTracks()[0].onended=()=>{if(this.running){this.stop();this.onUpdate({status:'error',error:'La caméra a été déconnectée. Rebranche-la, puis réessaie.',ready:false,input:neutralInput()});}};
   this.frame=requestAnimationFrame(t=>this.tick(t));
  }catch(e){
   stream?.getTracks().forEach(t=>t.stop());detector?.close();
   if(gen!==this.generation)return;
   this.stop();const errors={NotAllowedError:'Accès caméra refusé. Autorise la caméra dans les réglages du navigateur, puis réessaie.',NotFoundError:'Aucune caméra détectée. Branche une webcam, puis réessaie.',NotReadableError:'Caméra occupée ou inaccessible. Ferme les autres applications qui l’utilisent.',OverconstrainedError:'La caméra ne prend pas en charge ce format.'};
   this.onUpdate({status:'error',error:(e.name==='BrowserUnavailableError'?e.message:errors[e.name])||`Impossible de démarrer le suivi. Vérifie la connexion pour télécharger MediaPipe, puis réessaie. ${e.message||''}`,ready:false,input:neutralInput(),progress:0});
  }
 }
 tick(now){
  if(!this.running)return;
  try{
   if(this.video.readyState>=2&&now-this.lastFrame>=40&&this.lastVideo!==this.video.currentTime){
    this.lastFrame=now;this.lastVideo=this.video.currentTime;
    const result=this.detector.detectForVideo(this.video,now);const landmarks=result.landmarks?.[0];
    const data=this.controls.update(landmarks,now,this.video.videoWidth/this.video.videoHeight||4/3);this.draw(landmarks,data);
    this.onUpdate({...data,quiet:now-this.lastUI<100});if(now-this.lastUI>=100)this.lastUI=now;
   }else if(now-this.lastFrame>250){this.onUpdate({status:'lost',ready:false,input:neutralInput(),quiet:false});}
  }catch(e){this.stop();this.onUpdate({status:'error',error:'Le suivi de la main a été interrompu. Relance la caméra ou joue au clavier.',ready:false,input:neutralInput()});return;}
  this.frame=requestAnimationFrame(t=>this.tick(t));
 }
 draw(lm,data){
  const c=this.canvas,ctx=c.getContext('2d'),w=c.width,h=c.height;ctx.clearRect(0,0,w,h);
  if(data.origin){ctx.strokeStyle='#ffffff60';ctx.setLineDash([4,4]);ctx.strokeRect((data.origin.x-.045)*w,(data.origin.y-.045)*h,.09*w,.09*h);ctx.setLineDash([]);ctx.beginPath();ctx.arc(data.origin.x*w,data.origin.y*h,4,0,7);ctx.stroke();}
  if(!lm)return;
  ctx.lineWidth=2;ctx.strokeStyle=data.input.boost?'#d5fb69':'#63d9ff';
  for(const [a,b] of connections){ctx.beginPath();ctx.moveTo((1-lm[a].x)*w,lm[a].y*h);ctx.lineTo((1-lm[b].x)*w,lm[b].y*h);ctx.stroke();}
  for(let i=0;i<lm.length;i++){ctx.fillStyle=i===4?'#d5fb69':i===0?'#fff':'#63d9ff';ctx.beginPath();ctx.arc((1-lm[i].x)*w,lm[i].y*h,i===0||i===4?5:2.5,0,7);ctx.fill();}
 }
 recalibrate(){this.controls.recalibrate();this.onUpdate({status:'searching',input:neutralInput(),ready:false,progress:0});}
 setSensitivity(value){this.controls.range=value;}
 stop(){
  this.generation++;this.running=false;cancelAnimationFrame(this.frame);
  if(this.stream){this.stream.getTracks().forEach(t=>{t.onended=null;t.stop();});this.stream=null;}
  this.video.srcObject=null;this.detector?.close();this.detector=null;this.controls.reset();
  this.canvas.getContext('2d')?.clearRect(0,0,this.canvas.width,this.canvas.height);
 }
}
