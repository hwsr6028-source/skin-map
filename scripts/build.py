import csv, html, pathlib, datetime, os, shutil
from urllib.parse import quote
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'dist'
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir()
(OUT/'assets').mkdir()
shutil.copy2(ROOT/'assets'/'style.css',OUT/'assets'/'style.css')
DOMAIN=os.environ.get('SITE_URL','https://example.pages.dev').rstrip('/')
with open(ROOT/'data'/'pages.csv',encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
def esc(s):return html.escape(str(s or ''),quote=True)
def url(row):return '/region/'+row['region_slug']+'/'+(row['procedure_slug']+'/' if row['type']=='procedure' else '')
def link(row):return '<a class="tile" href="'+url(row)+'"><span class="eyebrow">'+('시술 가이드' if row['type']=='procedure' else '지역 가이드')+'</span><strong>'+esc(row['region']+row['procedure'] if row['type']=='procedure' else row['region']+'피부과')+'</strong><small>가이드 보기 ↗</small></a>'
def frame(title,desc,path,body,index=True):
 canonical=DOMAIN+path
 robots='index,follow' if index else 'noindex,follow'
 return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="{robots}"><link rel="canonical" href="{esc(canonical)}"><meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(canonical)}"><link rel="stylesheet" href="/assets/style.css"><script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebSite","name":"스킨맵","url":"{esc(DOMAIN)}/"}}</script></head><body><header class="site-header"><div class="shell nav"><a class="wordmark" href="/">SKIN<span>MAP</span><i>.</i></a><nav><a href="/#regions">지역별 정보</a><a href="/#procedures">시술별 정보</a><a href="/#about">운영 안내</a></nav></div></header><main>{body}</main><footer id="about"><div class="shell foot"><div><b>SKINMAP</b><p>지역별 피부과·피부 시술 정보를 정리하는 가이드입니다.<br>의료기관이 아니며 진료나 시술을 제공하지 않습니다.</p></div><div><span>© {datetime.date.today().year} SKINMAP</span><p>의료 정보는 일반적인 안내이며 진단이나 치료를 대신하지 않습니다.<br>발행 전 의료 전문가 검토를 권장합니다.</p></div></div></footer></body></html>'''
def save(path,content):
 out=OUT/path.lstrip('/')/'index.html';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(content,encoding='utf8')
published=[r for r in rows if r['status']=='published']
regions=[r for r in published if r['type']=='region']
procedures=[r for r in published if r['type']=='procedure']
hero='''<section class="hero"><div class="shell hero-inner"><div><div class="micro">LOCAL SKINCARE DIRECTORY <span>•</span> REGION × TREATMENT</div><h1>내 피부에 맞는 정보,<br><em>내 동네</em>에서 시작하세요.</h1><p>지역별 피부과 선택 기준부터 주요 리프팅 시술의 특징까지.<br>처음 알아볼 때 필요한 정보를 하나씩 정리했습니다.</p><a href="#regions" class="cta">지역별 정보 둘러보기 <span>↗</span></a><div class="hero-stat"><span>03 <small>지역 가이드</small></span><span>03 <small>시술 가이드</small></span><span>100% <small>정보 탐색</small></span></div></div><div class="orb-wrap" aria-hidden="true"><div class="orb"></div><div class="orb-label one">SKIN HEALTH <b>01</b></div><div class="orb-label two">DISCOVER<br>YOUR ROUTINE</div></div></div></section>'''
home=hero+'<section class="section shell" id="regions"><div class="section-head"><div><span class="kicker">01 / LOCATION</span><h2>지역으로 찾아보기</h2><p>지역별로 확인할 선택 기준과 접근성 정보를 살펴보세요.</p></div><span class="count">'+str(len(regions))+' LOCATIONS</span></div><div class="cards">'+''.join(map(link,regions))+'</div></section>'+'<section class="section tinted" id="procedures"><div class="shell"><div class="section-head"><div><span class="kicker">02 / PROCEDURE</span><h2>시술로 찾아보기</h2><p>시술 원리와 상담 전 확인할 사항을 정리했습니다.</p></div><span class="count">'+str(len(procedures))+' GUIDES</span></div><div class="cards">'+''.join(map(link,procedures))+'</div></div></section>'+'<section class="shell note"><span class="kicker">OUR PRINCIPLE</span><h2>검색을 넘어, 도움이 되는 정보로.</h2><p>지역명만 바꾼 반복 페이지 대신 각 지역 및 시술의 고유한 정보를 보강하여 발행합니다. 게시된 내용은 의료 전문가의 진단을 대신하지 않습니다.</p></section>'
save('/',frame('스킨맵 | 지역별 피부과·시술 정보', '강남·노원·동탄 피부과 선택 가이드와 울쎄라·써마지·볼뉴머 등 시술 정보를 확인하세요.','/',home))
for r in published:
 path=url(r); is_proc=r['type']=='procedure'; kw=r['region']+(r['procedure'] if is_proc else '피부과'); related=[x for x in published if x!=r and (x['region']==r['region'] or (is_proc and x['type']=='procedure'))][:4]
 breadcrumb='<a href="/">홈</a> <span> / </span> '+('<a href="/region/'+r['region_slug']+'/">'+esc(r['region'])+'</a> <span> / </span> ' if is_proc and any(x['type']=='region' and x['region_slug']==r['region_slug'] for x in regions) else '')+esc(kw)
 body=f'''<section class="article-top"><div class="shell"><div class="crumb">{breadcrumb}</div><span class="kicker">{'TREATMENT GUIDE' if is_proc else 'LOCAL GUIDE'}</span><h1>{esc(kw)}<br><em>선택 가이드</em></h1><p>{esc(r['intro'])}</p></div></section><section class="shell article-grid"><article class="article"><span class="kicker">01 / INTRODUCTION</span><h2>{esc(kw)} 알아보기</h2><p>{esc(r['intro'])}</p><span class="kicker">02 / LOCAL INFORMATION</span><h2>{esc(r['region'])} 지역 체크포인트</h2><p>{esc(r['local_info'])}</p><span class="kicker">03 / THINGS TO KNOW</span><h2>상담 전에 알아둘 점</h2><p>{esc(r['detail'])}</p><span class="kicker">04 / SAFETY FIRST</span><h2>주의사항</h2><p>{esc(r['considerations'])}</p><div class="disclaimer">이 페이지는 교육 목적의 기초 안내 자료입니다. 개인별 적합성과 위험성은 의료진의 진료로 확인해야 합니다. 공개 발행 전 지역 고유정보, 원자료 출처 및 의료 전문가 검토를 보강하세요.</div></article><aside><div class="sidebar"><span class="kicker">EXPLORE MORE</span><h3>함께 살펴보기</h3>{''.join('<a href="'+url(x)+'">'+esc(x['region']+(x['procedure'] if x['type']=='procedure' else '피부과'))+' <span>↗</span></a>' for x in related)}<a href="/">전체 가이드 <span>↗</span></a></div></aside></section>'''
 save(path,frame(r['title'],r['description'],path,body,index=False)) # draft content held noindex until verified
# Explicit noindex for all generated draft examples. Remove only after substantial editorial review.
(OUT/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+DOMAIN+'/sitemap.xml\n',encoding='utf8')
now=datetime.date.today().isoformat()
(OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n<url><loc>'+DOMAIN+'/</loc><lastmod>'+now+'</lastmod></url>\n</urlset>',encoding='utf8')
print('Built',len(published)+1,'pages ->',OUT)
