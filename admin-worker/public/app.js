const $=id=>document.getElementById(id);
let editFile=null,editSha=null,editingSlug="";
let allPosts=[],activeCategory="all";
const selectedPosts=new Set();
let postPage=1;
const PAGE_SIZE=10;
const PAGE_GROUP_SIZE=10;
const categories=[["health","병원·건강"],["law","법률"],["interior","인테리어"],["moving","이사·생활"],["realestate","부동산"],["finance","금융·경제"],["tech","IT·디지털"],["education","교육·취업"],["travel","여행·취미"],["general","비즈니스·기타"],["fortune","점집"],["tattoo","타투"],["shopping","구매대행"],["supplements","건강식품"]];
const categoryName=id=>categories.find(x=>x[0]===id)?.[1]||"미분류";
const fields=["title","keyword","description","category","thumbnail","body","region","procedure","date","status"];
const api=async (path,opts={})=>{
 const res=await fetch("/api/"+path,{credentials:"same-origin",cache:"no-store",headers:{"content-type":"application/json"},...opts});
 const data=await res.json().catch(()=>({error:"서버 응답을 확인할 수 없습니다."}));
 if(!res.ok)throw Error(data.error||"요청이 실패했습니다.");return data;
};
const normalize=x=>String(x||"").toLowerCase().normalize("NFC").trim().replace(/\s+/g,"-").replace(/[^가-힣a-z0-9-]/g,"").replace(/-+/g,"-").replace(/^-|-$/g,"").slice(0,130);
function preview(){
 const slug=normalize($("keyword").value)||(!editFile?"":editingSlug);
 $("slug-preview").textContent=slug?"https://skin-map.pages.dev/blog/"+slug+"/":"키워드를 입력해 주세요.";
}
$("keyword").addEventListener("input",preview);

function isSafeWebLink(url){return /^https?:\/\/[^\s]+$/i.test(String(url||"").trim());}
function putIntoBody(markdown){
 const editor=$("body");
 const start=editor.selectionStart??editor.value.length,end=editor.selectionEnd??start;
 const before=editor.value.slice(0,start),after=editor.value.slice(end);
 const insert=(before&&!before.endsWith("\n")?"\n\n":"")+markdown+(after&&!after.startsWith("\n")?"\n\n":"");
 editor.setRangeText(insert,start,end,"end");
 editor.dispatchEvent(new Event("input",{bubbles:true}));editor.focus();
}
function renderPreviewText(text,container){
 // Only text nodes and validated anchors. Never inject source HTML.
 const re=/\[(.*?)\]\((https?:\/\/[^)\s]+)\)|(https?:\/\/[^\s<>]+)/g;
 let last=0,m;
 while((m=re.exec(text))!==null){
  if(m.index>last)container.appendChild(document.createTextNode(text.slice(last,m.index)));
  const value=m[1]??m[3],url=m[2]??m[3];
  const anchor=document.createElement("a");anchor.href=url.replace(/[.,!?;:]+$/,"");anchor.target="_blank";anchor.rel="noopener noreferrer";anchor.textContent=value;
  container.appendChild(anchor);last=re.lastIndex;
 }
 if(last<text.length)container.appendChild(document.createTextNode(text.slice(last)));
}
function updateBodyLivePreview(){
 const container=$("body-live-preview");
 if(!container)return;
 container.replaceChildren();
 const body=$("body").value||"";
 if(!body.trim()){
  const p=document.createElement("p");p.textContent="본문을 입력하면 이곳에 이미지와 글이 표시됩니다.";container.appendChild(p);return;
 }
 for(const line of body.split(/\r?\n/)){
  const trimmed=line.trim();if(!trimmed)continue;
  const linked=trimmed.match(/^\[!\[([^\]]*)\]\(([^)\s]+)\)\]\((https?:\/\/[^)\s]+)\)$/);
  const plain=trimmed.match(/^!\[([^\]]*)\]\(([^)\s]+)\)$/);
  const match=linked||plain;
  if(match){
   const imageUrl=match[2];
   if(imageUrl.startsWith("/assets/uploads/")||isSafeWebLink(imageUrl)){
    const figure=document.createElement("figure"),img=document.createElement("img");
    img.src=imageUrl;img.alt=match[1]||"본문 이미지";img.loading="lazy";
    if(linked){const anchor=document.createElement("a");anchor.href=linked[3];anchor.target="_blank";anchor.rel="noopener noreferrer";anchor.appendChild(img);figure.appendChild(anchor);}
    else figure.appendChild(img);
    container.appendChild(figure);continue;
   }
  }
  const heading=trimmed.match(/^(#{1,3})\s+(.+)$/);
  const el=document.createElement(heading?"h"+Math.min(4,heading[1].length+1):trimmed.startsWith("- ")?"li":"p");
  renderPreviewText(heading?heading[2]:trimmed.startsWith("- ")?trimmed.slice(2):trimmed,el);
  container.appendChild(el);
 }
}
$("insert-link-btn").addEventListener("click",()=>{
 const url=$("insert-link-url").value.trim();
 if(!isSafeWebLink(url))return alert("https:// 또는 http://로 시작하는 링크 주소를 입력해주세요.");
 const editor=$("body"),selected=editor.value.slice(editor.selectionStart,editor.selectionEnd).trim();
 putIntoBody(selected?"["+selected.replace(/[\[\]]/g,"")+"]("+url+")":url);
});
$("body").addEventListener("input",updateBodyLivePreview);

