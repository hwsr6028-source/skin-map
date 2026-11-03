from pathlib import Path
import re, struct, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
folder=root/'dist'/'assets'/'seo-covers'
files=list(folder.glob('*.png')) if folder.exists() else []
if not files: raise SystemExit('FAIL: 자동 PNG 파일을 찾을 수 없습니다')
for p in files:
    data=p.read_bytes()
    if data[:8]!=b'\x89PNG\r\n\x1a\n':raise SystemExit('FAIL: PNG가 아님 '+str(p))
    w,h=struct.unpack('>II',data[16:24])
    if w<600 or h<315:raise SystemExit(f'FAIL: 이미지 크기 부족 {p.name} {w}x{h}')
print(f'OK: 자동 PNG {len(files)}개, 유효한 PNG 헤더/크기 확인')
articles=list((root/'dist'/'blog').glob('*/index.html'))
missing=[]
for p in articles:
    html=p.read_text(encoding='utf-8')
    if 'class="article-cover"' not in html or '<meta property="og:image"' not in html:missing.append(str(p))
if missing:raise SystemExit('FAIL: 대표 이미지 또는 og:image 없는 문서: '+', '.join(missing[:5]))
print(f'OK: 블로그 HTML {len(articles)}개 대표 이미지/OG 메타 확인')
