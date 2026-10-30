import csv, html, pathlib, datetime, os, shutil, hashlib, base64
from email.utils import format_datetime
from urllib.parse import quote
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'dist'
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir()
(OUT/'assets').mkdir()
# Public advertising-inquiry favicon derived from the approved design.
(OUT/'favicon.png').write_bytes(base64.b64decode('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'))
shutil.copy2(ROOT/'assets'/'style.css',OUT/'assets'/'style.css')
shutil.copy2(ROOT/'assets'/'analytics.js',OUT/'assets'/'analytics.js')
shutil.copytree(ROOT/'admin', OUT/'admin', dirs_exist_ok=True)
if (ROOT/'assets'/'uploads').exists(): shutil.copytree(ROOT/'assets'/'uploads',OUT/'assets'/'uploads',dirs_exist_ok=True)
DOMAIN=os.environ.get('SITE_URL','https://skin-map.pages.dev').rstrip('/')
with open(ROOT/'data'/'pages.csv',encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
def esc(s):return html.escape(str(s or ''),quote=True)
def url(row):return '/region/'+row['region_slug']+'/'+(row['procedure_slug']+'/' if row['type']=='procedure' else '')
def link(row):return '<a class="tile" href="'+url(row)+'"><span class="eyebrow">'+('시술 가이드' if row['type']=='procedure' else '지역 가이드')+'</span><strong>'+esc(row['region']+row['procedure'] if row['type']=='procedure' else row['region']+'피부과')+'</strong><small>가이드 보기 ↗</small></a>'
# Blog-only floating inquiry shortcuts. A valid phone number activates the call button.
KAKAO_CHAT_URL='https://open.kakao.com/o/scHdSpTi'
CONTACT_PHONE=''.join(ch for ch in os.environ.get('CONTACT_PHONE','01082536028') if ch.isdigit() or ch=='+')
def blog_floating_contact(path):
 if not path.startswith('/blog/'): return ''
 kakao='<a class="float-contact-item float-contact-kakao" href="'+KAKAO_CHAT_URL+'" target="_blank" rel="noopener noreferrer" aria-label="카카오톡 오픈채팅으로 광고 상담하기"><span class="float-contact-symbol" aria-hidden="true">TALK</span><span>카톡상담</span></a>'
 phone=('<a class="float-contact-item float-contact-phone" href="tel:'+CONTACT_PHONE+'" aria-label="전화상담 연결"><svg viewBox="0 0 24 24" aria-hidden="true" width="23" height="23" fill="currentColor"><path d="M6.62 10.79a15.05 15.05 0 006.59 6.59l2.2-2.2a1 1 0 011.01-.24 11.36 11.36 0 003.58.57 1 1 0 011 1V20a1 1 0 01-1 1C10.61 21 3 13.39 3 4a1 1 0 011-1h3.5a1 1 0 011 1c0 1.25.2 2.45.57 3.58a1 1 0 01-.25 1.01z"/></svg><span>전화상담</span></a>' if len(CONTACT_PHONE)>=9 else '')
 return '<aside class="floating-contact" aria-label="광고 상담 바로가기">'+kakao+phone+'</aside>'
def frame(title,desc,path,body,index=True,image=None):
 canonical=DOMAIN+path
 image_src=(str(image or "").strip())
 if image_src.startswith("/"):image_src=DOMAIN+image_src
 image_meta=('<meta property="og:image" content="'+esc(image_src)+'"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="'+esc(image_src)+'">') if image_src.startswith("https://") else ""
 robots='index,follow' if index else 'noindex,follow'
 return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="google-site-verification" content="n90ax_Rr4TxN5s1JgLTOYITAbJftYgZmlzP-vPiJCW4"><meta name="naver-site-verification" content="097949900434cde74cee16d2cabf5519a973384e"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="{robots}"><link rel="icon" type="image/png" sizes="64x64" href="/favicon.png"><link rel="shortcut icon" href="/favicon.png"><link rel="apple-touch-icon" href="/favicon.png"><link rel="canonical" href="{esc(canonical)}"><meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(canonical)}">{image_meta}<link rel="stylesheet" href="/assets/style.css"><script async src="https://www.googletagmanager.com/gtag/js?id=G-ER6KYZHWK6"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag("js",new Date());gtag("config","G-ER6KYZHWK6");</script><script defer src="/assets/analytics.js"></script><script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebSite","name":"정보세상","url":"{esc(DOMAIN)}/"}}</script></head><body><header class="site-header"><div class="shell nav"><a class="wordmark" href="/">정보<span>세상</span><i>.</i></a><nav aria-label="주요 메뉴"><a href="/about/">회사 소개</a><a href="/#services">서비스</a><a href="/#industries">전문 분야</a><a href="/blog/">콘텐츠</a><a href="https://info-world-admin.hwsr6028.workers.dev/" target="_blank" rel="noopener noreferrer" aria-label="관리자 로그인 새 창 열기">관리자 ↗</a><a class="nav-contact" href="/contact/">광고 문의 ↗</a></nav></div></header><main>{body}</main><footer id="about"><div class="shell foot"><div><b>정보세상</b><p>업종과 검색 의도를 연결하는 콘텐츠 제작·SEO 광고 스튜디오입니다.<br>기획부터 원고 제작과 운영까지 콘텐츠 중심의 솔루션을 안내합니다.</p></div><div><span>© {datetime.date.today().year} 정보세상</span><p>콘텐츠의 검색 노출 및 성과는 보장되지 않습니다.<br>의료·법률·금융 정보는 해당 전문가 검토가 필요합니다.</p></div></div></footer>{blog_floating_contact(path)}</body></html>'''
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
            obj['_source_file']=f.name
            raw_post=f.read_bytes()
            obj['_source_sha']=hashlib.sha1(b'blob '+str(len(raw_post)).encode('ascii')+b'\0'+raw_post).hexdigest()
            posts.append(obj)
    except Exception as e:
        print('Skipped post',f.name,':',e)
