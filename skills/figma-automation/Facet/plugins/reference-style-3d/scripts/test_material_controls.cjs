// Exercise the actual controls functions in a small DOM fixture; not visual QA.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),assert=require('node:assert/strict');
const plugin=path.resolve(__dirname,'..');
const html=fs.readFileSync(process.argv[2]||path.join(plugin,'ui/controls.html'),'utf8');
let code=html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
const cards=JSON.parse(fs.readFileSync(path.join(plugin,'assets/materials/catalog.json'),'utf8')).cards;
const catalog=JSON.parse(html.match(/id="r-catalog" type="application\/json">([\s\S]*?)<\/script>/)[1]);
catalog.referenceFacets=JSON.parse(fs.readFileSync(path.join(plugin,'skills/reference-style-3d/references/reference-facets.json'),'utf8'));
catalog.graphics=JSON.parse(fs.readFileSync(path.join(plugin,'skills/reference-style-3d/references/graphics.json'),'utf8'));
catalog.effects=JSON.parse(fs.readFileSync(path.join(plugin,'skills/reference-style-3d/references/effects.json'),'utf8'));
catalog.materialPresets=JSON.parse(fs.readFileSync(path.join(plugin,'skills/reference-style-3d/references/material-presets.json'),'utf8'));
const elements=new Map();function el(id){if(!elements.has(id))elements.set(id,{value:id==='r-topic'?'Тест':'',textContent:'',dataset:{},classList:{remove(){},add(){}},attrs:{},setAttribute(k,v){this.attrs[k]=String(v)},getAttribute(k){return this.attrs[k]},removeAttribute(k){delete this.attrs[k]},focus(){},closest(){return null},showModal(){this.open=true},close(){this.open=false},querySelector(){return el('nested');},replaceChildren(){},addEventListener(type,fn){this.listeners??={};this.listeners[type]=fn},querySelectorAll(){return[];},hidden:true});return elements.get(id);}
el('r-catalog').textContent=JSON.stringify(catalog);el('r-plugin-palettes').textContent='{"palettes":[]}';el('r-material-library').textContent=JSON.stringify({materials:cards});
el('r-reference-library').textContent='{"image":null}';el('r-initial-settings').textContent='{"settings":null}';
const root=el('ri');root.querySelector=selector=>el(selector.slice(1));
const sent=[],saved=[];
const context={document:{getElementById:el,addEventListener(){}},window:{openai:{setWidgetState(s){saved.push(s)},sendFollowUpMessage(s){sent.push(s)}},addEventListener(){}},TextEncoder,console};
code=code.replace(/initPresetCatalog\(\);[\s\S]*?\}\)\(\);/,`globalThis.api={acceptMaterialSets,saveMaterialSet,deleteMaterialSet,loadMaterialSets,get personalMaterialSets(){return personalMaterialSets},resetSettings,undoReset,defaults,restorePresets,referenceLibrary,get activePresetId(){return activePresetId},set activePresetId(value){activePresetId=value},get libraryState(){return {presets,presetItems,favorites:[...favoriteIds],saved,personalMaterialSets}},requestReference,effectSelectionReason,effectConstraint,renderReference,renderFull:render,state,validMaterialIds,toggleMaterial,updateMaterials,submittedSettings,prompt,restore,save,submit,selectedMaterialIds,effectValidationError,normalizeEffects,materialPresets,openMaterials,closeMaterials,setMaterialTab,receiveSnapshot,changed,get dirty(){return dirty}};renderMaterials=()=>{};summary=()=>{};render=()=>{};close=()=>{};})();`);
vm.createContext(context);vm.runInContext(code,context);
(async()=>{const a=context.api, ids=cards.map(c=>c.id);
assert.equal(JSON.stringify(a.materialPresets),JSON.stringify(catalog.materialPresets));assert.ok(a.materialPresets.length>=20);for(const p of a.materialPresets){assert.ok(p.ids.length>=2&&p.ids.length<=12);assert.equal(new Set(p.ids).size,p.ids.length);for(const id of p.ids)assert.ok(ids.includes(id));}
a.openMaterials('cards');assert.equal(el('r-material-dialog').open,true);assert.equal(el('r-material-cards').hidden,false);a.closeMaterials();assert.equal(el('r-material-dialog').open,false);
assert.equal(a.state.materials.mode,'auto');assert.equal(a.state.materials.base,null);
for(const id of ids.slice(0,13))a.toggleMaterial(id);
assert.equal(a.selectedMaterialIds().length,12);assert.equal(a.state.materials.base,ids[0]);assert.match(el('r-material-message').textContent,/12/);
a.updateMaterials([ids[4],ids[0],ids[4],'bad']);assert.equal(a.state.materials.base,ids[4]);assert.equal(a.state.materials.accents.join(','),ids[0]);
const submitted=a.submittedSettings();assert.equal(submitted.settingsVersion,3);for(const old of ['materialIds','metal','pearl','mode','size','objects','detailMode','detail'])assert.equal(old in submitted,false);
const originalColors=JSON.stringify(a.state.colors);a.state.palette='natural';assert.equal('colors' in a.submittedSettings(),false);a.state.palette='custom';assert.equal(JSON.stringify(a.submittedSettings().colors),originalColors);
await a.save();assert.equal(saved[0].modelContent.settings.materials.base,ids[4]);
a.restore({modelContent:{panel:'reference-style-3d-v4',settings:{topic:'Old',materialIds:[ids[3],ids[2]],metal:0,pearl:100,effects:[{id:'fold',strength:70},{id:'melt',strength:70},{id:'levitate',strength:40},{id:'wood',strength:10}]}}});
assert.equal(a.state.materials.base,ids[4]);assert.equal(el('r-snapshot-notice').hidden,false);assert.match(el('r-snapshot-notice').textContent,/не применён/);
a.restore({modelContent:{panel:'reference-style-3d-v6',settings:{settingsVersion:3,topic:'New',materials:{mode:'selected',base:'wood',accents:['paper']},effects:[]}}});assert.equal(a.state.materials.base,'wood');assert.equal(el('r-snapshot-notice').hidden,true);
a.state.effects=[{id:'fold',strength:70,target:''},{id:'melt',strength:70,target:''}];assert.equal(a.effectValidationError(),'');
a.state.effects=[{id:'fold',strength:70,target:''},{id:'levitate',strength:70,target:''}];assert.equal(a.effectValidationError(),'');
a.state.effects=[{id:'wood',strength:0,target:''}];assert.notEqual(a.effectValidationError(),'');
// More than two effects and repeated scopes are retained; invalid identities still block.
const many=['fold','melt','inflate','levitate','cascade'].map(id=>({id,strength:50,target:''}));
a.state.effects=many;assert.equal(a.effectValidationError(),'');assert.equal(a.normalizeEffects([...many,many[0]]).length,many.length);
a.restore({modelContent:{panel:'reference-style-3d-v6',settings:{settingsVersion:3,topic:'Many effects',graphicType:'scene',effects:many}}});assert.equal(a.state.effects.length,5);
for(const invalid of [[...many,many[0]],[{id:'hybrid',strength:50,target:''}],[{id:'fold',strength:101,target:''}]]){a.state.effects=invalid;assert.notEqual(a.effectValidationError(),'');}
a.state.effects=[];a.updateMaterials([]);await a.submit();assert.equal(sent.length,0);assert.match(el('r-status').textContent,/основной материал/);
a.state.materials={mode:'auto',base:null,accents:[]};await a.submit();assert.equal(sent.length,1);const payload=JSON.parse(sent[0].prompt.split('\n')[1]);assert.equal(payload.schemaVersion,1);assert.equal(payload.settings.settingsVersion,3);assert.equal(payload.settings.materials.mode,'auto');assert.equal('metal' in payload.settings,false);
const handleClick=root.listeners.click;const click=button=>handleClick({target:{closest(){return {disabled:false,dataset:{},hasAttribute(){return false},...button}}}});
const before={topic:a.state.topic,graphicType:a.state.graphicType,count:a.state.count,colors:JSON.stringify(a.state.colors)};
for(let i=0;i<a.materialPresets.length;i++){click({dataset:{materialPreset:String(i)},hasAttribute(k){return k==='data-material-preset'}});assert.equal(a.selectedMaterialIds().join(),a.materialPresets[i].ids.join());}
assert.deepEqual({topic:a.state.topic,graphicType:a.state.graphicType,count:a.state.count,colors:JSON.stringify(a.state.colors)},before);
click({id:'r-material-reset'});assert.equal(a.state.materials.mode,'auto');assert.equal(a.selectedMaterialIds().length,0);
a.updateMaterials([ids[0]]);click({id:'r-material-clear'});assert.equal(a.state.materials.mode,'auto');assert.match(el('r-status').textContent,/сброшен/);
click({id:'r-material-open'});assert.equal(el('r-material-dialog').open,true);click({id:'r-material-done'});assert.equal(el('r-material-dialog').open,false);
// Independent snapshots must not inherit values from a prior form.
a.state.avoid='OLD AVOID';a.state.subjects='OLD SUBJECTS';a.state.count=16;a.state.effects=[{id:'fold',strength:50,target:''}];
a.restore({modelContent:{panel:'reference-style-3d-v6',settings:{settingsVersion:3,topic:'Fresh'}}});
assert.equal(a.state.avoid,'');assert.equal(a.state.subjects,'');assert.equal(a.state.count,4);assert.equal(a.state.effects.length,0);
a.restore({modelContent:{panel:'reference-style-3d-v6',settings:{settingsVersion:3,topic:'Safe',effects:[null,{}, {id:'fold',strength:32.7}]}}});
assert.equal(a.state.effects.length,1);assert.equal(a.state.effects[0].strength,33);
a.changed();a.state.topic='Unsaved edit';
assert.equal(a.receiveSnapshot({modelContent:{panel:'reference-style-3d-v6',settings:{settingsVersion:3,topic:'Late old'}}}),false);
assert.equal(a.state.topic,'Unsaved edit');
// A delayed save completion must not mark later edits as saved.
let finish;context.window.openai.setWidgetState=()=>new Promise(resolve=>{finish=resolve});
a.save();await Promise.resolve();a.changed();finish();await Promise.resolve();await Promise.resolve();assert.equal(a.dirty,true);
context.window.openai.setWidgetState=s=>{saved.push(s)};
a.state.graphicType='scene';a.state.detailLevel='minimal';a.state.arrangement='orbit';assert.equal(a.submittedSettings().graphicType,'scene');assert.equal(a.submittedSettings().detailLevel,'minimal');
// Unbound reference intent uses the normal chat action and asks for the image before generation.
a.state.effects=[];a.state.materials={mode:'selected',base:'wood',accents:['paper']};
a.state.reference={facets:['palette','materials','camera'],note:'Блики на предмете справа'};
a.renderFull();assert.equal(el('r-palette-mode').textContent,'Из референса');assert.equal(el('r-whiteBase').disabled,true);
assert.match(el('r-view').innerHTML,/Ракурс: из референса/);
const manualMaterials=JSON.stringify(a.state.materials),manualColors=JSON.stringify(a.state.colors),sentBefore=sent.length;
await a.submit();assert.equal(sent.length,sentBefore+1);assert.equal(html.includes('id="r-fallback"'),false);assert.match(sent.at(-1).prompt,/попроси его прислать до генерации/);assert.match(sent.at(-1).prompt,/продолжи это же задание/);
const refPayload=JSON.parse(sent.at(-1).prompt.split('\n')[1]);assert.deepEqual(Array.from(refPayload.settings.reference.facets),['palette','materials','camera']);assert.equal('image' in refPayload.settings.reference,false);
a.restore({modelContent:{panel:'reference-style-3d-v6',settings:refPayload.settings}});assert.equal(a.state.reference.note,'Блики на предмете справа');
click({id:'r-reference-clear'});assert.equal(a.state.reference.facets.length,0);assert.equal(JSON.stringify(a.state.materials),manualMaterials);assert.equal(JSON.stringify(a.state.colors),manualColors);
assert.equal('reference' in a.submittedSettings(),false);
// Only immutable image metadata belongs in state or messages; previews stay in renderer data.
const boundImage={path:'/test/reference.png',name:'Референс.png',sha256:'a'.repeat(64)};
const thumbnail='data:image/png;base64,preview-only';
a.restore({modelContent:{panel:'reference-style-3d-v6',settings:{...refPayload.settings,reference:{...refPayload.settings.reference,image:{...boundImage,thumbnail}}}}});
assert.equal(JSON.stringify(a.state.reference.image),JSON.stringify(boundImage));assert.equal('thumbnail' in a.state.reference.image,false);
await a.save();assert.equal(JSON.stringify(saved.at(-1).modelContent.settings.reference.image),JSON.stringify(boundImage));assert.ok(!JSON.stringify(saved.at(-1)).includes(thumbnail));
const boundBefore=sent.length;await a.submit();assert.equal(sent.length,boundBefore+1);assert.match(sent.at(-1).prompt,/явно указанное изображение/);
const boundPayload=JSON.parse(sent.at(-1).prompt.split('\n')[1]);assert.deepEqual(boundPayload.settings.reference.image,boundImage);assert.ok(!sent.at(-1).prompt.includes(thumbnail));
assert.equal(JSON.stringify(a.state.materials),manualMaterials);assert.equal(JSON.stringify(a.state.colors),manualColors);
// Clearing borrowed properties keeps the bound image available, but excludes it from generation.
click({id:'r-reference-clear'});assert.equal(a.state.reference.facets.length,0);assert.equal(JSON.stringify(a.state.reference.image),JSON.stringify(boundImage));assert.equal('reference' in a.submittedSettings(),false);
await a.submit();assert.equal('reference' in JSON.parse(sent.at(-1).prompt.split('\n')[1]).settings,false);
// Removing the image keeps selected properties and asks for a replacement on the next send.
a.state.reference.facets=['palette','ornament'];a.state.reference.note='Только мотив';click({id:'r-reference-remove'});
assert.deepEqual(Array.from(a.state.reference.facets),['palette','ornament']);assert.equal(a.state.reference.note,'Только мотив');assert.equal('image' in a.state.reference,false);
assert.equal(JSON.stringify(a.state.colors),manualColors);await a.submit();assert.match(sent.at(-1).prompt,/попроси его прислать до генерации/);
a.state.reference={facets:['composition'],note:''};a.state.effects=[{id:'levitate',strength:50,target:''}];assert.match(a.effectValidationError(),/референса/);
a.state.reference={facets:['composition','effects'],note:''};assert.equal(a.effectValidationError(),'');
// Reference structure owns the subject count; dormant icon/object must not erase placement.
for(const graphicType of ['icon','object']){
const snapshot={modelContent:{panel:'reference-style-3d-v6',settings:{settingsVersion:3,topic:'Reference layout',graphicType,arrangement:'orbit',reference:{facets:['structure'],note:''}}}};
a.restore(snapshot);assert.equal(a.state.arrangement,'orbit');assert.equal(a.submittedSettings().arrangement,'orbit');
// Deselecting complexity returns to the manual single-subject type.
root.listeners.change({target:{dataset:{referenceFacet:'structure'},checked:false}});
assert.equal(a.state.graphicType,graphicType);assert.equal(a.state.arrangement,'auto');assert.equal(a.submittedSettings().arrangement,'auto');
// Resetting all reference facets follows the same normalization.
a.restore(snapshot);assert.equal(a.state.arrangement,'orbit');click({id:'r-reference-clear'});
assert.equal(a.state.arrangement,'auto');assert.equal('reference' in a.submittedSettings(),false);
// A manual single-subject snapshot still normalizes a stale non-auto placement.
a.restore({modelContent:{panel:'reference-style-3d-v6',settings:{...snapshot.modelContent.settings,reference:{facets:[],note:''}}}});
assert.equal(a.state.arrangement,'auto');
}
// Clearing reference guidance must preserve valid placement for multi-subject types.
a.restore({modelContent:{panel:'reference-style-3d-v6',settings:{settingsVersion:3,topic:'Group layout',graphicType:'group',arrangement:'orbit',reference:{facets:['structure'],note:''}}}});
click({id:'r-reference-clear'});assert.equal(a.state.arrangement,'orbit');
// Multi-subject types keep placement and independent detail; a single-subject type normalizes it.
a.state.detailLevel='rich';a.state.colors=['#2455F5','#FFFFFF'];const switchColors=JSON.stringify(a.state.colors);
click({dataset:{graphic:'scene'}});assert.equal(a.state.arrangement,'orbit');assert.equal(a.state.detailLevel,'rich');
click({dataset:{graphic:'group'}});assert.equal(a.state.arrangement,'orbit');assert.equal(a.state.detailLevel,'rich');
click({dataset:{graphic:'icon'}});assert.equal(a.state.arrangement,'auto');assert.equal(a.state.detailLevel,'rich');assert.equal(JSON.stringify(a.state.colors),switchColors);
// A missing host does not turn generation into a copy/paste flow.
const send=context.window.openai.sendFollowUpMessage,sendCount=sent.length;
delete context.window.openai.sendFollowUpMessage;el('r-fallback').hidden=true;el('r-prompt').value='';
await a.submit();assert.equal(sent.length,sendCount);assert.equal(html.includes('id="r-fallback"'),false);assert.equal(el('r-prompt').value,'');assert.match(el('r-status').textContent,/открыть её в чате/);
// Failed send restores the button; the same settings can be retried successfully.
context.window.openai.sendFollowUpMessage=async()=>{throw new Error('Host unavailable')};
const retrySettings=JSON.stringify(a.submittedSettings());await a.submit();assert.equal(el('r-submit').disabled,false);assert.match(el('r-status').textContent,/Нажмите «Создать» ещё раз/);assert.equal(html.includes('id="r-fallback"'),false);
context.window.openai.sendFollowUpMessage=send;await a.submit();assert.equal(sent.length,sendCount+1);assert.equal(JSON.stringify(JSON.parse(sent.at(-1).prompt.split('\n')[1]).settings),retrySettings);assert.equal(el('r-submit').disabled,false);
// Successful or failed sends must not erase a synchronous save warning.
delete context.window.openai.setWidgetState;await a.submit();assert.match(el('r-status').textContent,/Подтвердите отправку/);assert.match(el('r-status').textContent,/Сохранение недоступно/);
context.window.openai.sendFollowUpMessage=async()=>{throw new Error('Host unavailable')};await a.submit();assert.match(el('r-status').textContent,/Нажмите «Создать» ещё раз/);assert.match(el('r-status').textContent,/Сохранение недоступно/);
context.window.openai.sendFollowUpMessage=send;context.window.openai.setWidgetState=s=>{saved.push(s)};
// Requesting an attachment snapshots settings before the native chat request.
a.state.topic='Saved before attachment';a.state.reference={facets:['palette'],note:'One accent',image:boundImage};
const metadataBefore=JSON.stringify(a.state.reference.image),calls=[];
context.window.openai.setWidgetState=s=>{calls.push('save');saved.push(s)};
context.window.openai.sendFollowUpMessage=s=>{calls.push('send');sent.push(s)};
await a.requestReference();assert.deepEqual(calls,['save','send']);
const attach=sent.at(-1);assert.equal(attach.title,'Добавить референс');assert.match(attach.prompt,/Генерацию не запускай/);
const attachSettings=JSON.parse(attach.prompt.split('\n')[1]).settings;
assert.equal(attachSettings.topic,a.state.topic);assert.equal('image' in attachSettings.reference,false);
assert.equal(JSON.stringify(a.state.reference.image),metadataBefore);assert.equal(attachSettings.reference.facets[0],'palette');
// Async save failure survives native send success; a superseded failure cannot overwrite a newer save.
a.state.reference={facets:[],note:''};a.state.effects=[];a.state.materials={mode:'auto',base:null,accents:[]};
let sendResolve;context.window.openai.sendFollowUpMessage=()=>new Promise(resolve=>{sendResolve=resolve});
context.window.openai.setWidgetState=()=>Promise.reject(new Error('save failed'));
const pendingSend=a.submit();await new Promise(setImmediate);
assert.match(el('r-status').textContent,/Не удалось сохранить/);sendResolve();await pendingSend;
assert.match(el('r-status').textContent,/Подтвердите/);assert.match(el('r-status').textContent,/Не удалось сохранить/);
let oldReject;context.window.openai.setWidgetState=()=>new Promise((_,reject)=>{oldReject=reject});a.save();
context.window.openai.setWidgetState=()=>Promise.resolve();a.save();await new Promise(setImmediate);
el('r-status').textContent='Newer successful action';oldReject(new Error('old save'));
await new Promise(setImmediate);assert.equal(el('r-status').textContent,'Newer successful action');
assert.equal(el('r-save-label').textContent,'Сохранено');
// Incompatible effects are explained before selection; parameters are not silently changed.
a.state.effects=[];a.state.graphicType='scene';a.state.arrangement='orbit';
const levitate=catalog.effects.find(e=>e.id==='levitate'),nest=catalog.effects.find(e=>e.id==='nest');
assert.equal(a.effectSelectionReason(levitate),'');assert.match(a.effectConstraint(levitate),/расположение/);a.state.effects=[{id:'levitate',strength:60,target:''}];assert.equal(a.effectValidationError(),'');a.state.effects=[];
a.state.arrangement='auto';a.state.reference={facets:['composition'],note:''};assert.match(a.effectSelectionReason(levitate),/референса/);
a.state.reference={facets:[],note:''};a.state.graphicType='icon';assert.equal(a.effectSelectionReason(nest),'');assert.match(a.effectConstraint(nest),/слабо/);a.state.effects=[{id:'nest',strength:60,target:''}];assert.equal(a.effectValidationError(),'');a.state.effects=[];
a.state.graphicType='scene';assert.equal(a.effectSelectionReason(nest),'');
delete context.window.openai.sendFollowUpMessage;await a.requestReference();assert.match(el('r-status').textContent,/в чате Codex/);assert.equal(html.includes('id="r-fallback"'),false);
context.window.openai.sendFollowUpMessage=()=>Promise.reject(new Error('attachment request failed'));await a.requestReference();assert.match(el('r-status').textContent,/Не удалось запросить референс/);assert.equal(el('r-reference-add').disabled,false);
context.window.openai.sendFollowUpMessage=send;context.window.openai.setWidgetState=s=>{saved.push(s)};
// Renderer-bound settings/images outrank late host snapshots. Ordinary clean forms still restore.
const explicitSettings={settingsVersion:3,topic:'Explicit renderer snapshot',graphicType:'group',arrangement:'orbit'};
for(const binding of ['settings','image','none']){
el('r-initial-settings').textContent=JSON.stringify({settings:binding==='settings'?explicitSettings:null});
el('r-reference-library').textContent=JSON.stringify({image:binding==='image'?{...boundImage,thumbnail}:null});
const boot={document:context.document,window:{openai:{},addEventListener(){}},TextEncoder,console};vm.createContext(boot);vm.runInContext(code,boot);
boot.api.restore({modelContent:{panel:'reference-style-3d-v6',settings:{...explicitSettings,...(binding==='image'?{reference:{facets:['materials'],note:'',image:{...boundImage,thumbnail}}}:{})}}});
const applied=boot.api.receiveSnapshot({modelContent:{panel:'reference-style-3d-v6',settings:{settingsVersion:3,topic:'Late unrelated form'}}});
assert.equal(applied,binding==='none');assert.equal(boot.api.state.topic,binding==='none'?'Late unrelated form':explicitSettings.topic);
if(binding==='image'){assert.equal(JSON.stringify(boot.api.state.reference.image),JSON.stringify(boundImage));assert.ok(!JSON.stringify(boot.api.submittedSettings()).includes(thumbnail));}
}
// Warnings do not prevent a real send or silently normalize the requested effect combination.
context.window.openai.sendFollowUpMessage=s=>{sent.push(s)};
a.state.materials={mode:'auto',base:null,accents:[]};a.state.reference={facets:[],note:''};a.state.topic='Effects warnings';
for(const graphicType of ['scene','icon']){
a.state.graphicType=graphicType;a.state.arrangement=graphicType==='scene'?'diagonal':'auto';a.state.effects=many;
const expected=JSON.stringify(a.submittedSettings()),count=sent.length;await a.submit();assert.equal(sent.length,count+1);assert.equal(JSON.stringify(JSON.parse(sent.at(-1).prompt.split('\n')[1]).settings),expected);
}
a.state.effects=[...many,many[0]];const blockedCount=sent.length;await a.submit();assert.equal(sent.length,blockedCount);assert.match(el('r-status').textContent,/повторный/);
// Reset is a browser draft operation: libraries survive and Undo restores the exact draft and preset.
context.window.referenceBrowser={};context.window.openai.setWidgetState=s=>{saved.push(s);return Promise.resolve()};
a.state.topic='Before reset';a.state.subjects='One\nTwo';a.state.avoid='No letters';a.state.reference={facets:['palette'],note:'Keep this',image:boundImage};a.referenceLibrary.image={...boundImage,thumbnail};a.state.effects=[{id:'fold',strength:67,target:'edge'}];a.state.materials={mode:'selected',base:'wood',accents:['paper']};
a.restorePresets({privateContent:{activePresetId:null,presets:[{id:'kept',name:'Keep preset',settings:{}}]}});
a.activePresetId='kept-active-preset';
const exactDraft=JSON.stringify(a.state),libraryBefore=JSON.stringify(a.libraryState),imageBefore=JSON.stringify(a.referenceLibrary.image),activeBefore=a.activePresetId;
a.resetSettings();await new Promise(setImmediate);
assert.equal(JSON.stringify(a.state),JSON.stringify({...a.defaults,topic:''}));assert.equal(a.activePresetId,null);assert.equal(a.referenceLibrary.image,null);assert.equal(el('r-undo-reset').hidden,false);assert.equal(saved.at(-1).modelContent.settings.topic,'');assert.equal('image' in saved.at(-1).modelContent.settings.reference,false);assert.equal(JSON.stringify(a.libraryState),libraryBefore);
a.undoReset();await new Promise(setImmediate);
assert.equal(JSON.stringify(a.state),exactDraft);assert.equal(a.activePresetId,activeBefore);assert.equal(JSON.stringify(a.referenceLibrary.image),imageBefore);assert.equal(JSON.stringify(saved.at(-1).modelContent.settings),exactDraft);assert.equal(JSON.stringify(a.libraryState),libraryBefore);assert.equal(el('r-undo-reset').hidden,true);
// Explicit removal persists an empty binding. Reloading its snapshot cannot resurrect the image.
click({id:'r-reference-remove'});await new Promise(setImmediate);assert.equal('image' in saved.at(-1).modelContent.settings.reference,false);assert.equal(a.referenceLibrary.image,null);
const removedSnapshot=JSON.parse(JSON.stringify(saved.at(-1)));a.restore(removedSnapshot);assert.equal('image' in a.state.reference,false);
assert.match(html,/!restoredDraft&&!initialSettings.settings&&imageMetadata\(referenceLibrary.image\)/);
click({id:'r-reference-clear'});await new Promise(setImmediate);assert.equal(saved.at(-1).modelContent.settings.reference.facets.length,0);a.restore(saved.at(-1));assert.equal(a.state.reference.facets.length,0);
// A failed reset save remains recoverable and does not claim persistence.
context.window.openai.setWidgetState=()=>Promise.reject(new Error('offline'));a.resetSettings();await new Promise(setImmediate);assert.equal(a.dirty,true);assert.equal(el('r-save-label').textContent,'Не удалось сохранить');assert.equal(el('r-undo-reset').hidden,false);assert.match(el('r-status').textContent,/Не удалось сохранить/);
// Personal material sets save the exact ordered materials, apply without altering other axes, and survive reset.
const libraryCalls=[],setRecord={id:'glass-metal',name:'Стекло и металл',materials:{mode:'selected',base:'wood',accents:['paper','leather']}};
context.window.referenceBrowser.library=async operation=>{libraryCalls.push(operation);return {ok:true,materialSets:operation.action==='delete_material_set'?[]:[setRecord]}};
await a.loadMaterialSets();assert.equal(a.personalMaterialSets[0].name,setRecord.name);assert.equal(libraryCalls.at(-1).action,'load_material_sets');
a.state.materials={mode:'selected',base:'paper',accents:['wood']};a.state.topic='Preserve topic';const nonMaterials={...JSON.parse(JSON.stringify(a.state))};delete nonMaterials.materials;
click({dataset:{materialSet:setRecord.id}});assert.equal(JSON.stringify(a.state.materials),JSON.stringify(setRecord.materials));const afterApply={...JSON.parse(JSON.stringify(a.state))};delete afterApply.materials;assert.equal(JSON.stringify(afterApply),JSON.stringify(nonMaterials));
el('r-material-set-name').value='My exact set';await a.saveMaterialSet();assert.equal(libraryCalls.at(-1).action,'save_material_set');assert.equal(JSON.stringify(libraryCalls.at(-1).materials),JSON.stringify(setRecord.materials));assert.equal(libraryCalls.at(-1).name,'My exact set');assert.equal(el('r-material-save-form').hidden,true);
const setDraft=JSON.stringify(a.state);await a.deleteMaterialSet(setRecord.id);assert.equal(a.personalMaterialSets.length,0);assert.equal(JSON.stringify(a.state),setDraft);assert.equal(libraryCalls.at(-1).id,setRecord.id);
a.acceptMaterialSets([setRecord]);context.window.referenceBrowser.library=async()=>{throw new Error('Набор с таким именем уже существует')};el('r-material-set-name').value='Duplicate';el('r-material-save-form').hidden=false;await a.saveMaterialSet();assert.equal(el('r-material-save-form').hidden,false);assert.match(el('r-material-set-error').textContent,/уже существует/);assert.equal(JSON.stringify(a.state),setDraft);assert.equal(a.personalMaterialSets.length,1);
context.window.openai.setWidgetState=()=>Promise.resolve();a.resetSettings();assert.equal(a.personalMaterialSets.length,1);a.undoReset();assert.equal(JSON.stringify(a.state),setDraft);
console.log('PASS UI: material/palette controls, bound and unbound reference sends, metadata-only snapshots, reference reset/removal, independent graphic axes, renderer precedence, no-host/error/retry handling and preserved save warnings.');
})().catch(e=>{console.error(e);process.exitCode=1;});
