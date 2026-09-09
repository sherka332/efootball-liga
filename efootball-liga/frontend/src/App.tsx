import {useEffect,useState} from "react"; import {api,API} from "./api";

declare global { interface Window { Telegram?: any } }

export default function App(){
 const [me,setMe]=useState<any>(null),[seasons,setSeasons]=useState<any[]>([]),[selected,setSelected]=useState<any>(null),[stand,setStand]=useState<any[]>([]),[matches,setMatches]=useState<any[]>([]),[err,setErr]=useState("");
 const tg=window.Telegram?.WebApp;
 useEffect(()=>{ tg?.ready(); tg?.expand(); autoLogin(); load(); },[]);
 async function autoLogin(){
   const initData=tg?.initData;
   if(initData && !localStorage.getItem("token")){
     try{const x=await api("/api/auth/telegram",{method:"POST",body:JSON.stringify({init_data:initData})}); localStorage.setItem("token",x.token);setMe(x.user); }
     catch(e:any){setErr(e.message)}
   } else if(localStorage.getItem("token")) {try{setMe(await api("/api/me"))}catch{}}
 }
 async function load(){try{setSeasons(await api("/api/seasons"))}catch(e:any){setErr(e.message)}}
 async function openSeason(s:any){setSelected(s);setStand(await api(`/api/seasons/${s.id}/standings`));setMatches(await api(`/api/seasons/${s.id}/matches`))}
 async function join(){await api(`/api/seasons/${selected.id}/join`,{method:"POST"}); alert("Ligaga qo‘shildingiz");}
 return <main><header><h1>⚽ eFootball Liga</h1><div>{me?`👤 ${me.first_name||me.username} ${me.role==="ADMIN"?"👑":""}`:"Telegram Mini App"}</div></header>
 {err&&<div className="error">{err}</div>}
 {!selected?<section><h2>Ligalar</h2>{seasons.map(s=><button className="card" key={s.id} onClick={()=>openSeason(s)}><b>{s.name}</b><span>{s.status}</span></button>)}</section>:
 <section><button onClick={()=>setSelected(null)}>← Orqaga</button><h2>{selected.name}</h2>{selected.status==="OPEN"&&<button onClick={join}>Ligaga qo‘shilish</button>}
 <h3>🏆 Turnir jadvali</h3><table><thead><tr><th>#</th><th>O‘yinchi</th><th>O</th><th>G</th><th>D</th><th>M</th><th>Ochko</th></tr></thead><tbody>{stand.map((x,i)=><tr key={x.user_id}><td>{i+1}</td><td>{x.username}</td><td>{x.played}</td><td>{x.win}</td><td>{x.draw}</td><td>{x.loss}</td><td><b>{x.points}</b></td></tr>)}</tbody></table>
 <h3>🎮 O‘yinlar</h3>{matches.map(m=><div className="match" key={m.id}><small>Tur {m.round_number}</small><div>{m.home} <b>{m.played?`${m.home_score} : ${m.away_score}`:"vs"}</b> {m.away}</div></div>)}</section>}
 <footer>Telegram Mini App • <span onClick={()=>{localStorage.removeItem("token");location.reload()}}>Chiqish</span></footer></main>
}