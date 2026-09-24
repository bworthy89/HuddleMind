import {cookies} from 'next/headers';
import {redirect} from 'next/navigation';
import {validSession,cookieName} from '../lib/auth.mjs';
import {summarize} from '../lib/overview.mjs';
import SignOut from './sign-out';
export const dynamic='force-dynamic';
type Game={week:number;season_index:number;away_team:string;home_team:string;status:string;controlled_team_is_home:boolean};
type Snapshot={observed_at:string;payload:{roster:{team:{name:string;players:unknown[]};coach:{first_name:string;last_name:string}};season:{calendar_year:number;week:number;season_index:number;stage:{label:string}};schedule:Game[];recruiting:{targets:unknown[];hours_total:number;hours_assigned:number}|null}};
type Bridge={dynasty_id:string;status:string;last_seen_at:string|null;report:{capture_running:boolean;pending_count:number;last_capture_at:string|null;last_delivery_at:string|null;capture_error:string|null;delivery_error:string|null}|null};
type Dashboard={dynasties:{dynasty_id:string;snapshot:Snapshot|null;received_at:string|null}[];bridges:Bridge[]};
function timestamp(value:string|null){return value?new Date(value).toLocaleString('en-US',{timeZone:'America/New_York',dateStyle:'medium',timeStyle:'short'})+' ET':'Not yet reported';}
export default async function Overview(){
 if(!validSession((await cookies()).get(cookieName)?.value))redirect('/login');
 let data:Dashboard|null=null;
 try{
   const response=await fetch((process.env.HUDDLEMIND_RECEIVER_URL||'http://receiver:8080')+'/v1/dashboard',{headers:{Authorization:'Bearer '+process.env.HUDDLEMIND_READ_TOKEN},cache:'no-store',signal:AbortSignal.timeout(10000)});
   if(!response.ok)throw new Error();data=await response.json();
 }catch{}
 const entry=data?.dynasties[0],snapshot=entry?.snapshot,p=snapshot?.payload;
 const bridge=data?.bridges.find(b=>b.dynasty_id===entry?.dynasty_id),summary=p?summarize(p):null;
 return <div className="shell"><aside><div className="brand">Huddle<span>Mind</span></div><div className="active">Overview</div><p className="note">Roster, Schedule, and Recruiting screens are coming next.</p><a href="/preview/">Design preview ↗</a></aside><div><header><div className="brand">Huddle<span>Mind</span></div><span className="dynasty">{p?.roster.team.name||'Your dynasty'}</span><SignOut/></header><main>
 <a className="status" href="#bridge"><span className={bridge?.status==='online'?'dot':'dot muted'}/>{bridge?'Bridge '+bridge.status:'Bridge status unavailable'} <span>· View details</span></a>
 {!data?<section className="card"><h1>We couldn’t load your dynasty</h1><p>Your saved snapshots have not been removed. Refresh to try again.</p><a className="button" href="/app">Try again</a></section>:!p?<section className="card"><h1>Your headquarters is ready</h1><p>No snapshot has arrived yet. Start capture on your gaming PC and let the bridge deliver your first observation.</p></section>:<>
 <div className="eyebrow">Your dynasty, at a glance</div><h1>{p.roster.team.name}</h1><p>Coach {p.roster.coach.first_name} {p.roster.coach.last_name}</p>
 <div className="chips"><span>{p.season.calendar_year} season</span><span>Week {p.season.week}</span><span>{p.season.stage.label}</span></div>
 <p className="freshness">Snapshot captured {timestamp(snapshot!.observed_at)}<br/><small>Showing the latest received snapshot. Online status does not mean a new save was captured.</small></p>
 <div className="overview"><section className="card hero"><div className="eyebrow">Next scheduled game{summary!.next.length>1?'s':''}</div>{summary!.next.length?summary!.next.map((g:Game,i:number)=><div className="match" key={i}><h2>{g.away_team}<small>Away</small></h2><span>AT</span><h2>{g.home_team}<small>Home</small></h2><p>Week {g.week}</p></div>):<p>No upcoming game in this snapshot.</p>}<div className="rule"/><p>{p.roster.team.name} season record</p><strong className="record">{summary!.wins}–{summary!.losses}{summary!.ties?'–'+summary!.ties:''}</strong></section>
 <div className="grid"><section className="card"><p>Roster</p><strong className="stat">{p.roster.team.players.length}</strong><small>players</small></section><section className="card"><p>Recruiting board</p><strong className="stat">{p.recruiting?.targets.length??'—'}</strong><small>{p.recruiting?'targets':'Unavailable'}</small></section><section className="card"><p>Recruiting hours</p><strong className="stat">{p.recruiting?.hours_total??'—'}</strong><small>total</small></section><section className="card"><p>Assigned hours</p><strong className="stat">{p.recruiting?.hours_assigned??'—'}</strong><small>current board</small></section></div></div></>}
 <section className="card" id="bridge"><h2>Bridge status</h2><p className="note">Last reported state{bridge?.status==='offline'?' · May be out of date':''}</p><dl><dt>Last contact</dt><dd>{timestamp(bridge?.last_seen_at||null)}</dd><dt>Capture watcher</dt><dd>{bridge?.report?(bridge.report.capture_running?'Running':'Not running'):'Unknown'}</dd><dt>Pending observations</dt><dd>{bridge?.report?.pending_count??'Unknown'}</dd><dt>Last successful capture</dt><dd>{timestamp(bridge?.report?.last_capture_at||null)}</dd><dt>Last delivery</dt><dd>{timestamp(bridge?.report?.last_delivery_at||null)}</dd><dt>Reported errors</dt><dd>{bridge?.report?([bridge.report.capture_error,bridge.report.delivery_error].filter(Boolean).join(', ')||'None'):'Unknown'}</dd></dl><a href="/app">Refresh status</a></section>
 <footer>Read-only dynasty view · All times Eastern · <a href="/preview/">Sample design preview</a></footer></main></div><nav><a className="active" href="/app">⌂<br/>Overview</a><a href="#bridge">◉<br/>Bridge status</a></nav></div>
}
