# 정보세상: 구글시트 원고 → 관리자 임시저장

연결 대상: https://docs.google.com/spreadsheets/d/1aPtwkQoMtnkg4HYYy--gpW0bndD2FHu2CFRKCsroNco/edit?gid=1562949546

## 읽는 컬럼
- 대상 탭: gid `1562949546` (상세페이지문안)
- 10행부터 탐색, B열 핵심 키워드, C열 생성된 전체 원고, D열 작성 완료 여부
- C열 텍스트: 첫 줄 제목, 그 다음 핵심키워드, URL, 본문
- URL 안내 줄은 버리고 B열 키워드로 슬러그 생성
- D열이 `완료`로 시작하고 원고가 충분히 길 때만 전송
- 완료된 원고는 공개 게시글(`status=published`, `seo_approved=true`)로 생성

## 한 번만 설정
1. Cloudflare Workers 및 Pages에서 **info-world-admin (Worker)** → 설정 → 변수 및 비밀 → **비밀** 유형 `SHEET_IMPORT_KEY` 생성.
   - 본인이 임의 생성한 32자 이상의 랜덤 영문/숫자 비밀키 사용. 공개하지 마세요.
   - 기존 `ADMIN_PASSWORD`, `GITHUB_TOKEN` 은 그대로 유지.
2. 구글시트에서 **확장 프로그램 → Apps Script**로 이동.
3. 저장소의 `admin-worker/google-sheets-sync.gs` 코드를 복사하여 Apps Script 편집기에 붙여넣고 저장.
4. Apps Script 왼쪽 **프로젝트 설정(톱니바퀴) → 스크립트 속성**에 이름 `SHEET_IMPORT_KEY` 값으로 Cloudflare와 **동일한** 비밀키 등록.
5. 함수 선택에서 `syncSheetDrafts`를 한 번 **실행**하고 Google 권한 요청을 승인.
6. 실행 로그에서 `{"created":...,"exists":...,"skipped":...,"failed":...}` 결과 확인. 관리자에 글이 생겼는지 확인.
7. 검증 후 함수 `installDraftSyncTrigger`를 한 번 실행하면 5분마다 동기화.
8. 자동 동기화를 중단하려면 `stopDraftSyncTrigger` 실행.

## 안전 장치와 제한
- **같은 키워드라도 다른 작성 작업이면 새 URL로 등록**됩니다. 작업마다 고유 ID를 부여하므로 기존 글을 덮어쓰지 않습니다.\n- 같은 작업의 자동 재시도는 중복 저장하지 않습니다. 기존 10행을 지우고 다시 쓰면 새 작업으로 등록합니다.\n- `installDraftSyncTrigger()` 실행 시 5분 동기화와 B/C열 수동 편집 감지 트리거를 함께 설치합니다. Apps Script 코드 변경 후 반드시 다시 실행하세요.\n- 생성 프로그램이 구글시트 값을 자동으로 지웠다가 같은 내용으로 다시 넣는 경우, Apps Script onEdit 트리거는 자동 프로그램 수정에 반응하지 않습니다. 이때는 원본 자동화에서 작업 ID를 전달하거나 `resetDraftImportRows()` (원본 탭에서 해당 행을 선택한 뒤 실행)를 실행해야 같은 텍스트의 재작성까지 인식할 수 있습니다.
- 기존 글은 수정/삭제하지 않고 새 원고만 생성합니다. 완료된 새 글은 공개되며 Cloudflare Pages 배포 성공 후 홈페이지에 나타납니다.
- Apps Script는 자체 Script Properties로 성공한 행의 텍스트 지문을 보관하며 원본 시트는 수정하지 않음.
- 실패한 행은 다음 실행 시 재시도함. 편집 중인 원고는 D열이 `완료`가 되기 전까지 건너뜀.
- 모든 자동화에는 Apps Script/Cloudflare/GitHub 사용량 제한이 적용됨. 시간당 및 월간 배포 횟수를 확인하세요.
- API 주소가 변경되면 Apps Script의 `INFO_WORLD.API`도 변경해야 함.
