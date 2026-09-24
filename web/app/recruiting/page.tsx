import SnapshotSection,{loadSectionSnapshot} from '../snapshot-section';
import RecruitingView from './recruiting-view';
export const dynamic='force-dynamic';
export default async function Recruiting(){
 const state=await loadSectionSnapshot(),p=state.snapshot?.payload;
 return <SnapshotSection section="recruiting" state={state}>{p&&<RecruitingView board={p.recruiting??null} team={p.roster.team.name}/>}</SnapshotSection>;
}
