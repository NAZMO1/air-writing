import {Engine} from './game.mjs';
import {CameraController} from './gesture/camera.mjs';
const $=id=>document.getElementById(id);
let control='camera',handReady=false,manualPause=false,busy=false,hand={input:{}},lastView;
const labels={off:'Caméra éteinte',loading:'Autorise l’accès à la caméra…',model:'Chargement de MediaPipe…',searching:'Montre une main de face',calibrating:'Garde le poignet immobile une seconde',tracking:'Main détectée · prêt à piloter',lost:'Main perdue · partie en pause',error:'Caméra indisponible'};
const game=new Engine($('game'),render);
const camera=new CameraController($('video'),$('overlay'),data=>{
 handReady=data.ready;hand=data;
 if(control!=='camera')return;
 game.input=data.input;
 if(data.ready&&game.mode==='demo')game.training();
 if(game.mode!=='demo'){const paused=!data.ready||manualPause;if(paused!==game.paused)game.setPaused(paused);game.input=data.input;}
 if(data.quiet)return;
 $('status').textContent=labels[data.status]||labels.off;
 $('placeholder').hidden=['tracking','searching','calibrating','lost'].includes(data.status);
 $('pill').classList.toggle('ready',data.ready);$('pill-label').textContent=data.ready?'SUIVI ACTIF':'EN ATTENTE';
 $('center').disabled=!camera.running;$('stop').disabled=!camera.running&&!busy;
 $('direction').children[0].textContent=data.input.axisX<-.15?'← Gauche':data.input.axisX>.15?'Droite →':'Centré';
 $('direction').children[1].textContent=data.input.axisY<-.15?'↑ Monter':data.input.axisY>.15?'↓ Descendre':'Altitude stable';
 $('direction').children[2].textContent=data.input.boost?'Pouce sorti':'Pouce replié';
 $('direction').children[2].classList.toggle('lit',data.input.boost);
 if(data.status==='error')showError(data.error);
});
function showError(text=''){$('error').hidden=!text;$('error').textContent=text;}
function render(v){
 lastView=v;const active=v.mode!=='demo';
 $('blue-score').textContent=active?v.score[0]:0;$('orange-score').textContent=active?v.score[1]:0;
 $('time').textContent=!active?'02:00':v.time===0?'BUT EN OR':`${Math.floor(Math.ceil(v.time)/60)}:${String(Math.ceil(v.time)%60).padStart(2,'0')}`;
 $('phase').textContent=v.paused?'PAUSE':active?'SOLO':'MATCH';$('mode-label').textContent=active?'MATCH SOLO · CONTRE LE BOT':'L’ARÈNE T’ATTEND';
 const boost=active?Math.round(v.boost):100;$('fuel').style.width=`${boost}%`;$('fuel-label').textContent=`${boost} %`;
 const turbo=control==='camera'&&hand.input?.boost;$('turbo-status').textContent=turbo?'ϟ TURBO ACTIVÉ':'ϟ RÉSERVE TURBO';$('turbo-status').classList.toggle('turbo-active',!!turbo);
 for(const id of ['pause','replay','quit'])$(id).hidden=!active;
 $('pause').textContent=v.paused?'Reprendre':'Pause';$('pause').disabled=control==='camera'&&!handReady;
 const paused=active&&v.paused&&v.phase!=='ended';$('pause-overlay').hidden=!paused;
 if(paused){$('pause-title').textContent=control==='camera'&&!handReady?'En attente de ta main':'Partie en pause';$('pause-tip').textContent=control==='camera'&&!handReady?labels[hand.status]||labels.off:'Le chrono attend.';$('resume').hidden=control==='camera'&&!handReady;}
 $('ended').hidden=!(active&&v.phase==='ended');$('touch').hidden=!(active&&control==='keyboard');
}
function updateMode(){ $('camera-tab').classList.toggle('selected',control==='camera');$('keyboard-tab').classList.toggle('selected',control==='keyboard');$('start').hidden=control!=='camera';render(lastView); }
function stopCamera(){camera.stop();handReady=false;busy=false;hand={status:'off',input:{}};game.input={};$('status').textContent=labels.off;$('placeholder').hidden=false;$('pill').classList.remove('ready');$('pill-label').textContent='EN ATTENTE';$('start').disabled=false;$('start').textContent='Activer la caméra ↗';$('center').disabled=true;$('stop').disabled=true;for(const [i,text] of ['Centré','Altitude stable','Pouce replié'].entries())$('direction').children[i].textContent=text;$('direction').children[2].classList.remove('lit');if(game.mode!=='demo')game.setPaused(true);}
$('start').onclick=async()=>{control='camera';manualPause=false;handReady=false;game.input={};if(game.mode!=='demo')game.setPaused(true);showError();busy=true;$('start').disabled=true;$('start').textContent='Chargement…';$('stop').disabled=false;await camera.start();busy=false;$('start').disabled=false;$('start').textContent=camera.running?'Relancer la caméra ↗':'Activer la caméra ↗';};
$('stop').onclick=stopCamera;$('center').onclick=()=>{manualPause=false;camera.recalibrate();};
$('keyboard-tab').onclick=()=>{stopCamera();control='keyboard';manualPause=false;keys.clear();game.training();showError();updateMode();};
$('camera-tab').onclick=()=>{if(control==='camera')return;control='camera';game.input={};if(game.mode!=='demo')game.setPaused(true);updateMode();};
function pause(){if(control==='camera'&&!handReady)return;manualPause=!manualPause;game.setPaused(manualPause);}
function replay(){game.replay();manualPause=false;game.setPaused(control==='camera'&&!handReady);}
$('pause').onclick=pause;$('resume').onclick=pause;$('replay').onclick=replay;$('again').onclick=replay;
$('quit').onclick=()=>{stopCamera();manualPause=false;game.leave();showError();};
$('sensitivity').oninput=e=>camera.setSensitivity(.52-Number(e.target.value));
const mapping={ArrowLeft:'left',a:'left',q:'left',ArrowRight:'right',d:'right',ArrowUp:'jump',w:'jump',z:'jump',' ':'jump',Shift:'boost'},keys=new Set();
function keyboard(e,down){if(control!=='keyboard'||['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName))return;const action=mapping[e.key];if(!action)return;e.preventDefault();if(down)keys.add(e.key);else keys.delete(e.key);game.input[action]=[...keys].some(k=>mapping[k]===action);}
window.addEventListener('keydown',e=>keyboard(e,true));window.addEventListener('keyup',e=>keyboard(e,false));
window.addEventListener('blur',()=>{keys.clear();game.input={};if(game.mode!=='demo'){manualPause=true;game.setPaused(true);}});
document.addEventListener('visibilitychange',()=>{if(document.hidden){stopCamera();manualPause=true;}});
for(const button of document.querySelectorAll('[data-action]')){button.onpointerdown=e=>{e.preventDefault();button.setPointerCapture(e.pointerId);game.input[button.dataset.action]=true;};for(const event of ['pointerup','pointercancel','lostpointercapture'])button.addEventListener(event,()=>game.input[button.dataset.action]=false);}
window.addEventListener('pagehide',()=>{camera.stop();game.destroy();});
render({score:[0,0],time:120,phase:'waiting',boost:100,mode:'demo',paused:false});