function showLogin(isLogged){
 $("login-panel").hidden=isLogged;$("app-panel").hidden=!isLogged;$("account").hidden=!isLogged;
}
async function load(){
 const me=await api("me");
 showLogin(me.authenticated);
 if(me.authenticated){await list();reset();loadAnalytics();loadNaverStatus();}
}
$("login-form").addEventListener("submit",async e=>{
 e.preventDefault();$("login-error").textContent="";
 const f=new FormData(e.target);
 try{await api("login",{method:"POST",body:JSON.stringify({username:f.get("username"),password:f.get("password")})});$("login-form").reset();await load();}
 catch(err){$("login-error").textContent=err.message;}
});
$("logout").addEventListener("click",async()=>{
 try{await api("logout",{method:"POST",body:"{}"});}catch{}
 editFile=null;editSha=null;showLogin(false);
});
function reset(){
 editFile=null;editSha=null;editingSlug="";
 $("delete-post").hidden=true;
 $("post-form").reset();$("status").value="published";$("seo_approved").checked=true;$("date").value=new Date().toISOString().slice(0,10);
 $("editor-title").textContent="새 글 작성";$("message").textContent="";$("upload-result").textContent="";preview();updateBodyLivePreview();
}
$("new-post").addEventListener("click",()=>{reset();if(activeCategory!=="all")$("category").value=activeCategory;$("editor-title").scrollIntoView({behavior:"smooth",block:"start"});});
function renderCategories(){
 const stats=$("category-stats");stats.replaceChildren();
 const counts={};
 for(const p of allPosts.filter(p=>p.status==="published")){const k=p.category||"general";counts[k]=(counts[k]||0)+1;}
 const options=[["all","전체 공개 글"],...categories];
 for(const [key,label] of options){
   const button=document.createElement("button");button.type="button";
   button.className="category-stat"+(activeCategory===key?" selected":"");
   button.setAttribute("aria-pressed",String(activeCategory===key));
   const name=document.createElement("span");name.className="category-stat-label";name.textContent=label;
   const num=document.createElement("strong");num.className="category-stat-count";
   num.textContent=String(key==="all"?allPosts.filter(p=>p.status==="published").length:counts[key]||0);
   button.append(name,num);
   button.onclick=()=>{activeCategory=key;postPage=1;selectedPosts.clear();renderCategories();renderPosts();};
   stats.appendChild(button);
 }
}
function shownPosts(){
 const query=$("post-search").value.trim().toLowerCase(),state=$("status-filter").value;
 return allPosts.filter(p=>(activeCategory==="all"||p.category===activeCategory)&&(state==="all"||p.status===state)&&(!query||[p.title,p.file,p.date,categoryName(p.category)].join(" ").toLowerCase().includes(query)));
}
function refreshBulkControls(){
 const chosen=allPosts.filter(p=>selectedPosts.has(p.file));
 $("selected-count").textContent=chosen.length+"개 선택됨";
 const current=shownPosts().slice((postPage-1)*PAGE_SIZE,postPage*PAGE_SIZE);
 const checked=current.filter(p=>selectedPosts.has(p.file)).length;
 $("select-visible").checked=current.length>0&&checked===current.length;
 $("select-visible").indeterminate=checked>0&&checked<current.length;
 $("bulk-trash").disabled=!chosen.some(p=>p.status!=="trash");
 $("bulk-restore").disabled=!chosen.some(p=>p.status==="trash");
 $("bulk-category").disabled=!chosen.length;
}
function renderPosts(){
 const root=$("post-list");root.replaceChildren();
 const shown=shownPosts(),pages=Math.max(1,Math.ceil(shown.length/PAGE_SIZE));
 postPage=Math.min(Math.max(postPage,1),pages);
 $("filtered-count").textContent=shown.length+"개";
 if(!shown.length){
   const empty=document.createElement("p");empty.className="empty-post-list";
   empty.textContent=allPosts.length?"조건에 해당하는 글이 없습니다.":"아직 작성된 글이 없습니다.";
   root.append(empty);
 }else{
   const table=document.createElement("table");table.className="post-management-table";
   const thead=document.createElement("thead"),hrow=document.createElement("tr");
   for(const [text,className] of [["선택","col-select"],["글 제목","col-title"],["분류","col-category"],["작성일","col-date"],["상태","col-status"],["관리","col-actions"]]){
     const th=document.createElement("th");th.textContent=text;th.className=className;th.scope="col";hrow.append(th);
   }
   thead.append(hrow);table.append(thead);
   const tbody=document.createElement("tbody");
   for(const p of shown.slice((postPage-1)*PAGE_SIZE,postPage*PAGE_SIZE)){
     const tr=document.createElement("tr"),cell=(className)=>{const td=document.createElement("td");td.className=className;tr.append(td);return td;};
     const checkCell=cell("col-select"),checkbox=document.createElement("input");
     checkbox.type="checkbox";checkbox.className="post-select-checkbox";
     checkbox.checked=selectedPosts.has(p.file);checkbox.setAttribute("aria-label",(p.title||p.file)+" 선택");
     checkbox.addEventListener("change",()=>{checkbox.checked?selectedPosts.add(p.file):selectedPosts.delete(p.file);refreshBulkControls();});
     checkCell.append(checkbox);
     const titleCell=cell("col-title"),title=document.createElement("button");
     title.type="button";title.className="post-title-button";title.textContent=p.title||p.file;title.title=p.title||p.file;
     if(p.status==="trash"){title.disabled=true;}else{title.addEventListener("click",()=>openPost(p.file));}
     titleCell.append(title);
     cell("col-category").textContent=categoryName(p.category);
     cell("col-date").textContent=String(p.date||"").slice(0,10).replaceAll("-",". ");
     const statusCell=cell("col-status");
     const status=document.createElement("span");status.className=p.status==="published"?"status-live":p.status==="trash"?"status-trash":"status-draft";
     status.textContent=p.status==="published"?"공개":p.status==="draft"?"임시":p.status==="trash"?"휴지통":"확인 필요";
     statusCell.append(status);
     const actions=cell("col-actions"),buttons=document.createElement("div");buttons.className="compact-row-actions";
     const actionButton=(label,callback,kind)=>{
       const b=document.createElement("button");b.type="button";b.textContent=label;
       b.className="row-action "+kind;b.addEventListener("click",callback);buttons.append(b);
     };
     if(p.status==="trash"){
       actionButton("복원",()=>bulkAction("restore",[p]),"restore");
       if(p.deleted_at){
         const due=document.createElement("span");due.className="trash-due";
         const expiry=new Date(p.deleted_at).getTime()+72*3600000;
         if(Number.isFinite(expiry))due.title="삭제 예정: "+new Date(expiry).toLocaleString("ko-KR");
         actions.append(due);
       }
     }else{
       actionButton("수정",()=>openPost(p.file),"edit");
       actionButton("삭제",()=>bulkAction("trash",[p]),"remove");
     }
     actions.prepend(buttons);tbody.append(tr);
   }
   table.append(tbody);const scroller=document.createElement("div");scroller.className="post-table-scroll";scroller.append(table);root.append(scroller);
 }
 const nav=$("post-pages");nav.replaceChildren();
 if(pages>1){
   const first=Math.floor((postPage-1)/PAGE_GROUP_SIZE)*PAGE_GROUP_SIZE+1;
   const last=Math.min(pages,first+PAGE_GROUP_SIZE-1);
   const add=(label,target,disabled=false,isActive=false)=>{
     const btn=document.createElement("button");btn.type="button";btn.className="page-number"+(isActive?" is-current":"");
     btn.textContent=label;btn.disabled=disabled;btn.setAttribute("aria-label",isActive?"현재 "+label+"페이지":label+" 페이지");
     if(isActive)btn.setAttribute("aria-current","page");
     btn.addEventListener("click",()=>{postPage=target;renderPosts();});
     nav.append(btn);
   };
   add("‹ 이전 10",Math.max(1,first-1),first===1);
   for(let number=first;number<=last;number++)add(String(number),number,false,number===postPage);
   add("다음 10 ›",last+1,last>=pages);
 }
 refreshBulkControls();
}
async function list(force=false){
 const root=$("post-list");root.textContent="글 목록 불러오는 중...";
 try{
   const d=await api("posts"+(force?"?refresh=1":""));
   allPosts=d.posts||[];
   selectedPosts.clear();
   renderCategories();renderPosts();
 }catch(e){root.textContent="글 목록을 불러오지 못했습니다: "+e.message;throw e;}
}
$("post-search").addEventListener("input",()=>{postPage=1;selectedPosts.clear();renderPosts()});
$("status-filter").addEventListener("change",()=>{postPage=1;selectedPosts.clear();renderPosts()});
$("refresh-posts").addEventListener("click",()=>list(true).catch(err=>alert(err.message)));
$("select-visible").addEventListener("change",e=>{
 for(const p of shownPosts().slice((postPage-1)*PAGE_SIZE,postPage*PAGE_SIZE)){
   if(e.target.checked)selectedPosts.add(p.file);else selectedPosts.delete(p.file);
 }
 renderPosts();
});
async function bulkAction(action,custom=null){
 const selected=custom||allPosts.filter(p=>selectedPosts.has(p.file));
 const target=selected.filter(p=>action==="restore"?p.status==="trash":action==="trash"?p.status!=="trash":true);
 if(!target.length)return alert("처리할 글을 선택하세요.");
 if(target.length>30)return alert("한 번에 최대 30개 글을 선택할 수 있습니다.");
 const label=action==="trash"?"휴지통으로 이동":action==="restore"?"복원":"카테고리 변경";
 if(!confirm(target.length+"개 글을 "+label+"하시겠습니까?"+(action==="trash"?"\n3일간 복원할 수 있으며, 이후 자동 삭제됩니다.":"")))return;
 let category=null;
 if(action==="category"){category=$("bulk-category-target").value;if(!category)return alert("변경할 카테고리를 선택하세요.");}
 const buttons=[$("bulk-trash"),$("bulk-restore"),$("bulk-category")];
 buttons.forEach(b=>b.disabled=true);
 $("message").textContent=label+" 진행 중...";
 try{
   const result=await api("posts/bulk",{method:"POST",body:JSON.stringify({action,category,items:target.map(p=>({file:p.file,sha:p.sha}))})});
   await list(true);
   $("message").textContent=label+" "+(result.success||0)+"건 완료"+(result.failed?" / 실패 "+result.failed+"건":"")+". 홈페이지 배포 후 반영됩니다.";
   if(result.failed)alert((result.results||[]).filter(x=>!x.ok).slice(0,5).map(x=>x.file+": "+x.error).join("\\n"));
 }catch(err){$("message").textContent=label+" 실패: "+err.message;alert(err.message);}
 finally{refreshBulkControls();}
}
$("bulk-trash").onclick=()=>bulkAction("trash");
$("bulk-restore").onclick=()=>bulkAction("restore");
$("bulk-category").onclick=()=>bulkAction("category");
async function deletePost(file,sha,title){
 const p=allPosts.find(x=>x.file===file)||{file,sha,title,status:"published"};
 await bulkAction("trash",[p]);
}
async function openPost(file){
 try{
   const data=await api("post?file="+encodeURIComponent(file));
   editFile=file;editSha=data.sha;editingSlug=data.article.slug||file.replace(/\.json$/,"");
   $("delete-post").hidden=false;
   for(const field of fields)$(field).value=data.article[field]??"";
   // Legacy article categories remain editable, without showing retired categories in navigation.
   const legacy={dermatology:"health",lifting:"health",skinbooster:"health",other:"general"};
   if(legacy[data.article.category])$("category").value=legacy[data.article.category];
   $("status").value="published";$("seo_approved").checked=true;
   $("editor-title").textContent="글 수정: "+(data.article.title||file);$("message").textContent="";preview();updateBodyLivePreview();
   document.querySelector(".editor").scrollIntoView({behavior:"smooth",block:"start"});
 }catch(e){alert(e.message);}
}
$("delete-post").addEventListener("click",async()=>{
 await deletePost(editFile,editSha,$("title").value.trim()||editFile);
});
$("post-form").addEventListener("submit",async e=>{
 e.preventDefault();const button=$("save-btn");button.disabled=true;$("message").textContent="저장 중...";
 const article={};for(const field of fields)article[field]=$(field).value;
 article.status="published";article.seo_approved=true;
 try{
  const proposed=normalize(article.keyword);
  if(editFile&&proposed!==editingSlug){
    if(!confirm("핵심키워드가 변경되어 게시글 URL도 바뀝니다.\n\n이전 주소: /blog/"+editingSlug+"/\n새 주소: /blog/"+proposed+"/\n\n기존 주소는 새 주소로 연결됩니다. 계속하시겠습니까?"))return;
  }
  const r=await api("post",{method:"POST",body:JSON.stringify({file:editFile,sha:editSha,article})});
  $("message").textContent="저장 완료! 홈페이지 자동 배포가 시작됩니다.";
  await list(true);await openPost(r.file);
 }catch(err){$("message").textContent=err.message;}finally{button.disabled=false;}
});
$("upload-btn").addEventListener("click",async()=>{
 const file=$("file-input").files[0];if(!file)return alert("이미지 파일을 선택하세요.");
 if(file.size>2*1024*1024)return alert("2MB 이하 이미지만 가능합니다.");
 const reader=new FileReader();
 reader.onload=async()=>{
  try{
   const content=String(reader.result).split(",")[1];
   const r=await api("upload",{method:"POST",body:JSON.stringify({name:file.name,base64:content})});
   const result=$("upload-result");result.replaceChildren();
   const span=document.createElement("span");span.textContent=r.url;result.appendChild(span);
   const btn=document.createElement("button");btn.className="quiet";btn.type="button";btn.textContent="커서 위치에 본문 이미지 삽입";
   btn.onclick=()=>{
    const editor=$("body");
    const start=editor.selectionStart==null?editor.value.length:editor.selectionStart;
    const end=editor.selectionEnd==null?start:editor.selectionEnd;
    const before=editor.value.slice(0,start),after=editor.value.slice(end);
    const label=file.name.replace(/\.[^.]+$/,"").replace(/[\[\]()]/g," ").trim()||"본문 이미지";
    const insert=(before&&!before.endsWith("\n")?"\n\n":"")+"!["+label+"]("+r.url+")"+(after&&!after.startsWith("\n")?"\n\n":"");
        editor.setRangeText(insert,start,end,"end");
    editor.dispatchEvent(new Event("input",{bubbles:true}));
    editor.focus();
    editor.scrollTop=Math.max(0,editor.scrollHeight*(editor.selectionStart/Math.max(1,editor.value.length))-(editor.clientHeight/2));
   };
   result.appendChild(btn);
   const linkedBtn=document.createElement("button");linkedBtn.className="quiet";linkedBtn.type="button";linkedBtn.textContent="클릭 링크가 있는 이미지 삽입";
   linkedBtn.onclick=()=>{
    const target=$("insert-link-url").value.trim();
    if(!isSafeWebLink(target))return alert("먼저 이동할 링크 주소를 입력해주세요.");
    const imageLabel=file.name.replace(/\.[^.]+$/,"").replace(/[\[\]()]/g," ").trim()||"본문 이미지";
    putIntoBody("[!["+imageLabel+"]("+r.url+")]("+target+")");
   };
   result.appendChild(linkedBtn);
   const coverBtn=document.createElement("button");coverBtn.className="quiet";coverBtn.type="button";coverBtn.textContent="대표 이미지로 지정";
   coverBtn.onclick=()=>{$("thumbnail").value=r.url;};
   result.appendChild(coverBtn);
  }catch(e){alert(e.message);}
 };
 reader.readAsDataURL(file);
});

