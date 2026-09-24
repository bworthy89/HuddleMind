import SnapshotSection,{loadSectionSnapshot} from '../snapshot-section';
import ScheduleView from './schedule-view';
export const dynamic='force-dynamic';
export default async function Schedule(){
 const state=await loadSectionSnapshot(),p=state.snapshot?.payload;
 return <SnapshotSection section="schedule" state={state}>{p&&<ScheduleView games={p.schedule??null} season={p.season} team={p.roster.team.name}/>}</SnapshotSection>;
}
