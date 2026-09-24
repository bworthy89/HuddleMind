const finals = new Set(['HomeWon', 'AwayWon', 'Tied']);
const pending = new Set(['Unscheduled', 'Unplayed', 'HomeScheduled', 'AwayScheduled']);

// Status establishes completion; a saved zero score alone does not mean a tie.
export function gameResult(game) {
  if (game.status === 'Tied') return 'T';
  if (finals.has(game.status)) return (game.status === 'HomeWon') === game.controlled_team_is_home ? 'W' : 'L';
  return null;
}
export function gameState(game) {
  return finals.has(game.status) ? 'completed' : pending.has(game.status) ? 'pending' : 'unknown';
}
export function seasonSchedule(games, season) {
  const sorted = games.filter(g => g.season_index === season.season_index)
    .sort((a,b) => a.week-b.week || a.record_id.table_id-b.record_id.table_id || a.record_id.row_id-b.record_id.row_id);
  const counts = {wins:0, losses:0, ties:0, pending:0, unknown:0};
  for (const game of sorted) {
    const result = gameResult(game);
    if (result) counts[{W:'wins', L:'losses', T:'ties'}[result]]++;
    else counts[gameState(game)]++;
  }
  // Preserve multiple fixtures at the same next week instead of choosing arbitrarily.
  const nextWeek = Math.min(...sorted.filter(g => ['Unplayed','HomeScheduled','AwayScheduled'].includes(g.status) && g.week >= season.week).map(g => g.week));
  return {games:sorted, counts, nextWeek};
}
