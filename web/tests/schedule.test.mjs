import {test} from 'node:test';
import assert from 'node:assert/strict';
import {gameResult,gameState,seasonSchedule} from '../lib/schedule.mjs';
const game={record_id:{table_id:1,row_id:0},season_index:0,week:1,status:'AwayWon',controlled_team_is_home:false,home_score:0,away_score:7};
test('results follow status and controlled side, not score guesses',()=>{
 assert.equal(gameResult(game),'W');
 assert.equal(gameResult({...game,controlled_team_is_home:true}),'L');
 assert.equal(gameResult({...game,status:'HomeWon'}),'L');
 assert.equal(gameResult({...game,status:'HomeWon',controlled_team_is_home:true}),'W');
 assert.equal(gameResult({...game,status:'Tied',away_score:0}),'T');
 for(const status of ['Unplayed','HomeScheduled','AwayScheduled','Unscheduled']){
  assert.equal(gameResult({...game,status}),null);assert.equal(gameState({...game,status}),'pending');
 }
 assert.equal(gameState({...game,status:'NewStatus'}),'unknown');
});
test('season filtering, order, unknowns and next-week ambiguity preserve input',()=>{
 const games=[{...game,week:4,status:'Unplayed'},{...game,status:'NewStatus'},game,{...game,season_index:1},
 {...game,week:4,status:'HomeScheduled'},{...game,week:2,status:'Unscheduled'}];
 const before=structuredClone(games),result=seasonSchedule(games,{season_index:0,week:3});
 assert.deepEqual(result.counts,{wins:1,losses:0,ties:0,pending:3,unknown:1});
 assert.equal(result.nextWeek,4);assert.equal(result.games.filter(g=>g.week===result.nextWeek).length,2);
 assert.deepEqual(result.games.map(g=>g.week),[1,1,2,4,4]);assert.deepEqual(games,before);
 assert.equal(seasonSchedule([],{season_index:0,week:0}).games.length,0);
});