# Remove generator-only URL identifiers mistakenly included in SEO snippets.
# A prefix is removed only when it looks like a machine slug (at least 2 hyphens).
def strip_generator_prefix(value):
    value=str(value or '').lstrip()
    # Remove a leading internal ASCII slug and optional annotation only.
    pattern=r'^[a-z0-9]+(?:-[a-z0-9]+){2,}(?:[ \t]*\(※[^\n)]*\))?[ \t]*'
    value=re.sub(pattern,'',value,count=1)
    return value.lstrip(' \t\r\n')
for post in posts:
    post['description']=strip_generator_prefix(post.get('description',''))
    post['body']=strip_generator_prefix(post.get('body',''))

# Featured blog cards and static category / pagination pages
from urllib.parse import unquote
CATEGORIES={'health':'병원·건강','law':'법률','interior':'인테리어','moving':'이사·생활','realestate':'부동산','finance':'금융·경제','tech':'IT·디지털','education':'교육·취업','travel':'여행·취미','general':'비즈니스·기타','fortune':'점집','tattoo':'타투','shopping':'구매대행','supplements':'건강식품'}
PAGE_SIZE=9
# Match the worker/admin's canonical category rules for existing Sheets posts.
# Keep explicitly selected non-general categories; infer legacy 'general' rows
# from the keyword/title so the public site and admin display agree.
CATEGORY_PATTERNS=[
 ('fortune',r'점집|사주|운세|타로|신점|철학관|무속'),
 ('tattoo',r'타투|문신|반영구|타투이스트|레터링타투'),
 ('shopping',r'구매대행|해외직구|배송대행|수입대행|직구대행'),
 ('supplements',r'건강식품|건강기능식품|영양제|비타민|유산균|프로바이오틱스'),
 ('moving',r'이사|포장이사|이삿짐|용달|입주청소|청소업체|폐기물|생활서비스'),
 ('education',r'학원|과외|수학|영어교육|초등|중등|고등|입시|교육|유학|취업|자격증'),
 ('law',r'법률|변호사|법무사|소송|계약분쟁|이혼|형사|민사|상속|개인회생'),
 ('interior',r'인테리어|리모델링|도배|장판|욕실|주방공사|싱크대|타일'),
 ('realestate',r'부동산|전세|월세|아파트|분양|매매|공인중개'),
 ('finance',r'금융|경제|보험|대출|세금|주식|투자|절세'),
 ('tech',r'IT|디지털|스마트폰|컴퓨터|노트북|앱|소프트웨어|AI|인공지능'),
 ('travel',r'여행|관광|캠핑|호텔|항공|숙박'),
 ('health',r'병원|건강|피부과|성형|치과|의원|의료|시술|한의원|리프팅|스킨부스터'),
]
def category_of(post):
    value=str(post.get('category') or '').strip()
    legacy={'dermatology':'health','lifting':'health','skinbooster':'health','other':'general'}
    value=legacy.get(value,value)
    if value in CATEGORIES and value!='general':
        return value
    subject=str(post.get('keyword') or '')+' '+str(post.get('title') or '')+' '+str(post.get('procedure') or '')
    for category,pattern in CATEGORY_PATTERNS:
        if re.search(pattern,subject,re.IGNORECASE):
            return category
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
 'general':('#eef3ef','#375e4c','#cadfd0','INFORMATION'),
 'fortune':('#f1eafa','#674c84','#dac8f1','FORTUNE'),
 'tattoo':('#edf0f3','#414f5d','#c9d1d9','TATTOO'),
 'shopping':('#f7efe8','#806044','#e7cdb2','GLOBAL SHOPPING'),
 'supplements':('#e8f4ed','#376e50','#bee1ca','WELLNESS')
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

