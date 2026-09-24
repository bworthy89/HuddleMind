import {test} from 'node:test';import assert from 'node:assert/strict';import {summarize} from '../lib/overview.mjs';
test('current season results follow statuses and keep next-game ambiguity',()=>{
 const game={season_index:0,week:1,status:'AwayWon',controlled_team_is_home:false};
 const result=summarize({season:{season_index:0,week:2},schedule:[game,{...game,status:'Tied'},
  {...game,status:'HomeWon'}, {...game,season_index:1}, {...game,status:'Unknown'},
  {...game,week:2,status:'Unplayed'}, {...game,week:2,status:'HomeScheduled'},
  {...game,week:3,status:'Unplayed'}]});
 assert.equal(result.wins,1);assert.equal(result.losses,1);assert.equal(result.ties,1);assert.equal(result.next.length,2);
});
test('empty season has no invented next opponent',()=>assert.equal(summarize({season:{season_index:0,week:2},schedule:[]}).next.length,0));