// GitHub Actions results are execution statuses; do not imply search indexing.
async function loadNaverStatus(){
 const status=$("naver-status"),container=$("naver-results"),tbody=$("naver-runs");
 status.textContent="실행 기록을 불러오는 중입니다.";container.hidden=true;
 try{
  const data=await api("indexnow-status?days="+encodeURIComponent($("naver-range").value));
  const counts=data.counts||{};
  $("naver-success").textContent=statNumber(counts.success);
  $("naver-cancelled").textContent=statNumber(counts.cancelled);
  $("naver-failed").textContent=statNumber(counts.failure);
  $("naver-pending").textContent=statNumber(counts.pending);
  tbody.replaceChildren();
  const labels={success:"실행 성공",cancelled:"취소",failure:"실패",timed_out:"시간 초과",skipped:"건너뜀"};
  for(const item of data.runs||[]){
   const tr=tbody.insertRow();
   const title=tr.insertCell();title.textContent=item.title||"실행 기록";
   const outcome=tr.insertCell();outcome.textContent=item.status==="completed"?(labels[item.conclusion]||item.conclusion||"완료"):"진행·대기";
   const when=tr.insertCell();when.textContent=item.date?new Date(item.date).toLocaleString("ko-KR"):"-";
   const linkCell=tr.insertCell();
   if(/^https:\/\/github\.com\//.test(item.url||"")){
    const link=document.createElement("a");link.textContent="실행 로그 ↗";link.href=item.url;link.target="_blank";link.rel="noopener noreferrer";linkCell.appendChild(link);
   }else linkCell.textContent="-";
  }
  status.textContent="최근 "+data.days+"일 실행 "+(data.runs||[]).length+"건"+(data.limited?" · 최근 100건까지만 조회":"")+" · 실제 색인은 별도 확인";
  container.hidden=false;
 }catch(err){status.textContent="실행 현황 조회 실패: "+err.message;}
}
$("refresh-naver").addEventListener("click",loadNaverStatus);
$("naver-range").addEventListener("change",loadNaverStatus);

