import {NextRequest,NextResponse} from 'next/server';
import {cookieName,validSession} from '../../../lib/auth.mjs';
import {dynastyCookie} from '../../../lib/dynasties.mjs';
import {fetchDashboard} from '../../../lib/dashboard';
export async function POST(request:NextRequest){
 const headers={'Cache-Control':'no-store'};
 if(request.headers.get('origin')!==process.env.HUDDLEMIND_WEB_ORIGIN)return NextResponse.json({error:'Request origin rejected'},{status:403,headers});
 if(!validSession(request.cookies.get(cookieName)?.value))return NextResponse.json({error:'Please sign in again.'},{status:401,headers});
 if(Number(request.headers.get('content-length')||0)>2048)return NextResponse.json({error:'Request too large'},{status:413,headers});
 let id;
 try{const raw=await request.text();if(raw.length>2048)throw new Error();id=JSON.parse(raw).dynasty_id;if(typeof id!=='string'||!id||id.length>128)throw new Error();}
 catch{return NextResponse.json({error:'Invalid dynasty selection.'},{status:400,headers});}
 try{
  const data=await fetchDashboard();
  if(!data.dynasties.some(d=>d.dynasty_id===id))return NextResponse.json({error:'This dynasty is not available to your account.'},{status:403,headers});
  const response=NextResponse.json({ok:true},{headers});
  response.cookies.set(dynastyCookie,id,{httpOnly:true,secure:true,sameSite:'strict',path:'/app',maxAge:2592000});
  return response;
 }catch{return NextResponse.json({error:'Could not switch dynasties. Try again.'},{status:503,headers});}
}
