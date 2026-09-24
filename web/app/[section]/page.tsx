import {cookies} from 'next/headers';
import {notFound,redirect} from 'next/navigation';
import Link from 'next/link';
import {validSession,cookieName} from '../../lib/auth.mjs';
import BottomNav from '../bottom-nav';
import SignOut from '../sign-out';
export const dynamic='force-dynamic';
export default async function Section({params}:{params:Promise<{section:string}>}){
 const {section}=await params;
 const labels={roster:'Roster',schedule:'Schedule',recruiting:'Recruiting'};
 if(!(section in labels))notFound();
 if(!validSession((await cookies()).get(cookieName)?.value))redirect('/login');
 const title=labels[section as keyof typeof labels];
 return <div className="shell"><aside><div className="brand">Huddle<span>Mind</span></div><Link href="/">Overview</Link>{Object.entries(labels).map(([id,label])=><Link key={id} className={section===id?'active':''} href={'/'+id}>{label}</Link>)}</aside><div><header><div className="brand">Huddle<span>Mind</span></div><SignOut/></header><main><h1>{title}</h1><section className="card" style={{marginTop:24}}><h2>Coming next</h2><p>This screen is not connected yet. Your live dynasty summary is available on Overview.</p><Link href="/">Back to Overview →</Link></section><p className="note">You can still explore the planned {title.toLowerCase()} layout in the <a href={'/preview/#'+section}>sample design preview</a>.</p></main></div><BottomNav active={section}/></div>;
}
