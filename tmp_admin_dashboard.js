
// Show print dialog overlay using flex
document.getElementById('printDialogOverlay').style.display = 'none';
function _setPrintSelectOptions(selectId, values, defaultLabel, labelFn) {
  const select = document.getElementById(selectId);
  if (!select) return;
  const unique = [...new Set((values||[]).filter(Boolean))].sort((a,b)=>String(a).localeCompare(String(b)));
  select.innerHTML = `<option value="">${defaultLabel}</option>` + unique.map(v=>`<option value="${escHtml(v)}">${escHtml(labelFn ? labelFn(v) : v)}</option>`).join('');
}

function prepareConcernPrintFilters() {
  _setPrintSelectOptions(
    'printLocationFilter',
    allConcernData.map(r=>r.location||'').filter(Boolean),
    'All Locations'
  );
  _setPrintSelectOptions(
    'printHazardTypeFilter',
    allConcernData.filter(r=>r._rtype==='Hazard').map(r=>r.hazard_type||'').filter(Boolean),
    'All Main Hazard Types',
    _printHazardTypeLabel
  );
}

function openPrintDialog(t) {
  _printTarget = t;
  const today = new Date();
  const firstDay = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0];
  document.getElementById('printDateFrom').value = firstDay;
  document.getElementById('printDateTo').value   = today.toISOString().split('T')[0];
  document.getElementById('printStatusFilter').value = '';
  document.getElementById('printLocationFilter').value = '';
  document.getElementById('printHazardTypeFilter').value = '';
  document.getElementById('printPriorityFilter').value = '';
  const hasStatus = ['dashboard-reports','concern'].includes(t);
  const isConcern = t === 'concern';
  document.getElementById('printStatusRow').style.display = hasStatus ? 'flex' : 'none';
  document.getElementById('printLocationRow').style.display = isConcern ? 'flex' : 'none';
  document.getElementById('printHazardTypeRow').style.display = isConcern ? 'flex' : 'none';
  document.getElementById('printPriorityRow').style.display = isConcern ? 'flex' : 'none';
  if (isConcern) prepareConcernPrintFilters();
  const labels = {
    'dashboard-reports': 'Hazard & Concern Report',
    'dashboard-notifs':  'Notification Alerts',
    'fire':              'Fire Protection Inspections',
    'concern':           'Hazard & Concern/Suggestion Report',
    'investigation':     'Investigation Reports'
  };
  document.getElementById('printDialogLabel').textContent = labels[t] || 'Table';
  document.getElementById('printDialogOverlay').style.display = 'flex';
}
function closePrintDialog() {
  document.getElementById('printDialogOverlay').style.display = 'none';
}

// Hook into fire data loading to capture raw data for printing
const _origLoadFirePage = typeof loadFirePage === 'function' ? loadFirePage : null;
if (_origLoadFirePage) {
  loadFirePage = async function() {
    await _origLoadFirePage();
    // Data is already captured via renderFireExtTable overrides below
  };
}
const _origRFE = typeof renderFireExtTable === 'function' ? renderFireExtTable : null;
if (_origRFE) {
  renderFireExtTable = function(rows) { _fireExtData = rows||[]; _origRFE(rows); };
}
const _origRFL = typeof renderFireLightTable === 'function' ? renderFireLightTable : null;
if (_origRFL) {
  renderFireLightTable = function(rows) { _fireLightData = rows||[]; _origRFL(rows); };
}
const _origRFH = typeof renderFireHoseTable === 'function' ? renderFireHoseTable : null;
if (_origRFH) {
  renderFireHoseTable = function(rows) { _fireHoseData = rows||[]; _origRFH(rows); };
}

/* ═══ CHART PRINTING WITH CONCLUSIONS ═══ */

