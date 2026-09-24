'use client';
export default function SignOut(){return <button className="signout" onClick={async()=>{const response=await fetch('/app/api/session',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'logout'})});if(response.ok)location.assign('/app/login');else alert('Could not sign out. Please try again.');}}>Sign out</button>}
