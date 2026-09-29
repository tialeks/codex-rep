// Real Python page/filter payloads exercised through actual UI handlers; not visual QA.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),assert=require('node:assert/strict'),{spawnSync}=require('node:child_process');
const plugin=path.resolve(__dirname,'..');
const html=fs.readFileSync(process.argv[2]||path.join(plugin,'ui/controls.html'),'utf8');
const backend=spawnSync(process.env.PYTHON||'python3',['-c',String.raw`
import json,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,sys.argv[1])
import presets
settings=dict(settingsVersion=3,graphicType='scene',detailLevel='rich',count=9,camera='side',shot='wide',creativity=5,whiteBase=False,arrangement='depth',background='white',palette='natural',effects=[],materials=dict(mode='auto',base=None,accents=[]),recognizable=True)
rows=[dict(id='p'+str(i),name='Preset '+str(i),source='collection',settings=dict(settings,graphicType='object' if i<6 else 'scene'),preview='previews/'+'a'*64+'.webp',imageSha256='b'*64) for i in range(19)]
with patch.object(presets,'read_store',return_value=dict(schemaVersion=1,presets=rows,favorites=['p12'])):
    pages=[presets.public_library(Path('/tmp/paged-presets-fixture'),page=n,filters={'type':'scene'}) for n in (1,2,3)]
    pages.append(presets.public_library(Path('/tmp/paged-presets-fixture'),page=1,filters={'search':'missing'}))
print(json.dumps(pages))
`,__dirname],{encoding:'utf8',env:{...process.env,PYTHONDONTWRITEBYTECODE:'1'}});
assert.equal(backend.status,0,backend.stderr);
const pages=JSON.parse(backend.stdout);
function fixture(library){
 const elements=new Map();
 function el(id){if(!elements.has(id))elements.set(id,{id,value:id==='r-topic'?'Тема пользователя':'',textContent:'',dataset:{},classList:{remove(){},add(){}},attrs:{},disabled:false,setAttribute(k,v){this.attrs[k]=String(v)},getAttribute(k){return this.attrs[k]},hasAttribute(k){return Object.hasOwn(this.attrs,k)},removeAttribute(k){delete this.attrs[k]},focus(){},closest(selector){return selector==='button'?this:null},showModal(){this.open=true},close(){this.open=false},querySelector(){return el('nested')},replaceChildren(){},addEventListener(type,fn){this.listeners??={};this.listeners[type]=fn},querySelectorAll(){return[]},hidden:true});return elements.get(id);}
 const catalog=JSON.parse(html.match(/id="r-catalog" type="application\/json">([\s\S]*?)<\/script>/)[1]);
 const refs=path.join(plugin,'skills/reference-style-3d/references');
 for(const [key,file] of [['referenceFacets','reference-facets'],['graphics','graphics'],['effects','effects']])catalog[key]=JSON.parse(fs.readFileSync(path.join(refs,file+'.json'),'utf8'));
 el('r-catalog').textContent=JSON.stringify(catalog);
 el('r-plugin-palettes').textContent='{"palettes":[]}';
 el('r-material-library').textContent=JSON.stringify({materials:JSON.parse(fs.readFileSync(path.join(plugin,'assets/materials/catalog.json'),'utf8')).cards});
 el('r-reference-library').textContent='{"image":null}';el('r-initial-settings').textContent='{"settings":null}';
 el('r-preset-library').textContent=JSON.stringify(library);
 const root=el('ri');root.querySelector=selector=>el(selector.slice(1));
 const sent=[];
 const context={document:{getElementById:el,addEventListener(){}},window:{openai:{setWidgetState(){},sendFollowUpMessage(message){sent.push(message);return Promise.resolve()}},addEventListener(){}},TextEncoder,console};
 let code=html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
 code=code.replace(/initPresetCatalog\(\);[\s\S]*?\}\)\(\);/,`globalThis.api={renderPresetGrid,state,presetView};render=()=>{};close=()=>{};summary=()=>{};initPresetCatalog();for(const key of filterKeys)$('filter-'+key).value=presetLibrary.filters?.[key]||(key==='scope'?'all':'');$('preset-search').value=presetLibrary.filters?.search||'';renderPresetGrid();})();`);
 vm.createContext(context);vm.runInContext(code,context);
 return {el,root,sent,context,api:context.api,click:async id=>root.listeners.click({target:el(id)}),request:()=>JSON.parse(sent.at(-1).prompt.split('\n')[1])};
}
(async()=>{
 const f=fixture(pages[1]),{el}=f;
 assert.equal(el('r-preset-count').textContent,'Пресеты: 13');
 assert.equal(el('r-preset-page').textContent,'2 / 3');
 assert.equal(el('r-filter-type').value,'scene');
 assert.equal(el('r-preset-prev').disabled,false);assert.equal(el('r-preset-next').disabled,false);
 const grid=el('r-preset-grid').innerHTML;
 assert.equal((grid.match(/class="preset-card"/g)||[]).length,6);
 for(const row of pages[1].presets)assert.ok(grid.includes('data-apply-preset="'+row.id+'"'));
 assert.ok(!grid.includes('data-apply-preset="p6"'));
 await f.click('r-preset-next');assert.equal(f.request().operation.page,3);
 assert.deepEqual(f.request().operation.filters,pages[1].filters);
 assert.equal(f.request().operation.action,'load_preset_library');
 await f.click('r-preset-prev');assert.equal(f.request().operation.page,1);
 assert.equal(el('r-preset-page').textContent,'2 / 3','Sending a request must not pretend the new page arrived');
 el('r-filter-detail').value='minimal';f.root.listeners.change({target:el('r-filter-detail')});
 el('r-preset-search').value='A result outside this page';f.root.listeners.input({target:el('r-preset-search')});
 assert.equal(el('r-preset-grid').innerHTML,grid,'Pending filters must not reduce the loaded page locally');
 assert.equal(el('r-preset-count').textContent,'Пресеты: 13');
 assert.equal(el('r-preset-empty').hidden,true);
 assert.match(el('r-preset-library-status').textContent,/Показать/);
 assert.equal(el('r-preset-prev').disabled,true);assert.equal(el('r-preset-next').disabled,true);
 const before=f.sent.length;await f.click('r-preset-next');assert.equal(f.sent.length,before,'Disabled page navigation sends nothing');
 await f.click('r-preset-search-go');
 assert.equal(f.request().operation.page,1);assert.equal(f.request().operation.filters.detail,'minimal');assert.equal(f.request().operation.filters.search,'A result outside this page');
 assert.equal(f.request().settings.topic,'Тема пользователя');assert.ok(!f.sent.at(-1).prompt.includes('thumbnail'));
 let prevented=false;f.root.listeners.keydown({target:el('r-preset-search'),key:'Enter',preventDefault(){prevented=true}});await new Promise(resolve=>setImmediate(resolve));
 assert.equal(prevented,true);assert.equal(f.request().operation.page,1);
 // Favorites persist the displayed page's applied filters, not edits still pending.
 const heart=el('test-heart');heart.dataset.favoritePreset='p12';await f.click('test-heart');
 assert.equal(f.request().operation.action,'set_favorite');assert.equal(f.request().operation.page,2);
 assert.deepEqual(f.request().operation.filters,pages[1].filters);
 await f.click('r-filter-reset');assert.equal(f.request().operation.page,1);
 assert.equal(f.request().operation.filters.scope,'all');assert.ok(Object.entries(f.request().operation.filters).every(([k,v])=>k==='scope'||v===''));
 const first=fixture(pages[0]);assert.equal(first.el('r-preset-prev').disabled,true);assert.equal(first.el('r-preset-next').disabled,false);
 const last=fixture(pages[2]);assert.equal(last.el('r-preset-page').textContent,'3 / 3');assert.equal(last.el('r-preset-next').disabled,true);assert.equal(last.el('r-preset-prev').disabled,false);assert.equal((last.el('r-preset-grid').innerHTML.match(/class="preset-card"/g)||[]).length,1);
 const empty=fixture(pages[3]);assert.equal(empty.el('r-preset-count').textContent,'Пресеты: 0');assert.equal(empty.el('r-preset-page').textContent,'1 / 1');assert.equal(empty.el('r-preset-empty').hidden,false);assert.equal(empty.el('r-preset-prev').disabled,true);assert.equal(empty.el('r-preset-next').disabled,true);
 console.log('PASS paged presets: real backend filters/total/pages, next/prev, pending filters, submit/Enter/reset, favorites preserve applied page, boundaries and empty result.');
})().catch(e=>{console.error(e);process.exitCode=1});
