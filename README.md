# SKINMAP — 지역×시술 SEO 스타터

## 실행
Python 3만 필요하며 외부 패키지 설치가 필요하지 않습니다.

```bash
python scripts/build.py
python -m http.server 8000 --directory dist
```
브라우저에서 http://localhost:8000 접속

## 페이지 관리
- `data/pages.csv`: `region`(지역) / `procedure`(지역×시술) 행을 추가합니다.
- `status=published`: 사이트에 페이지를 생성합니다. 다만 초안은 검색 노출되지 않도록 **noindex 처리**됩니다.
- **중요:** `scripts/build.py`의 `frame(..., index=False)` 부분은 실제 전문가 감수, 고유 지역 정보/출처 추가 및 의료광고 검토 후 특정 페이지에 한해 `index=True`로 바꾸세요.
- 사이트맵은 안전상 검토 완료 전 메인페이지만 포함합니다. 페이지를 공개할 때 `sitemap.xml`에도 검토 완료 페이지만 추가하도록 빌드 코드를 확장하세요.
- `SITE_URL` 환경변수로 실제 도메인을 지정합니다. 기본값 example.pages.dev는 반드시 변경해야 합니다.

## Cloudflare Pages 무료 배포
1. GitHub에 이 폴더를 새 저장소로 업로드합니다.
2. Cloudflare > Workers & Pages > Create application > Pages > Import Git repository.
3. Framework preset: None, Build command: `python3 scripts/build.py`, Build output directory: `dist`.
4. Environment variables: `SITE_URL=https://<본인-프로젝트>.pages.dev` 등록 후 배포합니다.
5. robots.txt와 sitemap.xml을 확인하고 Search Console 등록.

## SEO 및 규정 체크
- 유사한 지역명만 치환한 대량 페이지는 검색 스팸/도어웨이 페이지 문제가 생길 수 있습니다.
- 지역별 교통편·실제 서비스 범위·검증된 시술정보·출처·게시일·감수자를 보강하세요.
- 의료정보·의료광고 규정을 검토하세요. 광고/제휴 관계도 표시하세요.
- 현재 샘플 지역 페이지는 검색 색인 `noindex` 상태입니다.
- URL 중복, title·description 고유성, 내부 링크, 모바일 접근성 등을 확인하세요.