DEFAULT_INQUIRY_BANNER='/assets/uploads/default-inquiry-banner.svg'
def card_image(post):
    # An explicitly uploaded thumbnail always overrides the shared inquiry banner.
    cover=image_url(post.get('thumbnail',''))
    if cover:return cover
    return DEFAULT_INQUIRY_BANNER
def blog_card(post):
    img=card_image(post)
    pic=('<span class="blog-card-media"><img loading="lazy" decoding="async" src="'+esc(img)+'" alt="'+esc(post.get('title',''))+'"></span>' if img else '<span class="blog-card-media blog-card-placeholder"><span>정보세상</span></span>')
    path='/blog/'+esc(post['slug'])+'/'
    cat=CATEGORIES[category_of(post)]
    date=str(post.get('date',''))[:10]
    return '<a class="blog-card" href="'+path+'">'+pic+'<span class="blog-card-copy"><span class="blog-card-meta">'+esc(cat)+' · '+esc(date)+'</span><strong>'+esc(post.get('title',''))+'</strong><span class="blog-card-description">'+esc(post.get('description',''))+'</span><span class="blog-card-more">글 읽기 ↗</span></span></a>'
posts.sort(key=lambda x:(str(x.get('updated_at') or x.get('imported_at') or x.get('created_at') or x.get('date') or ''),str(x.get('date','')),str(x.get('title',''))),reverse=True)
# Articles without a custom thumbnail use the same branded inquiry banner.
for article in posts:
    path='/blog/'+article['slug']+'/'
    title=article.get('title','')
    desc=article.get('description','')
    page='<section class="article-top"><div class="shell"><div class="crumb"><a href="/">홈</a> / <a href="/blog/">블로그</a></div><span class="kicker">'+esc(CATEGORIES[category_of(article)])+'</span><h1>'+esc(title)+'</h1><p>'+esc(desc)+'</p></div></section>'
    cover=card_image(article)
    cover_html='<figure class="article-cover"><img src="'+esc(cover)+'" alt="'+esc(title)+' 대표 이미지" width="1200" height="675" decoding="async"></figure>' if cover else ''
    # Article-level HTML links expose additional pages to search crawlers.
    related=[p for p in posts if p['slug']!=article['slug'] and category_of(p)==category_of(article)]
    related.sort(key=lambda p:str(p.get('imported_at') or p.get('updated_at') or p.get('date') or ''),reverse=True)
    related_html=('<nav class="related-articles" aria-label="관련 정보"><h2>같은 분야의 다른 글</h2><ul>'+''.join('<li><a href="/blog/'+quote(p['slug'],safe='-')+'/">'+esc(p.get('title',''))+'</a></li>' for p in related[:4])+'</ul></nav>') if related else ''
    page+='<section class="shell article-grid"><article class="article">'+cover_html+markdown_to_html(article.get('body',''))+related_html+'<div class="disclaimer">본 콘텐츠는 일반적인 정보 제공 목적이며 개인별 상황에 맞는 전문 상담을 대신하지 않습니다.</div></article></section>'
    save(path,frame(title,desc,path,page,index=bool(article.get('seo_approved',False)),image=cover))
