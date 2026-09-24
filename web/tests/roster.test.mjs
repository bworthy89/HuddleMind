import {test} from 'node:test';import assert from 'node:assert/strict';
import {visiblePlayers,playerDetails,playerKey,fullName} from '../lib/roster.mjs';
const player=(first,position,overall,table=1,row=1)=>({first_name:first,last_name:'Example',position,overall,record_id:{table_id:table,row_id:row}});
test('search trims input and ignores case; sorts a copy with deterministic rating ties',()=>{
 const players=[player('Zed','QB',80),player('Amy','QB',80,1,2),player('Ben','WR',90,1,3)];
 assert.deepEqual(visiblePlayers(players).map(p=>p.first_name),['Ben','Amy','Zed']);
 assert.deepEqual(players.map(p=>p.first_name),['Zed','Amy','Ben']);
 assert.equal(visiblePlayers(players,'  aMY  ')[0].first_name,'Amy');
 assert.deepEqual(visiblePlayers(players,'','All','name').map(p=>p.first_name),['Amy','Ben','Zed']);
 assert.equal(visiblePlayers(players,'missing').length,0);
});
test('exact positions, defense grouping, empty roster, and unknown positions',()=>{
 const players=[player('A','QB',80),player('B','CB',75),player('C','ROLB',77),player('D','Unknown (99)',72)];
 assert.equal(visiblePlayers(players,'','QB').length,1);
 assert.equal(visiblePlayers(players,'','Defense').length,2);
 assert.equal(visiblePlayers(players,'','Unknown (99)').length,1);
 assert.deepEqual(visiblePlayers([]),[]);
});
test('details require both ID parts and distinguish missing from no placement',()=>{
 const p=player('Test','QB',80,2,1);
 const depth=[{position:'QB',depth:2,player_id:p.record_id},{position:'HB',depth:1,player_id:{table_id:1,row_id:1}},{position:'QB',depth:1,player_id:null}];
 const health=[{player_id:{table_id:1,row_id:1},status:'wrong'},{player_id:p.record_id,status:'right'}];
 assert.equal(playerDetails(p,depth,health).depth.length,1);
 assert.equal(playerDetails(p,depth,health).health.status,'right');
 assert.equal(playerDetails(p,null,[]).depth,null);
 assert.deepEqual(playerDetails(p,[],[]).depth,[]);
 assert.equal(playerDetails(p,[],[]).health,null);
 assert.equal(playerKey(p),'2-1');assert.equal(fullName(p),'Test Example');
});
