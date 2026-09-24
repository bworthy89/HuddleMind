import {cookies} from 'next/headers';
import {redirect} from 'next/navigation';
import {validSession,cookieName} from './auth.mjs';
import {dynastyCookie,selectDynasty,dynastyOptions} from './dynasties.mjs';

export async function fetchDashboard(){
 const response=await fetch((process.env.HUDDLEMIND_RECEIVER_URL||'http://receiver:8080')+'/v1/dashboard',{
  headers:{Authorization:'Bearer '+process.env.HUDDLEMIND_READ_TOKEN},cache:'no-store',signal:AbortSignal.timeout(10000)});
 if(!response.ok)throw new Error('Dashboard unavailable');
 return response.json();
}
// Every tab resolves the same cookie against current authorization and fetches without caching.
export async function loadDashboard(){
 const jar=await cookies();
 if(!validSession(jar.get(cookieName)?.value))redirect('/login');
 try{
  const data=await fetchDashboard(),selection=selectDynasty(data.dynasties,jar.get(dynastyCookie)?.value);
  return {available:true,data,entry:selection.entry,snapshot:selection.entry?.snapshot??null,
   options:dynastyOptions(data.dynasties),changed:selection.changed};
 }catch{return {available:false,data:null,entry:null,snapshot:null,options:[],changed:false};}
}
