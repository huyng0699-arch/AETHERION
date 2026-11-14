// Execute the actual frontend HTTP adapters against the live verification API.
// Web storage is in memory here; this does not claim a browser-rendering check.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const require=createRequire(path.join(root,'apps/mobile/package.json'));
const ts=require('typescript'), cache=new Map(), settings=new Map(), session=new Map();
const normalAuthOnly=process.argv.includes('--normal-auth-only');
const access=JSON.parse(fs.readFileSync(path.join(root,normalAuthOnly?'.runtime/local-access.json':'.runtime/verification-access.json'),'utf8'));
const storage={getItem:async key=>settings.get(key)||null,setItem:async(key,value)=>settings.set(key,value)};
const sessionStorage={getItem:key=>session.get(key)||null,setItem:(key,value)=>session.set(key,value),removeItem:key=>session.delete(key)};
function load(file){
 file=path.resolve(file);if(cache.has(file))return cache.get(file);
 const source=fs.readFileSync(file,'utf8');
 const js=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,esModuleInterop:true}}).outputText;
 const exports={},module={exports};cache.set(file,exports);
 const resolve=name=>{
   if(name==='react-native')return{Platform:{OS:'web'}};
   if(name==='@react-native-async-storage/async-storage')return storage;
   if(name==='expo-secure-store')return{};
   if(name.startsWith('.')){const resolved=path.resolve(path.dirname(file),name);if(resolved.endsWith('.json'))return JSON.parse(fs.readFileSync(resolved,'utf8'));return load(resolved+'.ts');}
   return require(name);
 };
 vm.runInNewContext(js,{exports,module,require:resolve,URL,process:{env:{}},__DEV__:false,window:{location:new URL(access.url)},sessionStorage,fetch,AbortController,setTimeout,clearTimeout,console},{filename:file});
 return module.exports;
}
const api=name=>load(path.join(root,'apps/mobile/src/api',name+'.ts'));
const client=api('client'),auth=api('auth'),subjects=api('subjects'),health=api('health'),science=api('science'),care=api('care'),assistant=api('assistant'),sessions=load(path.join(root,'apps/mobile/src/storage/session.ts'));
const checks=[];
async function check(name,run){try{await run();checks.push({name,status:'PASS'});console.log('PASS '+name);}catch(error){checks.push({name,status:'FAIL',error:error.message});console.log('FAIL '+name+': '+error.message);}}
let identity;
await client.saveServerUrl(access.url);
await check('Frontend readiness adapter reads real SQLite state',async()=>{assert.equal((await client.checkServer()).database,'ok');});
await check('Frontend auth adapter signs in and scopes persisted session',async()=>{identity=await auth.signIn(access.username,access.password);assert.equal(identity.server_url,access.url);await sessions.writeSession(identity);assert.equal((await auth.validateSession(identity.access_token)).username,access.username);});
if (normalAuthOnly) {
 await check('Normal origin change rejects stale bearer before a network call',async()=>{await client.saveServerUrl('http://127.0.0.1:65531');await assert.rejects(auth.validateSession(identity.access_token),error=>error.status===401&&error.code==='SESSION_SERVER_MISMATCH');});
 await check('Login uses captured origin even while another URL is stored',async()=>{await auth.signOut();identity=await auth.signIn(access.username,access.password,access.url);assert.equal(identity.server_url,access.url);await sessions.writeSession(identity);});
 await check('Logout revokes captured server token without touching another origin',async()=>{await auth.signOut();assert.equal(await sessions.readSession(),null);assert.equal((await fetch(access.url+'/api/v1/auth/me',{headers:{Authorization:'Bearer '+identity.access_token}})).status,401);});
} else {
await check('Frontend subject adapter resolves wildcard to registered profiles',async()=>{const rows=await subjects.listSubjects(identity.access_token);assert.ok(rows.some(row=>row.subject_id==='integration-check-profile'));assert.ok(rows.every(row=>row.subject_id!=='*'));});
await check('Frontend Health and Monitor read actual no-data responses',async()=>{assert.equal((await health.getAvailability('integration-check-profile',identity.access_token)).availability_status,'NO_DATA');assert.equal((await health.getObservations('integration-check-profile',identity.access_token)).observations.length,0);});
await check('Frontend Library search and detail preserve original content',async()=>{assert.equal((await science.getKnowledgeStatus()).json_articles,118);const result=await science.searchScienceArticles('dehydration',3);assert.ok(result.items.length);const detail=await science.getScienceArticle(result.items[0].article_id);assert.ok(detail.sections.length);assert.equal(detail.clinical_decision_support,false);});
await check('Frontend AI adapter reads availability without inventing output',async()=>{const result=await assistant.getAssistantStatus(identity.access_token);assert.equal(typeof result.local_available,'boolean');assert.equal(typeof result.cloud_available,'boolean');if(!result.local_available)await assert.rejects(assistant.sendAssistantChat(identity.access_token,{messages:[{role:'user',content:'Integration check only'}],provider:'local',cloud_consent:false,locale:'en'}),error=>error.status===503);});
await check('Frontend Care adapters persist and reload an explicit test record',async()=>{const result=await care.startCareEpisode({subject_id:'integration-check-profile',chief_concern:'Frontend integration verification only',symptom_terms:[],interview_answers:{},explicit_consent:true},identity.access_token);const next=await care.advanceCareEpisode(result.episode.episode_id,{next_phase:'EVALUATE',summary:'Integration verification only',human_confirmed:true},identity.access_token);assert.equal(next.episode.current_phase,'EVALUATE');assert.equal((await care.getCareEpisode(result.episode.episode_id,identity.access_token)).current_phase,'EVALUATE');});
await check('Changing server origin blocks stale bearer before transmission',async()=>{await client.saveServerUrl('http://127.0.0.1:65531');await assert.rejects(auth.validateSession(identity.access_token),error=>error.status===401&&error.code==='SESSION_SERVER_MISMATCH');await client.saveServerUrl(access.url);});
await check('Frontend sign out clears storage and revokes the captured bearer',async()=>{await auth.signOut();assert.equal(await sessions.readSession(),null);const response=await fetch(access.url+'/api/v1/auth/me',{headers:{Authorization:'Bearer '+identity.access_token}});assert.equal(response.status,401);});
}
const report={scope:'Actual frontend TypeScript HTTP adapters and session code executed against the live API with in-memory web-storage adapters. No browser layout/device assertion.',checks,total:checks.length,passed:checks.filter(item=>item.status==='PASS').length};
report.pass_percent=Math.round(100*report.passed/report.total);
fs.writeFileSync(path.join(root,normalAuthOnly?'docs/evidence/mobile-normal-auth-origin.json':'.runtime/verification/frontend-api-report.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify({passed:report.passed,total:report.total,pass_percent:report.pass_percent}));
process.exitCode=report.passed===report.total?0:1;
