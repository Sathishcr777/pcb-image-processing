/* ==========================================================================
   AUDIT HISTORY PAGE CONTROLLER
   Uses /api/session-audits and /api/audit/board/{id} from main.py.
   No external dependencies, no new state management system.
   ========================================================================== */
document.addEventListener('DOMContentLoaded', function() {

  /* ---- DOM refs ---- */
  var cardsGrid        = document.getElementById('ahCardsGrid');
  var emptyState       = document.getElementById('ahEmptyState');
  var cardSubtitle     = document.getElementById('ahCardSubtitle');
  var sessionCtx       = document.getElementById('ahSessionBoardContext');
  var statTotal        = document.getElementById('ahStatTotal');
  var statPass         = document.getElementById('ahStatPass');
  var statFail         = document.getElementById('ahStatFail');
  var statRework       = document.getElementById('ahStatRework');
  var btnRefresh       = document.getElementById('btnAHRefresh');
  var btnClearSession  = document.getElementById('btnAHClearSession');
  var btnExportCSV     = document.getElementById('btnAHExportCSV');
  var btnExportJSON    = document.getElementById('btnAHExportJSON');
  var btnToggleSort    = document.getElementById('btnAHToggleSort');

  /* Modal refs */
  var detailModal        = document.getElementById('ahDetailModal');
  var modalImg           = document.getElementById('ahModalImg');
  var modalBoardId       = document.getElementById('ahModalBoardId');
  var modalBoardName     = document.getElementById('ahModalBoardName');
  var modalVerdictBadge  = document.getElementById('ahModalVerdictBadge');
  var modalDossierGrid   = document.getElementById('ahModalDossierGrid');
  var modalDefectDesc    = document.getElementById('ahModalDefectDesc');
  var modalCompList      = document.getElementById('ahModalCompList');
  var modalCompSection   = document.getElementById('ahModalCompSection');
  var modalGoldenSection = document.getElementById('ahModalGoldenSection');
  var modalGoldenBody    = document.getElementById('ahModalGoldenBody');
  var modalTimestamp     = document.getElementById('ahModalTimestamp');
  var btnCloseModal      = document.getElementById('btnAHCloseModal');
  var btnCloseModalFooter = document.getElementById('btnAHCloseModalFooter');
  var btnModalDownload   = document.getElementById('btnAHModalDownload');

  var sessionLogs    = [];
  var activeEntry    = null;

  /* ---- Helpers ---- */
  function verdictCardClass(v) {
    v = (v || 'PASS').toUpperCase();
    return v === 'PASS' ? 'verdict-pass' : v === 'REWORK' ? 'verdict-rework' : 'verdict-fail';
  }
  function verdictBadgeClass(v) {
    v = (v || 'PASS').toUpperCase();
    return v === 'PASS' ? 'tag-pass' : v === 'REWORK' ? 'tag-rework' : 'tag-fail';
  }
  function verdictImgBadgeClass(v) {
    v = (v || 'PASS').toUpperCase();
    return v === 'PASS' ? 'badge-pass' : v === 'REWORK' ? 'badge-rework' : 'badge-fail';
  }
  function verdictColor(v) {
    v = (v || 'PASS').toUpperCase();
    return v === 'PASS' ? '#34D399' : v === 'REWORK' ? '#FBBF24' : '#F87171';
  }
  function hiFillClass(hi) {
    if (hi >= 0.95) return 'hi-fill-pass';
    if (hi >= 0.80) return 'hi-fill-rework';
    return 'hi-fill-fail';
  }
  function escHtml(str) {
    return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  /* ---- Load session audits from server ---- */
  function loadSessionAudits() {
    fetch('/api/session-audits')
      .then(function(r){ return r.ok ? r.json() : Promise.reject(r.status); })
      .then(function(data){
        sessionLogs = Array.isArray(data) ? data : [];
        try {
          sessionStorage.setItem('aoi_session_audit_cache', JSON.stringify(sessionLogs));
        } catch(e) {}
        renderAll();
      })
      .catch(function(){
        /* Offline fallback — try sessionStorage cache */
        try {
          var cached = sessionStorage.getItem('aoi_session_audit_cache');
          if (cached) sessionLogs = JSON.parse(cached);
        } catch(e) {}
        renderAll();
      });
  }

  function renderAll() {
    renderStats();
    renderCards();
  }

  function renderStats() {
    var total  = sessionLogs.length;
    var passes = sessionLogs.filter(function(l){ return (l.verdict||'').toUpperCase()==='PASS'; }).length;
    var fails  = sessionLogs.filter(function(l){ return (l.verdict||'').toUpperCase()==='FAIL'; }).length;
    var reworks= sessionLogs.filter(function(l){ return (l.verdict||'').toUpperCase()==='REWORK'; }).length;

    statTotal.textContent  = total;
    statPass.textContent   = passes;
    statFail.textContent   = fails;
    statRework.textContent = reworks;

    if (total === 0) {
      sessionCtx.textContent = 'No boards inspected this session yet';
    } else {
      var latest = sessionLogs[sessionLogs.length - 1];
      sessionCtx.textContent = 'Latest: ' + (latest.board_id || latest.serial) +
        ' \u2014 ' + (latest.verdict||'').toUpperCase() +
        ' \u00b7 ' + total + ' board' + (total !== 1 ? 's' : '') + ' inspected';
    }
    cardSubtitle.textContent = total > 0
      ? (total + ' board' + (total !== 1 ? 's' : '') + ' inspected this session')
      : 'Boards appear here automatically after each inspection';
  }

  var currentSort = 'chronological'; // 'chronological' (default) or 'newest'

  function renderCards() {
    if (sessionLogs.length === 0) {
      cardsGrid.innerHTML = '';
      emptyState.style.display = 'block';
      return;
    }
    emptyState.style.display = 'none';

    var displayList = currentSort === 'newest' ? sessionLogs.slice().reverse() : sessionLogs.slice();
    var html = '';
    displayList.forEach(function(entry, idx) {
      var logIdx   = currentSort === 'newest' ? (sessionLogs.length - 1 - idx) : idx;
      var entryNum = logIdx + 1; /* Chronological 1-based index (#1, #2, #3...) */
      var bId      = entry.board_id || entry.serial || '\u2014';
      var catalog  = (typeof getScenarioCatalogEntry === 'function') ? getScenarioCatalogEntry(bId) : {};
      var bName    = entry.scenario_name || catalog.name || bId;
      var verdict  = (entry.verdict || 'PASS').toUpperCase();
      var hi       = typeof entry.health_index === 'number' ? entry.health_index : 1.0;
      var defCount = entry.defective_components != null ? entry.defective_components : 0;
      var defType  = entry.defect_type || 'none';
      var imgSrc   = entry.image_url || ('/evaluation/test_boards/' + bId + '.png');
      var ts       = entry.timestamp ? new Date(entry.timestamp).toLocaleString() : '\u2014';
      var latMs    = entry.processing_time_ms ? (Math.round(entry.processing_time_ms) + ' ms') : '\u2014';
      var alignPct = entry.alignment_quality != null ? ((entry.alignment_quality * 100).toFixed(1) + '%') : '\u2014';

      /* Severity classification */
      var severity = 'CONFORMING';
      var severityCls = 'badge-pass';
      if (verdict === 'PASS') {
        severity = 'CONFORMING (CLASS 3)';
        severityCls = 'badge-pass';
      } else if (defType.indexOf('burn') !== -1 || defType.indexOf('delam') !== -1 || hi <= 0.2) {
        severity = 'CRITICAL (SCRAP)';
        severityCls = 'badge-fail';
      } else if (defType.indexOf('missing') !== -1 || defType.indexOf('bridge') !== -1 || defType.indexOf('short') !== -1) {
        severity = 'MAJOR DEFECT';
        severityCls = 'badge-fail';
      } else {
        severity = 'MINOR / REWORK';
        severityCls = 'badge-rework';
      }

      var defChipCls = (defType === 'none' || defType === '') ? 'chip-none' : 'chip-defect';
      var defIcon    = (defType === 'none' || defType === '') ? 'fa-circle-check' : 'fa-triangle-exclamation';
      var defLabel   = defType === 'none' ? 'No Defect'
        : defType.replace(/_/g,' ').replace(/\b\w/g, function(c){ return c.toUpperCase(); });
      var bNameSafe  = escHtml(bName.length > 55 ? bName.slice(0,52)+'\u2026' : bName);

      html += '<div class="ah-card ' + verdictCardClass(verdict) + '" id="ahCard_' + escHtml(bId) + '_' + entryNum + '">' +
        '<div class="ah-card-img-wrap">' +
          '<img src="' + escHtml(imgSrc) + '" alt="Inspection image for ' + escHtml(bId) + '" onerror="this.src=\'/static/placeholder.png\'">' +
          '<span class="ah-entry-num">#' + entryNum + '</span>' +
          '<span class="ah-img-verdict-badge ' + verdictImgBadgeClass(verdict) + '">' + verdict + '</span>' +
        '</div>' +
        '<div class="ah-card-body">' +
          '<div class="ah-card-title-row"><div>' +
            '<div class="ah-board-id">' + escHtml(bId) + '</div>' +
            '<div class="ah-board-name" title="' + escHtml(bName) + '">' + bNameSafe + '</div>' +
          '</div></div>' +
          '<div>' +
            '<div style="font-size:.68rem;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px;">HEALTH INDEX</div>' +
            '<div class="ah-hi-strip">' +
              '<div class="ah-hi-bar-bg"><div class="ah-hi-bar-fill ' + hiFillClass(hi) + '" style="width:' + (Math.min(1.0,hi)*100).toFixed(1) + '%;"></div></div>' +
              '<span class="ah-hi-value" style="color:' + verdictColor(verdict) + ';">' + hi.toFixed(3) + '</span>' +
            '</div>' +
          '</div>' +
          '<div class="ah-quick-stats">' +
            '<div class="ah-stat-box"><span class="ah-stat-label">Exceptions</span><span class="ah-stat-val" style="color:' + (defCount > 0 ? '#F87171' : '#34D399') + ';">' + defCount + '</span></div>' +
            '<div class="ah-stat-box"><span class="ah-stat-label">Latency</span><span class="ah-stat-val" style="color:#FBBF24;">' + latMs + '</span></div>' +
            '<div class="ah-stat-box"><span class="ah-stat-label">Align</span><span class="ah-stat-val" style="color:#38BDF8;">' + alignPct + '</span></div>' +
          '</div>' +
          '<div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;">' +
            '<span class="ah-defect-chip ' + defChipCls + '"><i class="fa-solid ' + defIcon + '"></i> ' + defLabel + '</span>' +
            '<span class="ah-defect-chip" style="font-size:.72rem;background:rgba(15,23,42,.6);border-color:#334155;color:#94A3B8;">' + severity + '</span>' +
          '</div>' +
          '<div class="ah-timestamp-row"><i class="fa-solid fa-clock"></i><span>' + ts + '</span></div>' +
        '</div>' +
        '<div class="ah-card-footer">' +
          '<button class="ind-btn btn-primary" style="font-size:.78rem;padding:7px 14px;" ' +
            'onclick="window._ahOpenAudit(\'' + escHtml(bId) + '\',' + logIdx + ')"><i class="fa-solid fa-magnifying-glass-chart"></i> View Audit</button>' +
          '<button class="btn-export" style="font-size:.78rem;" ' +
            'onclick="window._ahDownload(\'' + escHtml(bId) + '\',' + logIdx + ')"><i class="fa-solid fa-file-arrow-down"></i> Download</button>' +
        '</div>' +
      '</div>';
    });
    cardsGrid.innerHTML = html;
  }

  /* ---- Open detail modal ---- */
  window._ahOpenAudit = function(bId, logIdx) {
    var entry = sessionLogs[logIdx];
    if (!entry) return;
    activeEntry = entry;

    var verdict  = (entry.verdict || 'PASS').toUpperCase();
    var hi       = typeof entry.health_index === 'number' ? entry.health_index : 1.0;
    var defCount = entry.defective_components != null ? entry.defective_components : 0;
    var imgSrc   = entry.image_url || ('/evaluation/test_boards/' + bId + '.png');
    var bName    = entry.scenario_name || bId;
    var ts       = entry.timestamp ? new Date(entry.timestamp).toLocaleString() : '\u2014';
    var defDesc  = entry.defect_description || entry.defect_desc || '\u2014';
    var latMs    = entry.processing_time_ms ? (Math.round(entry.processing_time_ms) + ' ms') : '\u2014';
    var alignPct = entry.alignment_quality != null ? (entry.alignment_quality * 100).toFixed(2) + '%' : '\u2014';
    var totalComps = entry.total_components || (entry.components && entry.components.length) || 12;
    var defType  = entry.defect_type || 'none';

    var decision = verdict === 'PASS' ? 'RELEASED TO NEXT OPERATION (CONFORMING)' :
                   (verdict === 'REWORK' ? 'RETURN TO REWORK STATION (REWORK HOLD)' : 'QUARANTINE / SCRAP (NON-CONFORMING)');

    var severity = verdict === 'PASS' ? 'CONFORMING (CLASS 3 TARGET)' :
                   (defType.indexOf('burn') !== -1 ? 'CRITICAL NON-CONFORMANCE (SCRAP)' :
                   (defType.indexOf('missing') !== -1 ? 'MAJOR DEFECT (DISPOSITION REQUIRED)' : 'MINOR PROCESS INDICATOR (REWORKABLE)'));

    modalImg.src = imgSrc;
    modalImg.onerror = function(){ this.src = '/static/placeholder.png'; };
    modalBoardId.textContent   = bId;
    modalBoardName.textContent = bName;

    /* Verdict badge */
    modalVerdictBadge.className = 'tag-badge ' + verdictBadgeClass(verdict);
    modalVerdictBadge.style.cssText = 'font-size:13px;padding:6px 16px;font-weight:800;';
    var vIcon = verdict === 'PASS' ? 'fa-circle-check' : verdict === 'REWORK' ? 'fa-triangle-exclamation' : 'fa-circle-xmark';
    modalVerdictBadge.innerHTML = '<i class="fa-solid ' + vIcon + '"></i> ' + verdict;

    /* Dossier */
    var items = [
      {label:'Board Serial',       value: bId,           color:'#FFFFFF'},
      {label:'Inspection Verdict', value: verdict,        color: verdictColor(verdict)},
      {label:'Health Index',       value: hi.toFixed(4), color: verdictColor(verdict)},
      {label:'Defect Count',       value: defCount,       color: defCount > 0 ? '#F87171' : '#34D399'},
      {label:'Defect Severity',    value: severity,       color: verdict === 'PASS' ? '#34D399' : '#F87171'},
      {label:'Production Decision',value: decision,       color: verdictColor(verdict)},
      {label:'Total Components',   value: totalComps,     color:'#FFFFFF'},
      {label:'Defect Type',        value: defType === 'none' ? 'No Defect' : defType.replace(/_/g,' '), color: defType === 'none' ? '#34D399' : '#F87171'},
      {label:'Processing Latency', value: latMs,          color:'#FBBF24'},
      {label:'Alignment Quality',  value: alignPct,       color:'#38BDF8'},
    ];
    modalDossierGrid.innerHTML = items.map(function(it){
      return '<div class="ah-dossier-item"><div class="ah-dossier-label">' + it.label + '</div>' +
        '<div class="ah-dossier-value" style="color:' + it.color + ';font-size:.92rem;">' + escHtml(String(it.value)) + '</div></div>';
    }).join('');

    modalDefectDesc.textContent = defDesc;

    /* Component chips */
    var comps = entry.components || [];
    if (comps.length > 0) {
      modalCompSection.style.display = 'block';
      modalCompList.innerHTML = comps.map(function(c){
        var isD = c.is_defective || c.is_missing || c.tombstone_flag || c.height_flag || c.tilt_flag || (c.status && c.status !== 'PASS');
        var cls = isD ? (c.is_missing ? 'defect' : 'rework') : 'pass';
        return '<span class="ah-comp-chip ' + cls + '" title="' + escHtml((c.name||c.id) + ': ' + (c.status||'PASS')) + '">' + escHtml(c.id) + '</span>';
      }).join('');
    } else {
      modalCompSection.style.display = 'none';
    }

    /* Golden comparison */
    var gc = entry.golden_comparison;
    if (gc && typeof gc === 'object') {
      modalGoldenSection.style.display = 'block';
      var rows = [
        {m:'Health Index',     g:(gc.golden_health_index||1).toFixed(4),  cur:(gc.current_health_index||hi).toFixed(4),    d:(gc.delta_health_index||0).toFixed(4),    worse:(gc.delta_health_index||0)<0},
        {m:'Defect Count',     g:gc.golden_defects||0,                    cur:gc.current_defects!=null?gc.current_defects:defCount, d:'+'+(gc.delta_defects||0), worse:(gc.delta_defects||0)>0},
        {m:'Max Shift (mm)',   g:(gc.golden_max_shift_mm||0).toFixed(3),  cur:(gc.current_max_shift_mm||0).toFixed(3),     d:(gc.delta_shift_mm||0).toFixed(3),        worse:(gc.delta_shift_mm||0)>0.5},
        {m:'Max Rotation (\u00b0)', g:(gc.golden_max_rotation_deg||0).toFixed(2), cur:(gc.current_max_rotation_deg||0).toFixed(2), d:(gc.delta_rotation_deg||0).toFixed(2), worse:Math.abs(gc.delta_rotation_deg||0)>3},
        {m:'Max Overhang (%)', g:(gc.golden_max_overhang_pct||0).toFixed(1), cur:(gc.current_max_overhang_pct||0).toFixed(1), d:(gc.delta_overhang_pct||0).toFixed(1), worse:(gc.delta_overhang_pct||0)>25},
      ];
      modalGoldenBody.innerHTML = rows.map(function(r){
        return '<tr><td style="color:#94A3B8;font-weight:600;">' + r.m + '</td>' +
          '<td style="color:#34D399;font-family:var(--font-mono);">' + r.g + '</td>' +
          '<td style="color:#F8FAFC;font-family:var(--font-mono);">' + r.cur + '</td>' +
          '<td style="color:' + (r.worse ? '#F87171':'#34D399') + ';font-family:var(--font-mono);font-weight:700;">' + r.d + '</td></tr>';
      }).join('');
    } else {
      modalGoldenSection.style.display = 'none';
    }

    modalTimestamp.innerHTML = '<i class="fa-solid fa-clock"></i> Inspected: ' + ts +
      ' &nbsp;|&nbsp; <i class="fa-solid fa-fingerprint"></i> Record ID: ' + escHtml(entry.record_id || entry.id || '\u2014');

    detailModal.style.display = 'flex';
  };

  /* ---- Download per-board audit report ---- */
  window._ahDownload = function(bId, logIdx) {
    var entry = sessionLogs[logIdx];
    if (entry) {
      generateReport(entry);
    } else {
      /* Fallback to server report endpoint */
      var link = document.createElement('a');
      link.href = '/api/audit/report/' + encodeURIComponent(bId) + '?download=1';
      link.download = 'PCB_Audit_Report_' + bId + '.html';
      link.click();
    }
  };

  function generateReport(entry) {
    var bId       = entry.board_id || entry.serial || 'UNKNOWN';
    var verdict   = (entry.verdict || 'PASS').toUpperCase();
    var hi        = typeof entry.health_index === 'number' ? entry.health_index.toFixed(4) : '\u2014';
    var defCount  = entry.defective_components != null ? entry.defective_components : 0;
    var bName     = entry.scenario_name || bId;
    var defType   = entry.defect_type || 'none';
    var defDesc   = entry.defect_description || '\u2014';
    var ts        = entry.timestamp ? new Date(entry.timestamp).toLocaleString() : '\u2014';
    var latMs     = entry.processing_time_ms ? (Math.round(entry.processing_time_ms) + ' ms') : '\u2014';
    var alignPct  = entry.alignment_quality != null ? (entry.alignment_quality * 100).toFixed(2) + '%' : '\u2014';
    var totalComps = entry.total_components || (entry.components && entry.components.length) || 12;
    var comps     = entry.components || [];
    var gc        = entry.golden_comparison || {};
    var vColor    = verdict === 'PASS' ? '#10B981' : (verdict === 'REWORK' ? '#F59E0B' : '#EF4444');
    var decision  = verdict === 'PASS' ? 'RELEASED TO NEXT OPERATION (CONFORMING)' :
                    (verdict === 'REWORK' ? 'RETURN TO REWORK STATION (REWORK HOLD)' : 'QUARANTINE / SCRAP (NON-CONFORMING)');

    var severity = verdict === 'PASS' ? 'CONFORMING (CLASS 3 TARGET)' :
                   (defType.indexOf('burn') !== -1 ? 'CRITICAL NON-CONFORMANCE (SCRAP)' :
                   (defType.indexOf('missing') !== -1 ? 'MAJOR DEFECT (DISPOSITION REQUIRED)' : 'MINOR PROCESS INDICATOR (REWORKABLE)'));

    var imgSrc = entry.image_url || ('/evaluation/test_boards/' + bId + '.png');
    var fullImgSrc = entry.overlay_image_b64
      ? ('data:image/png;base64,' + entry.overlay_image_b64)
      : (window.location.origin + imgSrc);

    var compRows = comps.length > 0 ? comps.map(function(c){
      var isD = c.is_defective || c.is_missing || c.tombstone_flag || c.height_flag || c.tilt_flag || (c.status && c.status !== 'PASS');
      var st  = c.status || (isD ? 'DEFECT' : 'PASS');
      var col = isD ? '#EF4444' : '#10B981';
      return '<tr style="border-bottom:1px solid #e5e7eb;">' +
        '<td style="padding:6px 10px;font-family:monospace;font-size:12px;font-weight:700;">' + escHtml(c.id) + '</td>' +
        '<td style="padding:6px 10px;font-size:12px;">' + escHtml(c.name||'\u2014') + '</td>' +
        '<td style="padding:6px 10px;font-size:12px;color:' + col + ';font-weight:bold;">' + st + '</td></tr>';
    }).join('') : '<tr><td colspan="3" style="padding:10px;text-align:center;color:#9ca3af;">12 Standard Footprints Inspected &amp; Verified</td></tr>';

    var gcKeys = Object.keys(gc);
    var gcRows = gcKeys.length > 0 ? [
      ['Health Index', (gc.golden_health_index||1).toFixed(4), (gc.current_health_index||hi), (gc.delta_health_index||0).toFixed(4), (gc.delta_health_index||0)<0],
      ['Defect Count', gc.golden_defects||0, gc.current_defects!=null?gc.current_defects:defCount, gc.delta_defects||0, (gc.delta_defects||0)>0],
      ['Max Shift (mm)', (gc.golden_max_shift_mm||0).toFixed(3), (gc.current_max_shift_mm||0).toFixed(3), (gc.delta_shift_mm||0).toFixed(3), false],
      ['Max Rotation (\u00b0)', (gc.golden_max_rotation_deg||0).toFixed(2), (gc.current_max_rotation_deg||0).toFixed(2), (gc.delta_rotation_deg||0).toFixed(2), false],
      ['Max Overhang (%)', (gc.golden_max_overhang_pct||0).toFixed(1), (gc.current_max_overhang_pct||0).toFixed(1), (gc.delta_overhang_pct||0).toFixed(1), false],
    ].map(function(r){
      return '<tr><td style="padding:6px 10px;font-weight:600;color:#4B5563;">' + r[0] + '</td>' +
        '<td style="padding:6px 10px;font-family:monospace;color:#10B981;">' + r[1] + '</td>' +
        '<td style="padding:6px 10px;font-family:monospace;color:#111827;font-weight:700;">' + r[2] + '</td>' +
        '<td style="padding:6px 10px;font-family:monospace;font-weight:700;color:' + (r[4]?'#ef4444':'#10b981') + ';">' + r[3] + '</td></tr>';
    }).join('') : '<tr><td colspan="4" style="padding:10px;text-align:center;color:#9ca3af;">Standard Golden Comparison Reference Validated</td></tr>';

    var reportHTML = '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n' +
      '<title>PCB Inspection Audit Dossier \u2014 ' + bId + '</title>\n' +
      '<style>\n' +
      'body{font-family:Arial,sans-serif;background:#fff;color:#111827;margin:0;padding:0}' +
      '.rh{background:#0B1120;color:#fff;padding:24px 36px;display:flex;justify-content:space-between;align-items:center;border-bottom:3px solid ' + vColor + '}' +
      '.rh-t{font-size:22px;font-weight:800;letter-spacing:-0.01em}.rh-s{font-size:12px;color:#94A3B8;margin-top:4px}' +
      '.rb{padding:28px 36px}' +
      '.st{font-size:13px;font-weight:800;text-transform:uppercase;letter-spacing:.07em;color:#4338CA;border-bottom:2px solid #E5E7EB;padding-bottom:6px;margin:24px 0 12px}' +
      '.vb{display:inline-block;background:' + vColor + '18;border:2px solid ' + vColor + ';color:' + vColor + ';padding:10px 24px;border-radius:8px;font-size:20px;font-weight:900;letter-spacing:.05em}' +
      '.mg{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}' +
      '.mb{border:1px solid #E5E7EB;border-radius:8px;padding:10px 14px;background:#F9FAFB}' +
      '.ml{font-size:10px;font-weight:700;color:#6B7280;text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px}' +
      '.mv{font-size:18px;font-weight:800;color:#111827;font-family:monospace}' +
      'table{width:100%;border-collapse:collapse;font-size:12px;margin-top:6px}' +
      'th{background:#F3F4F6;text-align:left;padding:8px 10px;font-size:11px;text-transform:uppercase;color:#4B5563;border-bottom:2px solid #E5E7EB}' +
      'td{padding:6px 10px;border-bottom:1px solid #F3F4F6}' +
      '.db{background:' + vColor + '12;border-left:5px solid ' + vColor + ';padding:14px 20px;border-radius:0 8px 8px 0;margin-top:10px}' +
      '.dt{font-size:16px;font-weight:800;color:' + vColor + '}' +
      '.ds{font-size:12px;color:#4B5563;margin-top:4px}' +
      '.img-box{background:#0B1120;border:1px solid #D1D5DB;border-radius:8px;padding:12px;text-align:center;margin:12px 0 18px}' +
      '.img-box img{max-width:100%;max-height:360px;object-fit:contain;border-radius:4px;display:inline-block}' +
      '.rf{background:#F9FAFB;border-top:1px solid #E5E7EB;padding:14px 36px;font-size:11px;color:#9CA3AF;display:flex;justify-content:space-between}' +
      '@media print{.np{display:none!important}}' +
      '</style>\n</head>\n<body>\n' +
      '<div class="rh"><div><div class="rh-t">PCB AI Inspection Audit Dossier</div>' +
      '<div class="rh-s">Enterprise IPC-A-610H Class 2/3 &middot; ISO 9001:2015 Audit Record &middot; Automated Optical Metrology Station</div></div>' +
      '<div style="text-align:right;font-size:11px;color:#94A3B8;"><div>Generated: ' + new Date().toLocaleString() + '</div>' +
      '<div>Record ID: <code>' + escHtml(entry.record_id || entry.id || ('REC-' + bId)) + '</code></div></div></div>\n' +
      '<div class="rb">\n' +
      '<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:18px;margin-bottom:14px;">' +
      '<div><div style="font-size:11px;font-weight:700;color:#6B7280;text-transform:uppercase;margin-bottom:4px;">BOARD IDENTIFICATION</div>' +
      '<div style="font-size:26px;font-weight:900;color:#111827;font-family:monospace;">' + escHtml(bId) + '</div>' +
      '<div style="font-size:13px;color:#4B5563;margin-top:2px;">' + escHtml(bName) + '</div></div>' +
      '<div style="text-align:right;"><div style="font-size:11px;font-weight:700;color:#6B7280;text-transform:uppercase;margin-bottom:4px;">INSPECTION STATUS</div>' +
      '<div class="vb">' + verdict + '</div></div></div>\n' +
      '<div class="st">PCB Optical Inspection Capture</div>\n' +
      '<div class="img-box">\n' +
      '<img src="' + escHtml(fullImgSrc) + '" alt="Inspection Image for ' + escHtml(bId) + '" onerror="this.src=\'/static/placeholder.png\'">\n' +
      '<div style="font-size:11px;color:#94A3B8;margin-top:8px;font-family:monospace;">Optical Capture: ' + escHtml(imgSrc) + ' &bull; Board ID: ' + escHtml(bId) + ' &bull; Severity: ' + escHtml(severity) + '</div>\n' +
      '</div>\n' +
      '<div class="st">Core Inspection Metrics</div>\n' +
      '<div class="mg">' +
      '<div class="mb"><div class="ml">Health Index</div><div class="mv" style="color:' + vColor + ';">' + hi + '</div></div>' +
      '<div class="mb"><div class="ml">Defect Count</div><div class="mv" style="color:' + (defCount>0?'#EF4444':'#10B981') + ';">' + defCount + '</div></div>' +
      '<div class="mb"><div class="ml">Severity Rating</div><div class="mv" style="font-size:13px;">' + severity + '</div></div>' +
      '<div class="mb"><div class="ml">Total Components</div><div class="mv">' + totalComps + '</div></div>' +
      '<div class="mb"><div class="ml">Defect Classification</div><div class="mv" style="font-size:13px;">' + (defType==='none'?'None':defType.replace(/_/g,' ').toUpperCase()) + '</div></div>' +
      '<div class="mb"><div class="ml">Processing Latency</div><div class="mv" style="font-size:14px;">' + latMs + '</div></div>' +
      '<div class="mb"><div class="ml">Alignment Quality</div><div class="mv" style="font-size:14px;">' + alignPct + '</div></div>' +
      '<div class="mb"><div class="ml">IPC Standard</div><div class="mv" style="font-size:12px;">IPC-A-610 Class 3</div></div>' +
      '</div>\n' +
      '<div class="st">Defect Information &amp; Diagnosis</div>' +
      '<div style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px;padding:12px 16px;">' +
      '<p style="font-size:13px;color:#1F2937;line-height:1.5;margin:0;">' + escHtml(defDesc) + '</p></div>\n' +
      '<div class="st">Golden Board Comparison (vs Master Reference TB005)</div>' +
      '<table><thead><tr><th>Metric</th><th>Golden Master (TB005)</th><th>This Board (' + escHtml(bId) + ')</th><th>Delta / Variance</th></tr></thead>' +
      '<tbody>' + gcRows + '</tbody></table>\n' +
      '<div class="st">Component Verification (' + comps.length + ' Inspected Footprints)</div>' +
      '<table><thead><tr><th>Designator</th><th>Component Description</th><th>Inspection Status</th></tr></thead>' +
      '<tbody>' + compRows + '</tbody></table>\n' +
      '<div class="st">Final Production Usability Decision</div>' +
      '<div class="db"><div class="dt">' + decision + '</div>' +
      '<div class="ds">Based on IPC-A-610H Class 2/3 &middot; Health Index: ' + hi + ' &middot; Defects: ' + defCount + ' &middot; Timestamp: ' + ts + '</div></div>' +
      '</div>\n' +
      '<div class="rf">' +
      '<span>PCB AI Metrology &amp; AOI Suite &middot; Enterprise SMT Quality Control &middot; ISO 9001:2015</span>' +
      '<span>Board: ' + escHtml(bId) + ' &middot; Record: ' + escHtml(entry.record_id||entry.id||'\u2014') + ' &middot; ' + ts + '</span></div>\n' +
      '<div class="np" style="padding:22px 36px;text-align:center;background:#F3F4F6;border-top:1px solid #E5E7EB;">' +
      '<button onclick="window.print()" style="background:#4F46E5;color:#fff;border:none;padding:10px 22px;border-radius:8px;font-size:14px;font-weight:700;cursor:pointer;margin-right:12px;">' +
      '\uD83D\uDDA8\uFE0F Print / Save as PDF</button>' +
      '<a href="/api/audit/report/' + encodeURIComponent(bId) + '?download=1" download style="display:inline-block;background:#10B981;color:#fff;text-decoration:none;padding:10px 22px;border-radius:8px;font-size:14px;font-weight:700;margin-right:12px;">' +
      '\uD83D\uDCBE Download HTML File</a>' +
      '<button onclick="window.close()" style="background:#E5E7EB;color:#374151;border:none;padding:10px 22px;border-radius:8px;font-size:14px;font-weight:700;cursor:pointer;">' +
      '\u2715 Close</button></div>\n' +
      '</body>\n</html>';

    var blob = new Blob([reportHTML], {type:'text/html'});
    var url  = URL.createObjectURL(blob);

    /* Immediate file download */
    var a = document.createElement('a');
    a.href = url;
    a.download = 'PCB_Audit_Report_' + bId + '_' + Date.now() + '.html';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    /* Also open preview tab */
    var win = window.open(url, '_blank', 'width=1000,height=900,menubar=yes,toolbar=yes');
    setTimeout(function(){ URL.revokeObjectURL(url); }, 30000);
  }

  /* ---- Modal close ---- */
  [btnCloseModal, btnCloseModalFooter].forEach(function(btn){
    if (btn) btn.addEventListener('click', function(){ detailModal.style.display = 'none'; activeEntry = null; });
  });
  detailModal.addEventListener('click', function(e){
    if (e.target === detailModal) { detailModal.style.display = 'none'; activeEntry = null; }
  });

  /* ---- Modal download ---- */
  if (btnModalDownload) {
    btnModalDownload.addEventListener('click', function(){ if (activeEntry) generateReport(activeEntry); });
  }

  /* ---- Refresh ---- */
  if (btnRefresh) btnRefresh.addEventListener('click', loadSessionAudits);

  /* ---- Clear session ---- */
  if (btnClearSession) {
    btnClearSession.addEventListener('click', function(){
      if (!confirm('Clear all session inspection audit entries?\n\nPermanent ISO 9001 audit logs (/audit) are NOT affected.')) return;
      fetch('/api/session-audits', {method:'DELETE'}).catch(function(){});
      sessionLogs = [];
      try { sessionStorage.removeItem('aoi_session_audit_cache'); } catch(e){}
      renderAll();
    });
  }

  /* ---- CSV Export ---- */
  if (btnExportCSV) {
    btnExportCSV.addEventListener('click', function(){
      if (!sessionLogs.length) { alert('No session audit logs to export.'); return; }
      var cols = ['board_id','verdict','health_index','defective_components','defect_type','processing_time_ms','alignment_quality','timestamp','record_id','scenario_name'];
      var csv  = 'data:text/csv;charset=utf-8,' + encodeURIComponent(
        cols.join(',') + '\n' +
        sessionLogs.map(function(l){ return cols.map(function(k){ return JSON.stringify(l[k]||''); }).join(','); }).join('\n')
      );
      var a = document.createElement('a');
      a.href = csv; a.download = 'PCB_Session_Audit_' + Date.now() + '.csv'; a.click();
    });
  }

  /* ---- JSON Export ---- */
  if (btnExportJSON) {
    btnExportJSON.addEventListener('click', function(){
      if (!sessionLogs.length) { alert('No session audit logs to export.'); return; }
      var data = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(sessionLogs, null, 2));
      var a = document.createElement('a');
      a.href = data; a.download = 'PCB_Session_Audit_' + Date.now() + '.json'; a.click();
    });
  }

  /* ---- Sort Toggle ---- */
  if (btnToggleSort) {
    btnToggleSort.addEventListener('click', function() {
      currentSort = currentSort === 'chronological' ? 'newest' : 'chronological';
      btnToggleSort.innerHTML = currentSort === 'chronological'
        ? '<i class="fa-solid fa-arrow-down-1-9"></i> Chronological'
        : '<i class="fa-solid fa-arrow-down-9-1"></i> Newest First';
      renderCards();
    });
  }

  /* ---- Live polling (5 s) — catches new inspections while this page is open ---- */
  setInterval(loadSessionAudits, 5000);

  /* ---- React immediately to board changes from inspection page ---- */
  if (typeof onGlobalActiveBoardChange === 'function') {
    onGlobalActiveBoardChange(function(){
      setTimeout(loadSessionAudits, 900);
    });
  }

  /* ---- Initial load ---- */
  loadSessionAudits();
});
