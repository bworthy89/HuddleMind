import './style.css';
export const viewport={width:'device-width',initialScale:1,viewportFit:'cover',themeColor:'#0b1420'};
export const metadata={title:'HuddleMind',description:'Your dynasty headquarters',robots:'noindex, nofollow'};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>}
