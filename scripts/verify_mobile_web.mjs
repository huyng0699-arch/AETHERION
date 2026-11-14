import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';
import assert from 'node:assert/strict';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const output=path.join(root,'.runtime','verification');
await fs.mkdir(output,{recursive:true});
const access=JSON.parse(await fs.readFile(path.join(root,'.runtime','verification-access.json'),'utf8'));
const checks=[],errors=[];
async function check(name,fn){try{await fn();checks.push({name,status:'PASS'});console.log('PASS '+name);}catch(error){checks.push({name,status:'FAIL',error:error.message});console.log('FAIL '+name+': '+error.message);}}
async function api(route,options={}){const r=await fetch(access.url+route,{...options,headers:{'Content-Type':'application/json',...(options.headers||{})},body:options.body?JSON.stringify(options.body):undefined});return{status:r.status,body:await r.json()};}
let token;
await check('API readiness includes SQLite',async()=>{const r=await api('/ready');assert.equal(r.status,200);assert.equal(r.body.database,'ok');});
await check('Protected data rejects anonymous access',async()=>{assert.equal((await api('/api/v1/subjects')).status,401);});
await check('Invalid credentials rejected',async()=>{assert.equal((await api('/api/v1/auth/login',{method:'POST',body:{username:access.username,password:'wrong-integration-password'}})).status,401);});
await check('Real sign-in and bearer identity',async()=>{const r=await api('/api/v1/auth/login',{method:'POST',body:{username:access.username,password:access.password}});assert.equal(r.status,200);token=r.body.access_token;const me=await api('/api/v1/auth/me',{headers:{Authorization:'Bearer '+token}});assert.equal(me.body.username,access.username);});
const auth=()=>({Authorization:'Bearer '+token});
await check('Permission wildcard cannot be registered as a patient ID',async()=>{const r=await api('/api/v1/subjects',{method:'POST',headers:auth(),body:{subject_id:'*',display_name:'Must not persist'}});assert.equal(r.status,422);});
await check('Wildcard permission resolves concrete profiles',async()=>{const id='integration-check-profile';const r=await api('/api/v1/subjects',{method:'POST',headers:auth(),body:{subject_id:id,display_name:'Integration check only',scope:'engineering_test'}});assert.ok([200,201].includes(r.status));const list=await api('/api/v1/subjects',{headers:auth()});assert.equal(list.status,200);assert.ok(list.body.subjects.some(s=>s.subject_id===id));assert.ok(list.body.subjects.every(s=>s.subject_id!=='*'));});
await check('Empty profile remains NO_DATA',async()=>{const r=await api('/api/v1/subjects/integration-check-profile/summary',{headers:auth()});assert.equal(r.body.availability_status,'NO_DATA');assert.equal(r.body.observation_count,0);});
await check('Current server exposes authenticated AI status',async()=>{assert.equal((await api('/api/v1/assistant/status')).status,401);const r=await api('/api/v1/assistant/status',{headers:auth()});assert.equal(r.status,200);assert.equal(typeof r.body.local_available,'boolean');assert.equal(typeof r.body.cloud_available,'boolean');});
await check('Cloud request requires explicit consent',async()=>{const r=await api('/api/v1/assistant/chat',{method:'POST',headers:auth(),body:{messages:[{role:'user',content:'Integration check only'}],provider:'cloud',cloud_consent:false,locale:'en'}});assert.equal(r.status,422);});
await check('Consent required before a care record is written',async()=>{const r=await api('/api/v1/care/episodes',{method:'POST',headers:auth(),body:{subject_id:'integration-check-profile',chief_concern:'Integration check only',symptom_terms:[],interview_answers:{},explicit_consent:false}});assert.equal(r.status,422);});
await check('Care record persists human confirmed transitions',async()=>{const r=await api('/api/v1/care/episodes',{method:'POST',headers:auth(),body:{subject_id:'integration-check-profile',chief_concern:'Integration verification only; not a medical record',symptom_terms:[],interview_answers:{},explicit_consent:true}});assert.ok([200,201].includes(r.status));assert.equal(r.body.clinical_assessment,'NOT_ASSESSED');const id=r.body.episode.episode_id;const next=await api('/api/v1/care/episodes/'+id+'/advance',{method:'POST',headers:auth(),body:{next_phase:'EVALUATE',summary:'Integration verification only',human_confirmed:true}});assert.equal(next.status,200);const read=await api('/api/v1/care/episodes/'+id,{headers:auth()});assert.equal(read.body.episode.current_phase,'EVALUATE');});
await check('Logged-out bearer is revoked',async()=>{const login=await api('/api/v1/auth/login',{method:'POST',body:{username:access.username,password:access.password}});const headers={Authorization:'Bearer '+login.body.access_token};await api('/api/v1/auth/logout',{method:'POST',headers});assert.equal((await api('/api/v1/auth/me',{headers})).status,401);});

