(()=>{
const token=__SESSION_TOKEN__,sessionKey=__SESSION_KEY__,storageKey='reference-style-settings:'+sessionKey;
async function post(path,body){const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-Session-Token':token},body:JSON.stringify(body)});const result=await response.json();if(!response.ok)throw Error(result.error||'Ошибка сохранения');return result;}
const restored=__SERVER_RESTORE__;
let saved=restored.state; if(!saved)try{saved=JSON.parse(localStorage.getItem(storageKey)||'null')}catch{}
function publish(name,detail){window.dispatchEvent(new CustomEvent(name,{detail}));}
let statusTimer,statusFlight;
function refreshStatus(){
 if(statusFlight)return statusFlight;
 clearTimeout(statusTimer);
 statusFlight=(async()=>{
 const controller=new AbortController();let timeout;
 try{
 const expired=new Promise((_,reject)=>{timeout=setTimeout(()=>{controller.abort();reject(Error('Сервер не ответил вовремя'));},10000);});
 const read=(async()=>{const response=await fetch('/status',{cache:'no-store',signal:controller.signal});if(!response.ok)throw Error('Сервер недоступен');return response.json();})();
 const state=await Promise.race([read,expired]);window.referenceBrowser.queue=state;publish('reference-queue-updated',state);return state;
 }catch{const state={...window.referenceBrowser.queue,requests:window.referenceBrowser.queue?.requests||[],listener:{waiting:false},consumer:{active:false,expiresAt:null},offline:true};window.referenceBrowser.queue=state;publish('reference-queue-updated',state);return state;}
 finally{clearTimeout(timeout);statusFlight=null;statusTimer=setTimeout(refreshStatus,document.hidden?10000:2500);}
 })();
 return statusFlight;
}
let savedPanel;try{savedPanel=localStorage.getItem(storageKey+':panel')}catch{}
window.referenceBrowser={
 panel:['settings','presets','history'].includes(savedPanel)?savedPanel:null,
 setPanel:value=>{if(!['settings','presets','history'].includes(value))return;window.referenceBrowser.panel=value;try{localStorage.setItem(storageKey+':panel',value)}catch{}},
 disconnect:async()=>{const result=await post('/disconnect',{});await refreshStatus();return result;},
 referenceImage:restored.referenceImage,
 queue:{requests:[],listener:{waiting:false}},
 refreshStatus,
 repeatHistory:id=>post('/repeat-history',{id}),
 history:async(page=1)=>{const response=await fetch('/history?page='+Math.max(1,Math.floor(page))+'&pageSize=12',{cache:'no-store'});const result=await response.json();if(!response.ok)throw Error(result.error||'Не удалось загрузить историю');if(!Array.isArray(result.items)||!Number.isInteger(result.total)||!Number.isInteger(result.page)||result.pageSize!==12)throw Error('Некорректный ответ истории');return result;},
 removeRequest:async(id)=>{const result=await post('/remove-request',{id});await refreshStatus();return result;},
 library:async(operation)=>{const result=await post('/library',operation);publish('reference-library-updated',result);return result;},
 upload:async(file)=>{if(file.size>15000000)throw Error('Максимум 15 МБ');const data=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.onerror=()=>reject(Error('Не удалось прочитать изображение'));reader.readAsDataURL(file)});return post('/reference',{name:file.name,data});}
};
// Queue writes are independent. Serialize state writes so old settings cannot overwrite newer edits.
let stateWrites=Promise.resolve();
window.openai={widgetState:saved,setWidgetState:(value)=>{const snapshot=JSON.parse(JSON.stringify(value));window.openai.widgetState=snapshot;try{localStorage.setItem(storageKey,JSON.stringify(snapshot))}catch{}stateWrites=stateWrites.catch(()=>{}).then(()=>post('/state',snapshot));return stateWrites;},sendFollowUpMessage:async(value)=>{let payload;try{payload=JSON.parse(value.prompt.slice(value.prompt.indexOf('\n')+1))}catch{throw Error('Некорректный снимок задания')}if(payload.operation)return window.referenceBrowser.library(payload.operation);const result=await post('/request',value);refreshStatus();return result;}};
refreshStatus();
})();
