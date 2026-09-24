// Record IDs identify players within this snapshot; they are not cross-save identities.
export const playerKey = player => `${player.record_id.table_id}-${player.record_id.row_id}`;
export const fullName = player => `${player.first_name} ${player.last_name}`.trim();
const defense = new Set(['LE','RE','DT','LOLB','MLB','ROLB','CB','FS','SS']);
export function visiblePlayers(players, query='', position='All', sort='overall') {
  const term=query.trim().toLocaleLowerCase();
  return players.filter(player=>fullName(player).toLocaleLowerCase().includes(term)&&
    (position==='All'||player.position===position||position==='Defense'&&defense.has(player.position)))
    .sort((a,b)=>(sort==='overall'?b.overall-a.overall:0)||
      fullName(a).localeCompare(fullName(b),undefined,{sensitivity:'base'})||playerKey(a).localeCompare(playerKey(b)));
}
export function playerDetails(player, depthChart, health) {
  const same = id => id?.table_id===player.record_id.table_id&&id?.row_id===player.record_id.row_id;
  return {depth:depthChart===null?null:depthChart.filter(slot=>same(slot.player_id)).sort((a,b)=>a.position.localeCompare(b.position)||a.depth-b.depth),
          health:health.find(item=>same(item.player_id))??null};
}
