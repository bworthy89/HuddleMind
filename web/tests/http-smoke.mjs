// Production-build HTTP checks use a temporary account, never the owner's setup key.
import {spawn} from 'node:child_process';
import {mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';import {join} from 'node:path';
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
const dir=mkdtempSync(join(tmpdir(),'huddlemind-http-'));
const origin='http://127.0.0.1:3017';
const receiver=createServer((request,response)=>{response.setHeader('Content-Type','application/json');response.end(JSON.stringify({dynasties:[{dynasty_id:'sample',snapshot:{observed_at:'2026-09-23T18:00:00Z',payload:{roster:{team:{name:'Sample Team',players:[]},coach:{first_name:'Sample',last_name:'Coach'}},season:{calendar_year:2026,week:2,season_index:0,stage:{label:'Season'}},schedule:[],recruiting:null}}}],bridges:[]}));});
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
 const home=await fetch(origin+'/app',{headers:{Cookie:cookie.split(';')[0]}});assert.equal(home.status,200);assert.ok((await home.text()).includes('Sample Team'));
 await new Promise(r=>receiver.close(r));
 const unavailable=await fetch(origin+'/app',{headers:{Cookie:cookie.split(';')[0]}});assert.ok((await unavailable.text()).includes('We couldn’t load your dynasty'));
 const logout=await post({action:'logout'});assert.ok(logout.headers.get('set-cookie').includes('Max-Age=0'));
 console.log('Production HTTP smoke passed: route protection, CSRF, enrollment, login, cookie flags, error state, logout.');
}finally{receiver.close();server.kill();await new Promise(r=>server.once('exit',r));rmSync(dir,{recursive:true,force:true});}
