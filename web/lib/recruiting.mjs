export function enumLabel(value) { return value?.label ?? 'Unavailable'; }
export function targetKey(target) { return `${target.record_id.table_id}-${target.record_id.row_id}`; }
// A nonpositive rank is not presented as a real placement in the rankings.
export function rankLabel(rank) { return Number.isInteger(rank) && rank > 0 ? '#'+rank : 'Unranked / unavailable'; }
export function visibleTargets(targets, query='', position='All', stage='All', sort='rank') {
  const rank = t => Number.isInteger(t.national_rank) && t.national_rank > 0 ? t.national_rank : Infinity;
  return targets.filter(t => t.name.toLowerCase().includes(query.trim().toLowerCase()) &&
    (position === 'All' || enumLabel(t.position) === position) && (stage === 'All' || enumLabel(t.stage) === stage))
    .sort((a,b) => (sort === 'hours' ? (b.hours_spent_current ?? -1)-(a.hours_spent_current ?? -1) : sort === 'rank' ? rank(a)-rank(b) : 0) ||
      a.name.localeCompare(b.name, 'en', {sensitivity:'base'}) || targetKey(a).localeCompare(targetKey(b)));
}
