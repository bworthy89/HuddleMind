import {ratingGroups} from '../../lib/ratings.mjs';
export default function PlayerRatings({ratings}:{ratings?:{field:string;value:number|null}[]}){
 return <section className="card"><h2>Saved ratings</h2><p className="note">Values stored in the save. Their relationship to base ratings and temporary in-game boosts has not been verified.</p>{!ratings?.length?<p>Individual ratings are unavailable in this snapshot. They will appear after a new save is captured by the updated bridge.</p>:ratingGroups(ratings).map(({group,ratings})=><details className="rating-group" key={group} open={group==='Physical and mental'}><summary>{group}</summary><dl>{ratings.map(r=><div className="rating-item" key={r.field}><dt>{r.label}</dt><dd>{r.value??'Unavailable'}</dd></div>)}</dl></details>)}</section>;
}