# Public metadata index used by the admin to avoid hundreds of individual
# GitHub Content API requests. No private content or credentials are included.
manifest=[]
for post in posts:
    manifest.append({
        'file':post['_source_file'],
        'sha':post['_source_sha'],
        'title':str(post.get('title') or post['_source_file']),
        'category':category_of(post),
        'status':'published',
        'date':str(post.get('date') or '')[:10],
        'latestAt':str(post.get('updated_at') or post.get('imported_at') or post.get('created_at') or post.get('date') or ''),
        'sourceRow':int(str(post.get('source_row') or '0')) if str(post.get('source_row') or '0').isdigit() else 0,
    })
(OUT/'posts-manifest.json').write_text(json.dumps({'posts':manifest},ensure_ascii=False,separators=(',',':')),encoding='utf-8')

def listing_path(category,num):
    root='/blog/' if not category else '/blog/category/'+category+'/'
    return root if num==1 else root+'page/'+str(num)+'/'
def category_nav(active):
    all_count=len(posts)
    links=[('<a class="'+('active' if not active else '')+'" href="/blog/">전체 <span>'+str(all_count)+'</span></a>')]
    for key,label in CATEGORIES.items():
        count=sum(category_of(p)==key for p in posts)
        if True:
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
 ('fortune','점집','운세·사주','11'),
 ('tattoo','타투','타투·아트','12'),
 ('shopping','구매대행','해외 구매 서비스','13'),
 ('supplements','건강식품','건강식품·영양','14'),
]
industry_tiles=''.join('<a class="agency-industry" href="/blog/category/'+key+'/"><span class="agency-industry-number">'+number+'</span><strong>'+esc(short)+'</strong><span class="agency-industry-arrow">↗</span></a>' for key,short,detail,number in category_info)
agency_hero="""<section class="agency-hero"><div class="shell agency-hero-grid"><div class="agency-hero-copy"><span class="agency-kicker"><span class="agency-dot"></span> CONTENT MARKETING STUDIO · 정보세상</span><h1>검색에서 발견되고,<br><em>콘텐츠로 설득되는</em><br>브랜드를 만듭니다.</h1><p>키워드 전략부터 업종별 전문 원고, 자체 콘텐츠 발행과 SEO 운영까지.<br>브랜드의 이야기가 필요한 고객에게 닿도록 설계합니다.</p><div class="agency-hero-actions"><a class="agency-button" href="https://open.kakao.com/o/scHdSpTi" target="_blank" rel="noopener noreferrer">카카오톡 광고 문의 <span>↗</span></a><a class="agency-text-link" href="#services">서비스 알아보기 <span>↘</span></a></div><div class="agency-hero-small"><span>STRATEGY</span><span>CONTENT</span><span>SEO</span><span>GROWTH</span></div></div><div class="agency-visual" aria-label="콘텐츠 전략 프로세스 그래픽"><div class="visual-orbit orbit-a"></div><div class="visual-orbit orbit-b"></div><div class="agency-visual-head">INFORMATION<br>MEETS<br><span>IMPACT.</span></div><div class="visual-plate plate-top"><span>01 / RESEARCH</span><strong>Keyword Insight</strong><small>검색 의도 분석</small></div><div class="visual-plate plate-middle"><span>02 / CONTENT</span><strong>Editorial Strategy</strong><small>콘텐츠 기획·제작</small></div><div class="visual-plate plate-bottom"><span>03 / OPTIMIZE</span><strong>SEO &amp; Publishing</strong><small>발행 및 개선</small></div><div class="visual-decoration">✳</div></div></div></section>"""
agency_intro="""<section class="agency-intro shell"><div class="agency-intro-mark">WHAT WE DO <span>↘</span></div><p>좋은 광고는 단순한 노출로 끝나지 않습니다.<br><strong>검색 의도에 맞는 정보</strong>가 신뢰를 만들고,<br>신뢰는 다음 행동으로 이어질 수 있습니다.</p></section>"""
agency_services="""<section class="agency-section agency-section-dark" id="services"><div class="shell"><div class="agency-section-head"><div><span class="agency-section-label">01 — SERVICES</span><h2>콘텐츠의 시작부터<br>운영까지, 하나의 흐름으로.</h2></div><p>목표와 업종에 맞는 키워드 구조를 세우고,<br>실질적인 정보를 담은 콘텐츠를 기획합니다.</p></div><div class="agency-services-grid"><article class="agency-service"><span class="service-number">01 /</span><div class="service-icon">⌕</div><h3>키워드·SEO 전략</h3><p>지역, 업종, 서비스 키워드를 분석하고 검색 의도에 맞는 주제와 정보 구조를 설계합니다.</p><span class="service-foot">Keyword Research ↗</span></article><article class="agency-service"><span class="service-number">02 /</span><div class="service-icon">✎</div><h3>자체 콘텐츠 제작</h3><p>브랜드의 서비스와 전문성을 전달하는 정보성 원고, 블로그 콘텐츠, 상세페이지 카피를 제작합니다.</p><span class="service-foot">Content Production ↗</span></article><article class="agency-service"><span class="service-number">03 /</span><div class="service-icon">▧</div><h3>콘텐츠 발행·운영</h3><p>카테고리와 주제에 따라 콘텐츠를 정리하고, 지속적으로 관리할 수 있는 발행 구조를 구축합니다.</p><span class="service-foot">Content Operation ↗</span></article><article class="agency-service"><span class="service-number">04 /</span><div class="service-icon">↗</div><h3>성과 확인·개선</h3><p>검색 색인, 노출, 유입 데이터를 점검하고 다음 콘텐츠의 우선순위를 조정합니다.</p><span class="service-foot">SEO Optimization ↗</span></article></div></div></section>"""
agency_process="""<section class="agency-section shell" id="process"><div class="agency-section-head"><div><span class="agency-section-label">02 — WORK PROCESS</span><h2>감이 아닌,<br>과정으로 만드는 콘텐츠.</h2></div><p>업종과 목적을 이해하는 것부터 출발해<br>발행 이후의 점검까지 이어갑니다.</p></div><div class="agency-process-grid"><div><span>STEP 01</span><strong>브랜드·업종 이해</strong><p>서비스와 타깃 고객을 살펴보고 콘텐츠 방향을 정합니다.</p></div><div><span>STEP 02</span><strong>키워드 및 주제 설계</strong><p>고객이 실제로 찾는 질문과 정보 주제를 정리합니다.</p></div><div><span>STEP 03</span><strong>원고 제작과 검토</strong><p>읽기 쉬운 구성으로 집필하고 사실관계를 확인합니다.</p></div><div><span>STEP 04</span><strong>발행·SEO 점검</strong><p>페이지 구성과 색인 상태를 확인하고 개선 방향을 찾습니다.</p></div></div></section>"""
agency_industries='<section class="agency-section agency-section-cream" id="industries"><div class="shell"><div class="agency-section-head"><div><span class="agency-section-label">03 — INDUSTRIES</span><h2>다양한 분야,<br>각기 다른 검색의 언어.</h2></div><p>병원·법률·이사·인테리어를 비롯해<br>업종별 정보와 주제를 폭넓게 다룹니다.</p></div><div class="agency-industries-grid">'+industry_tiles+'</div></div></section>'
agency_blog='<section class="agency-section shell" id="insights"><div class="agency-section-head"><div><span class="agency-section-label">04 — CONTENT LIBRARY</span><h2>정보세상의<br>콘텐츠를 만나보세요.</h2></div><a class="agency-text-link" href="/blog/">전체 콘텐츠 보러가기 <span>↗</span></a></div><div class="blog-cards agency-blog-grid">'+featured_cards+'</div></section>'
agency_contact="""<section class="agency-contact-band" id="inquiry"><div class="shell agency-contact-layout"><div><span class="agency-section-label">05 — LET'S TALK</span><h2>우리 브랜드에 맞는<br>콘텐츠가 필요하신가요?</h2><p>업종과 목표, 필요한 콘텐츠를 정리해 주시면<br>어떤 방식으로 접근할지 함께 검토할 수 있습니다.</p></div><a class="agency-button agency-button-white" href="https://open.kakao.com/o/scHdSpTi" target="_blank" rel="noopener noreferrer">카카오톡 광고 문의 <span>↗</span></a></div></section>"""
agency_home=agency_hero+agency_intro+agency_services+agency_process+agency_industries+agency_blog+agency_contact
save('/',frame('정보세상 | 자체 콘텐츠 제작·SEO·콘텐츠 마케팅', '정보세상은 업종별 자체 콘텐츠 제작, 지역 키워드 기획, SEO 검색 최적화 및 콘텐츠 운영을 소개합니다. 브랜드에 맞는 콘텐츠 전략을 확인하세요.','/',agency_home))
# Static contact landing: no fabricated contact details or unconfigured inbound form.
# Advertiser inquiries go to the owner's KakaoTalk Open Chat (not a Kakao Channel).
KAKAO_INQUIRY_URL='https://open.kakao.com/o/scHdSpTi'
inquiry_action='<a class="agency-button" href="'+KAKAO_INQUIRY_URL+'" target="_blank" rel="noopener noreferrer" aria-label="카카오톡 오픈채팅으로 광고 문의하기">카카오톡으로 광고 문의 <span>↗</span></a><p class="contact-secondary">버튼을 누르면 카카오톡 오픈채팅으로 이동합니다. 업종, 홍보할 키워드, 희망 일정 등을 남겨 주세요.</p>'
contact_body='<section class="agency-contact-page"><div class="shell"><span class="agency-section-label">CONTACT / INFORMATION WORLD</span><h1>당신의 브랜드를 위한<br><em>콘텐츠의 다음 단계.</em></h1><p class="contact-lead">업종·서비스·목표 키워드를 공유해 주시면 맞는 콘텐츠 방향을 검토할 수 있습니다.</p><div class="contact-columns"><div class="contact-detail"><h2>이런 내용을 준비해 주세요.</h2><p>01. 업종 및 서비스 소개</p><p>02. 홍보가 필요한 지역·키워드</p><p>03. 원하는 원고 유형과 콘텐츠 수량</p><p>04. 희망 일정 및 전달 사항</p></div><div class="contact-detail"><h2>문의 방법</h2>'+inquiry_action+'</div></div><p class="contact-caution">콘텐츠 발행이나 검색 노출이 특정 검색순위 또는 성과를 보장하지는 않습니다. 의료·법률 분야는 관련 법령과 전문 검토가 필요합니다.</p></div></section>'
save('/contact/',frame('광고·콘텐츠 제작 문의 | 정보세상','자체 콘텐츠 제작과 SEO 콘텐츠 운영 관련 문의 안내','/contact/',contact_body))

