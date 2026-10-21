// 정보세상 전용 관리자 API — Cloudflare Workers.
// REQUIRED secrets: ADMIN_PASSWORD (strong, random), GITHUB_TOKEN (contents read/write on one repo).
const enc = new TextEncoder();
const dec = new TextDecoder();
const COOKIE = "info_world_session";
const SESSION_AGE = 8 * 60 * 60; // server-side expiry; session cookie intentionally has no Max-Age.
const MAX_BODY = 3 * 1024 * 1024;
const tries = new Map(); // best-effort per isolate; use Cloudflare rate limiting for production.
let postsCache=null; // Short-lived metadata cache to reduce repeat GitHub API calls.
const json = (obj, status=200, extra={}) => new Response(JSON.stringify(obj), {status, headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store","x-content-type-options":"nosniff",...extra}});
const safeEq = (a,b) => {
  if (a.length !== b.length) return false;
  let diff=0; for(let i=0;i<a.length;i++)diff|=a[i]^b[i];return diff===0;
};
const hex = b => Array.from(new Uint8Array(b)).map(x=>x.toString(16).padStart(2,"0")).join("");
async function digest(s){return new Uint8Array(await crypto.subtle.digest("SHA-256",enc.encode(s)));}
async function key(env){
  const material=await crypto.subtle.importKey("raw",enc.encode("session:v1:"+env.ADMIN_PASSWORD+":"+env.GITHUB_TOKEN),"HKDF",false,["deriveKey"]);
  return crypto.subtle.deriveKey({name:"HKDF",hash:"SHA-256",salt:enc.encode("info-world-admin-v1"),info:enc.encode("cookie-sign")},material,{name:"HMAC",hash:"SHA-256",length:256},false,["sign","verify"]);
}
const b64u = bytes => btoa(String.fromCharCode(...bytes)).replaceAll("+","-").replaceAll("/","_").replace(/=+$/,"");
const unb64u = s => Uint8Array.from(atob(s.replaceAll("-","+").replaceAll("_","/")),c=>c.charCodeAt(0));
async function makeSession(env){
  const payload=b64u(enc.encode(JSON.stringify({u:env.ADMIN_USERNAME,e:Math.floor(Date.now()/1000)+SESSION_AGE,n:crypto.randomUUID()})));
  const sig=b64u(new Uint8Array(await crypto.subtle.sign("HMAC",await key(env),enc.encode(payload))));
  return payload+"."+sig;
}
async function authenticated(req,env){
  const cookie=(req.headers.get("cookie")||"").split(";").map(x=>x.trim()).find(x=>x.startsWith(COOKIE+"="));
  if(!cookie)return false;
  try{
    const [payload,signature]=cookie.slice(COOKIE.length+1).split(".");
    if(!payload||!signature)return false;
    if(!(await crypto.subtle.verify("HMAC",await key(env),unb64u(signature),enc.encode(payload))))return false;
    const data=JSON.parse(dec.decode(unb64u(payload)));
    return data.u===env.ADMIN_USERNAME && data.e>Math.floor(Date.now()/1000);
  }catch{return false;}
}
function sameOrigin(req){
  const origin=req.headers.get("origin");
  return origin===new URL(req.url).origin;
}
function cookieSet(token){return COOKIE+"="+token+"; Path=/; HttpOnly; Secure; SameSite=Strict";}
function cookieClear(){return COOKIE+"=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0";}
async function github(env,method,path,body){
  const url="https://api.github.com/repos/"+env.GITHUB_REPO+"/"+path;
  const result=await fetch(url,{method,headers:{"Accept":"application/vnd.github+json","Authorization":"Bearer "+env.GITHUB_TOKEN,"X-GitHub-Api-Version":"2022-11-28","User-Agent":"info-world-admin"},body:body===undefined?undefined:JSON.stringify(body)});
  const data=await result.json().catch(()=>({}));
  if(!result.ok)throw {status:result.status,message:data.message||"GitHub 요청 오류"};
  return data;
}
const IMPORT_CATEGORIES=[
 ["moving",/이사|포장이사|이삿짐|용달|입주청소|청소업체|폐기물|생활서비스/],
 ["education",/학원|과외|수학|영어교육|초등|중등|고등|입시|교육|유학|취업|자격증/],
 ["law",/법률|변호사|법무사|소송|계약분쟁|이혼|형사|민사|상속|개인회생/],
 ["interior",/인테리어|리모델링|도배|장판|욕실|주방공사|싱크대|타일/],
 ["realestate",/부동산|전세|월세|아파트|분양|매매|공인중개/],
 ["finance",/금융|경제|보험|대출|세금|주식|투자|절세/],
 ["tech",/IT|디지털|스마트폰|컴퓨터|노트북|앱|소프트웨어|AI|인공지능/i],
 ["travel",/여행|관광|캠핑|호텔|항공|숙박/],
 ["health",/병원|건강|피부과|성형|치과|의원|의료|시술|한의원|리프팅|스킨부스터/]
];
function categoryFor(keyword,title){
  const subject=String(keyword||"")+" "+String(title||"");
  return IMPORT_CATEGORIES.find(([k,re])=>re.test(subject))?.[0]||"general";
}
function parseSheetDraft(raw,keyword){
 const lines=String(raw||"").replace(/\r\n?/g,"\n").split("\n");
 // Generated layout: title, core keyword, URL, then prose.
 const first=lines.findIndex(l=>l.trim().length>0);
 if(first<0)throw {status:422,message:"완성된 원고가 없습니다."};
 const clean=x=>String(x||"").trim().replace(/^(?:[#*]+\s*)?(?:제목|title)\s*[:：]\s*/i,"").trim();
 const title=clean(lines[first]).slice(0,180);
 let idx=first+1;
 // Only discard metadata at the top, never 'url' or keyword mentions in body paragraphs.
 let removed=0;
 while(idx<lines.length&&removed<10){
   const line=lines[idx].trim();
   if(!line){idx++;removed++;continue;}
   if(/^(?:핵심\s*키워드|키워드|메인\s*키워드|keyword)\s*[:：]/i.test(line)||line.normalize("NFC")===keyword.normalize("NFC")){idx++;removed++;continue;}
   if(/^(?:url|주소|글\s*주소|슬러그|slug)\s*[:：]/i.test(line)||/^https?:\/\//i.test(line)){idx++;removed++;continue;}
   if(/^(?:본문|원고|내용)\s*[:：]?\s*$/i.test(line)){idx++;removed++;continue;}
   break;
 }
 const body=lines.slice(idx).join("\n").trim();
 if(title.length<3||body.length<80||!keyword)throw {status:422,message:"제목/키워드/본문이 부족하여 가져오지 않았습니다."};
 return {title,body};
}
const fileName = n => typeof n==="string" && /^[가-힣a-z0-9][가-힣a-z0-9-]{0,150}\.json$/.test(n);
const slugify = x => String(x||"").toLowerCase().normalize("NFC").trim().replace(/\s+/g,"-").replace(/[^가-힣a-z0-9-]/g,"").replace(/-+/g,"-").replace(/^-|-$/g,"").slice(0,130);
function decodeFile(b64){return JSON.parse(dec.decode(Uint8Array.from(atob(b64.replace(/\s/g,"")),c=>c.charCodeAt(0))));}
function encodeFile(obj){return btoa(String.fromCharCode(...enc.encode(JSON.stringify(obj,null,2)+"\n")));}
async function input(req){
  if(Number(req.headers.get("content-length")||"0")>MAX_BODY)throw {status:413,message:"본문 크기를 줄여주세요."};
  return req.json().catch(()=>{throw {status:400,message:"입력 형식 오류"};});
}
function mustConfigure(env){return !!(env.ADMIN_PASSWORD&&env.GITHUB_TOKEN&&env.ADMIN_USERNAME&&env.GITHUB_REPO);}
export default {
 async fetch(req,env){
  const u=new URL(req.url),path=u.pathname;
  if(!path.startsWith("/api/"))return env.ASSETS.fetch(req);
  if(!mustConfigure(env))return json({error:"관리자 비밀번호 또는 GitHub 저장용 토큰이 아직 설정되지 않았습니다."},503);
  try{
   if(["POST","DELETE"].includes(req.method)&&path!=="/api/sheet-import"&&!sameOrigin(req))return json({error:"요청 출처가 올바르지 않습니다."},403);
   if(path==="/api/login"&&req.method==="POST"){
    const ip=req.headers.get("cf-connecting-ip")||"unknown";
    const entry=tries.get(ip)||{n:0,until:0};
    if(Date.now()<entry.until)return json({error:"로그인 시도가 많습니다. 잠시 뒤 다시 시도하세요."},429);
    const body=await input(req);
    const goodUser=safeEq(await digest(String(body.username||"")),await digest(env.ADMIN_USERNAME));
    const goodPwd=safeEq(await digest(String(body.password||"")),await digest(env.ADMIN_PASSWORD));
    if(!goodUser||!goodPwd){
      const count=entry.n+1;tries.set(ip,{n:count,until:count>=5?Date.now()+15*60*1000:0});
      return json({error:"아이디 또는 비밀번호가 올바르지 않습니다."},401);
    }
    tries.delete(ip);
    return json({ok:true},200,{"set-cookie":cookieSet(await makeSession(env))});
   }
   if(path==="/api/logout"&&req.method==="POST")return json({ok:true},200,{"set-cookie":cookieClear()});
   if(path==="/api/me"&&req.method==="GET")return json({authenticated:await authenticated(req,env)});
   if(path!=="/api/sheet-import"&&!(await authenticated(req,env)))return json({error:"로그인이 필요합니다."},401);
   if(path==="/api/sheet-import"&&req.method==="POST"){
     if(!env.SHEET_IMPORT_KEY||String(env.SHEET_IMPORT_KEY).length<24)
       return json({error:"시트 연동 비밀키(SHEET_IMPORT_KEY)가 설정되지 않았습니다."},503);
     const provided=String(req.headers.get("x-import-key")||"");
     if(!provided||!(safeEq(await digest(provided),await digest(env.SHEET_IMPORT_KEY))))
       return json({error:"시트 연동 인증 실패"},401);
     const d=await input(req);
     const keyword=String(d.keyword||"").normalize("NFC").trim().slice(0,140);
     const slug=slugify(keyword);
     if(!slug||!fileName(slug+".json"))return json({error:"B열 키워드로 URL을 만들 수 없습니다."},422);
     const {title,body}=parseSheetDraft(d.content,keyword);
     const file=slug+".json";
     const branch=env.GITHUB_BRANCH||"main";
     const filePath="contents/content/posts/"+encodeURIComponent(file);
     // Protect all existing posts, including drafts, from being overwritten.
     try{
       await github(env,"GET",filePath+"?ref="+encodeURIComponent(branch));
       return json({ok:true,result:"exists",file,message:"같은 키워드의 기존 글이 있어 건너뛰었습니다."});
     }catch(e){if(e.status!==404)throw e;}
     const date=/^\d{4}-\d{2}-\d{2}$/.test(String(d.date||""))?String(d.date):new Date().toISOString().slice(0,10);
     const description=body.replace(/[#*\[\]<>]/g,"").replace(/\s+/g," ").slice(0,150);
     const article={
       title,keyword,slug,category:categoryFor(keyword,title),description,body,
       thumbnail:"",date,status:"draft",seo_approved:false,
       source:"google-sheets",source_sheet_id:String(d.sheetId||"").slice(0,80),
       source_row:Number.isInteger(d.row)&&d.row>=1?d.row:null
     };
     try{
       await github(env,"PUT",filePath,{message:"Import Google Sheets draft: "+title,content:encodeFile(article),branch});
       postsCache=null;
     }catch(e){
       if(e.status===422||e.status===409)return json({ok:false,error:"중복 등록 충돌: 다시 시도 전에 관리자 목록을 확인해 주세요."},409);
       throw e;
     }
     return json({ok:true,result:"created",file,category:article.category});
   }
   if(path==="/api/posts"&&req.method==="GET"){
    if(u.searchParams.get("refresh")!=="1"&&postsCache&&postsCache.repo===env.GITHUB_REPO&&postsCache.branch===(env.GITHUB_BRANCH||"main")&&Date.now()<postsCache.expires)
      return json({posts:postsCache.posts});
    const branch=env.GITHUB_BRANCH||"main";
    const listing=await github(env,"GET","contents/content/posts?ref="+encodeURIComponent(branch));
    const files=(Array.isArray(listing)?listing:[]).filter(x=>fileName(x.name));
    // Read existing post metadata too: category, title, publication status and date.
    // Bounded concurrency avoids bursts against GitHub's secondary rate limit.
    const posts=[];
    for(let i=0;i<files.length;i+=6){
      const batch=await Promise.all(files.slice(i,i+6).map(async f=>{
        try{
          const r=await github(env,"GET","contents/content/posts/"+encodeURIComponent(f.name)+"?ref="+encodeURIComponent(branch));
          const article=decodeFile(r.content);
          const category=String(article.category||"general");
          return {file:f.name,sha:r.sha,title:String(article.title||f.name),category,status:article.status==="published"?"published":"draft",date:String(article.date||"").slice(0,10)};
        }catch{
          return {file:f.name,sha:f.sha,title:f.name,category:"general",status:"unknown",date:"",metadataError:true};
        }
      }));
      posts.push(...batch);
    }
    posts.sort((a,b)=>b.date.localeCompare(a.date)||a.title.localeCompare(b.title,"ko"));
    postsCache={repo:env.GITHUB_REPO,branch,expires:Date.now()+90_000,posts};
    return json({posts});
   }
   if(path==="/api/post"&&req.method==="GET"){
    const file=u.searchParams.get("file");
    if(!fileName(file))return json({error:"파일명이 올바르지 않습니다."},400);
    const r=await github(env,"GET","contents/content/posts/"+encodeURIComponent(file)+"?ref="+encodeURIComponent(env.GITHUB_BRANCH||"main"));
    return json({file,sha:r.sha,article:decodeFile(r.content)});
   }
   if(path==="/api/post"&&req.method==="POST"){
    const data=await input(req);
    const d=data.article||{},editing=Boolean(data.file);
    const title=String(d.title||"").trim(),keyword=String(d.keyword||"").trim();
    if(!title||(!editing&&!keyword)||!String(d.body||"").trim())return json({error:"제목, 핵심 키워드, 본문은 필수입니다."},400);
    const slug=editing?String(d.slug||data.file.replace(/\.json$/,"")):slugify(keyword);
    if(!slug||!fileName(slug+".json"))return json({error:"키워드를 짧고 명확하게 입력해 주세요."},400);
    const file=editing?data.file:slug+".json";
    if(!fileName(file))return json({error:"잘못된 파일명입니다."},400);
    const allowed=new Set(["health","law","interior","moving","realestate","finance","tech","education","travel","general","dermatology","lifting","skinbooster","other"]);
    const status=d.status==="published"?"published":"draft";
    const article={...d,slug,title,keyword,category:allowed.has(d.category)?d.category:"general",description:String(d.description||"").slice(0,500),
      body:String(d.body),thumbnail:String(d.thumbnail||""),status,seo_approved:d.seo_approved===true,
      date:String(d.date||new Date().toISOString().slice(0,10)).slice(0,10)};
    const args={message:(editing?"Update ":"Publish ")+title,content:encodeFile(article),branch:env.GITHUB_BRANCH||"main"};
    if(editing){
      if(typeof data.sha!=="string"||!data.sha)throw {status:400,message:"수정 시 현재 파일 정보가 필요합니다."};
      args.sha=data.sha;
    }
    try{
      await github(env,"PUT","contents/content/posts/"+encodeURIComponent(file),args);
      postsCache=null;
    }catch(e){
      if(e.status===422)throw {status:409,message:"이미 같은 키워드 주소의 글이 있습니다. 키워드를 변경하세요."};
      throw e;
    }
    return json({ok:true,file,url:"https://skin-map.pages.dev/blog/"+encodeURIComponent(slug)+"/"});
   }
   if(path==="/api/post"&&req.method==="DELETE"){
    // Only authenticated admin may delete. GitHub requires current blob SHA.
    const data=await input(req);
    const file=data.file,sha=data.sha;
    if(!fileName(file)||typeof sha!=="string"||!/^[a-f0-9]{40}$/.test(sha))
      return json({error:"삭제할 글의 파일 정보가 올바르지 않습니다. 글을 다시 선택해 주세요."},400);
    try{
      await github(env,"DELETE","contents/content/posts/"+encodeURIComponent(file),{
        message:"Delete article "+file,sha,branch:env.GITHUB_BRANCH||"main"
      });
      postsCache=null;
    }catch(e){
      if(e.status===409||e.status===422)
        throw {status:409,message:"다른 변경사항이 있어 삭제하지 못했습니다. 글을 다시 불러온 뒤 시도해 주세요."};
      throw e;
    }
    return json({ok:true,file});
   }
   if(path==="/api/upload"&&req.method==="POST"){
     const d=await input(req);
     const name=String(d.name||"").replace(/[^a-zA-Z0-9._-]/g,"-");
     const bytes=String(d.base64||"");
     if(!/^[a-zA-Z0-9_-]{1,90}\.(png|jpg|jpeg|webp|gif)$/i.test(name)||bytes.length>2.8e6||!/^[A-Za-z0-9+/=]+$/.test(bytes))return json({error:"2MB 이하 이미지(PNG/JPG/WebP/GIF)만 업로드할 수 있습니다."},400);
     const actual=atob(bytes);
     if(actual.length>2*1024*1024)return json({error:"이미지가 너무 큽니다."},413);
     const uploaded=crypto.randomUUID()+"-"+name;
     await github(env,"PUT","contents/assets/uploads/"+uploaded,{message:"Upload blog image "+name,content:bytes,branch:env.GITHUB_BRANCH||"main"});
     return json({url:"/assets/uploads/"+uploaded});
   }
   return json({error:"찾을 수 없는 경로입니다."},404);
  }catch(e){return json({error:e.message||"처리 중 오류가 발생했습니다."},e.status>=400&&e.status<=599?e.status:500);}
 }
};
