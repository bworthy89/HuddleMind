import {test} from 'node:test';import assert from 'node:assert/strict';
import {selectDynasty,dynastyOptions} from '../lib/dynasties.mjs';
const entries=[{dynasty_id:'empty',snapshot:null},{dynasty_id:'one',snapshot:{payload:{roster:{team:{name:'Tulane'}}}}},{dynasty_id:'two',snapshot:{payload:{roster:{team:{name:'Tulane'}}}}}];
test('selection is authorized, stable, and can explicitly select an empty dynasty',()=>{
 assert.equal(selectDynasty(entries).entry.dynasty_id,'one');
 assert.equal(selectDynasty(entries,'two').entry.dynasty_id,'two');
 assert.equal(selectDynasty(entries,'empty').entry.snapshot,null);
 assert.equal(selectDynasty(entries,'unauthorized').entry.dynasty_id,'one');
 assert.equal(selectDynasty(entries,'unauthorized').changed,true);
 assert.equal(selectDynasty([], 'one').entry,null);
});
test('same-team dynasties and missing snapshots have distinguishable labels',()=>{
 const options=dynastyOptions(entries);
 assert.notEqual(options[1].label,options[2].label);
 assert.ok(options[0].label.includes('Awaiting first snapshot'));
});
