import Link from 'next/link';
import {loadDashboard} from '../../lib/dashboard';
import DynastySelector from '../dynasty-selector';
import BottomNav from '../bottom-nav';
import SignOut from '../sign-out';
import RosterView from './roster-view';
export const dynamic='force-dynamic';
export default async function Roster(){
 const state=await loadDashboard(),{data,snapshot}=state,details=snapshot?.payload;
 return <div className="shell"><aside><div className="brand">Huddle<span>Mind</span></div><Link href="/">Overview</Link><Link className="active" aria-current="page" href="/roster">Roster</Link><Link href="/schedule">Schedule</Link><Link href="/recruiting">Recruiting</Link></aside><div><header><div className="brand">Huddle<span>Mind</span></div><span className="dynasty">{details?.roster.team.name||'Your dynasty'}</span><SignOut/></header><main>
 {state.available&&<DynastySelector options={state.options} selected={state.entry?.dynasty_id} changed={state.changed}/>}
 {!data?<section className="card"><h1>Roster unavailable</h1><p>We couldn’t reach your snapshot. Your saved data has not been removed.</p><Link href="/roster">Try again</Link></section>:!details?<section className="card"><h1>No snapshot received yet</h1><p>Your roster will appear after the bridge delivers a snapshot.</p></section>:<><p className="freshness">Snapshot captured {new Date(snapshot.observed_at).toLocaleString('en-US',{timeZone:'America/New_York',dateStyle:'medium',timeStyle:'short'})} ET</p><RosterView players={details.roster.team.players} team={details.roster.team.name} depth={details.depth_chart??null} health={details.health??[]}/></>}
 </main></div><BottomNav active="roster"/></div>;
}
