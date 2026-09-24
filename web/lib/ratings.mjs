const groups={
 'Physical and mental':['Speed','Acceleration','Agility','ChangeOfDirection','Strength','Awareness','Jumping','Stamina','Toughness','Injury','Confidence'],
 'Passing':['ThrowPower','ThrowAccuracy','ThrowAccuracyShort','ThrowAccuracyMid','ThrowAccuracyDeep','ThrowOnTheRun','ThrowUnderPressure','PlayAction','BreakSack'],
 'Ball carrying':['Carrying','BCVision','BreakTackle','Trucking','StiffArm','SpinMove','JukeMove'],
 'Receiving':['Catching','CatchInTraffic','SpectacularCatch','ShortRouteRunning','MediumRouteRunning','DeepRouteRunning','Release'],
 'Blocking':['PassBlock','PassBlockPower','PassBlockFinesse','RunBlock','RunBlockPower','RunBlockFinesse','ImpactBlocking','LeadBlock'],
 'Defense':['Tackle','HitPower','Pursuit','PlayRecognition','BlockShedding','PowerMoves','FinesseMoves','ManCoverage','ZoneCoverage','Press'],
 'Special teams':['KickPower','KickAccuracy','KickReturn','LongSnap'],
};
export function ratingGroups(ratings=[]){
 const values=new Map(ratings.map(r=>[r.field,r.value]));
 return Object.entries(groups).map(([group,names])=>({group,ratings:names.map(name=>({
  field:name+'Rating',label:name==='BCVision'?'Ball carrier vision':name.replace(/([a-z])([A-Z])/g,'$1 $2'),
  value:values.get(name+'Rating')??null,
 }))}));
}
