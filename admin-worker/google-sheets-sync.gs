/**
 * 정보세상 - Google Sheets 원고를 관리자 임시저장으로 전송.
 * 원본 시트는 수정하지 않습니다. 행 10부터 B=키워드, C=원고, D=완료 상태입니다.
 *
 * 설치: 구글시트 확장 프로그램 > Apps Script에서 이 파일을 붙여넣고
 * 프로젝트 설정 > 스크립트 속성에 SHEET_IMPORT_KEY 등록.
 * Cloudflare info-world-admin Worker의 비밀 변수 SHEET_IMPORT_KEY와 동일해야 합니다.
 * 처음에는 syncSheetDrafts()를 수동 실행한 다음 installDraftSyncTrigger()로 주기 실행.
 */
const INFO_WORLD = Object.freeze({
  SPREADSHEET_ID: '1aPtwkQoMtnkg4HYYy--gpW0bndD2FHu2CFRKCsroNco',
  SHEET_GID: 1562949546,
  START_ROW: 10,
  API: 'https://info-world-admin.hwsr6028.workers.dev/api/sheet-import',
  MAX_PER_RUN: 10
});

function syncSheetDrafts() {
  const key = PropertiesService.getScriptProperties().getProperty('SHEET_IMPORT_KEY');
  if (!key || key.length < 24) throw new Error('스크립트 속성 SHEET_IMPORT_KEY를 먼저 등록하세요.');
  const sheet = SpreadsheetApp.openById(INFO_WORLD.SPREADSHEET_ID).getSheetById(INFO_WORLD.SHEET_GID);
  if (!sheet) throw new Error('지정한 탭(gid)을 찾을 수 없습니다.');
  const last = sheet.getLastRow();
  if (last < INFO_WORLD.START_ROW) return {created: 0, exists: 0, skipped: 0, failed: 0};
  const values = sheet.getRange(INFO_WORLD.START_ROW, 2, last - INFO_WORLD.START_ROW + 1, 3).getDisplayValues();
  const scriptProps = PropertiesService.getScriptProperties();
  const log = {created: 0, exists: 0, skipped: 0, failed: 0};
  let attempted = 0;
  for (let i = 0; i < values.length; i++) {
    if (attempted >= INFO_WORLD.MAX_PER_RUN) break;
    const [keywordRaw, contentRaw, stateRaw] = values[i];
    const keyword = String(keywordRaw || '').trim();
    const content = String(contentRaw || '').trim();
    const state = String(stateRaw || '').trim();
    if (!keyword || content.length < 120 || !/^완료/.test(state)) {
      log.skipped++; continue;
    }
    const row = INFO_WORLD.START_ROW + i;
    const fingerprint = Utilities.base64EncodeWebSafe(
      Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, keyword + '\n' + content)
    ).replace(/=+$/, '').slice(0, 30);
    const prop = 'imported:' + INFO_WORLD.SHEET_GID + ':' + row;
    if (scriptProps.getProperty(prop) === fingerprint) {
      log.skipped++; continue;
    }
    attempted++;
    try {
      const response = UrlFetchApp.fetch(INFO_WORLD.API, {
        method: 'post',
        contentType: 'application/json',
        headers: {'X-Import-Key': key},
        payload: JSON.stringify({
          sheetId: String(INFO_WORLD.SHEET_GID),
          row,
          keyword,
          content
        }),
        muteHttpExceptions: true,
        followRedirects: false
      });
      const status = response.getResponseCode();
      const data = JSON.parse(response.getContentText() || '{}');
      if (status !== 200 || !data.ok) throw new Error('HTTP ' + status + ' ' + (data.error || data.message || '알 수 없는 오류'));
      // Created and already-existing posts are both safe to mark processed.
      scriptProps.setProperty(prop, fingerprint);
      if (data.result === 'created') log.created++;
      else log.exists++;
    } catch (error) {
      log.failed++;
      console.error('행 ' + row + ': ' + error.message);
      // API/network error -> do not mark processed, retry on next run.
    }
  }
  console.log(JSON.stringify(log));
  return log;
}
function installDraftSyncTrigger() {
  const handler = 'syncSheetDrafts';
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === handler)
    .forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger(handler).timeBased().everyMinutes(5).create();
  console.log('5분마다 완료된 구글시트 원고를 임시저장으로 가져옵니다.');
}
function stopDraftSyncTrigger() {
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === 'syncSheetDrafts')
    .forEach(t => ScriptApp.deleteTrigger(t));
}
