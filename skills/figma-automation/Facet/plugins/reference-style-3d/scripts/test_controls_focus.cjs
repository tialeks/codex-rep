// Focus lifecycle and async popup ownership using the actual picker handlers.
// This fixture models node replacement and focus; it is not visual/browser QA.
const fs=require('node:fs'), path=require('node:path'), vm=require('node:vm'), assert=require('node:assert/strict');
const plugin=path.resolve(__dirname,'..');
const target=process.argv[2]||path.join(plugin,'ui/controls.html');
const html=fs.readFileSync(target,'utf8');
let code=html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
let active=null;
const nodes=[];
const dataKey=s=>s.replace(/^data-/,'').replace(/-([a-z])/g,(_,c)=>c.toUpperCase());
function matches(node,selector){
  if(selector.includes(','))return selector.split(',').some(s=>matches(node,s.trim()));
  if(selector.startsWith('#'))return node.id===selector.slice(1);
  if(selector==='[hidden]')return node.hidden;
  if(selector==='button:not(:disabled)')return node.tagName==='BUTTON'&&!node.disabled;
  const attr=selector.match(/^\[([^=\]]+)(?:=["']?([^"'\]]*)["']?)?\]$/);
  if(attr)return node.hasAttribute(attr[1])&&(attr[2]===undefined||String(node.getAttribute(attr[1]))===attr[2]);
  return node.tagName===selector.toUpperCase();
}
class Element{
  constructor(tag='div',attrs={},parent=null){
    this.tagName=tag.toUpperCase();this.attrs={...attrs};this.id=attrs.id||'';this.dataset={};
    for(const [key,value] of Object.entries(attrs))if(key.startsWith('data-'))this.dataset[dataKey(key)]=value;
    this.parent=parent;this.children=[];this.isConnected=true;this.hidden='hidden' in attrs;this.disabled='disabled' in attrs;
    this.value=attrs.value||'';this.textContent='';this.style={};this.listeners={};
    this.classList={add(){},remove(){}};nodes.push(this);if(parent)parent.children.push(this);
  }
  setAttribute(key,value){this.attrs[key]=String(value)}
  getAttribute(key){return this.attrs[key]}
  hasAttribute(key){return Object.hasOwn(this.attrs,key)}
  descendants(){return this.children.flatMap(child=>[child,...child.descendants()]).filter(child=>child.isConnected)}
  querySelectorAll(selector){return this.descendants().filter(node=>matches(node,selector))}
  querySelector(selector){return this.querySelectorAll(selector)[0]||null}
  closest(selector){for(let node=this;node;node=node.parent)if(matches(node,selector))return node;return null}
  contains(node){return node===this||this.descendants().includes(node)}
  focus(){assert.ok(this.isConnected,'must focus a connected node');assert.equal(this.disabled,false,'must focus an enabled node');active=this}
  detach(){for(const child of this.children)child.detach();this.isConnected=false;if(active===this)active=null}
  replaceChildren(){for(const child of this.children)child.detach();this.children=[]}
  set innerHTML(markup){this._html=markup;this.replaceChildren();parse(markup,this)}
  get innerHTML(){return this._html||''}
  addEventListener(name,fn){this.listeners[name]=fn}
  getBoundingClientRect(){return {left:0,top:0,bottom:30,width:620,height:900}}
  get offsetHeight(){return 200}
  showModal(){this.open=true}
  close(){this.open=false}
}
function parse(markup,parent){
  for(const match of markup.matchAll(/<(button|input|textarea|div|span|canvas|details|summary|dialog|section|label|ol|p|footer|select|option)\b([^>]*)>/g)){
    const attrs={};for(const attr of match[2].matchAll(/([\w-]+)(?:="([^"]*)")?/g))attrs[attr[1]]=attr[2]??'';
    new Element(match[1],attrs,parent);
  }
}
const root=new Element('div',{id:'ri'});
parse(html.slice(html.indexOf('<div id="ri"')+1,html.indexOf('<script id="r-catalog"')),root);
const get=id=>nodes.findLast(node=>node.id===id&&node.isConnected)||null;
const catalog=JSON.parse(html.match(/id="r-catalog" type="application\/json">([\s\S]*?)<\/script>/)[1]);
for(const [key,name] of [['graphics','graphics'],['referenceFacets','reference-facets'],['effects','effects']])catalog[key]=JSON.parse(fs.readFileSync(path.join(plugin,'skills/reference-style-3d/references',name+'.json'),'utf8'));
catalog.materialPresets=JSON.parse(fs.readFileSync(path.join(plugin,'skills/reference-style-3d/references/material-presets.json'),'utf8'));
const cards=JSON.parse(fs.readFileSync(path.join(plugin,'assets/materials/catalog.json'),'utf8')).cards;
for(const [id,data] of [['r-catalog',catalog],['r-plugin-palettes',{palettes:[]}],['r-material-library',{materials:cards}]])new Element('script',{id},root).textContent=JSON.stringify(data);
const documentListeners={};
const context={document:{getElementById:id=>id==='ri'?root:get(id),addEventListener(name,fn){documentListeners[name]=fn}},window:{openai:{setWidgetState(){},sendFollowUpMessage(){}},addEventListener(){}},Image:class{},TextEncoder,console};
// Leave picker rendering and all handlers real; bypass unrelated initial rendering.
code=code.replace(/initPresetCatalog\(\);[\s\S]*?\}\)\(\);/,`globalThis.api={state,open,close,openMaterials,closeMaterials,updateMaterials,openPalettes,openColor,applyColor,openEffects,savedMenu,paletteRequest,presetMenu,renderPalettes,renderEffects};render=()=>{renderPalettes();renderEffects()};summary=()=>{};})();`);
vm.createContext(context);vm.runInContext(code,context);
const a=context.api,popup=get('r-popup');
const find=selector=>{const found=root.querySelector(selector);assert.ok(found,'missing '+selector);return found};
const click=node=>root.listeners.click({target:{closest(){return node}}});
const expectFocus=selector=>assert.ok(active===find(selector),'focus '+selector);
function deferred(){let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no});return {promise,resolve,reject}}
(async()=>{
  a.renderPalettes();a.renderEffects();
  assert.equal(get('r-advanced'),null);const originalColors=JSON.stringify(a.state.colors);
  root.listeners.change({target:{id:'r-palette-toggle',checked:false}});assert.equal(a.state.palette,'natural');assert.equal(get('r-custom-colors').hidden,true);assert.equal(JSON.stringify(a.state.colors),originalColors);
  root.listeners.change({target:{id:'r-palette-toggle',checked:true}});assert.equal(a.state.palette,'custom');assert.equal(get('r-custom-colors').hidden,false);assert.equal(JSON.stringify(a.state.colors),originalColors);
  a.openPalettes(get('r-all-palettes'));const oldPalette=find('[data-palette="contrast-original"]');oldPalette.focus();click(oldPalette);assert.equal(oldPalette.isConnected,false);expectFocus('#r-all-palettes');
  a.openColor(find('[data-color="0"]'),0);const oldSwatch=find('[data-color="0"]');a.applyColor('#123456');assert.equal(oldSwatch.isConnected,false);expectFocus('[data-color="0"]');assert.equal(a.state.colors[0],'#123456');
  const count=a.state.colors.length;a.openColor(get('r-add-color'),-1);a.applyColor('#ABCDEF');expectFocus('[data-color="'+count+'"]');
  click(find('[data-remove-color="'+count+'"]'));expectFocus('[data-color="'+(count-1)+'"]');assert.equal(a.state.colors.length,count);
  const preservedColors=[...a.state.colors];a.state.colors=['#123456'];a.renderPalettes();const lastRemove=find('[data-remove-color="0"]');assert.equal(lastRemove.disabled,true);click(lastRemove);assert.equal(a.state.colors.length,1);a.state.colors=preservedColors;a.renderPalettes();
  a.openColor(find('[data-color="0"]'),0);get('r-hex').focus();const invalidFocus=active;a.applyColor('bad color');assert.ok(active===invalidFocus);assert.equal(popup.hidden,false);a.close(true);expectFocus('[data-color="0"]');
  a.openEffects(get('r-add-effect'));click(find('[data-effect="fold"]'));expectFocus('[data-strength="0"]');
  a.openEffects(get('r-add-effect'));click(find('[data-effect="levitate"]'));assert.equal(get('r-add-effect').disabled,false);expectFocus('[data-strength="1"]');
  a.openEffects(get('r-add-effect'));click(find('[data-effect="inflate"]'));expectFocus('[data-strength="2"]');assert.equal(a.state.effects.length,3);assert.equal(get('r-effects-warning').hidden,false);assert.equal(get('r-add-effect').disabled,false);
  click(find('[data-remove-effect="2"]'));assert.equal(get('r-effects-warning').hidden,true);
  click(find('[data-remove-effect="0"]'));expectFocus('[data-remove-effect="0"]');click(find('[data-remove-effect="0"]'));expectFocus('#r-add-effect');
  a.presetMenu(get('r-presets'));assert.equal(get('r-preset-catalog').hidden,false);click(get('r-settings-tab'));assert.equal(get('r-settings-panel').hidden,false);
  a.openPalettes(get('r-all-palettes'));get('r-submit').focus();documentListeners.focusin({target:get('r-submit')});assert.equal(popup.hidden,true);expectFocus('#r-submit');
  a.savedMenu(get('r-saved'));const pending=deferred();context.window.openai.sendFollowUpMessage=()=>pending.promise;const first=a.paletteRequest();
  a.close(true);a.open(get('r-all-palettes'),'<button id="new-choice">New choice</button>','New picker');get('new-choice').focus();get('r-status').textContent='New action';pending.resolve();await first;
  assert.equal(popup.hidden,false);assert.equal(popup.getAttribute('aria-label'),'New picker');expectFocus('#new-choice');assert.equal(get('r-status').textContent,'New action');
  a.savedMenu(get('r-saved'));const rejected=deferred();context.window.openai.sendFollowUpMessage=()=>rejected.promise;const second=a.paletteRequest();
  a.close(true);a.savedMenu(get('r-saved'));get('r-refresh-palettes').focus();const newerButton=active;get('r-status').textContent='Later action';rejected.reject(new Error('offline'));await second;
  assert.equal(popup.hidden,false);assert.ok(active===newerButton);assert.equal(newerButton.disabled,false);assert.equal(get('r-status').textContent,'Later action');
  let libraryRequest;const paletteSnapshot=JSON.stringify(a.state);context.window.openai.sendFollowUpMessage=request=>{libraryRequest=request;return Promise.resolve()};await a.paletteRequest();assert.equal(JSON.stringify(JSON.parse(libraryRequest.prompt.split('\n')[1]).settings),paletteSnapshot);assert.equal(popup.hidden,true);expectFocus('#r-saved');
  a.savedMenu(get('r-saved'));context.window.openai.sendFollowUpMessage=()=>Promise.reject(new Error('offline'));await a.paletteRequest();assert.equal(popup.hidden,false);assert.equal(get('r-refresh-palettes').disabled,false);assert.match(get('r-status').textContent,/Не удалось/);
  delete context.window.openai.sendFollowUpMessage;await a.paletteRequest();assert.equal(popup.hidden,true);assert.equal(get('r-fallback'),null);expectFocus('#r-saved');assert.match(get('r-status').textContent,/в чате Codex/);
  a.state.materials={mode:'selected',base:'wood',accents:['paper','leather']};a.openMaterials('cards');
  click(find('[data-material-remove="paper"]'));expectFocus('[data-material-remove="leather"]');
  click(find('[data-material-remove="leather"]'));expectFocus('[data-material-remove="wood"]');
  click(find('[data-material-remove="wood"]'));expectFocus('#r-material-close');a.closeMaterials();expectFocus('#r-material-open');
  // Dialog backdrop and Escape both restore focus; clicks inside the surface keep it open.
  a.openMaterials('cards');const materialDialog=get('r-material-dialog');
  materialDialog.listeners.click({target:materialDialog,clientX:10,clientY:10});assert.equal(materialDialog.open,true);
  materialDialog.listeners.click({target:materialDialog,clientX:-1,clientY:10});assert.equal(materialDialog.open,false);expectFocus('#r-material-open');
  a.openMaterials('cards');let cancelPrevented=false;materialDialog.listeners.cancel({preventDefault(){cancelPrevented=true}});assert.equal(cancelPrevented,true);assert.equal(materialDialog.open,false);expectFocus('#r-material-open');
  a.openPalettes(get('r-all-palettes'));documentListeners.pointerdown({target:get('r-submit')});assert.equal(popup.hidden,true);
  console.log('PASS: palette/color/effect/preset focus after node replacement; invalid color focus; stale success/error preserve newer popup; current success/error; snapshot-preserving library requests; no-API guidance; keyboard exit closes popup.');
})().catch(error=>{console.error(error);process.exitCode=1});
