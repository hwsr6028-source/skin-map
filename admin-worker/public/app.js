const $=id=>document.getElementById(id);
let editFile=null,editSha=null,editingSlug="";
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
 $("post-form").reset();$("date").value=new Date().toISOString().slice(0,10);
 $("editor-title").textContent="새 글 작성";$("message").textContent="";$("upload-result").textContent="";preview();
}
$("new-post").addEventListener("click",reset);
async function list(){
 const d=await api("posts"),root=$("post-list");
 root.replaceChildren();
 if(!d.posts.length){root.textContent="아직 작성된 글이 없습니다.";return;}
 for(const p of d.posts){
   const button=document.createElement("button");button.type="button";button.textContent=p.file;
   button.onclick=()=>openPost(p.file);root.appendChild(button);
 }
}
async function openPost(file){
 try{
   const data=await api("post?file="+encodeURIComponent(file));
   editFile=file;editSha=data.sha;editingSlug=data.article.slug||file.replace(/\.json$/,"");
   for(const field of fields)$(field).value=data.article[field]??"";
   $("seo_approved").checked=data.article.seo_approved===true;
   $("editor-title").textContent="글 수정: "+(data.article.title||file);$("message").textContent="";preview();
   window.scrollTo({top:0,behavior:"smooth"});
 }catch(e){alert(e.message);}
}
$("post-form").addEventListener("submit",async e=>{
 e.preventDefault();const button=$("save-btn");button.disabled=true;$("message").textContent="저장 중...";
 const article={};for(const field of fields)article[field]=$(field).value;
 article.seo_approved=$("seo_approved").checked;if(editFile)article.slug=editingSlug;
 try{
  const r=await api("post",{method:"POST",body:JSON.stringify({file:editFile,sha:editSha,article})});
  $("message").textContent="저장 완료! 홈페이지 자동 배포가 시작됩니다.";
  await list();await openPost(r.file);
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