await check('Knowledge search indexes the actual repository records',async()=>{const r=await api('/api/v1/knowledge/status');assert.equal(r.status,200);assert.equal(r.body.json_articles,118);assert.ok(r.body.missing_slots.includes('CLIFF-119'));assert.equal(r.body.clinical_rules_validated,false);const search=await api('/api/v1/knowledge/articles?query=dehydration&limit=3');assert.ok(search.body.matched>0);assert.ok(search.body.items.length<=3);});
await check('Library article preserves sections and source provenance',async()=>{const r=await api('/api/v1/knowledge/articles/CLIFF-001');assert.equal(r.status,200);assert.equal(r.body.summary.article_id,'CLIFF-001');assert.ok(r.body.sections.length>0);assert.ok(r.body.source.source_url||r.body.source.final_url);assert.equal(r.body.clinical_decision_support,false);});
await check('NASA demo retains 19 timepoints and 83 reported values',async()=>{const source=JSON.parse(await fs.readFile(path.join(root,'apps/mobile/assets/ma7_source.json'),'utf8'));assert.equal(source.is_synthetic,false);assert.equal(source.is_live,false);assert.equal(source.groups.reduce((n,g)=>n+g.records.length,0),19);assert.equal(source.groups.flatMap(g=>g.records).flatMap(r=>Object.values(r.measures)).filter(v=>v.value!==null).length,83);});
await check('Expo HTML and icon font are served by this API process',async()=>{const page=await fetch(access.url);assert.equal(page.status,200);assert.ok((await page.text()).includes('_expo/static/js/web/'));const folder=path.join(root,'apps/mobile/dist/assets/node_modules/@expo/vector-icons/build/vendor/react-native-vector-icons/Fonts');const font=(await fs.readdir(folder)).find(f=>f.startsWith('Ionicons.'));assert.ok(font);const r=await fetch(access.url+'/assets/node_modules/@expo/vector-icons/build/vendor/react-native-vector-icons/Fonts/'+font);assert.equal(r.status,200);assert.ok((await r.arrayBuffer()).byteLength>300000);});
await check('Private runtime account file is not web-accessible',async()=>{assert.equal((await fetch(access.url+'/.runtime/verification-access.json')).status,404);});
await check('Server route contract covers all mobile data endpoints',async()=>{const r=await api('/openapi.json');for(const name of ['/ready','/api/v1/auth/login','/api/v1/auth/me','/api/v1/auth/logout','/api/v1/subjects','/api/v1/subjects/{subject_id}/summary','/api/v1/observations','/api/v1/care/episodes','/api/v1/care/episodes/{episode_id}/advance','/api/v1/assistant/status','/api/v1/assistant/chat','/api/v1/knowledge/status','/api/v1/knowledge/articles','/api/v1/knowledge/articles/{article_id}'])assert.ok(r.body.paths[name],'Missing route '+name);});

