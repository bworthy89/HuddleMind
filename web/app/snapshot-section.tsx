import Link from 'next/link';
import {loadDashboard} from '../lib/dashboard';
import DynastySelector from './dynasty-selector';
import BottomNav from './bottom-nav';
import SignOut from './sign-out';
import type {ReactNode} from 'react';

// Check the session before requesting private data. The read token stays on the server.
export const loadSectionSnapshot=loadDashboard;
export default function SnapshotSection({section,state,children}:{section:'schedule'|'recruiting';state:Awaited<ReturnType<typeof loadSectionSnapshot>>;children:ReactNode}){
 const title=section==='schedule'?'Schedule':'Recruiting',snapshot=state.snapshot;
 return <div className="shell"><aside><div className="brand">Huddle<span>Mind</span></div>{[['Overview','/'],['Roster','/roster'],['Schedule','/schedule'],['Recruiting','/recruiting']].map(([label,href])=><Link key={href} href={href} className={href==='/'+section?'active':''} aria-current={href==='/'+section?'page':undefined}>{label}</Link>)}</aside><div><header><div className="brand">Huddle<span>Mind</span></div><span className="dynasty">{snapshot?.payload.roster.team.name||'Your dynasty'}</span><SignOut/></header><main>
 {state.available&&<DynastySelector options={state.options} selected={state.entry?.dynasty_id} changed={state.changed}/>}
 {!state.available?<section className="card"><h1>{title} unavailable</h1><p>We couldn’t reach your snapshot. Your saved data has not been removed.</p><a href={'/app/'+section}>Try again</a></section>:!snapshot?<section className="card"><h1>No snapshot received yet</h1><p>Your {section} will appear after the bridge delivers a snapshot.</p></section>:<><p className="freshness">Snapshot captured {new Date(snapshot.observed_at).toLocaleString('en-US',{timeZone:'America/New_York',dateStyle:'medium',timeStyle:'short'})} ET</p>{children}</>}
 </main></div><BottomNav active={section}/></div>;
}
