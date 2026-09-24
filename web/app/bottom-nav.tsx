import Link from 'next/link';
const tabs=[
 {id:'overview',label:'Overview',href:'/',path:'M3 10 12 3 21 10M5 9v12h5v-7h4v7h5V9'},
 {id:'roster',label:'Roster',href:'/roster',path:'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8M17 4a4 4 0 0 1 0 8M22 21v-2a4 4 0 0 0-3-4'},
 {id:'schedule',label:'Schedule',href:'/schedule',path:'M4 5h16v16H4zM7 3v4M17 3v4M4 10h16'},
 {id:'recruiting',label:'Recruiting',href:'/recruiting',path:'M6 3h9l4 4v14H6zM14 3v5h5M9 12h7M9 16h5'},
];
export default function BottomNav({active='overview'}:{active?:string}){
 return <nav className="bottom-nav" aria-label="Main navigation">{tabs.map(tab=><Link key={tab.id} href={tab.href} className={active===tab.id?'active':''} aria-current={active===tab.id?'page':undefined}><svg viewBox="0 0 24 24" aria-hidden="true"><path d={tab.path}/></svg><span>{tab.label}</span></Link>)}</nav>;
}