// Admin analytics is read-only. All counts are supplied by the authenticated Worker.
const statNumber = n => new Intl.NumberFormat("ko-KR").format(Number(n)||0);
function analyticsTable(headers,rows){
 const table=document.createElement("table");table.className="analytics-table";
 const thead=table.createTHead(),tr=thead.insertRow();
 for(const h of headers){const th=document.createElement("th");th.textContent=h;tr.appendChild(th);}
 const body=table.createTBody();
 for(const row of rows){const tr=body.insertRow();for(const cell of row){const td=tr.insertCell();td.textContent=String(cell);}}
 return table;
}
async function loadAnalytics(){
 const status=$("analytics-status"),results=$("analytics-results"),setup=$("analytics-setup");
 status.textContent="통계를 불러오는 중입니다.";results.hidden=true;setup.hidden=true;
 try{
  const data=await api("analytics?range="+encodeURIComponent($("analytics-range").value));
  if(!data.configured){status.textContent=data.message||"연결 설정이 필요합니다.";setup.hidden=false;return;}
  const total=(field)=>(data.daily||[]).reduce((sum,item)=>sum+(Number(item[field])||0),0);
  $("stat-users").textContent=statNumber(total("users"));
  $("stat-views").textContent=statNumber(total("views"));
  $("stat-kakao").textContent=statNumber(data.clicks?.kakao);
  $("stat-phone").textContent=statNumber(data.clicks?.phone);
  $("stat-article").textContent=statNumber(data.clicks?.article);
  const daily=(data.daily||[]).map(x=>[String(x.date||"").replace(/^(\d{4})(\d{2})(\d{2})$/,"$1-$2-$3"),statNumber(x.users),statNumber(x.views)]);
  const pages=(data.pages||[]).map(x=>[x.path,statNumber(x.views)]);
  $("analytics-daily").replaceChildren(analyticsTable(["날짜","활성 사용자","조회수"],daily));
  $("analytics-pages").replaceChildren(analyticsTable(["페이지 주소","조회수"],pages));
  status.textContent="GA4 통계 연결됨 · 최근 "+data.range+"일 기준";
  results.hidden=false;
 }catch(e){status.textContent="GA4 통계를 불러오지 못했습니다: "+e.message;setup.hidden=false;}
}
$("ga-connect").addEventListener("click",()=>{window.location.assign("/api/ga-oauth/start");});
$("refresh-analytics").addEventListener("click",loadAnalytics);
$("analytics-range").addEventListener("change",loadAnalytics);

load().catch(e=>{$("login-panel").hidden=false;$("login-error").textContent=e.message;});
