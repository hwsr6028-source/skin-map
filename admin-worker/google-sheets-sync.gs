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
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) return {created: 0, exists: 0, skipped: 0, failed: 0, busy: true};
  try {
    const key = PropertiesService.getScriptProperties().getProperty('SHEET_IMPORT_KEY');
    if (!key || key.length < 24) throw new Error('스크립트 속성 SHEET_IMPORT_KEY를 먼저 등록하세요.');
    const sheet = SpreadsheetApp.openById(INFO_WORLD.SPREADSHEET_ID).getSheetById(INFO_WORLD.SHEET_GID);
    if (!sheet) throw new Error('지정한 탭(gid)을 찾을 수 없습니다.');
    const last = sheet.getLastRow();
    if (last < INFO_WORLD.START_ROW) return {created: 0, exists: 0, skipped: 0, failed: 0};
    const values = sheet.getRange(INFO_WORLD.START_ROW, 2, last - INFO_WORLD.START_ROW + 1, 3).getDisplayValues();
    const props = PropertiesService.getScriptProperties();
    const log = {created: 0, exists: 0, skipped: 0, failed: 0};
    let attempted = 0;
    for (let i = 0; i < values.length; i++) {
      const [keywordRaw, contentRaw, stateRaw] = values[i];
      const keyword = String(keywordRaw || '').trim();
      const content = String(contentRaw || '').trim();
      const state = String(stateRaw || '').trim();
      const row = INFO_WORLD.START_ROW + i;
      const prefix = 'imported:' + INFO_WORLD.SHEET_GID + ':' + row;
      // Clearing B/C (or the entire row) resets its previous import state,
      // including while no finished draft is present.
      if (!keyword || !content) {
        props.deleteProperty(prefix);
        props.deleteProperty(prefix + ':event');
        props.deleteProperty(prefix + ':revision');
        log.skipped++;
        continue;
      }
      if (content.length < 120 || !/^완료/.test(state)) {
        log.skipped++;
        continue;
      }
      const fingerprint = Utilities.base64EncodeWebSafe(
        Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, keyword + '\\n' + content)
      ).replace(/=+$/, '').slice(0, 30);
      if (props.getProperty(prefix) === fingerprint) {
        log.skipped++;
        continue;
      }
      if (attempted >= INFO_WORLD.MAX_PER_RUN) break;
      // Each new writing event gets an ID independent of the row and keyword.
      // The ID is retained on API failure, so retries are idempotent.
      const revisionKey = prefix + ':revision';
      const eventKey = prefix + ':event';
      const pendingFingerprint = props.getProperty(revisionKey);
      let eventId = props.getProperty(eventKey);
      if (!eventId || pendingFingerprint !== fingerprint) {
        eventId = Utilities.getUuid().replace(/-/g, '');
        props.setProperty(eventKey, eventId);
        props.setProperty(revisionKey, fingerprint);
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
            content,
            importId: eventId
          }),
          muteHttpExceptions: true,
          followRedirects: false
        });
        const status = response.getResponseCode();
        const data = JSON.parse(response.getContentText() || '{}');
        if (status !== 200 || !data.ok) throw new Error('HTTP ' + status + ' ' + (data.error || data.message || '알 수 없는 오류'));
        props.setProperty(prefix, fingerprint);
        if (data.result === 'created') log.created++;
        else log.exists++;
      } catch (error) {
        log.failed++;
        console.error('행 ' + row + ': ' + error.message);
      }
    }
    console.log(JSON.stringify(log));
    return log;
  } finally {
    lock.releaseLock();
  }
}
// Editing B/C in an already completed row is a new writing event—even if the
// resulting text matches the previous text. Programmatic Sheet changes do not
// fire onEdit; changing back to identical content without a visible clear/edit
// is not distinguishable without a source-side submission ID.
function resetDraftImportOnEdit(e) {
  if (!e || !e.range) return;
  const sheet = e.range.getSheet();
  if (String(sheet.getParent().getId()) !== INFO_WORLD.SPREADSHEET_ID ||
      sheet.getSheetId() !== INFO_WORLD.SHEET_GID) return;
  const range = e.range;
  if (range.getLastRow() < INFO_WORLD.START_ROW ||
      range.getLastColumn() < 2 || range.getColumn() > 3) return;
  const props = PropertiesService.getScriptProperties();
  for (let row = Math.max(INFO_WORLD.START_ROW, range.getRow()); row <= range.getLastRow(); row++) {
    const prefix = 'imported:' + INFO_WORLD.SHEET_GID + ':' + row;
    props.deleteProperty(prefix);
    props.deleteProperty(prefix + ':event');
    props.deleteProperty(prefix + ':revision');
  }
}
function installDraftSyncTrigger() {
  const handlers = ['syncSheetDrafts', 'resetDraftImportOnEdit'];
  ScriptApp.getProjectTriggers()
    .filter(t => handlers.includes(t.getHandlerFunction()))
    .forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('syncSheetDrafts').timeBased().everyMinutes(5).create();
  const book = SpreadsheetApp.openById(INFO_WORLD.SPREADSHEET_ID);
  ScriptApp.newTrigger('resetDraftImportOnEdit').forSpreadsheet(book).onEdit().create();
  console.log('5분 자동 동기화 및 B/C열 수정 시 재등록 상태 초기화 설정 완료.');
}
// Run manually for selected rows when another script rewrites the exact same
// keyword/text without triggering onEdit (Google does not emit edit events for
// programmatic changes). Select only rows intended to be re-published.
function resetDraftImportRows() {
  const sheet = SpreadsheetApp.openById(INFO_WORLD.SPREADSHEET_ID).getSheetById(INFO_WORLD.SHEET_GID);
  const active = SpreadsheetApp.getActiveSpreadsheet();
  if (!active || String(active.getId()) !== INFO_WORLD.SPREADSHEET_ID) {
    throw new Error('연동된 원본 시트에서 다시 게시할 행을 선택해 주세요.');
  }
  const selected = active.getActiveRange();
  if (!selected || selected.getSheet().getSheetId() !== INFO_WORLD.SHEET_GID) {
    throw new Error('연동된 탭에서 행을 선택해 주세요.');
  }
  const props = PropertiesService.getScriptProperties();
  const start = Math.max(INFO_WORLD.START_ROW, selected.getRow());
  const end = selected.getLastRow();
  if (end < start) throw new Error('10행 이후의 다시 게시할 행을 선택해 주세요.');
  for (let row=start; row<=end; row++) {
    const prefix='imported:' + INFO_WORLD.SHEET_GID + ':' + row;
    props.deleteProperty(prefix);
    props.deleteProperty(prefix + ':event');
    props.deleteProperty(prefix + ':revision');
  }
  console.log('선택한 '+(end-start+1)+'개 행의 등록 기록을 초기화했습니다. syncSheetDrafts 실행 시 새 게시글로 등록합니다.');
}
function stopDraftSyncTrigger() {
  ScriptApp.getProjectTriggers()
    .filter(t => ['syncSheetDrafts','resetDraftImportOnEdit'].includes(t.getHandlerFunction()))
    .forEach(t => ScriptApp.deleteTrigger(t));
}