if (!process.argv.includes('--api-only')) {
const port=Number(process.env.AETHERION_CDP_PORT||9238);
let edge;
let browserLog='';
if (!process.env.AETHERION_CDP_PORT) {
 try {
  edge=spawn(process.env.AETHERION_BROWSER||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',['--headless=new','--disable-gpu','--no-first-run',`--remote-debugging-port=${port}`,'--remote-debugging-address=127.0.0.1',`--user-data-dir=${path.join(root,'.runtime','headless-profile')}`,'about:blank'],{windowsHide:true,stdio:['ignore','ignore','pipe']});
  edge.stderr.on('data',chunk=>{browserLog+=chunk.toString();});edge.on('error',error=>{browserLog+=error.message;});
 } catch(error) { browserLog+=error.message; }
}
let socket;
async function waitFor(fn,timeout=15000){const end=Date.now()+timeout;let last;while(Date.now()<end){try{const value=await fn();if(value)return value;}catch(e){last=e;}await new Promise(r=>setTimeout(r,120));}throw last||new Error('Timed out waiting for visible state');}
try{
 await waitFor(async()=>{const r=await fetch(`http://127.0.0.1:${port}/json/version`);return r.ok;});
 const tab=await (await fetch(`http://127.0.0.1:${port}/json/new?${encodeURIComponent(access.url)}`,{method:'PUT'})).json();
 socket=new WebSocket(tab.webSocketDebuggerUrl);
 await new Promise((resolve,reject)=>{socket.addEventListener('open',resolve,{once:true});socket.addEventListener('error',reject,{once:true});});
 let seq=0;const pending=new Map();
 socket.addEventListener('message',event=>{const msg=JSON.parse(event.data);if(msg.id){const p=pending.get(msg.id);if(p){pending.delete(msg.id);clearTimeout(p.timeout);msg.error?p.reject(new Error(msg.error.message)):p.resolve(msg.result);}}else if(msg.method==='Runtime.exceptionThrown')errors.push(msg.params.exceptionDetails.text);});
 const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++seq;const timeout=setTimeout(()=>{pending.delete(id);reject(new Error('CDP timeout '+method));},20000);pending.set(id,{resolve,reject,timeout});socket.send(JSON.stringify({id,method,params}));});
 const evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw new Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);return r.result.value;};
 const text=()=>evaluate('document.body.innerText');
 const click=async(label,role='button')=>{await evaluate(`(()=>{const items=[...document.querySelectorAll('[role="${role}"]')];const target=items.find(el=>el.getAttribute('aria-label')===${JSON.stringify(label)}||el.textContent.trim()===${JSON.stringify(label)});if(!target)throw new Error('Control absent: '+${JSON.stringify(label)});target.click();return true;})()`);};
 const fill=async(label,value)=>evaluate(`(()=>{const el=[...document.querySelectorAll('input,textarea')].find(el=>el.getAttribute('aria-label')===${JSON.stringify(label)});if(!el)throw new Error('Input absent: '+${JSON.stringify(label)});Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(el,${JSON.stringify(value)});el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));return true;})()`);
 const has=async value=>(await text()).includes(value);
 const shot=async name=>{const r=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});await fs.writeFile(path.join(output,name+'.png'),Buffer.from(r.data,'base64'));};
 await send('Runtime.enable');await send('Page.enable');await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
 await send('Page.navigate',{url:access.url});await waitFor(()=>has('Welcome back'));
 await check('Mobile cold start is login with visible Demo',async()=>{assert.ok(await has('Password'));assert.ok(await evaluate(`(()=>{const b=document.querySelector('[aria-label="Demo"]');if(!b)return false;const r=b.getBoundingClientRect();return r.width>0&&r.top>=0&&r.bottom<=844;})()`));await shot('mobile-login');});
 await check('Icon font loaded without missing glyph fallback',async()=>{await waitFor(()=>evaluate(`[...document.fonts].some(font=>font.family.toLowerCase().includes('ionicons')&&font.status==='loaded')`));});
 await check('Demo opens introduction before records',async()=>{await click('Demo');await waitFor(()=>has('83 reported values'));assert.ok(await has('Explore data'));await shot('mobile-demo-intro');});
 await check('Archive data preserves actual NASA values and units',async()=>{await click('Explore data');await waitFor(()=>has('Flight phases'));assert.ok(await has('57'));assert.ok(await has('beats/min'));assert.ok(await has('Phase mean'));await shot('mobile-demo-data');});
 await check('All archive groups and timepoints remain browsable',async()=>{await click('Next');await waitFor(()=>has('Countdown'));await click('Clinical exams','tab');await waitFor(()=>has('Clinical'));await click('Blood count','tab');await waitFor(()=>has('Blood count'));await click('Blood pressure','tab');await waitFor(()=>has('Blood pressure'));});
 await check('Demo returns through intro to login',async()=>{await click('Back');await waitFor(()=>has('Explore data'));await click('Back');await waitFor(()=>has('Welcome back'));});
 await check('Appearance changes all shared UI and persists',async()=>{await click('Appearance');await waitFor(()=>has('Amethyst'));await click('Ocean','radio');await click('Dark','radio');await click('Back');await waitFor(()=>has('Welcome back'));assert.equal(await evaluate(`localStorage.getItem('aetherion.mobile.appearance.v1')!==null`),true);await shot('mobile-login-dark');await send('Page.reload');await waitFor(()=>has('Welcome back'));assert.ok(await evaluate(`document.body.innerText.includes('Demo')`));});
 await check('Language changes on login and persists',async()=>{await click('Language');await waitFor(()=>has('Chào mừng trở lại'));await send('Page.reload');await waitFor(()=>has('Chào mừng trở lại'));await click('Ngôn ngữ');await waitFor(()=>has('Welcome back'));});
 await check('UI sign-in enters authenticated Portal',async()=>{await fill('Username',access.username);await fill('Password',access.password);await click('Sign in');await waitFor(()=>has('Care Journey'));assert.ok(await has('Server responded'));await shot('mobile-home');});
 await check('Health uses a concrete authorized subject',async()=>{await click('Health','button');await click('Choose a profile');await click('Integration check only');await waitFor(()=>has('integration-check-profile'));assert.ok(!await has('Subject: *'));assert.ok(await has('NO DATA')||await has('No data')||await has('No observations'));});
 await check('Monitor reads real endpoint with no invented readings',async()=>{await click('Monitor','tab');await waitFor(()=>has('Monitoring'));assert.ok(await has('No observations')||await has('No data'));});
 await check('AI screen reads the actual server availability',async()=>{await click('AI','tab');await waitFor(async()=>await has('AI unavailable')||await has('Local AI'));assert.ok(!await has('Not found'));});
 await check('Settings opens a separate Appearance page',async()=>{await click('More','tab');await waitFor(()=>has('Settings'));await click('Settings');await waitFor(()=>has('Appearance'));await click('Appearance');await waitFor(()=>has('Amethyst'));});
 await check('Reload always returns to login even with a saved session',async()=>{await send('Page.reload');await waitFor(()=>has('Welcome back'));assert.ok(await has('Continue as'));});
 await check('320px layout has no horizontal document overflow',async()=>{await send('Emulation.setDeviceMetricsOverride',{width:320,height:740,deviceScaleFactor:1,mobile:true});assert.ok(await evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'));await shot('mobile-login-320');});
 await check('Desktop browser keeps a phone-sized app canvas',async()=>{await send('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false});assert.ok(await evaluate(`document.querySelector('[aria-label="Demo"]').getBoundingClientRect().width<=470`));await shot('web-login-wide');});
 await check('No unhandled browser runtime errors',async()=>{assert.deepEqual(errors,[]);});
}catch(error){checks.push({name:'Headless browser run',status:'FAIL',error:error.message});console.log('FAIL Headless browser run: '+error.message);}
finally{if(socket)socket.close();edge?.kill();await fs.writeFile(path.join(output,'browser.log'),browserLog);}
}
const report={recorded_at_utc:new Date().toISOString(),scope:process.argv.includes('--api-only')?'Local API integration, static export delivery and source integrity. No browser interaction, native Android, clinical validation, or AI-model completion asserted.':'Local API and Expo Web on Windows; isolated integration database. No physical Android, clinical validation, or configured AI-model completion asserted.',browser:process.argv.includes('--api-only')?'NOT_RUN':'ATTEMPTED',checks,total:checks.length,passed:checks.filter(x=>x.status==='PASS').length,failed:checks.filter(x=>x.status==='FAIL').length};
report.pass_percent=Math.round(100*report.passed/report.total);
await fs.writeFile(path.join(output,'report.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify({passed:report.passed,total:report.total,pass_percent:report.pass_percent,report:path.join(output,'report.json')}));
process.exitCode=report.failed?1:0;
