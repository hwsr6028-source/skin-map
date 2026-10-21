# 정보세상: 구글시트 원고 → 관리자 임시저장

연결 대상: https://docs.google.com/spreadsheets/d/1aPtwkQoMtnkg4HYYy--gpW0bndD2FHu2CFRKCsroNco/edit?gid=1562949546

## 읽는 컬럼
- 대상 탭: gid `1562949546` (상세페이지문안)
- 10행부터 탐색, B열 핵심 키워드, C열 생성된 전체 원고, D열 작성 완료 여부
- C열 텍스트: 첫 줄 제목, 그 다음 핵심키워드, URL, 본문
- URL 안내 줄은 버리고 B열 키워드로 슬러그 생성
- D열이 `완료`로 시작하고 원고가 충분히 길 때만 전송
- 웹사이트에는 공개하지 않음(`status=draft`, `seo_approved=false`)

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
- 관리자 GitHub 저장소에 **같은 키워드 파일이 이미 존재하면 절대로 덮어쓰지 않음**. 삭제한 행을 다시 동기화하고 싶다면 스크립트 속성의 해당 행 상태를 직접 정리해야 합니다.
- 기존 글은 수정/삭제하지 않고 새 원고만 생성함. 임시저장 초안만 생성되며 실제 홈페이지 배포 과정은 발생할 수 있으나 공개 글에는 표시되지 않음.
- Apps Script는 자체 Script Properties로 성공한 행의 텍스트 지문을 보관하며 원본 시트는 수정하지 않음.
- 실패한 행은 다음 실행 시 재시도함. 편집 중인 원고는 D열이 `완료`가 되기 전까지 건너뜀.
- 모든 자동화에는 Apps Script/Cloudflare/GitHub 사용량 제한이 적용됨. 시간당 및 월간 배포 횟수를 확인하세요.
- API 주소가 변경되면 Apps Script의 `INFO_WORLD.API`도 변경해야 함.
