import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {enroll,verifyPassword,newSession,validSession,account} from '../lib/auth.mjs';
test('one-time enrollment, password hashing, and expiring signed sessions',()=>{
 const dir=mkdtempSync(join(tmpdir(),'huddlemind-auth-'));
 try{
  process.env.HUDDLEMIND_AUTH_FILE=join(dir,'auth.json');
  process.env.HUDDLEMIND_SETUP_KEY='synthetic-setup-key';
  process.env.HUDDLEMIND_SETUP_EXPIRES=String(Date.now()+60000);
  process.env.HUDDLEMIND_SESSION_SECRET='x'.repeat(48);
  assert.equal(enroll('short','synthetic-setup-key'),false);
  assert.equal(enroll('a long test passphrase','wrong'),false);
  assert.equal(enroll('a long test passphrase','synthetic-setup-key'),true);
  assert.equal(enroll('a different test passphrase','synthetic-setup-key'),false);
  assert.equal(verifyPassword('a long test passphrase'),true);
  assert.equal(verifyPassword('wrong'),false);
  assert.equal(JSON.stringify(account()).includes('a long test passphrase'),false);
  const now=Date.now(), session=newSession(now);
  assert.equal(validSession(session,now),true);
  assert.equal(validSession(session,now+43200001),false);
  assert.equal(validSession(session+'bad',now),false);
  assert.equal(validSession('garbage'),false);
  process.env.HUDDLEMIND_SESSION_SECRET='y'.repeat(48);
  assert.equal(validSession(session),false);
 }finally{rmSync(dir,{recursive:true,force:true});}
});