function generateChartConclusion(chartId, chartObj) {
  if (!chartObj || !chartObj.data) return '';
  
  const type = chartObj.type;
  const labels = chartObj.data.labels || [];
  const datasets = chartObj.data.datasets || [];
  
  let conclusion = '';
  
  if (chartId === 'chartSummary') {
    // Summary of Report per location
    const pending = datasets[0]?.data || [];
    const resolved = datasets[1]?.data || [];
    const totalPending = pending.reduce((a, b) => a + (b || 0), 0);
    const totalResolved = resolved.reduce((a, b) => a + (b || 0), 0);
    const totalReports = totalPending + totalResolved;
    const resolutionRate = totalReports > 0 ? ((totalResolved / totalReports) * 100).toFixed(1) : 0;
    
    let highestPendingLoc = labels[0] || 'N/A';
    let highestPendingCount = pending[0] || 0;
    pending.forEach((count, idx) => {
      if (count > highestPendingCount) {
        highestPendingCount = count;
        highestPendingLoc = labels[idx];
      }
    });
    
    conclusion = `<div style="background:#fffbf0;border-left:4px solid var(--gold);padding:12px 14px;border-radius:4px;font-size:.85rem;line-height:1.5;">
      <strong style="color:var(--gold-dark);">Summary:</strong> Across all locations, there are <strong>${totalPending}</strong> pending reports and <strong>${totalResolved}</strong> resolved reports. 
      The overall resolution rate is <strong>${resolutionRate}%</strong>. Location <strong>"${highestPendingLoc}"</strong> has the highest number of pending reports (<strong>${highestPendingCount}</strong>). 
      Immediate attention is recommended for locations with high pending counts.
    </div>`;
  } 
  else if (chartId === 'chartMonthly') {
    // Monthly summary report
    const data = datasets[0]?.data || [];
    const totalReports = data.reduce((a, b) => a + (b || 0), 0);
    const avgPerMonth = totalReports > 0 ? (totalReports / 12).toFixed(1) : 0;
    const maxMonth = Math.max(...data);
    const maxMonthIdx = data.indexOf(maxMonth);
    const maxMonthName = labels[maxMonthIdx] || 'N/A';
    const minMonth = Math.min(...(data.filter(d => d > 0) || [0]));
    const minMonthName = labels[data.indexOf(minMonth)] || 'N/A';
    
    conclusion = `<div style="background:#f0f5ff;border-left:4px solid #1a6bc4;padding:12px 14px;border-radius:4px;font-size:.85rem;line-height:1.5;">
      <strong style="color:#1a6bc4;">Monthly Trend:</strong> A total of <strong>${totalReports}</strong> reports were submitted throughout the year, averaging <strong>${avgPerMonth}</strong> reports per month. 
      <strong>${maxMonthName}</strong> had the highest activity with <strong>${maxMonth}</strong> reports. The lowest activity was in <strong>${minMonthName}</strong> with <strong>${minMonth}</strong> reports. 
      Monitor seasonal trends and adjust resource allocation accordingly.
    </div>`;
  } 
  else if (chartId === 'chartFire') {
    // Fire Protection Report Summary
    const data = datasets[0]?.data || [];
    const extinguisher = data[0] || 0;
    const emergencyLight = data[1] || 0;
    const hoseCabinet = data[2] || 0;
    const total = extinguisher + emergencyLight + hoseCabinet;
    
    conclusion = `<div style="background:#fff0f5;border-left:4px solid #c62828;padding:12px 14px;border-radius:4px;font-size:.85rem;line-height:1.5;">
      <strong style="color:#c62828;">Fire Protection Status:</strong> Total fire protection equipment inspected: <strong>${total}</strong>. 
      Fire Extinguishers: <strong>${extinguisher}</strong>, Emergency Lights: <strong>${emergencyLight}</strong>, Hose Cabinets: <strong>${hoseCabinet}</strong>. 
      Ensure all equipment is regularly maintained and accessible in case of emergency.
    </div>`;
  } 
  else if (chartId === 'chartReport') {
    // Report Summary (Pie Chart)
    const pending = datasets[0]?.data[0] || 0;
    const resolved = datasets[0]?.data[1] || 0;
    const total = pending + resolved;
    const resolutionRate = total > 0 ? ((resolved / total) * 100).toFixed(1) : 0;
    
    conclusion = `<div style="background:#f0fff4;border-left:4px solid #2e7d32;padding:12px 14px;border-radius:4px;font-size:.85rem;line-height:1.5;">
      <strong style="color:#2e7d32;">Report Status Distribution:</strong> Out of <strong>${total}</strong> total reports, <strong>${resolved}</strong> have been resolved and <strong>${pending}</strong> are still pending. 
      Resolution rate: <strong>${resolutionRate}%</strong>. Continue efforts to increase resolution rate and reduce pending backlog.
    </div>`;
  } 
  else if (chartId === 'chartConcernLocation') {
    // Report per location
    const pending = datasets[0]?.data || [];
    const resolved = datasets[1]?.data || [];
    const totalPending = pending.reduce((a, b) => a + (b || 0), 0);
    const totalResolved = resolved.reduce((a, b) => a + (b || 0), 0);
    const totalReports = totalPending + totalResolved;
    const resolutionRate = totalReports > 0 ? ((totalResolved / totalReports) * 100).toFixed(1) : 0;
    
    let highestPendingLoc = labels[0] || 'N/A';
    let highestPendingCount = pending[0] || 0;
    pending.forEach((count, idx) => {
      if (count > highestPendingCount) {
        highestPendingCount = count;
        highestPendingLoc = labels[idx];
      }
    });
    
    conclusion = `<div style="background:#fffbf0;border-left:4px solid var(--gold);padding:12px 14px;border-radius:4px;font-size:.85rem;line-height:1.5;">
      <strong style="color:var(--gold-dark);">Location Analysis:</strong> Across all locations, <strong>${totalPending}</strong> reports are pending and <strong>${totalResolved}</strong> have been resolved. 
      Overall resolution rate: <strong>${resolutionRate}%</strong>. Location <strong>"${highestPendingLoc}"</strong> requires priority attention with <strong>${highestPendingCount}</strong> pending reports.
    </div>`;
  }
  
  return conclusion;
}

