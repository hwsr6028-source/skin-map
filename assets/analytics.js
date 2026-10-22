/* Information World GA4 click events. No personal data or phone numbers are collected. */
(function(){
  "use strict";
  function emit(name, detail){
    if(typeof window.gtag!=="function")return;
    window.gtag("event",name,detail);
  }
  function linkType(link){
    var href=link.getAttribute("href")||"";
    if(/^tel:/i.test(href))return "phone";
    if(/^(https?:)?\/\/open\.kakao\.com\//i.test(href))return "kakao";
    if(/^\/blog\//.test(href)&&!/^\/blog\/(category|page)\//.test(href)&&!/^\/blog\/?$/.test(href))return "article";
    return null;
  }
  document.addEventListener("click",function(event){
    var link=event.target.closest&&event.target.closest("a[href]");
    if(!link)return;
    var kind=linkType(link);if(!kind)return;
    var path=(new URL(link.href,location.href)).pathname;
    var data={
      link_type:kind,
      link_path:kind==="article"?path:location.pathname,
      source_page:location.pathname,
      link_label:(link.innerText||link.getAttribute("aria-label")||"").trim().slice(0,100)
    };
    if(kind==="phone")emit("phone_click",data);
    else if(kind==="kakao")emit("kakao_click",data);
    else emit("article_click",data);
  },{passive:true});
})();