about_body='<section class="agency-about-top"><div class="shell"><span class="agency-section-label">ABOUT / INFORMATION WORLD</span><h1>브랜드의 전문성을<br><em>검색 가능한 콘텐츠로.</em></h1><p>정보세상은 업종별 콘텐츠 기획과 제작, 검색 최적화에 집중하는 콘텐츠 기반 웹 프로젝트입니다. 필요한 정보를 찾는 이용자와 서비스를 소개하는 브랜드 사이에 도움이 되는 연결을 고민합니다.</p></div></section><section class="agency-section shell"><div class="agency-section-head"><div><span class="agency-section-label">OUR APPROACH</span><h2>정보의 정확성과<br>읽는 경험을 함께 생각합니다.</h2></div><p>고객의 검색 의도를 출발점으로 잡고, 각 업종에 맞는 정보를 구조화합니다.</p></div><div class="agency-process-grid"><div><span>01 / STRATEGY</span><strong>검색 의도 우선</strong><p>키워드만 반복하지 않고 질문에 답하는 콘텐츠를 설계합니다.</p></div><div><span>02 / EDITORIAL</span><strong>가독성과 흐름</strong><p>정보를 이해하기 쉬운 제목과 소제목, 이미지 구성으로 정리합니다.</p></div><div><span>03 / REVIEW</span><strong>사실관계 확인</strong><p>전문 분야는 신뢰할 수 있는 자료와 전문가 검토가 중요합니다.</p></div><div><span>04 / OPERATIONS</span><strong>지속적인 개선</strong><p>발행 이후에도 정보의 최신성과 검색 상태를 살펴봅니다.</p></div></div></section><section class="agency-contact-band"><div class="shell agency-contact-layout"><div><span class="agency-section-label">LET’S CONNECT</span><h2>브랜드의 이야기를<br>콘텐츠로 정리해 보세요.</h2></div><a class="agency-button" href="https://open.kakao.com/o/scHdSpTi" target="_blank" rel="noopener noreferrer">카카오톡 광고 문의 ↗</a></div></section>'
save('/about/',frame('회사 소개 | 정보세상 콘텐츠 마케팅','정보세상의 콘텐츠 기획, 제작, SEO 운영 방식과 원칙을 소개합니다.','/about/',about_body))

