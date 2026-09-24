'use client';
import {useEffect,useState} from 'react';
export default function Login(){
 const [key,setKey]=useState(''),[password,setPassword]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 useEffect(()=>{const value=new URLSearchParams(location.hash.slice(1)).get('setup');if(value){setKey(value);history.replaceState(null,'',location.pathname);}},[]);
 async function submit(e:React.FormEvent){e.preventDefault();setBusy(true);setError('');try{
   const response=await fetch('/app/api/session',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:key?'setup':'login',password,key})});
   if(response.ok){location.assign('/app');return;}const data=await response.json();setError(data.error);
 }catch{setError('Could not reach HuddleMind. Please try again.');}finally{setBusy(false);}}
 return <main className="signin"><div className="brand">Huddle<span>Mind</span></div><p className="eyebrow">Your dynasty headquarters</p><section className="card"><h1>{key?'Make it yours':'Welcome back'}</h1><p>{key?'Choose a password to activate your private headquarters.':'Sign in to view your latest synced dynasty.'}</p><form onSubmit={submit}><label htmlFor="password">{key?'Create password':'Password'}</label><input id="password" type="password" minLength={key?14:1} maxLength={128} required autoComplete={key?'new-password':'current-password'} value={password} onChange={e=>setPassword(e.target.value)}/>{key&&<small>Use at least 14 characters. A memorable passphrase works well.</small>}<button className="primary" disabled={busy}>{busy?'Please wait…':key?'Create account':'Sign in'}</button><p role="alert">{error}</p></form></section><p className="note">Your bridge keeps syncing independently of this browser.</p></main>
}
