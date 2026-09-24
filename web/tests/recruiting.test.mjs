import {test} from 'node:test';import assert from 'node:assert/strict';
import {enumLabel,rankLabel,targetKey,visibleTargets} from '../lib/recruiting.mjs';
const target={record_id:{table_id:1,row_id:0},name:'Alex Sample',position:{label:'QB'},stage:{label:'Top5'},national_rank:10,hours_spent_current:0};
test('recruit filters combine, trim search and preserve unfamiliar labels',()=>{
 const targets=[target,{...target,record_id:{table_id:2,row_id:0},position:{label:'Unknown (99)'},stage:{label:'Unknown (8)'}}];
 assert.equal(visibleTargets(targets,' ALEX ','QB','Top5').length,1);
 assert.equal(visibleTargets(targets,'','Unknown (99)','Unknown (8)').length,1);
 assert.equal(visibleTargets(targets,'nobody').length,0);
 assert.notEqual(targetKey(targets[0]),targetKey(targets[1]));
});
test('recruit sorting puts unavailable ranks last and keeps zero hours and input intact',()=>{
 const targets=[{...target,name:'Unranked',national_rank:0},{...target,name:'Better',national_rank:1,hours_spent_current:25},target];
 const before=structuredClone(targets);
 assert.deepEqual(visibleTargets(targets).map(t=>t.name),['Better','Alex Sample','Unranked']);
 assert.equal(visibleTargets(targets,'','All','All','hours')[0].name,'Better');
 assert.equal(visibleTargets(targets,'','All','All','name')[0].name,'Alex Sample');
 assert.equal(visibleTargets([target])[0].hours_spent_current,0);assert.deepEqual(targets,before);
 assert.equal(rankLabel(0),'Unranked / unavailable');assert.equal(rankLabel(1),'#1');
 assert.equal(enumLabel({label:'Unknown (7)'}),'Unknown (7)');assert.equal(enumLabel(null),'Unavailable');
 assert.deepEqual(visibleTargets([]),[]);
});
