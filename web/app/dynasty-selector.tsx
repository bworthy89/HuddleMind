'use client';
import {useState} from 'react';
export default function DynastySelector({options,selected,changed}:{options:{id:string;label:string}[];selected?:string;changed?:boolean}){
 const [busy,setBusy]=useState(false),[error,setError]=useState('');
 async function choose(id:string){
  setBusy(true);setError('');
  try{
   const response=await fetch('/app/api/dynasty',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({dynasty_id:id})});
   if(!response.ok){const body=await response.json();throw new Error(body.error);}
   // Reload clears old player details and all client filters before showing another dynasty.
   window.location.replace(window.location.pathname);
  }catch(e){setError(e instanceof Error?e.message:'Could not switch dynasties.');setBusy(false);}
 }
 return <div className="dynasty-picker"><label htmlFor="dynasty-selection">Dynasty</label><select id="dynasty-selection" value={selected??''} disabled={busy||!options.length} onChange={e=>choose(e.target.value)}>{!options.length&&<option value="">No dynasties available</option>}{options.map(o=><option key={o.id} value={o.id}>{o.label}</option>)}</select>{busy&&<p role="status">Switching dynasty…</p>}{changed&&<p role="status">Your previous selection is no longer available. Showing an available dynasty.</p>}{error&&<p role="alert">{error}</p>}</div>;
}
