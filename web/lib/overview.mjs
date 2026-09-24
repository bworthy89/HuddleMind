// Keep schedule status authoritative; scores alone do not establish a final result.
export function summarize(payload) {
  const games=payload.schedule.filter(g=>g.season_index===payload.season.season_index);
  let wins=0,losses=0,ties=0;
  for(const g of games){
    if(g.status==='HomeWon')g.controlled_team_is_home?wins++:losses++;
    else if(g.status==='AwayWon')g.controlled_team_is_home?losses++:wins++;
    else if(g.status==='Tied')ties++;
  }
  const pending=games.filter(g=>['Unplayed','HomeScheduled','AwayScheduled'].includes(g.status)&&g.week>=payload.season.week);
  const nextWeek=Math.min(...pending.map(g=>g.week));
  return {wins,losses,ties,next:pending.filter(g=>g.week===nextWeek)};
}
