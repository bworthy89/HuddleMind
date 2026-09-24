// Production-build HTTP checks use a temporary account, never the owner's setup key.
import {spawn} from 'node:child_process';
import {mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';import {join} from 'node:path';
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
const dir=mkdtempSync(join(tmpdir(),'huddlemind-http-'));
const origin='http://127.0.0.1:3017';
const payload={roster:{team:{name:'Sample Team',players:[]},coach:{first_name:'Sample',last_name:'Coach'}},season:{calendar_year:2026,week:2,season_index:0,stage:{label:'Season'}},schedule:[],recruiting:null};
let snapshot={observed_at:'2026-09-23T18:00:00Z',payload};
let extra=[];
const receiver=createServer((request,response)=>{response.setHeader('Content-Type','application/json');response.end(JSON.stringify({dynasties:[{dynasty_id:'sample',snapshot},...extra],bridges:extra.length?[{dynasty_id:'second',status:'offline',last_seen_at:null,report:null}]:[]}));});
await new Promise(r=>receiver.listen(3018,'127.0.0.1',r));
const server=spawn(process.execPath,['node_modules/next/dist/bin/next','start','-p','3017'],{stdio:'ignore',env:{...process.env,
 HUDDLEMIND_AUTH_FILE:join(dir,'auth.json'),HUDDLEMIND_WEB_ORIGIN:origin,HUDDLEMIND_SESSION_SECRET:'s'.repeat(48),
 HUDDLEMIND_SETUP_KEY:'test-key',HUDDLEMIND_SETUP_EXPIRES:String(Date.now()+60000),HUDDLEMIND_RECEIVER_URL:'http://127.0.0.1:3018'}});
try{
 let ready=false;for(let i=0;i<40;i++){try{if((await fetch(origin+'/app/login')).ok){ready=true;break}}catch{}await new Promise(r=>setTimeout(r,250));}
 assert.equal(ready,true);
 const denied=await fetch(origin+'/app',{redirect:'manual'});assert.equal(denied.status,307);assert.ok(denied.headers.get('location').endsWith('/app/login'));
 const post=(body,site=origin)=>fetch(origin+'/app/api/session',{method:'POST',headers:{Origin:site,'Content-Type':'application/json'},body:JSON.stringify(body)});
 assert.equal((await post({action:'setup',key:'test-key',password:'a sufficiently long test password'},'https://wrong.example')).status,403);
 const created=await post({action:'setup',key:'test-key',password:'a sufficiently long test password'});assert.equal(created.status,200);
 const cookie=created.headers.get('set-cookie');for(const flag of ['HttpOnly','Secure','SameSite=strict','Path=/app'])assert.ok(cookie.includes(flag));
 assert.equal((await post({action:'setup',key:'test-key',password:'another sufficiently long password'})).status,401);
 assert.equal((await post({action:'login',password:'wrong'})).status,401);
 assert.equal((await post({action:'login',password:'a sufficiently long test password'})).status,200);
 const home=await fetch(origin+'/app',{headers:{Cookie:cookie.split(';')[0]}});assert.equal(home.status,200);const html=await home.text();assert.ok(html.includes('Sample Team'));
 assert.ok(html.includes('aria-label="Main navigation"'));
 for(const section of ['roster','schedule','recruiting']){
  assert.ok(html.includes('href="/app/'+section+'"'));
  const page=await fetch(origin+'/app/'+section,{headers:{Cookie:cookie.split(';')[0]}});
  assert.equal(page.status,200);assert.ok((await page.text()).includes({roster:'No roster players',schedule:'No scheduled games',recruiting:'Recruiting board unavailable'}[section]));
  assert.equal((await fetch(origin+'/app/'+section,{redirect:'manual'})).status,307);
 }
 const getPage=async section=>(await fetch(origin+'/app/'+section,{headers:{Cookie:cookie.split(';')[0]}})).text();
 payload.schedule=[{record_id:{table_id:1,row_id:0},season_index:0,week:1,status:'AwayWon',controlled_team_is_home:false,home_team:'Sample Home',away_team:'Sample Team',home_score:23,away_score:28},
 {record_id:{table_id:1,row_id:1},season_index:0,week:2,status:'Unplayed',controlled_team_is_home:true,home_team:'Sample Team',away_team:'Next Opponent',home_score:0,away_score:0}];
 const schedule=await getPage('schedule');for(const text of ['Sample Home','Next Opponent','Next scheduled','Win','Final'])assert.ok(schedule.includes(text));
 payload.recruiting={hours_total:480,hours_assigned:0,hours_processed:0,targets:[{record_id:{table_id:2,row_id:1},name:'Sample Recruit',position:{label:'QB'},stage:{label:'Top5'},scholarship:{label:'Offered'},national_rank:1,position_rank:1,hours_spent_current:0}]};
 const recruiting=await getPage('recruiting');for(const text of ['Sample Recruit','480','Top5','Offered','Current target hours'])assert.ok(recruiting.includes(text));
 payload.recruiting.targets=[];assert.ok((await getPage('recruiting')).includes('No recruiting targets'));
 const choose=(id,auth=cookie.split(';')[0],site=origin)=>fetch(origin+'/app/api/dynasty',{method:'POST',headers:{Cookie:auth,Origin:site,'Content-Type':'application/json'},body:JSON.stringify({dynasty_id:id})});
 extra=[{dynasty_id:'second',snapshot:{...snapshot,payload:{...payload,roster:{...payload.roster,team:{name:'Second Team',players:[]}}}}},{dynasty_id:'empty',snapshot:null}];
 assert.equal((await choose('second','')).status,401);
 assert.equal((await choose('second',cookie.split(';')[0],'https://wrong.example')).status,403);
 assert.equal((await choose('not-allowed')).status,403);
 const switched=await choose('second');assert.equal(switched.status,200);
 const selectionCookie=switched.headers.get('set-cookie');for(const flag of ['HttpOnly','Secure','SameSite=strict','Path=/app'])assert.ok(selectionCookie.includes(flag));
 const selectedAuth=cookie.split(';')[0]+'; '+selectionCookie.split(';')[0];
 for(const section of ['','roster','schedule','recruiting']){
  const page=await (await fetch(origin+'/app'+(section?'/'+section:''),{headers:{Cookie:selectedAuth}})).text();
  assert.ok(page.includes('<span class="dynasty">Second Team</span>'));
  if(!section)assert.ok(page.includes('Bridge offline'));
 }
 const empty=await choose('empty');const emptyAuth=cookie.split(';')[0]+'; '+empty.headers.get('set-cookie').split(';')[0];
 assert.ok((await (await fetch(origin+'/app/roster',{headers:{Cookie:emptyAuth}})).text()).includes('No snapshot received yet'));
 extra=[];const revoked=await (await fetch(origin+'/app/roster',{headers:{Cookie:selectedAuth}})).text();assert.ok(revoked.includes('Your previous selection is no longer available'));
 snapshot=null;for(const section of ['schedule','recruiting'])assert.ok((await getPage(section)).includes('No snapshot received yet'));
 await new Promise(r=>receiver.close(r));
 assert.equal((await choose('sample')).status,503);
 for(const section of ['schedule','recruiting'])assert.ok((await getPage(section)).includes('Your saved data has not been removed'));
 const unavailable=await fetch(origin+'/app',{headers:{Cookie:cookie.split(';')[0]}});assert.ok((await unavailable.text()).includes('We couldn’t load your dynasty'));
 const logout=await post({action:'logout'});assert.ok(logout.headers.get('set-cookie').includes('Max-Age=0'));
 console.log('Production HTTP smoke passed: route protection, CSRF, enrollment, login, cookie flags, error state, logout.');
}finally{receiver.close();server.kill();await new Promise(r=>server.once('exit',r));rmSync(dir,{recursive:true,force:true});}
