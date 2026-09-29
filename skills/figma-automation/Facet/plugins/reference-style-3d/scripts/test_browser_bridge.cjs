const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
(async()=>{
const source=fs.readFileSync(require('node:path').join(__dirname,'../ui/browser-bridge.js'),'utf8').replace('__SESSION_TOKEN__','"test"').replace('__SESSION_KEY__','"test"').replace('__SERVER_RESTORE__','{"state":null}');
let resolveFetch,calls=0,timers=0;const events=[];
const context={AbortController,window:{dispatchEvent:e=>events.push(e)},document:{hidden:false},localStorage:{getItem:()=>null},CustomEvent:class{constructor(type,options){this.type=type;this.detail=options.detail}},fetch:()=>{calls++;return new Promise(resolve=>resolveFetch=resolve)},setTimeout:()=>++timers,clearTimeout:()=>{}};
vm.runInNewContext(source,context);
const first=context.window.referenceBrowser.refreshStatus(),second=context.window.referenceBrowser.refreshStatus();assert.equal(first,second);assert.equal(calls,1);
resolveFetch({ok:true,json:async()=>({requests:[{id:'one'}],listener:{waiting:true}})});await first;
assert.equal(context.window.referenceBrowser.queue.requests[0].id,'one');assert.equal(timers,2);
const next=context.window.referenceBrowser.refreshStatus();assert.equal(calls,2);resolveFetch({ok:false});await next;
assert.equal(context.window.referenceBrowser.queue.offline,true);assert.equal(context.window.referenceBrowser.queue.listener.waiting,false);assert.equal(context.window.referenceBrowser.queue.requests[0].id,'one');assert.equal(events.length,2);
// Tab preference uses its own key and never persists a draft. Disconnect is authenticated and refreshes status.
const storage=new Map([['reference-style-settings:test:panel','history']]),requests=[];
const fresh={AbortController,window:{dispatchEvent(){}},document:{hidden:false},localStorage:{getItem:key=>storage.get(key)||null,setItem:(key,value)=>storage.set(key,value)},CustomEvent:context.CustomEvent,fetch:async(url,options)=>{requests.push({url,options});return {ok:true,json:async()=>url==='/disconnect'?{ok:true,consumer:{active:false}}:{requests:[],listener:{waiting:false},consumer:{active:false}}}},setTimeout:()=>1,clearTimeout(){}};
vm.runInNewContext(source,fresh);await fresh.window.referenceBrowser.refreshStatus();assert.equal(fresh.window.referenceBrowser.panel,'history');
fresh.window.referenceBrowser.setPanel('presets');assert.equal(storage.get('reference-style-settings:test:panel'),'presets');assert.equal(storage.has('reference-style-settings:test'),false);assert.equal(requests.some(call=>call.url==='/state'),false);
await fresh.window.referenceBrowser.disconnect();const disconnect=requests.find(call=>call.url==='/disconnect');assert.equal(disconnect.options.method,'POST');assert.equal(disconnect.options.headers['X-Session-Token'],'test');assert.equal(disconnect.options.body,'{}');assert.equal(requests.at(-1).url,'/status');
// A timed-out request preserves all cached data; a late response cannot replace recovery.
const timersById=new Map(),pending=[];let timerId=0;
const hanging={AbortController,window:{dispatchEvent(){}},document:{hidden:false},localStorage:{getItem:()=>null},CustomEvent:context.CustomEvent,
 fetch:(url,options)=>new Promise(resolve=>pending.push({resolve,signal:options.signal})),setTimeout:(fn,ms)=>{const id=++timerId;timersById.set(id,{fn,ms});return id},clearTimeout:id=>timersById.delete(id)};
vm.runInNewContext(source,hanging);const bridge=hanging.window.referenceBrowser;
const initial=bridge.refreshStatus();pending[0].resolve({ok:true,json:async()=>({requests:[{id:'cached'}],historyRevision:'revision-1',listener:{waiting:true}})});await initial;
const stalled=bridge.refreshStatus();const timeout=[...timersById.values()].find(timer=>timer.ms===10000);assert.ok(timeout);timeout.fn();await stalled;
assert.equal(pending[1].signal.aborted,true);assert.equal(bridge.queue.offline,true);assert.equal(bridge.queue.requests[0].id,'cached');assert.equal(bridge.queue.historyRevision,'revision-1');
const poll=[...timersById.values()].find(timer=>timer.ms===2500);assert.ok(poll);poll.fn();const recovered=bridge.refreshStatus();pending[2].resolve({ok:true,json:async()=>({requests:[{id:'fresh'}],historyRevision:'revision-2',listener:{waiting:true}})});await recovered;
pending[1].resolve({ok:true,json:async()=>({requests:[{id:'stale'}]})});await Promise.resolve();await Promise.resolve();assert.equal(bridge.queue.requests[0].id,'fresh');assert.equal(bridge.queue.offline,undefined);
console.log('PASS browser bridge: single-flight reads, authenticated disconnect, timeout recovery, preserved jobs/history and rejected late response.');
})().catch(error=>{console.error(error);process.exitCode=1});
