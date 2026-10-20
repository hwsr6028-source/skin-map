import csv, html, pathlib, datetime, os, shutil
from urllib.parse import quote
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'dist'
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir()
(OUT/'assets').mkdir()
shutil.copy2(ROOT/'assets'/'style.css',OUT/'assets'/'style.css')
shutil.copytree(ROOT/'admin', OUT/'admin', dirs_exist_ok=True)
if (ROOT/'assets'/'uploads').exists(): shutil.copytree(ROOT/'assets'/'uploads',OUT/'assets'/'uploads',dirs_exist_ok=True)
DOMAIN=os.environ.get('SITE_URL','https://skin-map.pages.dev').rstrip('/')
with open(ROOT/'data'/'pages.csv',encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
def esc(s):return html.escape(str(s or ''),quote=True)
def url(row):return '/region/'+row['region_slug']+'/'+(row['procedure_slug']+'/' if row['type']=='procedure' else '')
def link(row):return '<a class="tile" href="'+url(row)+'"><span class="eyebrow">'+('시술 가이드' if row['type']=='procedure' else '지역 가이드')+'</span><strong>'+esc(row['region']+row['procedure'] if row['type']=='procedure' else row['region']+'피부과')+'</strong><small>가이드 보기 ↗</small></a>'
def frame(title,desc,path,body,index=True):
 canonical=DOMAIN+path
 robots='index,follow' if index else 'noindex,follow'
 return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="{robots}"><link rel="canonical" href="{esc(canonical)}"><meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(canonical)}"><link rel="stylesheet" href="/assets/style.css"><script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebSite","name":"정보세상","url":"{esc(DOMAIN)}/"}}</script></head><body><header class="site-header"><div class="shell nav"><a class="wordmark" href="/">정보<span>세상</span><i>.</i></a><nav><a href="/blog/">전체 글</a><a href="/blog/category/health/">병원·건강</a><a href="/blog/category/law/">법률</a><a href="/blog/category/interior/">인테리어</a><a href="/blog/category/moving/">이사·생활</a></nav></div></header><main>{body}</main><footer id="about"><div class="shell foot"><div><b>정보세상</b><p>생활과 전문 분야의 정보를 폭넓게 정리하는 종합 정보 매거진입니다.<br>콘텐츠는 일반적인 정보이며 전문 상담을 대신하지 않습니다.</p></div><div><span>© {datetime.date.today().year} 정보세상</span><p>건강·법률·금융 정보는 개인 상황에 따라 다를 수 있습니다.<br>게시 전 사실 확인과 관련 전문가 검토를 권장합니다.</p></div></div></footer></body></html>'''
def save(path,content):
 out=OUT/path.lstrip('/')/'index.html';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(content,encoding='utf8')
published=[r for r in rows if r['status']=='published']
regions=[r for r in published if r['type']=='region']
procedures=[r for r in published if r['type']=='procedure']
hero='''<section class="hero"><div class="shell hero-inner"><div><div class="micro">LOCAL SKINCARE DIRECTORY <span>•</span> REGION × TREATMENT</div><h1>내 피부에 맞는 정보,<br><em>내 동네</em>에서 시작하세요.</h1><p>지역별 피부과 선택 기준부터 주요 리프팅 시술의 특징까지.<br>처음 알아볼 때 필요한 정보를 하나씩 정리했습니다.</p><a href="#regions" class="cta">지역별 정보 둘러보기 <span>↗</span></a><div class="hero-stat"><span>03 <small>지역 가이드</small></span><span>03 <small>시술 가이드</small></span><span>100% <small>정보 탐색</small></span></div></div><div class="orb-wrap" aria-hidden="true"><div class="orb"></div><div class="orb-label one">SKIN HEALTH <b>01</b></div><div class="orb-label two">DISCOVER<br>YOUR ROUTINE</div></div></div></section>'''
home=hero+'<section class="section shell" id="regions"><div class="section-head"><div><span class="kicker">01 / LOCATION</span><h2>지역으로 찾아보기</h2><p>지역별로 확인할 선택 기준과 접근성 정보를 살펴보세요.</p></div><span class="count">'+str(len(regions))+' LOCATIONS</span></div><div class="cards">'+''.join(map(link,regions))+'</div></section>'+'<section class="section tinted" id="procedures"><div class="shell"><div class="section-head"><div><span class="kicker">02 / PROCEDURE</span><h2>시술로 찾아보기</h2><p>시술 원리와 상담 전 확인할 사항을 정리했습니다.</p></div><span class="count">'+str(len(procedures))+' GUIDES</span></div><div class="cards">'+''.join(map(link,procedures))+'</div></div></section>'+'<section class="shell note"><span class="kicker">OUR PRINCIPLE</span><h2>검색을 넘어, 도움이 되는 정보로.</h2><p>지역명만 바꾼 반복 페이지 대신 각 지역 및 시술의 고유한 정보를 보강하여 발행합니다. 게시된 내용은 의료 전문가의 진단을 대신하지 않습니다.</p></section>'
save('/',frame('정보세상 | 병원·법률·인테리어·이사 생활정보', '건강, 법률, 인테리어, 이사, 부동산, 금융, IT, 교육, 여행까지 분야별 생활 정보와 가이드를 확인하세요.','/',home))
for r in published:
 path=url(r); is_proc=r['type']=='procedure'; kw=r['region']+(r['procedure'] if is_proc else '피부과'); related=[x for x in published if x!=r and (x['region']==r['region'] or (is_proc and x['type']=='procedure'))][:4]
 breadcrumb='<a href="/">홈</a> <span> / </span> '+('<a href="/region/'+r['region_slug']+'/">'+esc(r['region'])+'</a> <span> / </span> ' if is_proc and any(x['type']=='region' and x['region_slug']==r['region_slug'] for x in regions) else '')+esc(kw)
 body=f'''<section class="article-top"><div class="shell"><div class="crumb">{breadcrumb}</div><span class="kicker">{'TREATMENT GUIDE' if is_proc else 'LOCAL GUIDE'}</span><h1>{esc(kw)}<br><em>선택 가이드</em></h1><p>{esc(r['intro'])}</p></div></section><section class="shell article-grid"><article class="article"><span class="kicker">01 / INTRODUCTION</span><h2>{esc(kw)} 알아보기</h2><p>{esc(r['intro'])}</p><span class="kicker">02 / LOCAL INFORMATION</span><h2>{esc(r['region'])} 지역 체크포인트</h2><p>{esc(r['local_info'])}</p><span class="kicker">03 / THINGS TO KNOW</span><h2>상담 전에 알아둘 점</h2><p>{esc(r['detail'])}</p><span class="kicker">04 / SAFETY FIRST</span><h2>주의사항</h2><p>{esc(r['considerations'])}</p><div class="disclaimer">이 페이지는 교육 목적의 기초 안내 자료입니다. 개인별 적합성과 위험성은 의료진의 진료로 확인해야 합니다. 공개 발행 전 지역 고유정보, 원자료 출처 및 의료 전문가 검토를 보강하세요.</div></article><aside><div class="sidebar"><span class="kicker">EXPLORE MORE</span><h3>함께 살펴보기</h3>{''.join('<a href="'+url(x)+'">'+esc(x['region']+(x['procedure'] if x['type']=='procedure' else '피부과'))+' <span>↗</span></a>' for x in related)}<a href="/">전체 가이드 <span>↗</span></a></div></aside></section>'''
 save(path,frame(r['title'],r['description'],path,body,index=False)) # draft content held noindex until verified

# CMS markdown articles.
import json, re
def md_inline(line):
    safe=esc(line)
    def image_replace(m):
        alt=m.group(1)
        raw_url=html.unescape(m.group(2))
        if not (raw_url.startswith('/assets/uploads/') or raw_url.startswith('https://') or raw_url.startswith('http://')):
            return m.group(0)
        return '<img src="'+esc(raw_url)+'" alt="'+alt+'" loading="lazy" decoding="async" class="post-image">'
    safe=re.sub(r'!\[([^\]]*)\]\(([^)\s]+)\)',image_replace,safe)
    safe=re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)',lambda m:'<a href="'+esc(html.unescape(m.group(2)))+'" rel="noopener noreferrer">'+m.group(1)+'</a>',safe)
    safe=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',safe)
    return safe
def markdown_to_html(source):
    result=[]; paragraph=[]; listing=[]
    def flush():
        if paragraph:
            result.append('<p>'+ '<br>'.join(md_inline(x) for x in paragraph)+'</p>');paragraph.clear()
        if listing:
            result.append('<ul>'+''.join('<li>'+md_inline(x)+'</li>' for x in listing)+'</ul>');listing.clear()
    for line in str(source or '').splitlines():
        line=line.strip()
        if not line: flush();continue
        match=re.match(r'^(#{1,3})\s+(.+)$',line)
        if match:
            flush();level=len(match.group(1))+1
            result.append('<h'+str(level)+'>'+md_inline(match.group(2))+'</h'+str(level)+'>')
        elif line.startswith('- '):
            if paragraph: flush()
            listing.append(line[2:])
        else:
            if listing: flush()
            paragraph.append(line)
    flush()
    return '\n'.join(result)
posts=[]
for f in sorted((ROOT/'content'/'posts').glob('*.json')):
    try:
        obj=json.loads(f.read_text(encoding='utf8'))
        if obj.get('status')=='published':
            slug=obj.get('slug','')
            if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',slug): raise ValueError('Invalid post slug')
            posts.append(obj)
    except Exception as e:
        print('Skipped post',f.name,':',e)
# Featured blog cards and static category / pagination pages
from urllib.parse import unquote
CATEGORIES={'health':'병원·건강','law':'법률','interior':'인테리어','moving':'이사·생활','realestate':'부동산','finance':'금융·경제','tech':'IT·디지털','education':'교육·취업','travel':'여행·취미','general':'비즈니스·기타','dermatology':'피부과 정보','lifting':'리프팅','skinbooster':'스킨부스터','other':'기타 시술'}
PAGE_SIZE=9
def category_of(post):
    val=str(post.get('category','')).strip()
    if val in CATEGORIES:return val
    subject=str(post.get('procedure',''))+' '+str(post.get('title',''))
    if any(w in subject for w in ('울쎄라','써마지','온다','볼뉴머','슈링크','리프팅','덴서티','텐서마')):return 'lifting'
    if any(w in subject for w in ('리쥬란','쥬베룩','스킨부스터','리투오','물광','엑소좀')):return 'skinbooster'
    if any(w in subject for w in ('피부과','피부','시술','병원')):return 'health'
    return 'general'
def image_url(value):
    v=str(value or '').strip()
    if not v:return ''
    if v.startswith('https://') or v.startswith('http://'):return v
    if v.startswith('/assets/uploads/'):return v
    if v.startswith('assets/uploads/'):return '/'+v
    return ''
def card_image(post):
    cover=image_url(post.get('thumbnail',''))
    if cover:return cover
    match=re.search(r'!\[[^\]]*\]\(([^)\s]+)\)',str(post.get('body','')))
    return image_url(unquote(match.group(1))) if match else ''
def blog_card(post):
    img=card_image(post)
    pic=('<span class="blog-card-media"><img loading="lazy" decoding="async" src="'+esc(img)+'" alt="'+esc(post.get('title',''))+'"></span>' if img else '<span class="blog-card-media blog-card-placeholder"><span>정보세상</span></span>')
    path='/blog/'+esc(post['slug'])+'/'
    cat=CATEGORIES[category_of(post)]
    date=str(post.get('date',''))[:10]
    return '<a class="blog-card" href="'+path+'">'+pic+'<span class="blog-card-copy"><span class="blog-card-meta">'+esc(cat)+' · '+esc(date)+'</span><strong>'+esc(post.get('title',''))+'</strong><span class="blog-card-description">'+esc(post.get('description',''))+'</span><span class="blog-card-more">글 읽기 ↗</span></span></a>'
posts.sort(key=lambda x:(str(x.get('date','')),str(x.get('title',''))),reverse=True)
for article in posts:
    path='/blog/'+article['slug']+'/'
    title=article.get('title','')
    desc=article.get('description','')
    page='<section class="article-top"><div class="shell"><div class="crumb"><a href="/">홈</a> / <a href="/blog/">블로그</a></div><span class="kicker">'+esc(CATEGORIES[category_of(article)])+'</span><h1>'+esc(title)+'</h1><p>'+esc(desc)+'</p></div></section>'
    page+='<section class="shell article-grid"><article class="article">'+markdown_to_html(article.get('body',''))+'<div class="disclaimer">본 콘텐츠는 일반적인 정보 제공 목적이며 개인별 상황에 맞는 전문 상담을 대신하지 않습니다.</div></article></section>'
    save(path,frame(title,desc,path,page,index=bool(article.get('seo_approved',False))))
def listing_path(category,num):
    root='/blog/' if not category else '/blog/category/'+category+'/'
    return root if num==1 else root+'page/'+str(num)+'/'
def category_nav(active):
    all_count=len(posts)
    links=[('<a class="'+('active' if not active else '')+'" href="/blog/">전체 <span>'+str(all_count)+'</span></a>')]
    for key,label in CATEGORIES.items():
        count=sum(category_of(p)==key for p in posts)
        if key not in ('dermatology','lifting','skinbooster','other') or count:
            links.append('<a class="'+('active' if key==active else '')+'" href="'+listing_path(key,1)+'">'+esc(label)+' <span>'+str(count)+'</span></a>')
    return '<nav class="blog-filters" aria-label="블로그 카테고리">'+''.join(links)+'</nav>'
def render_listing(category=''):
    subset=[p for p in posts if not category or category_of(p)==category]
    total=max(1,(len(subset)+PAGE_SIZE-1)//PAGE_SIZE)
    for num in range(1,total+1):
        path=listing_path(category,num)
        current=subset[(num-1)*PAGE_SIZE:num*PAGE_SIZE]
        title=(CATEGORIES[category] if category else '정보세상 종합 정보 블로그')
        intro='<section class="article-top"><div class="shell"><span class="kicker">정보세상 JOURNAL</span><h1>'+esc(title)+'</h1><p>건강, 법률, 인테리어, 이사부터 생활 정보까지 폭넓게 살펴보세요.</p></div></section>'
        grid='<div class="blog-cards">'+''.join(blog_card(x) for x in current)+'</div>' if current else '<p>아직 이 카테고리에 공개된 글이 없습니다.</p>'
        page_links=''
        if total>1:
            for i in range(1,total+1):
                page_links+='<a '+('aria-current="page" class="active" ' if i==num else '')+'href="'+listing_path(category,i)+'">'+str(i)+'</a>'
        pager='<nav class="blog-pagination" aria-label="페이지 이동">'+page_links+'</nav>' if page_links else ''
        body=intro+'<section class="section shell">'+category_nav(category)+grid+pager+'</section>'
        save(path,frame(title+' | 정보세상', '다양한 분야별 최신 가이드와 실용 정보 모음',path,body,index=True))
render_listing()
for cat in CATEGORIES:
    if cat not in ('dermatology','lifting','skinbooster','other') or any(category_of(x)==cat for x in posts):render_listing(cat)
home_index=OUT/'index.html'
home_html=home_index.read_text(encoding='utf8')
featured=posts[:6]
featured_cards=''.join(blog_card(x) for x in featured)
if not featured_cards:
    featured_cards='<p>첫 번째 블로그 글을 기다리고 있습니다.</p>'
blog_section='<section class="section shell" id="blog"><div class="section-head"><div><span class="kicker">01 / BLOG</span><h2>최신 블로그 글</h2><p>일상에 필요한 다양한 분야의 새로운 정보를 확인해 보세요.</p></div><a class="blog-all-link" href="/blog/">전체 글 보기 ↗</a></div><div class="blog-cards">'+featured_cards+'</div></section>'
category_tiles=''.join('<a href="/blog/category/'+key+'/" class="topic-tile"><span class="topic-symbol">'+{'health':'✚','law':'⚖','interior':'▧','moving':'▣','realestate':'⌂','finance':'₩','tech':'⌘','education':'✎','travel':'✈','general':'···'}[key]+'</span><strong>'+esc(label)+'</strong><small>정보 보기 →</small></a>' for key,label in CATEGORIES.items() if key not in ('dermatology','lifting','skinbooster','other'))
topics_section='<section class="section shell" id="topics"><div class="section-head"><div><span class="kicker">DISCOVER TOPICS</span><h2>분야별 정보 둘러보기</h2><p>관심 있는 주제를 선택해 필요한 정보를 찾아보세요.</p></div></div><div class="topic-grid">'+category_tiles+'</div></section>'
home_html=home_html.replace('<section class="section shell" id="regions">',topics_section+blog_section+'<section class="section shell" id="regions">',1)
# The original region/procedure sample pages remain reachable at their old URLs but are no longer featured on the front page.
home_html=re.sub(r'<section class="section shell" id="regions">.*?<section class="shell note">.*?</section>', '', home_html, flags=re.S)
home_html=home_html.replace('LOCAL SKINCARE DIRECTORY','INFORMATION FOR EVERYDAY LIFE').replace('REGION × TREATMENT','ALL TOPICS').replace('내 피부에 맞는 정보,<br><em>내 동네</em>에서 시작하세요.','궁금한 모든 정보,<br><em>정보세상</em>에서 찾아보세요.').replace('지역별 피부과 선택 기준부터 주요 리프팅 시술의 특징까지.<br>처음 알아볼 때 필요한 정보를 하나씩 정리했습니다.','병원·건강, 법률, 인테리어, 이사·생활까지.<br>일상에 필요한 정보를 쉽고 꼼꼼하게 정리합니다.').replace('지역별 정보 둘러보기','최신 정보 둘러보기').replace('href="#regions"','href="#blog"')
home_html=re.sub(r'<div class="hero-stat">.*?</div>', '<div class="hero-stat"><span>HEALTH <small>병원·건강</small></span><span>LAW <small>법률 정보</small></span><span>LIFE <small>일상 가이드</small></span></div>', home_html, count=1, flags=re.S)
home_html=home_html.replace('SKIN HEALTH','USEFUL INFO').replace('DISCOVER<br>YOUR ROUTINE','EXPLORE<br>MORE')
home_html=home_html.replace('정보세상 | 지역별 피부과·시술 정보','정보세상 | 생활·전문 지식 정보')

home_index.write_text(home_html,encoding='utf8')
(OUT/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+DOMAIN+'/sitemap.xml\n',encoding='utf8')
now=datetime.date.today().isoformat()
sitemap_urls=['/','/blog/']+['/blog/'+x['slug']+'/' for x in posts if x.get('seo_approved',False)]
(OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join('<url><loc>'+DOMAIN+p+'</loc><lastmod>'+now+'</lastmod></url>\n' for p in sitemap_urls)+'</urlset>',encoding='utf8')
print('Built',len(published)+len(posts)+2,'pages ->',OUT)
