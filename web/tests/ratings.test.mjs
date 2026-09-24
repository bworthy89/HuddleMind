import {test} from 'node:test';import assert from 'node:assert/strict';
import {ratingGroups} from '../lib/ratings.mjs';
test('saved ratings distinguish zero, absent fields, and values above 99',()=>{
 const all=ratingGroups([{field:'SpeedRating',value:0},{field:'StrengthRating',value:127}]).flatMap(g=>g.ratings);
 assert.equal(all.find(r=>r.field==='SpeedRating').value,0);
 assert.equal(all.find(r=>r.field==='StrengthRating').value,127);
 assert.equal(all.find(r=>r.field==='AccelerationRating').value,null);
 assert.ok(ratingGroups().every(g=>g.ratings.every(r=>r.value===null)));
});