# Preserve discoverability after admin keyword / URL edits (Cloudflare Pages 301).
redirects=[]
current_slugs={p['slug'] for p in posts}
for post in posts:
    for old in post.get('previous_slugs',[]):
        if not isinstance(old,str):continue
        if not re.fullmatch(r'[가-힣ㄱ-ㅎㅏ-ㅣa-z0-9]+(?:-[가-힣ㄱ-ㅎㅏ-ㅣa-z0-9]+)*',old):continue
        if old==post['slug'] or old in current_slugs:continue
        source='/blog/'+quote(old,safe='-')+'/'
        target='/blog/'+quote(post['slug'],safe='-')+'/'
        redirects.append((source,target))
if redirects:
    unique={}
    for src,dst in redirects:unique[src]=dst
    (OUT/'_redirects').write_text(''.join(src+' '+dst+' 301\n' for src,dst in unique.items()),encoding='utf8')

# IndexNow host verification file. Public verification keys are intentionally published.
(OUT/'d507d99d18a0029f9e6a7f92d608f0d7.txt').write_text('d507d99d18a0029f9e6a7f92d608f0d7',encoding='utf8')
(OUT/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+DOMAIN+'/sitemap.xml\n',encoding='utf8')
now=datetime.date.today().isoformat()
# Generate a fresh sitemap on every deployment. Only public, indexing-approved posts are listed.
sitemap_entries=[('/',None),('/about/',None),('/contact/',None),('/blog/',None)]
# Include all real category pages and automatically generated pagination pages.
# These are generated by render_listing(), so URLs stay in sync after every build.
for key in CATEGORIES:
    if any(category_of(post)==key for post in posts):
        sitemap_entries.append((listing_path(key,1),None))
