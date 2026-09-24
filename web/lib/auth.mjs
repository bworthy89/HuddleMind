import { randomBytes, scryptSync, timingSafeEqual, createHmac } from 'node:crypto';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';

export const cookieName = '__Secure-huddlemind';
const authPath = () => process.env.HUDDLEMIND_AUTH_FILE || '/data/auth.json';
function secret() {
  const value = process.env.HUDDLEMIND_SESSION_SECRET;
  if (!value || value.length < 32) throw new Error('Session configuration missing');
  return value;
}
function equal(a, b) {
  const x = Buffer.from(a), y = Buffer.from(b);
  return x.length === y.length && timingSafeEqual(x, y);
}
export function account() {
  try { return JSON.parse(readFileSync(/* turbopackIgnore: true */ authPath(), 'utf8')); }
  catch (error) { if (error.code === 'ENOENT') return null; throw error; }
}
export function enroll(password, key) {
  if (typeof password !== 'string' || password.length < 14 || password.length > 128) return false;
  const expected = process.env.HUDDLEMIND_SETUP_KEY;
  if (!expected || typeof key !== 'string' || !equal(key, expected) ||
      Date.now() > Number(process.env.HUDDLEMIND_SETUP_EXPIRES || 0)) return false;
  if (account()) return false;
  const salt = randomBytes(32).toString('hex');
  const hash = scryptSync(password, salt, 64, {N:32768,r:8,p:1,maxmem:67108864}).toString('hex');
  mkdirSync(dirname(authPath()), {recursive:true, mode:0o700});
  try {
    // Exclusive creation makes enrollment single-use, even with concurrent requests.
    writeFileSync(authPath(), JSON.stringify({salt,hash,version:randomBytes(16).toString('hex')}), {flag:'wx',mode:0o600});
    return true;
  } catch(error) { if(error.code === 'EEXIST') return false; throw error; }
}
export function verifyPassword(password) {
  if (typeof password !== 'string' || password.length > 128) return false;
  const user = account();
  if (!user) return false;
  const hash = scryptSync(password, user.salt, 64, {N:32768,r:8,p:1,maxmem:67108864}).toString('hex');
  return equal(hash, user.hash);
}
export function newSession(now=Date.now()) {
  const user=account(); if(!user) throw new Error('Account not initialized');
  const data=Buffer.from(JSON.stringify({expires:now+12*60*60*1000,version:user.version,nonce:randomBytes(16).toString('hex')})).toString('base64url');
  return data+'.'+createHmac('sha256',secret()).update(data).digest('base64url');
}
export function validSession(value, now=Date.now()) {
  if(typeof value !== 'string'||value.length>1024) return false;
  try {
    const [data,signature,extra]=value.split('.');
    if(extra||!signature||!equal(signature,createHmac('sha256',secret()).update(data).digest('base64url'))) return false;
    const payload=JSON.parse(Buffer.from(data,'base64url').toString());
    return Number.isFinite(payload.expires)&&payload.expires>now&&payload.expires<=now+12*60*60*1000&&payload.version===account()?.version;
  } catch {return false;}
}