function printChart(chartId, title) {
  const chartElem = document.getElementById(chartId);
  if (!chartElem) {
    alert('Chart not found.');
    return;
  }
  
  // Get chart object from global scope based on ID
  let chartObj = null;
  if (chartId === 'chartSummary') chartObj = chartSummary;
  else if (chartId === 'chartMonthly') chartObj = chartMonthly;
  else if (chartId === 'chartFire') chartObj = chartFireMain;
  else if (chartId === 'chartReport') chartObj = chartReport;
  else if (chartId === 'chartConcernLocation') chartObj = chartConcernLocation;
  
  if (!chartObj) {
    alert('Chart data not initialized.');
    return;
  }
  
  // Convert chart to image
  const chartImage = chartElem.toDataURL('image/png');
  const conclusion = generateChartConclusion(chartId, chartObj);
  
  // Generate timestamp
  const now = new Date();
  const timestamp = now.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: '2-digit' }) + 
                    ' ' + now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  
  // Open print window
  const w = window.open('', '_blank');
  if (!w) {
    alert('Please allow popups to print the chart.');
    return;
  }
  
  w.document.write(`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escHtml(title)}</title>
  <style>
    @page {
      size: A4;
      margin: 20mm;
    }
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    body {
      font-family: 'Nunito', Arial, sans-serif;
      color: #2a1f00;
      background: #fff;
      line-height: 1.6;
    }
    .print-container {
      max-width: 900px;
      margin: 0 auto;
      padding: 20px;
      background: #fff;
    }
    .print-header {
      text-align: center;
      margin-bottom: 24px;
      border-bottom: 3px solid #E3AB00;
      padding-bottom: 12px;
    }
    .print-header h1 {
      font-size: 24px;
      font-weight: 900;
      color: #2a1f00;
      margin-bottom: 6px;
      text-transform: uppercase;
      letter-spacing: 1px;
    }
    .print-header .brand {
      font-size: 14px;
      font-weight: 700;
      color: #7a6010;
      margin-bottom: 2px;
    }
    .print-header .timestamp {
      font-size: 12px;
      color: #999;
      margin-top: 8px;
    }
    .chart-section {
      margin: 24px 0;
      text-align: center;
    }
    .chart-section img {
      max-width: 100%;
      height: auto;
      border: 1px solid #e0e0e0;
      border-radius: 4px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      margin: 12px 0;
    }
    .conclusion-section {
      margin: 20px 0;
      page-break-inside: avoid;
    }
    .conclusion-box {
      background: #fffbf0;
      border-left: 4px solid #E3AB00;
      padding: 12px 14px;
      border-radius: 4px;
      font-size: 14px;
      line-height: 1.6;
    }
    .print-footer {
      margin-top: 32px;
      padding-top: 12px;
      border-top: 1px solid #ddd;
      font-size: 12px;
      color: #999;
      text-align: center;
    }
    @media print {
      body {
        background: #fff;
      }
      .print-container {
        padding: 0;
      }
    }
  </style>
</head>
<body>
  <div class="print-container">
    <div class="print-header">
      <div class="brand">HAZARD HUB • Safety Management System</div>
      <h1>${escHtml(title)}</h1>
      <div class="timestamp">Generated: ${timestamp}</div>
    </div>
    
    <div class="chart-section">
      <img src="${chartImage}" alt="${escHtml(title)}">
    </div>
    
    <div class="conclusion-section">
      <div class="conclusion-box">
        ${conclusion}
      </div>
    </div>
    
    <div class="print-footer">
      <p>This is an automatically generated report from Hazard Hub Safety Management System.</p>
      <p style="margin-top: 8px;">For more information or assistance, please contact your Safety Officer.</p>
    </div>
  </div>
  
  <script>
    window.onload = function() {
      setTimeout(function() {
        window.print();
      }, 500);
    };
  <\/script>
</body>
</html>`);
  w.document.close();
}

