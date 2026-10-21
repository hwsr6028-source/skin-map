# 정보세상 관리자 (Cloudflare Workers)

기존 skin-map.pages.dev 홈페이지/글/SEO를 유지하며 **별도 ID/PW 관리자**를 운영합니다.

## 1. 배포
Cloudflare Workers & Pages → Create application → Continue with GitHub에서 **hwsr6028-source/skin-map** 저장소를 선택합니다. 기존 skin-map Pages가 아니라 새 Worker를 만듭니다.

- Worker 이름: `info-world-admin`
- 프로젝트 루트: `admin-worker`
- Build command: `npm install`
- Deploy command: `npm run deploy` (Cloudflare가 Wrangler를 실행한다면 `npx wrangler deploy`)
- Wrangler 파일: `admin-worker/wrangler.jsonc` (루트를 `admin-worker`로 설정한 경우 `wrangler.jsonc`)
- Production workers.dev URL을 활성화하세요.

기존 **sveltia-cms-auth** Worker와는 별개의 서비스입니다. 기존 OAuth CMS는 삭제하지 마세요.

## 2. 비밀번호와 GitHub 저장 권한
새 Worker → Settings → Variables and Secrets에서 **Production** 환경에 다음을 등록합니다.

- `ADMIN_USERNAME`: 일반 텍스트. 기본값 `admin`, 원하는 관리자 아이디로 변경 가능
- `ADMIN_PASSWORD`: Secret. 직접 정한 강력한 비밀번호(16자 이상 권장)
- `GITHUB_TOKEN`: Secret. GitHub fine-grained PAT, **hwsr6028-source/skin-map** 저장소만 선택하고 **Contents: Read and write** 권한만 부여
- `GITHUB_REPO`: 일반 텍스트. `hwsr6028-source/skin-map` (설정 파일에도 기본값 존재)
- `GITHUB_BRANCH`: 일반 텍스트. `main` (설정 파일에도 기본값 존재)

비밀번호·토큰은 절대 GitHub 소스코드나 채팅으로 보내지 마세요. Worker의 Secret 항목에만 입력하세요. 변수 추가 후 Worker를 재배포합니다.

## 3. 로그인
Worker 배포 URL을 북마크하세요. 관리자 아이디·비밀번호를 입력하면 세션 쿠키(브라우저 세션, 8시간 서버 만료)가 생성됩니다. 브라우저 종료 시 쿠키가 없어지는 것이 일반적이지만 Chrome의 '이전 세션 복원' 설정에서는 세션 쿠키가 복원될 수 있습니다. 반드시 **로그아웃**으로 세션을 종료하세요.

관리자는 기존 `content/posts/*.json` 형식을 사용합니다. 글 저장 → GitHub 커밋 → 기존 Cloudflare Pages 자동 재배포. 기존 글 URL·사이트맵·SEO 로직은 변경하지 않습니다.

## 4. 운영·보안
- 비밀번호 16자 이상, 유출되지 않은 별도 비밀번호 사용
- Cloudflare WAF/Rate Limiting에서 `/api/login` 요청 제한을 추가하세요 (코드에도 best-effort 제한 포함)
- Worker 주소는 공개 URL입니다. 비밀로 취급하지 마세요.
- 현재는 단일 관리자 계정만 지원합니다.
- Cloudflare Pages의 기존 `/admin/` OAuth CMS는 **별도 경로**로 남습니다. 새 로그인으로 완전히 교체·차단하려면 추가적인 라우팅/액세스 설계가 필요합니다.
- GitHub 토큰이 만료되면 글 저장이 실패하므로 다시 발급해야 합니다.
