const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
export async function api(path:string, options:any={}) {
  const token=localStorage.getItem("token");
  const headers:any={"Content-Type":"application/json",...(options.headers||{})};
  if(token) headers.Authorization=`Bearer ${token}`;
  const r=await fetch(API+path,{...options,headers});
  const data=await r.json().catch(()=>({}));
  if(!r.ok) throw new Error(data.detail||"Server error");
  return data;
}
export {API};
