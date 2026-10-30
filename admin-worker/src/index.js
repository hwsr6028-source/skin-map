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
 ["fortune",/점집|사주|운세|타로|신점|철학관|무속/],
 ["tattoo",/타투|문신|반영구|타투이스트|레터링타투/],
 ["shopping",/구매대행|해외직구|배송대행|수입대행|직구대행/],
 ["supplements",/건강식품|건강기능식품|영양제|비타민|유산균|프로바이오틱스/],
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
// Shared classification semantics with scripts/build.py.
// Explicit categories stay as edited; legacy "general" articles are inferred
// from their subject so public listings and admin stats agree.
function effectiveCategory(article){
 const legacy={dermatology:"health",lifting:"health",skinbooster:"health",other:"general"};
 const raw=String(article.category||"general").trim();
 const category=legacy[raw]||raw;
 const allowed=new Set(["health","law","interior","moving","realestate","finance","tech","education","travel","general","fortune","tattoo","shopping","supplements"]);
 if(allowed.has(category)&&category!=="general")return category;
 return categoryFor(String(article.keyword||"")+" "+String(article.procedure||""),String(article.title||""));
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

// GA4 keyless Google OAuth: refresh token encrypted in a secure, HttpOnly browser cookie.
// No Google credential is ever written into GitHub or exposed to front-end JavaScript.
const GA_OAUTH_COOKIE="iw_ga_oauth";
const GA_STATE_COOKIE="iw_ga_state";
const GA_OAUTH_TTL=90*24*60*60;
function cookieValue(req,name){
 const entry=(req.headers.get("cookie")||"").split(";").map(x=>x.trim()).find(x=>x.startsWith(name+"="));
 return entry?entry.slice(name.length+1):"";
}
async function oauthCipher(env){
 const material=await crypto.subtle.importKey("raw",enc.encode("ga4:oauth:v1:"+env.ADMIN_PASSWORD+":"+env.GITHUB_TOKEN),"HKDF",false,["deriveKey"]);
 return crypto.subtle.deriveKey({name:"HKDF",hash:"SHA-256",salt:enc.encode("iw-ga-oauth-v1"),info:enc.encode("refresh-token")},material,{name:"AES-GCM",length:256},false,["encrypt","decrypt"]);
}
async function encryptedOAuthToken(env,refreshToken){
 const iv=crypto.getRandomValues(new Uint8Array(12));
 const ciphertext=new Uint8Array(await crypto.subtle.encrypt({name:"AES-GCM",iv},await oauthCipher(env),enc.encode(refreshToken)));
 const combined=new Uint8Array(iv.length+ciphertext.length);combined.set(iv);combined.set(ciphertext,iv.length);
 return b64u(combined);
}
async function decryptedOAuthToken(req,env){
 const packed=cookieValue(req,GA_OAUTH_COOKIE);
 if(!packed)return "";
 try{
  const combined=unb64u(packed);
  if(combined.length<30)return "";
  return dec.decode(await crypto.subtle.decrypt({name:"AES-GCM",iv:combined.slice(0,12)},await oauthCipher(env),combined.slice(12)));
 }catch{return "";}
}
function gaOAuthReady(env){return !!(env.GA4_OAUTH_CLIENT_ID&&env.GA4_OAUTH_CLIENT_SECRET);}
function gaRedirect(req){return new URL("/api/ga-oauth/callback",new URL(req.url).origin).href;}
async function oauthAccessToken(req,env){
 const refresh=await decryptedOAuthToken(req,env);
 if(!refresh)throw {status:401,message:"GA4 Google 계정 연결이 필요합니다."};
 const response=await fetch("https://oauth2.googleapis.com/token",{
  method:"POST",headers:{"content-type":"application/x-www-form-urlencoded"},
  body:new URLSearchParams({client_id:env.GA4_OAUTH_CLIENT_ID,client_secret:env.GA4_OAUTH_CLIENT_SECRET,refresh_token:refresh,grant_type:"refresh_token"})
 });
 const data=await response.json();
 if(!response.ok||!data.access_token)throw {status:401,message:"GA4 Google 인증이 만료되었습니다. 계정을 다시 연결해 주세요."};
 return data.access_token;
}

// GA4 reports are fetched by the authenticated administrator via Google OAuth.
async function gaReport(env,token,body){
 const property=String(env.GA4_PROPERTY_ID||"560092337");
 if(!/^\d{6,20}$/.test(property))throw Error("GA4_PROPERTY_ID 설정이 올바르지 않습니다.");
 const response=await fetch("https://analyticsdata.googleapis.com/v1beta/properties/"+property+":runReport",{method:"POST",headers:{"authorization":"Bearer "+token,"content-type":"application/json"},body:JSON.stringify(body)});
 const data=await response.json();
 if(!response.ok)throw Error("GA4 조회 실패: "+String(data.error?.message||response.status).slice(0,260));
 return (data.rows||[]).map(row=>({dims:(row.dimensionValues||[]).map(x=>x.value),metrics:(row.metricValues||[]).map(x=>Number(x.value)||0)}));
}

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
   if(path==="/api/ga-oauth/callback"&&req.method==="GET"){
     if(!gaOAuthReady(env))return json({error:"OAuth 클라이언트 설정이 필요합니다."},503);
     const state=u.searchParams.get("state")||"";
     const nonce=cookieValue(req,GA_STATE_COOKIE);
     if(!nonce||!state||nonce!==state)return json({error:"Google 로그인 확인값이 일치하지 않습니다. 관리자에서 다시 연결해 주세요."},403);
     const code=u.searchParams.get("code");
     if(!code)return json({error:"Google 계정 인증이 취소되었거나 거부되었습니다."},400);
     const exchange=await fetch("https://oauth2.googleapis.com/token",{
       method:"POST",headers:{"content-type":"application/x-www-form-urlencoded"},
       body:new URLSearchParams({code,client_id:env.GA4_OAUTH_CLIENT_ID,client_secret:env.GA4_OAUTH_CLIENT_SECRET,redirect_uri:gaRedirect(req),grant_type:"authorization_code"})
     });
     const response=await exchange.json();
     if(!exchange.ok||!response.refresh_token)return json({error:"Google 인증에 실패했거나 갱신 토큰이 제공되지 않았습니다. 다시 연결해 주세요."},400);
     const secured=await encryptedOAuthToken(env,response.refresh_token);
     const headers=new Headers({"location":"/?ga_connected=1","cache-control":"no-store"});
     headers.append("set-cookie",GA_OAUTH_COOKIE+"="+secured+"; Path=/api; Secure; HttpOnly; SameSite=Lax; Max-Age="+GA_OAUTH_TTL);
     headers.append("set-cookie",GA_STATE_COOKIE+"=; Path=/api; Secure; HttpOnly; SameSite=Lax; Max-Age=0");
     return new Response(null,{status:302,headers});
   }

   if(path!=="/api/sheet-import"&&!(await authenticated(req,env)))return json({error:"로그인이 필요합니다."},401);
   if(path==="/api/ga-oauth/status"&&req.method==="GET")
     return json({configured:gaOAuthReady(env),connected:!!(await decryptedOAuthToken(req,env))});
   if(path==="/api/ga-oauth/start"&&req.method==="GET"){
     if(!gaOAuthReady(env))return json({error:"Cloudflare에 GA4_OAUTH_CLIENT_ID와 GA4_OAUTH_CLIENT_SECRET을 먼저 등록해 주세요."},503);
     const state=b64u(crypto.getRandomValues(new Uint8Array(32)));
     const params=new URLSearchParams({client_id:env.GA4_OAUTH_CLIENT_ID,redirect_uri:gaRedirect(req),response_type:"code",scope:"https://www.googleapis.com/auth/analytics.readonly",access_type:"offline",prompt:"consent select_account",state});
     const headers=new Headers({"location":"https://accounts.google.com/o/oauth2/v2/auth?"+params,"cache-control":"no-store"});
     headers.append("set-cookie",GA_STATE_COOKIE+"="+state+"; Path=/api; Secure; HttpOnly; SameSite=Lax; Max-Age=600");
     return new Response(null,{status:302,headers});
   }
   if(path==="/api/ga-oauth/disconnect"&&req.method==="POST"){
     const headers=new Headers({"content-type":"application/json","cache-control":"no-store"});
     headers.append("set-cookie",GA_OAUTH_COOKIE+"=; Path=/api; Secure; HttpOnly; SameSite=Lax; Max-Age=0");
     return new Response(JSON.stringify({ok:true}),{status:200,headers});
   }
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
       thumbnail:"",date,status:"published",seo_approved:true,
       source:"google-sheets",source_sheet_id:String(d.sheetId||"").slice(0,80),
       source_row:Number.isInteger(d.row)&&d.row>=1?d.row:null,imported_at:new Date().toISOString()
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
   if(path==="/api/analytics"&&req.method==="GET"){
     if(!gaOAuthReady(env))return json({configured:false,message:"Google OAuth 클라이언트 연결 설정이 필요합니다."});
     if(!(await decryptedOAuthToken(req,env)))return json({configured:false,message:"Google 계정을 연결해 주세요."});
     const range=u.searchParams.get("range")==="30"?"30daysAgo":"7daysAgo";
     const dates=[{startDate:range,endDate:"today"}];
     const token=await oauthAccessToken(req,env);
     const [daily,pages,events]=await Promise.all([
       gaReport(env,token,{dateRanges:dates,dimensions:[{name:"date"}],metrics:[{name:"activeUsers"},{name:"screenPageViews"}],orderBys:[{dimension:{dimensionName:"date"}}],limit:"31"}),
       gaReport(env,token,{dateRanges:dates,dimensions:[{name:"pagePath"}],metrics:[{name:"screenPageViews"}],orderBys:[{metric:{metricName:"screenPageViews"},desc:true}],limit:"15"}),
       gaReport(env,token,{dateRanges:dates,dimensions:[{name:"eventName"}],metrics:[{name:"eventCount"}],dimensionFilter:{filter:{fieldName:"eventName",inListFilter:{values:["kakao_click","phone_click","article_click"]}}},limit:"10"})
     ]);
     const clicks=Object.fromEntries(events.map(e=>[e.dims[0],e.metrics[0]]));
     return json({configured:true,range:u.searchParams.get("range")==="30"?30:7,daily:daily.map(r=>({date:r.dims[0],users:r.metrics[0],views:r.metrics[1]})),pages:pages.map(r=>({path:r.dims[0],views:r.metrics[0]})),clicks:{kakao:clicks.kakao_click||0,phone:clicks.phone_click||0,article:clicks.article_click||0},note:"일별 활성 사용자 합계는 기간 전체 고유 방문자 수와 다를 수 있습니다."});
   }
   if(path==="/api/indexnow-status"&&req.method==="GET"){
     // GitHub workflow execution results, not proof of Naver crawl or indexing.
     const days=u.searchParams.get("days")==="30"?30:7;
     const perPage=100;
     const endpoint="https://api.github.com/repos/"+env.GITHUB_REPO+"/actions/workflows/naver-indexnow.yml/runs?branch="+encodeURIComponent(env.GITHUB_BRANCH||"main")+"&per_page="+perPage;
     const headers={"accept":"application/vnd.github+json","user-agent":"info-world-admin","x-github-api-version":"2022-11-28"};
     if(env.GITHUB_TOKEN)headers.authorization="Bearer "+env.GITHUB_TOKEN;
     let response=await fetch(endpoint,{headers});
     // Some fine-grained Contents-only tokens cannot read Actions. Public repositories allow anonymous reads.
     if(response.status===403||response.status===404){const publicHeaders={...headers};delete publicHeaders.authorization;response=await fetch(endpoint,{headers:publicHeaders});}
     if(!response.ok)return json({error:"GitHub 자동화 실행 기록을 조회하지 못했습니다 (HTTP "+response.status+"). Actions 조회 권한을 확인해 주세요."},502);
     const data=await response.json();
     const since=Date.now()-days*86400000;
     const runs=(Array.isArray(data.workflow_runs)?data.workflow_runs:[]).filter(run=>Date.parse(run.created_at)>=since).map(run=>({
       id:run.id,
       title:String(run.display_title||run.head_commit?.message||"자동화 실행").slice(0,200),
       sha:String(run.head_sha||"").slice(0,10),
       status:String(run.status||"unknown"),
       conclusion:run.conclusion||null,
       date:run.created_at,
       url:run.html_url,
       event:run.event
     }));
     const counts={success:0,cancelled:0,failure:0,pending:0,other:0};
     for(const item of runs){
       if(item.status!=="completed")counts.pending++;
       else if(item.conclusion==="success")counts.success++;
       else if(item.conclusion==="cancelled")counts.cancelled++;
       else if(item.conclusion==="failure"||item.conclusion==="timed_out")counts.failure++;
       else counts.other++;
     }
     return json({days,runs,counts,limited:((data.total_count||0)>perPage),caveat:"GitHub Actions 성공은 네이버 IndexNow 전송/색인 성공과 동일하지 않습니다. 전송 HTTP 코드는 개별 실행 로그에서 확인해야 합니다."});
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
          const category=effectiveCategory(article);
          return {file:f.name,sha:r.sha,title:String(article.title||f.name),category,status:article.status==="published"?"published":"draft",date:String(article.date||"").slice(0,10),latestAt:String(article.updated_at||article.imported_at||article.created_at||article.date||""),sourceRow:Number(article.source_row)||0};
        }catch{
          return {file:f.name,sha:f.sha,title:f.name,category:"general",status:"unknown",date:"",latestAt:"",sourceRow:0,metadataError:true};
        }
      }));
      posts.push(...batch);
    }
    posts.sort((a,b)=>String(b.latestAt||"").localeCompare(String(a.latestAt||""))||((Number(b.sourceRow)||0)-(Number(a.sourceRow)||0))||String(b.date||"").localeCompare(String(a.date||""))||String(a.title||"").localeCompare(String(b.title||""),"ko"));
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
    if(!title||!keyword||!String(d.body||"").trim())return json({error:"제목, 핵심 키워드, 본문은 필수입니다."},400);
    const allowed=new Set(["health","law","interior","moving","realestate","finance","tech","education","travel","general","fortune","tattoo","shopping","supplements"]);
    const status="published"; // Saving from the admin publishes immediately.
    const branch=env.GITHUB_BRANCH||"main";
    let file,slug,previousSlugs=Array.isArray(d.previous_slugs)?d.previous_slugs:[];
    let rename=false;
    if(editing){
      if(!fileName(data.file)||typeof data.sha!=="string"||!/^[a-f0-9]{40}$/.test(data.sha))
        return json({error:"수정할 글의 파일 정보가 올바르지 않습니다."},400);
      const oldFile=data.file;
      const current=await github(env,"GET","contents/content/posts/"+encodeURIComponent(oldFile)+"?ref="+encodeURIComponent(branch));
      if(current.sha!==data.sha)return json({error:"다른 곳에서 변경된 글입니다. 새로 불러온 뒤 다시 저장해 주세요."},409);
      const oldArticle=decodeFile(current.content);
      const changed=String(oldArticle.keyword||"").trim()!==keyword;
      slug=changed?slugify(keyword):String(oldArticle.slug||oldFile.replace(/\.json$/,""));
      if(!fileName(slug+".json"))return json({error:"변경된 키워드로 URL을 만들 수 없습니다."},400);
      file=changed?slug+".json":oldFile;
      rename=file!==oldFile;
      previousSlugs=Array.isArray(oldArticle.previous_slugs)?oldArticle.previous_slugs:[];
      if(rename){
        const oldSlug=String(oldArticle.slug||oldFile.replace(/\.json$/,""));
        previousSlugs=[...new Set([...previousSlugs,oldSlug])].filter(x=>x!==slug).slice(-20);
        try{await github(env,"GET","contents/content/posts/"+encodeURIComponent(file)+"?ref="+encodeURIComponent(branch));
          return json({error:"변경하려는 URL에 이미 다른 글이 있습니다. 핵심키워드를 다르게 설정해 주세요."},409);
        }catch(err){if(err.status!==404)throw err;}
      }
    }else{
      slug=slugify(keyword);
      if(!fileName(slug+".json"))return json({error:"핵심 키워드로 URL을 만들 수 없습니다."},400);
      file=slug+".json";
    }
    const article={...d,slug,title,keyword,category:allowed.has(d.category)?d.category:"general",
      description:String(d.description||"").slice(0,500),body:String(d.body),thumbnail:String(d.thumbnail||""),
      status,seo_approved:true,updated_at:new Date().toISOString(),
      date:String(d.date||new Date().toISOString().slice(0,10)).slice(0,10),previous_slugs:previousSlugs};
    const filePath="content/posts/"+file;
    try{
      if(rename){
        // Atomic rename and edit: a single Git commit removes the old path and writes the new path.
        // No intermediate deployment with duplicate public pages.
        const ref=await github(env,"GET","git/ref/heads/"+encodeURIComponent(branch));
        const head=ref.object.sha;
        const base=await github(env,"GET","git/commits/"+head);
        const tree=await github(env,"POST","git/trees",{
          base_tree:base.tree.sha,
          tree:[
            {path:"content/posts/"+data.file,mode:"100644",type:"blob",sha:null},
            {path:filePath,mode:"100644",type:"blob",content:JSON.stringify(article,null,2)+"\n"}
          ]
        });
        const commit=await github(env,"POST","git/commits",{
          message:"Rename article URL: "+data.file+" → "+file,tree:tree.sha,parents:[head]
        });
        await github(env,"PATCH","git/refs/heads/"+encodeURIComponent(branch),{sha:commit.sha,force:false});
      }else{
        const args={message:(editing?"Update ":"Publish ")+title,content:encodeFile(article),branch};
        if(editing)args.sha=data.sha;
        await github(env,"PUT","contents/"+filePath,args);
      }
      postsCache=null;
    }catch(e){
      if(e.status===409||e.status===422)return json({error:"저장 충돌 또는 같은 URL이 존재합니다. 목록을 다시 불러온 뒤 확인해 주세요."},409);
      throw e;
    }
    return json({ok:true,file,renamed:rename,url:"https://skin-map.pages.dev/blog/"+encodeURIComponent(slug)+"/"});
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
