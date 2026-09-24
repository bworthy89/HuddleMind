import {NextRequest,NextResponse} from 'next/server';
import {enroll,verifyPassword,newSession,cookieName} from '../../../lib/auth.mjs';
export const runtime='nodejs';
let windowStart=0, attempts=0;
export async function POST(request:NextRequest){
  const headers={'Cache-Control':'no-store'};
  if(request.headers.get('origin')!==process.env.HUDDLEMIND_WEB_ORIGIN) return NextResponse.json({error:'Request origin rejected'},{status:403,headers});
  if(Date.now()-windowStart>60000){windowStart=Date.now();attempts=0;}
  if(++attempts>10)return NextResponse.json({error:'Too many attempts. Try again in a minute.'},{status:429,headers});
  if(Number(request.headers.get('content-length')||0)>2048)return NextResponse.json({error:'Request too large'},{status:413,headers});
  try{
    const raw=await request.text();if(raw.length>2048)throw new Error();
    const body=JSON.parse(raw);
    if(body.action==='logout'){
      const result=NextResponse.json({ok:true},{headers});
      result.cookies.set(cookieName,'',{httpOnly:true,secure:true,sameSite:'strict',path:'/app',maxAge:0});return result;
    }
    const ok=body.action==='setup'?enroll(body.password,body.key):body.action==='login'&&verifyPassword(body.password);
    if(!ok)return NextResponse.json({error:'Sign-in or setup could not be completed.'},{status:401,headers});
    const result=NextResponse.json({ok:true},{headers});
    result.cookies.set(cookieName,newSession(),{httpOnly:true,secure:true,sameSite:'strict',path:'/app',maxAge:43200});
    return result;
  }catch{return NextResponse.json({error:'Sign-in could not be completed.'},{status:400,headers});}
}
