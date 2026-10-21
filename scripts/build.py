import csv, html, pathlib, datetime, os, shutil, hashlib
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
 return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="google-site-verification" content="n90ax_Rr4TxN5s1JgLTOYITAbJftYgZmlzP-vPiJCW4"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="{robots}"><link rel="canonical" href="{esc(canonical)}"><meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(canonical)}"><link rel="stylesheet" href="/assets/style.css"><script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebSite","name":"정보세상","url":"{esc(DOMAIN)}/"}}</script></head><body><header class="site-header"><div class="shell nav"><a class="wordmark" href="/">정보<span>세상</span><i>.</i></a><nav aria-label="주요 메뉴"><a href="/#services">서비스</a><a href="/#process">진행 방식</a><a href="/#industries">전문 분야</a><a href="/blog/">콘텐츠</a><a class="nav-contact" href="/contact/">광고 문의 ↗</a></nav></div></header><main>{body}</main><footer id="about"><div class="shell foot"><div><b>정보세상</b><p>업종과 검색 의도를 연결하는 콘텐츠 제작·SEO 광고 스튜디오입니다.<br>기획부터 원고 제작과 운영까지 콘텐츠 중심의 솔루션을 안내합니다.</p></div><div><span>© {datetime.date.today().year} 정보세상</span><p>콘텐츠의 검색 노출 및 성과는 보장되지 않습니다.<br>의료·법률·금융 정보는 해당 전문가 검토가 필요합니다.</p></div></div></footer></body></html>'''
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
            # Sveltia stores the generated slug in the filename, not necessarily JSON.
            # Preserve legacy slug values for old posts; use the filename for new posts.
            slug=str(obj.get('slug') or f.stem).strip().lower()
            if not re.fullmatch(r'[가-힣ㄱ-ㅎㅏ-ㅣa-z0-9]+(?:-[가-힣ㄱ-ㅎㅏ-ㅣa-z0-9]+)*',slug):
                raise ValueError('Invalid post slug: '+slug)
            obj['slug']=slug
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

# Free SEO cover images: generated as SVG at every build, no external API or fee.
COVER_PALETTES={
 'health':('#e9f3ec','#335f49','#b4dbc1','HEALTH'),
 'law':('#ecedf8','#3c5181','#cbd3eb','LAW'),
 'interior':('#f7f0e6','#755537','#ead5b9','INTERIOR'),
 'moving':('#e9f3f8','#365e77','#bcdaea','MOVING'),
 'realestate':('#eff2e8','#4f6441','#d4dfc0','REAL ESTATE'),
 'finance':('#e8f4ef','#296955','#bce2d1','FINANCE'),
 'tech':('#efeffa','#4a548a','#ced0ef','TECH'),
 'education':('#f8eee8','#8b5843','#eed3c5','EDUCATION'),
 'travel':('#e9f4f9','#386e84','#c0dfeb','TRAVEL'),
 'general':('#eef3ef','#375e4c','#cadfd0','INFORMATION')
}
def auto_cover(post):
    title=str(post.get('title') or post.get('keyword') or '정보 가이드').strip()
    category=category_of(post)
    group=category if category in COVER_PALETTES else 'health'
    bg,ink,accent,label=COVER_PALETTES[group]
    digest=hashlib.sha256((post['slug']+'|'+title+'|'+category).encode('utf-8')).hexdigest()[:20]
    directory=OUT/'assets'/'covers'
    directory.mkdir(parents=True,exist_ok=True)
    # Wrap titles by visual glyph width, splitting long Korean phrases as needed.
    chars=[]
    for ch in title:
        chars.append((ch,1.65 if ord(ch)>127 else 1))
    lines=[];current='';width=0
    for ch,w in chars:
        if width+w>24 and current:
            lines.append(current.strip());current='';width=0
        if len(lines)==3:break
        current+=ch;width+=w
    if current and len(lines)<3:lines.append(current.strip())
    if not lines:lines=['정보 가이드']
    if len(lines)==3 and len(''.join(lines))<len(title):lines[-1]=lines[-1][:15].rstrip()+'…'
    start=260-34*(len(lines)-1)
    titles=''.join('<text x="74" y="'+str(start+73*i)+'" fill="'+ink+'" font-family="Noto Sans KR, Arial, sans-serif" font-size="52" font-weight="750">'+esc(line)+'</text>' for i,line in enumerate(lines))
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" viewBox="0 0 1200 675"><rect width="1200" height="675" fill="'+bg+'"/><circle cx="1085" cy="130" r="290" fill="'+accent+'" opacity=".46"/><circle cx="1050" cy="620" r="180" fill="'+accent+'" opacity=".35"/><path d="M74 120h1052M74 568h1052" stroke="'+ink+'" opacity=".18"/><text x="74" y="86" fill="'+ink+'" font-family="Arial,sans-serif" letter-spacing="5" font-size="24" font-weight="700">'+label+'</text>'+titles+'<text x="74" y="624" fill="'+ink+'" font-family="Noto Sans KR, Arial,sans-serif" font-size="29" font-weight="700">정보세상</text><text x="1004" y="621" fill="'+ink+'" font-family="Arial,sans-serif" font-size="23">GUIDE</text></svg>'
    (directory/(digest+'.svg')).write_text(svg,encoding='utf-8')
    return '/assets/covers/'+digest+'.svg'

def card_image(post):
    cover=image_url(post.get('thumbnail',''))
    if cover:return cover
    return post.get('_auto_cover') or auto_cover(post)
def blog_card(post):
    img=card_image(post)
    pic=('<span class="blog-card-media"><img loading="lazy" decoding="async" src="'+esc(img)+'" alt="'+esc(post.get('title',''))+'"></span>' if img else '<span class="blog-card-media blog-card-placeholder"><span>정보세상</span></span>')
    path='/blog/'+esc(post['slug'])+'/'
    cat=CATEGORIES[category_of(post)]
    date=str(post.get('date',''))[:10]
    return '<a class="blog-card" href="'+path+'">'+pic+'<span class="blog-card-copy"><span class="blog-card-meta">'+esc(cat)+' · '+esc(date)+'</span><strong>'+esc(post.get('title',''))+'</strong><span class="blog-card-description">'+esc(post.get('description',''))+'</span><span class="blog-card-more">글 읽기 ↗</span></span></a>'
posts.sort(key=lambda x:(str(x.get('date','')),str(x.get('title',''))),reverse=True)
for post in posts:
    if not image_url(post.get('thumbnail')):
        post['_auto_cover']=auto_cover(post)
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

# Agency-style brand homepage, composed after articles are available.
featured=posts[:6]
featured_cards=''.join(blog_card(x) for x in featured)
if not featured_cards:
    featured_cards='<div class="empty-posts">첫 번째 콘텐츠가 발행되면 이곳에 소개됩니다.</div>'
category_info=[
 ('health','병원·건강','의료·헬스케어', '01'),
 ('law','법률','법률·전문 서비스','02'),
 ('interior','인테리어','공간·인테리어','03'),
 ('moving','이사·생활','이사·생활 서비스','04'),
 ('realestate','부동산','부동산·주거','05'),
 ('finance','금융·경제','금융·경제','06'),
 ('tech','IT·디지털','IT·테크','07'),
 ('education','교육·취업','교육·커리어','08'),
 ('travel','여행·취미','여행·라이프스타일','09'),
 ('general','비즈니스·기타','기타 업종','10'),
]
industry_tiles=''.join('<a class="agency-industry" href="/blog/category/'+key+'/"><span class="agency-industry-number">'+number+'</span><strong>'+esc(short)+'</strong><span class="agency-industry-arrow">↗</span></a>' for key,short,detail,number in category_info)
agency_hero="""<section class="agency-hero"><div class="shell agency-hero-grid"><div class="agency-hero-copy"><span class="agency-kicker"><span class="agency-dot"></span> CONTENT MARKETING STUDIO · 정보세상</span><h1>검색에서 발견되고,<br><em>콘텐츠로 설득되는</em><br>브랜드를 만듭니다.</h1><p>키워드 전략부터 업종별 전문 원고, 자체 콘텐츠 발행과 SEO 운영까지.<br>브랜드의 이야기가 필요한 고객에게 닿도록 설계합니다.</p><div class="agency-hero-actions"><a class="agency-button" href="/contact/">광고·콘텐츠 제작 문의 <span>↗</span></a><a class="agency-text-link" href="#services">서비스 알아보기 <span>↘</span></a></div><div class="agency-hero-small"><span>STRATEGY</span><span>CONTENT</span><span>SEO</span><span>GROWTH</span></div></div><div class="agency-visual" aria-label="콘텐츠 전략 프로세스 그래픽"><div class="visual-orbit orbit-a"></div><div class="visual-orbit orbit-b"></div><div class="agency-visual-head">INFORMATION<br>MEETS<br><span>IMPACT.</span></div><div class="visual-plate plate-top"><span>01 / RESEARCH</span><strong>Keyword Insight</strong><small>검색 의도 분석</small></div><div class="visual-plate plate-middle"><span>02 / CONTENT</span><strong>Editorial Strategy</strong><small>콘텐츠 기획·제작</small></div><div class="visual-plate plate-bottom"><span>03 / OPTIMIZE</span><strong>SEO &amp; Publishing</strong><small>발행 및 개선</small></div><div class="visual-decoration">✳</div></div></div></section>"""
agency_intro="""<section class="agency-intro shell"><div class="agency-intro-mark">WHAT WE DO <span>↘</span></div><p>좋은 광고는 단순한 노출로 끝나지 않습니다.<br><strong>검색 의도에 맞는 정보</strong>가 신뢰를 만들고,<br>신뢰는 다음 행동으로 이어질 수 있습니다.</p></section>"""
agency_services="""<section class="agency-section agency-section-dark" id="services"><div class="shell"><div class="agency-section-head"><div><span class="agency-section-label">01 — SERVICES</span><h2>콘텐츠의 시작부터<br>운영까지, 하나의 흐름으로.</h2></div><p>목표와 업종에 맞는 키워드 구조를 세우고,<br>실질적인 정보를 담은 콘텐츠를 기획합니다.</p></div><div class="agency-services-grid"><article class="agency-service"><span class="service-number">01 /</span><div class="service-icon">⌕</div><h3>키워드·SEO 전략</h3><p>지역, 업종, 서비스 키워드를 분석하고 검색 의도에 맞는 주제와 정보 구조를 설계합니다.</p><span class="service-foot">Keyword Research ↗</span></article><article class="agency-service"><span class="service-number">02 /</span><div class="service-icon">✎</div><h3>자체 콘텐츠 제작</h3><p>브랜드의 서비스와 전문성을 전달하는 정보성 원고, 블로그 콘텐츠, 상세페이지 카피를 제작합니다.</p><span class="service-foot">Content Production ↗</span></article><article class="agency-service"><span class="service-number">03 /</span><div class="service-icon">▧</div><h3>콘텐츠 발행·운영</h3><p>카테고리와 주제에 따라 콘텐츠를 정리하고, 지속적으로 관리할 수 있는 발행 구조를 구축합니다.</p><span class="service-foot">Content Operation ↗</span></article><article class="agency-service"><span class="service-number">04 /</span><div class="service-icon">↗</div><h3>성과 확인·개선</h3><p>검색 색인, 노출, 유입 데이터를 점검하고 다음 콘텐츠의 우선순위를 조정합니다.</p><span class="service-foot">SEO Optimization ↗</span></article></div></div></section>"""
agency_process="""<section class="agency-section shell" id="process"><div class="agency-section-head"><div><span class="agency-section-label">02 — WORK PROCESS</span><h2>감이 아닌,<br>과정으로 만드는 콘텐츠.</h2></div><p>업종과 목적을 이해하는 것부터 출발해<br>발행 이후의 점검까지 이어갑니다.</p></div><div class="agency-process-grid"><div><span>STEP 01</span><strong>브랜드·업종 이해</strong><p>서비스와 타깃 고객을 살펴보고 콘텐츠 방향을 정합니다.</p></div><div><span>STEP 02</span><strong>키워드 및 주제 설계</strong><p>고객이 실제로 찾는 질문과 정보 주제를 정리합니다.</p></div><div><span>STEP 03</span><strong>원고 제작과 검토</strong><p>읽기 쉬운 구성으로 집필하고 사실관계를 확인합니다.</p></div><div><span>STEP 04</span><strong>발행·SEO 점검</strong><p>페이지 구성과 색인 상태를 확인하고 개선 방향을 찾습니다.</p></div></div></section>"""
agency_industries='<section class="agency-section agency-section-cream" id="industries"><div class="shell"><div class="agency-section-head"><div><span class="agency-section-label">03 — INDUSTRIES</span><h2>다양한 분야,<br>각기 다른 검색의 언어.</h2></div><p>병원·법률·이사·인테리어를 비롯해<br>업종별 정보와 주제를 폭넓게 다룹니다.</p></div><div class="agency-industries-grid">'+industry_tiles+'</div></div></section>'
agency_blog='<section class="agency-section shell" id="insights"><div class="agency-section-head"><div><span class="agency-section-label">04 — CONTENT LIBRARY</span><h2>정보세상의<br>콘텐츠를 만나보세요.</h2></div><a class="agency-text-link" href="/blog/">전체 콘텐츠 보러가기 <span>↗</span></a></div><div class="blog-cards agency-blog-grid">'+featured_cards+'</div></section>'
agency_contact="""<section class="agency-contact-band" id="inquiry"><div class="shell agency-contact-layout"><div><span class="agency-section-label">05 — LET'S TALK</span><h2>우리 브랜드에 맞는<br>콘텐츠가 필요하신가요?</h2><p>업종과 목표, 필요한 콘텐츠를 정리해 주시면<br>어떤 방식으로 접근할지 함께 검토할 수 있습니다.</p></div><a class="agency-button agency-button-white" href="/contact/">광고·제작 문의하기 <span>↗</span></a></div></section>"""
agency_home=agency_hero+agency_intro+agency_services+agency_process+agency_industries+agency_blog+agency_contact
save('/',frame('정보세상 | 자체 콘텐츠 제작·SEO·콘텐츠 마케팅', '정보세상은 업종별 자체 콘텐츠 제작, 지역 키워드 기획, SEO 검색 최적화 및 콘텐츠 운영을 소개합니다. 브랜드에 맞는 콘텐츠 전략을 확인하세요.','/',agency_home))
# Static contact landing: no fabricated contact details or unconfigured inbound form.
contact_email=os.environ.get('CONTACT_EMAIL','').strip()
if contact_email and re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',contact_email):
    inquiry_action='<a class="agency-button" href="mailto:'+quote(contact_email,safe='@.')+'?subject='+quote('정보세상 콘텐츠 제작 문의')+'">이메일로 문의하기 <span>↗</span></a><p class="contact-secondary">문의 이메일: '+esc(contact_email)+'</p>'
else:
    inquiry_action='<div class="contact-pending"><strong>문의 채널 준비 중입니다.</strong><p>실제 문의를 받으려면 운영 이메일 주소를 설정해야 합니다. 메일 주소가 준비되기 전에는 이 페이지에서 문의를 접수하지 않습니다.</p></div>'
contact_body='<section class="agency-contact-page"><div class="shell"><span class="agency-section-label">CONTACT / INFORMATION WORLD</span><h1>당신의 브랜드를 위한<br><em>콘텐츠의 다음 단계.</em></h1><p class="contact-lead">업종·서비스·목표 키워드를 공유해 주시면 맞는 콘텐츠 방향을 검토할 수 있습니다.</p><div class="contact-columns"><div class="contact-detail"><h2>이런 내용을 준비해 주세요.</h2><p>01. 업종 및 서비스 소개</p><p>02. 홍보가 필요한 지역·키워드</p><p>03. 원하는 원고 유형과 콘텐츠 수량</p><p>04. 희망 일정 및 전달 사항</p></div><div class="contact-detail"><h2>문의 방법</h2>'+inquiry_action+'</div></div><p class="contact-caution">콘텐츠 발행이나 검색 노출이 특정 검색순위 또는 성과를 보장하지는 않습니다. 의료·법률 분야는 관련 법령과 전문 검토가 필요합니다.</p></div></section>'
save('/contact/',frame('광고·콘텐츠 제작 문의 | 정보세상','자체 콘텐츠 제작과 SEO 콘텐츠 운영 관련 문의 안내','/contact/',contact_body))
(OUT/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+DOMAIN+'/sitemap.xml\n',encoding='utf8')
now=datetime.date.today().isoformat()
# Generate a fresh sitemap on every deployment. Only public, indexing-approved posts are listed.
sitemap_entries=[('/',None),('/contact/',None),('/blog/',None)]
for x in posts:
    if x.get('seo_approved',False) is True:
        sitemap_entries.append(('/blog/'+x['slug']+'/',str(x.get('date',''))[:10]))
sitemap_xml='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for p,modified in sitemap_entries:
    loc=esc(DOMAIN+quote(p,safe='/'))
    valid_date=bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}',modified or ''))
    sitemap_xml+='<url><loc>'+loc+'</loc>'+('<lastmod>'+modified+'</lastmod>' if valid_date else '')+'</url>\n'
sitemap_xml+='</urlset>'
(OUT/'sitemap.xml').write_text(sitemap_xml,encoding='utf8')
print('Built',len(published)+len(posts)+2,'pages ->',OUT)
