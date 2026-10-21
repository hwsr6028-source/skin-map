const $=id=>document.getElementById(id);
let editFile=null,editSha=null,editingSlug="";
let allPosts=[],activeCategory="all";
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
 const slug=editFile?editingSlug:normalize($("keyword").value);
 $("slug-preview").textContent=slug?"https://skin-map.pages.dev/blog/"+slug+"/":"키워드를 입력해 주세요.";
}
$("keyword").addEventListener("input",preview);
function showLogin(isLogged){
 $("login-panel").hidden=isLogged;$("app-panel").hidden=!isLogged;$("account").hidden=!isLogged;
}
async function load(){
 const me=await api("me");
 showLogin(me.authenticated);
 if(me.authenticated){await list();reset();}
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
 $("post-form").reset();$("date").value=new Date().toISOString().slice(0,10);
 $("editor-title").textContent="새 글 작성";$("message").textContent="";$("upload-result").textContent="";preview();
}
$("new-post").addEventListener("click",()=>{reset();if(activeCategory!=="all")$("category").value=activeCategory;$("editor-title").scrollIntoView({behavior:"smooth",block:"start"});});
function renderCategories(){
 const stats=$("category-stats");stats.replaceChildren();
 const counts={};
 for(const p of allPosts){const k=p.category||"general";counts[k]=(counts[k]||0)+1;}
 const options=[["all","전체 글"],...categories];
 for(const [key,label] of options){
   const button=document.createElement("button");button.type="button";
   button.className="category-stat"+(activeCategory===key?" selected":"");
   button.setAttribute("aria-pressed",String(activeCategory===key));
   const name=document.createElement("span");name.className="category-stat-label";name.textContent=label;
   const num=document.createElement("strong");num.className="category-stat-count";
   num.textContent=String(key==="all"?allPosts.length:counts[key]||0);
   button.append(name,num);
   button.onclick=()=>{activeCategory=key;renderCategories();renderPosts();};
   stats.appendChild(button);
 }
}
function renderPosts(){
 const root=$("post-list");root.replaceChildren();
 const query=$("post-search").value.trim().toLowerCase();
 const state=$("status-filter").value;
 const shown=allPosts.filter(p=>(activeCategory==="all"||p.category===activeCategory)&&(state==="all"||p.status===state)&&(!query||[p.title,p.file,p.date,categoryName(p.category)].join(" ").toLowerCase().includes(query)));
 $("filtered-count").textContent=shown.length+"개";
 if(!shown.length){const p=document.createElement("p");p.className="empty-post-list";p.textContent=allPosts.length?"조건에 해당하는 글이 없습니다.":"아직 작성된 글이 없습니다.";root.appendChild(p);return;}
 for(const p of shown){
   const item=document.createElement("article");item.className="post-list-item";
   const title=document.createElement("strong");title.className="post-list-name";title.textContent=p.title||p.file;title.title=p.title||p.file;
   const meta=document.createElement("div");meta.className="post-list-meta";
   const status=document.createElement("span");status.className=p.status==="published"?"status-live":"status-draft";status.textContent=p.status==="published"?"공개":p.status==="draft"?"임시저장":"상태 확인 필요";
   const category=document.createElement("span");category.textContent=categoryName(p.category);
   const date=document.createElement("span");date.textContent=p.date||"";
   meta.append(status,category,date);
   const actions=document.createElement("div");actions.className="post-list-actions";
   const edit=document.createElement("button");edit.type="button";edit.className="post-list-edit";edit.textContent="✎ 수정";edit.onclick=()=>openPost(p.file);
   const remove=document.createElement("button");remove.type="button";remove.className="post-list-delete";remove.textContent="삭제";remove.onclick=()=>deletePost(p.file,p.sha,p.title||p.file);
   actions.append(edit,remove);item.append(title,meta,actions);root.appendChild(item);
 }
}
async function list(force=false){
 const root=$("post-list");root.textContent="글 목록 불러오는 중...";
 try{
   const d=await api("posts"+(force?"?refresh=1":""));
   allPosts=d.posts||[];
   renderCategories();renderPosts();
 }catch(e){root.textContent="글 목록을 불러오지 못했습니다: "+e.message;throw e;}
}
$("post-search").addEventListener("input",renderPosts);
$("status-filter").addEventListener("change",renderPosts);
$("refresh-posts").addEventListener("click",()=>list(true).catch(err=>alert(err.message)));
async function deletePost(file,sha,title){
 if(!file||!sha)return alert("글 정보가 올바르지 않습니다. 목록을 다시 불러와 주세요.");
 if(!confirm("다음 글을 삭제하시겠습니까?\n\n"+title+"\n\n삭제하면 홈페이지에서 글이 내려갑니다."))return;
 if(prompt("최종 확인: '삭제'라고 입력해 주세요.")!=="삭제")return;
 $("message").textContent="삭제 중...";
 try{
   await api("post",{method:"DELETE",body:JSON.stringify({file,sha})});
   if(editFile===file)reset();
   await list(true);
   $("message").textContent="글 삭제 완료! 홈페이지 자동 배포가 시작됩니다.";
 }catch(err){$("message").textContent="삭제 실패: "+err.message;alert("삭제 실패: "+err.message);}
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
   $("seo_approved").checked=data.article.seo_approved===true;
   $("editor-title").textContent="글 수정: "+(data.article.title||file);$("message").textContent="";preview();
   window.scrollTo({top:0,behavior:"smooth"});
 }catch(e){alert(e.message);}
}
$("delete-post").addEventListener("click",async()=>{
 await deletePost(editFile,editSha,$("title").value.trim()||editFile);
});
$("post-form").addEventListener("submit",async e=>{
 e.preventDefault();const button=$("save-btn");button.disabled=true;$("message").textContent="저장 중...";
 const article={};for(const field of fields)article[field]=$(field).value;
 article.seo_approved=$("seo_approved").checked;if(editFile)article.slug=editingSlug;
 try{
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
   const btn=document.createElement("button");btn.className="quiet";btn.type="button";btn.textContent="본문에 삽입";
   btn.onclick=()=>{$("body").value+="\n\n![이미지 설명]("+r.url+")\n\n";};
   result.appendChild(btn);$("thumbnail").value=r.url;
  }catch(e){alert(e.message);}
 };
 reader.readAsDataURL(file);
});
load().catch(e=>{$("login-panel").hidden=false;$("login-error").textContent=e.message;});