for key in ('',*CATEGORIES.keys()):
    count=sum(category_of(p)==key for p in posts) if key else len(posts)
    total=max(1,(count+PAGE_SIZE-1)//PAGE_SIZE)
    for page_number in range(2,total+1):
        sitemap_entries.append((listing_path(key,page_number),None))
for x in posts:
    if x.get('seo_approved',False) is True:
        sitemap_entries.append(('/blog/'+x['slug']+'/',str(x.get('updated_at') or x.get('imported_at') or x.get('created_at') or x.get('date') or '')[:10]))
sitemap_xml='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for p,modified in sitemap_entries:
    loc=esc(DOMAIN+quote(p,safe='/'))
    valid_date=bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}',modified or ''))
    sitemap_xml+='<url><loc>'+loc+'</loc>'+('<lastmod>'+modified+'</lastmod>' if valid_date else '')+'</url>\n'
sitemap_xml+='</urlset>'
(OUT/'sitemap.xml').write_text(sitemap_xml,encoding='utf8')

# RSS 2.0 feed for Naver Search Advisor. Include only publicly available, indexable articles.
rss_items=[]
for post in sorted((p for p in posts if p.get('seo_approved') is True),key=lambda p:(str(p.get('updated_at') or p.get('imported_at') or p.get('created_at') or p.get('date') or ''),str(p.get('slug') or '')),reverse=True)[:50]:
    loc=DOMAIN+'/blog/'+quote(post['slug'],safe='-')+'/'
    title=esc(post.get('title') or post.get('keyword') or '정보세상 콘텐츠')
    description=esc(str(post.get('body') or post.get('description') or ''))
    date_raw=str(post.get('updated_at') or post.get('imported_at') or post.get('created_at') or post.get('date') or '').strip()
    try:
        moment=datetime.datetime.fromisoformat(date_raw.replace('Z','+00:00'))
        if moment.tzinfo is None:moment=moment.replace(tzinfo=datetime.timezone(datetime.timedelta(hours=9)))
    except (ValueError,TypeError):
        moment=datetime.datetime.now(datetime.timezone.utc)
    pub_date=format_datetime(moment)
    rss_items.append('<item><title>'+title+'</title><link>'+esc(loc)+'</link><guid isPermaLink="true">'+esc(loc)+'</guid><description>'+description+'</description><pubDate>'+pub_date+'</pubDate></item>')
rss_xml='<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
rss_xml+='<title>정보세상 블로그</title><link>'+esc(DOMAIN+'/blog/')+'</link><description>정보세상 최신 콘텐츠와 생활 정보</description><language>ko</language>'
rss_xml+=''.join(rss_items)+'</channel></rss>'
(OUT/'rss.xml').write_text(rss_xml,encoding='utf8')

print('Built',len(published)+len(posts)+2,'pages ->',OUT)
