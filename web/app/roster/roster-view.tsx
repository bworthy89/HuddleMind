'use client';
import {useEffect,useRef,useState} from 'react';
import PlayerRatings from './player-ratings';
import {fullName,playerKey,visiblePlayers,playerDetails} from '../../lib/roster.mjs';
type Id={table_id:number;row_id:number};
type Player={record_id:Id;first_name:string;last_name:string;position:string;overall:number;ratings?:{field:string;value:number|null}[]};
type Enum={value:number;label:string};
type Depth={position:string;depth:number;player_id:Id|null};
type Health={player_id:Id;status:Enum;injury_type:Enum;severity:Enum;injured_reserve:boolean};
export default function RosterView({players,depth,health,team}:{players:Player[];depth:Depth[]|null;health:Health[];team:string}){
 const [query,setQuery]=useState(''),[position,setPosition]=useState('All'),[sort,setSort]=useState('overall'),[selected,setSelected]=useState('');
 const heading=useRef<HTMLHeadingElement>(null),returnKey=useRef('');
 useEffect(()=>{const read=()=>{setSelected(new URLSearchParams(location.hash.slice(1)).get('player')||'');};read();window.addEventListener('hashchange',read);return()=>window.removeEventListener('hashchange',read);},[]);
 useEffect(()=>{if(selected){heading.current?.focus();window.scrollTo(0,0);}else if(returnKey.current){document.getElementById('player-'+returnKey.current)?.focus();returnKey.current='';}},[selected]);
 const selectedPlayer=players.find(p=>playerKey(p)===selected);
 const filtered=visiblePlayers(players,query,position,sort);
 const positions=Array.from(new Set(players.map(p=>p.position))).sort();
 function open(player:Player){returnKey.current=playerKey(player);location.hash='player='+encodeURIComponent(playerKey(player));}
 function back(){location.hash='';}
 if(selected){
  if(!selectedPlayer)return <><button className="back" onClick={back}>← Roster</button><h1 ref={heading} tabIndex={-1}>Player unavailable</h1><p>This player is not in the currently loaded snapshot.</p></>;
  const detail=playerDetails(selectedPlayer,depth,health);
  return <><button className="back" onClick={back}>← Roster</button><div className="eyebrow">Player details</div><h1 ref={heading} tabIndex={-1}>{fullName(selectedPlayer)}</h1><p>{selectedPlayer.position} · {team}</p><section className="card player-card"><dl><dt>Overall rating</dt><dd className="rating">{selectedPlayer.overall}</dd><dt>Position</dt><dd>{selectedPlayer.position}</dd></dl></section><PlayerRatings ratings={selectedPlayer.ratings}/><section className="card"><h2>Depth chart</h2>{detail.depth===null?<p>Unavailable in this snapshot.</p>:detail.depth.length===0?<p>No placement listed in this snapshot.</p>:<ul className="depth-list">{detail.depth.map((slot:Depth)=><li key={slot.position+'-'+slot.depth}><span>{slot.position}</span><strong>Depth {slot.depth}</strong></li>)}</ul>}</section><section className="card"><h2>Injury information</h2>{detail.health?<dl><dt>Status</dt><dd>{detail.health.status.label}</dd><dt>Injury type</dt><dd>{detail.health.injury_type.label}</dd><dt>Severity</dt><dd>{detail.health.severity.label}</dd><dt>Injured reserve</dt><dd>{detail.health.injured_reserve?'Yes':'No'}</dd></dl>:<p>Unavailable in this snapshot.</p>}</section><p className="verification">Depth-chart and injury fields are read from the save. Their final in-game verification is still pending.</p></>;
 }
 return <><h1>Roster</h1><p>{team} · {players.length} players</p><label className="sr-only" htmlFor="roster-search">Search players by name</label><input id="roster-search" className="roster-search" type="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search players…"/>
 <div className="position-chips" aria-label="Quick position filters">{['All','QB','HB','WR','Defense'].map(value=><button key={value} aria-pressed={position===value} className={position===value?'selected':''} onClick={()=>setPosition(value)}>{value}</button>)}</div>
 <div className="roster-controls"><label>Position<select value={position} onChange={e=>setPosition(e.target.value)}><option value="All">All positions</option><option value="Defense">Defense</option>{positions.map(value=><option key={value}>{value}</option>)}</select></label><label>Sort by<select value={sort} onChange={e=>setSort(e.target.value)}><option value="overall">Overall: high to low</option><option value="name">Name: A–Z</option></select></label></div>
 <p className="result-count" role="status">Showing {filtered.length} of {players.length} players</p>
 {players.length===0?<section className="card"><h2>No roster players</h2><p>This snapshot contains an empty roster.</p></section>:filtered.length===0?<section className="card"><h2>No matching players</h2><p>Try another name or position.</p><button className="back" onClick={()=>{setQuery('');setPosition('All');}}>Clear filters</button></section>:<div className="roster-table"><div className="roster-row table-heading" aria-hidden="true"><span>Player</span><span>Pos</span><span>OVR</span><span/></div>{filtered.map((player:Player)=><button id={'player-'+playerKey(player)} key={playerKey(player)} className="roster-row" onClick={()=>open(player)} aria-label={`${fullName(player)}, ${player.position}, overall ${player.overall}. View details`}><span className="player-name">{fullName(player)}</span><span>{player.position}</span><span className="rating">{player.overall}</span><span aria-hidden="true">›</span></button>)}</div>}
 <p className="note" style={{marginTop:20}}>Tap a player to view details from this snapshot.</p></>;
}
