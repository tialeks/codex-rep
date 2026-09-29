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
const elements=new Map();function el(id){if(!elements.has(id))elements.set(id,{value:id==='r-topic'?'Тест':'',textContent:'',dataset:{},classList:{remove(){},add(){}},attrs:{},setAttribute(k,v){this.attrs[k]=String(v)},getAttribute(k){return this.attrs[k]},removeAttribute(k){delete this.attrs[k]},focus(){},closest(){return null},showModal(){this.open=true},close(){this.open=false},querySelector(){return el('nested');},replaceChildren(){},addEventListener(type,fn){this.listeners??={};this.listeners[type]=fn},querySelectorAll(){return[];},hidden:true});return elements.get(id);}
el('r-catalog').textContent=JSON.stringify(catalog);el('r-plugin-palettes').textContent='{"palettes":[]}';el('r-material-library').textContent=JSON.stringify({materials:cards});
el('r-reference-library').textContent='{"image":null}';el('r-initial-settings').textContent='{"settings":null}';
const root=el('ri');root.querySelector=selector=>el(selector.slice(1));
const sent=[],saved=[];
const context={document:{getElementById:el,addEventListener(){}},window:{openai:{setWidgetState(s){saved.push(s)},sendFollowUpMessage(s){sent.push(s)}},addEventListener(){}},TextEncoder,console};
const book={id:'sample',name:'Керамика и лента',source:'collection',settings:{settingsVersion:3,graphicType:'object',detailLevel:'minimal',count:9,camera:'side',shot:'wide',creativity:5,whiteBase:false,arrangement:'auto',background:'transparent',palette:'natural',effects:[{id:'bend',strength:70,target:''}],materials:{mode:'selected',base:'ceramic',accents:['silver-satin']},recognizable:true}};
el('r-preset-library').textContent=JSON.stringify({loaded:true,presets:[book,{...book,id:'personal',name:'Мой набор',source:'personal',settings:{...book.settings,graphicType:'scene',detailLevel:'rich',palette:'custom',colors:['#123456','#ABCDEF'],effects:[]}}],favorites:['sample']});
code=code.replace(/initPresetCatalog\(\);[\s\S]*?\}\)\(\);/,`globalThis.api={state,showPanel,isHistoryView,historyState,repeatHistory,applyPreset,renderPresetGrid,presetView,presetRequest,favoritePreset,currentFavorite,submittedSettings,restorePresets};render=()=>{};close=()=>{};summary=()=>{};})();`);
vm.createContext(context);vm.runInContext(code,context);
(async()=>{const a=context.api;
a.state.topic='Новая тема';a.state.subjects='Мои предметы';a.state.avoid='Без букв';a.state.reference={facets:['palette','camera'],note:'Перенос',image:{path:'/other.png',name:'Другой',sha256:'a'.repeat(64)}};a.state.materials={mode:'selected',base:'wood',accents:['paper']};
a.applyPreset('sample');
assert.equal(a.state.topic,'Новая тема');assert.equal(a.state.subjects,'Мои предметы');assert.equal(a.state.avoid,'Без букв');
assert.equal(a.state.reference.facets.length,0);assert.equal(a.state.reference.image,undefined);
for(const key of ['camera','shot','graphicType','detailLevel','count','creativity','background','palette'])assert.equal(a.state[key],book.settings[key],key);
assert.equal(JSON.stringify(a.state.materials),JSON.stringify(book.settings.materials));assert.equal(JSON.stringify(a.state.effects),JSON.stringify(book.settings.effects));
assert.equal(el('r-settings-panel').hidden,false);assert.equal(el('r-generator-footer').hidden,false);assert.equal('colors' in a.submittedSettings(),false);
a.renderPresetGrid();assert.match(el('r-preset-count').textContent,/2/);
el('r-filter-detail').value='rich';a.renderPresetGrid();assert.match(el('r-preset-count').textContent,/1/);assert.ok(el('r-preset-grid').innerHTML.includes('Мой набор'));
el('r-filter-detail').value='';el('r-filter-effect').value='none';a.renderPresetGrid();assert.match(el('r-preset-count').textContent,/1/);
el('r-filter-effect').value='';el('r-filter-shot').value='close';a.renderPresetGrid();assert.equal(el('r-preset-empty').hidden,false);
el('r-filter-shot').value='';a.presetView.scope='favorites';a.renderPresetGrid();assert.ok(el('r-preset-grid').innerHTML.includes('Керамика и лента'));assert.ok(!el('r-preset-grid').innerHTML.includes('Мой набор'));
a.presetView.scope='personal';a.renderPresetGrid();assert.ok(el('r-preset-grid').innerHTML.includes('Мой набор'));
// Reload must restore the same scope in the visible filter and the catalog rows.
a.restorePresets({privateContent:{catalogView:{scope:'favorites'}}});
assert.equal(el('r-filter-scope').value,'favorites');assert.equal(a.presetView.scope,'favorites');
assert.ok(el('r-preset-grid').innerHTML.includes('Керамика и лента'));assert.ok(!el('r-preset-grid').innerHTML.includes('Мой набор'));
a.restorePresets({privateContent:{catalogView:{scope:'all'}}});
assert.equal(el('r-filter-scope').value,'all');assert.match(el('r-preset-count').textContent,/2/);
const stateBefore=JSON.stringify(a.state);context.window.openai.sendFollowUpMessage=()=>Promise.reject(new Error('offline'));await a.favoritePreset('sample');assert.equal(a.currentFavorite('sample'),true);assert.match(el('r-preset-library-status').textContent,/Не удалось/);assert.equal(JSON.stringify(a.state),stateBefore);
context.window.openai.sendFollowUpMessage=s=>{sent.push(s);return Promise.resolve()};await a.favoritePreset('sample');assert.equal(a.currentFavorite('sample'),false);assert.match(el('r-preset-library-status').textContent,/после выполнения/);
const request=JSON.parse(sent.at(-1).prompt.split('\n')[1]);assert.equal(request.operation.action,'set_favorite');assert.equal(request.operation.id,'sample');assert.equal(request.operation.favorite,false);assert.equal(request.operation.page,1);assert.equal(request.settings.topic,'Новая тема');assert.ok(!sent.at(-1).prompt.includes('thumbnail'));
delete context.window.openai.sendFollowUpMessage;assert.equal(await a.presetRequest({action:'save_generation_preset'}),false);assert.match(el('r-preset-library-status').textContent,/в чате Codex/);
// Top-level navigation keeps the draft and separates history from catalog filters.
context.window.referenceBrowser={history:async()=>({items:[],total:0,page:1,pageSize:12})};
a.historyState.loaded=true;
const draft=JSON.stringify(a.state),catalogPage=a.presetView.page;
a.showPanel('history');assert.equal(a.isHistoryView(),true);assert.equal(el('r-generator-footer').hidden,true);assert.equal(el('r-history-tab').attrs['aria-selected'],'true');
a.showPanel('presets');assert.equal(a.isHistoryView(),false);assert.equal(a.presetView.page,catalogPage);
a.showPanel('settings');assert.equal(el('r-generator-footer').hidden,false);assert.equal(JSON.stringify(a.state),draft);
// History restores the verified server snapshot, not the old archived reference path.
const restored={...book.settings,topic:'Original theme',count:9,reference:{facets:['lighting'],note:'Soft',image:{path:'/new-session/references/image.png',name:'Light',sha256:'a'.repeat(64)}}};
a.historyState.items=[{id:'history',settings:{...restored,topic:'Stale local topic'}}];
context.window.referenceBrowser.repeatHistory=async id=>{assert.equal(id,'history');return {settings:restored,referenceImage:{...restored.reference.image,thumbnail:'data:image/png;base64,AAAA'}}};
await a.repeatHistory('history');assert.equal(a.state.topic,'Original theme');assert.equal(a.state.count,9);assert.equal(a.state.reference.image.path,restored.reference.image.path);assert.equal(el('r-generator-footer').hidden,false);
const beforeFailure=JSON.stringify(a.state);context.window.referenceBrowser.repeatHistory=async()=>{throw Error('Archive binding invalid')};await a.repeatHistory('history');assert.equal(JSON.stringify(a.state),beforeFailure);assert.match(el('r-status').textContent,/Archive binding invalid/);
console.log('PASS presets: exact parameter application, preserved subject, cleared reference, independent filters, pending favorites and failed-send rollback.');
})().catch(e=>{console.error(e);process.exitCode=1});
