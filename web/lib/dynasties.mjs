export const dynastyCookie='__Secure-huddlemind-dynasty';
// A browser preference never grants access: select only from the receiver's authorized list.
export function selectDynasty(dynasties, preferred) {
 const selected=dynasties.find(d=>d.dynasty_id===preferred);
 return {entry:selected??dynasties.find(d=>d.snapshot)??dynasties[0]??null,
  changed:Boolean(preferred&&!selected)};
}
export function dynastyOptions(dynasties){
 const name=d=>d.snapshot?.payload.roster.team.name??'Awaiting first snapshot';
 return dynasties.map(d=>({id:d.dynasty_id,label:name(d)+(dynasties.filter(other=>name(other)===name(d)).length>1?' · '+d.dynasty_id:'')}));
}