/* ═══ REAL-TIME NOTIFICATION SYSTEM ═══ */

let _lastNotifId = 0;
let _notifPollId = null;

function openNotifPanel() {
  const panel = document.getElementById('notifPanel');
  if (panel) {
    panel.classList.toggle('open');
    loadNotifications();
  }
}

function closeNotifPanel(e) {
  if (e && e.target.id !== 'notifPanel') return;
  const panel = document.getElementById('notifPanel');
  if (panel) panel.classList.remove('open');
}

async function loadNotifications() {
  try {
    const res = await fetch(`${API}/notifications`);
    const data = await res.json();
    renderNotifications(data.notifications || []);
  } catch (e) {
    console.error('Failed to load notifications:', e);
  }
}

function renderNotifications(notifs) {
  const body = document.getElementById('notifPanelBody');
  if (!notifs || notifs.length === 0) {
    body.innerHTML = '<div class="notif-empty">No notifications</div>';
    return;
  }
  
  body.innerHTML = notifs.slice(0, 15).map(n => {
    const severity = (n.severity || 'low').toLowerCase();
    const badgeClass = severity === 'high' ? 'notif-badge-high' : 
                       severity === 'medium' ? 'notif-badge-medium' : 'notif-badge-low';
    const badgeText = severity.toUpperCase();
    const timeAgo = getTimeAgo(n.date);
    
    return `<div class="notif-item">
      <div class="notif-item-message">${escHtml(n.message || '—')}</div>
      <div class="notif-item-details">
        <span class="${badgeClass}">${badgeText}</span>
        <span>•</span>
        <span>${timeAgo}</span>
        ${n.location ? `<span>•</span><span>${escHtml(n.location)}</span>` : ''}
      </div>
    </div>`;
  }).join('');
}

async function pollNotifications() {
  try {
    const res = await fetch(`${API}/notifications`);
    const data = await res.json();
    const notifs = data.notifications || [];
    
    if (notifs.length === 0) {
      const dot = document.getElementById('notifBellDot');
      if (dot) dot.classList.remove('has-notif');
      return;
    }
    
    // Check for new notifications
    const latestNotif = notifs[0];
    const latestId = latestNotif.id || 0;
    
    if (latestId > _lastNotifId) {
      _lastNotifId = latestId;
      
      // Show badge
      const dot = document.getElementById('notifBellDot');
      if (dot) dot.classList.add('has-notif');
      
      // Show toast notification
      showNotificationToast(latestNotif);
    }
  } catch (e) {
    console.error('Notification polling failed:', e);
  }
}

function showNotificationToast(notif) {
  const severity = (notif.severity || 'low').toLowerCase();
  const container = document.body;
  
  const toast = document.createElement('div');
  toast.className = `notif-toast ${severity}`;
  toast.innerHTML = `
    <div class="notif-toast-title">New ${severity.toUpperCase()} Priority Report</div>
    <div class="notif-toast-message">${escHtml(notif.message || 'New report submitted')}</div>
  `;
  
  container.appendChild(toast);
  
  // Auto-remove toast after 6 seconds
  setTimeout(() => {
    toast.style.animation = 'slideInRight .3s ease reverse';
    setTimeout(() => toast.remove(), 300);
  }, 6000);
}

function getTimeAgo(dateStr) {
  if (!dateStr) return 'just now';
  
  try {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch (e) {
    return 'recently';
  }
}

// Start notification polling on page load
document.addEventListener('DOMContentLoaded', function() {
  setTimeout(() => {
    pollNotifications();
    setInterval(pollNotifications, 15000); // Poll every 15 seconds
  }, 1000);
});
