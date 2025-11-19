// FastTube Downloader - Popup Script with IDM-style Features
// This fixes the progress display issue and adds comprehensive download management

let downloads = {};
let history = [];
let settings = {
  notifications: true,
  autostart: true,
  sounds: false,
  maxDownloads: 3,
  defaultFormat: 'Best Video + Audio',
  defaultQuality: '',
  subtitles: true
};

// Initialize popup
document.addEventListener('DOMContentLoaded', () => {
  loadSettings();
  loadHistory();
  setupTabs();
  setupSettings();
  setupEventListeners();
  requestDownloads();

  // Poll for updates every second
  setInterval(requestDownloads, 1000);
});

// Load settings from storage
function loadSettings() {
  chrome.storage.sync.get([
    'notifications', 'autostart', 'sounds', 'maxDownloads',
    'format', 'quality', 'subs'
  ], (data) => {
    if (data.notifications !== undefined) settings.notifications = data.notifications;
    if (data.autostart !== undefined) settings.autostart = data.autostart;
    if (data.sounds !== undefined) settings.sounds = data.sounds;
    if (data.maxDownloads) settings.maxDownloads = data.maxDownloads;
    if (data.format) settings.defaultFormat = data.format;
    if (data.quality) settings.defaultQuality = data.quality;
    if (data.subs !== undefined) settings.subtitles = data.subs;

    updateSettingsUI();
  });
}

// Load download history
function loadHistory() {
  chrome.storage.local.get(['downloadHistory'], (data) => {
    if (data.downloadHistory) {
      history = data.downloadHistory;
      renderHistory();
    }
  });
}

// Save download to history
function saveToHistory(download) {
  const historyItem = {
    id: download.id || Date.now().toString(),
    title: download.title,
    url: download.url,
    status: download.status,
    timestamp: Date.now(),
    fileSize: download.fileSize || 'Unknown'
  };

  history.unshift(historyItem);

  // Keep only last 100 items
  if (history.length > 100) {
    history = history.slice(0, 100);
  }

  chrome.storage.local.set({ downloadHistory: history });
  renderHistory();
}

// Setup tab switching
function setupTabs() {
  const tabs = document.querySelectorAll('.tab');
  const tabContents = document.querySelectorAll('.tab-content');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetTab = tab.dataset.tab;

      // Remove active class from all tabs and contents
      tabs.forEach(t => t.classList.remove('active'));
      tabContents.forEach(tc => tc.classList.remove('active'));

      // Add active class to clicked tab and corresponding content
      tab.classList.add('active');
      document.getElementById(`${targetTab}-tab`).classList.add('active');
    });
  });
}

// Setup settings UI and event listeners
function setupSettings() {
  // Toggle switches
  const toggles = {
    'toggle-notifications': 'notifications',
    'toggle-autostart': 'autostart',
    'toggle-sounds': 'sounds',
    'toggle-subtitles': 'subtitles'
  };

  Object.entries(toggles).forEach(([id, setting]) => {
    const toggle = document.getElementById(id);
    if (toggle) {
      toggle.addEventListener('click', () => {
        settings[setting] = !settings[setting];
        toggle.classList.toggle('active');
        saveSettings();
      });
    }
  });

  // Select controls
  document.getElementById('max-downloads')?.addEventListener('change', (e) => {
    settings.maxDownloads = parseInt(e.target.value);
    saveSettings();
  });

  document.getElementById('default-format')?.addEventListener('change', (e) => {
    settings.defaultFormat = e.target.value;
    saveSettings();
  });

  document.getElementById('default-quality')?.addEventListener('change', (e) => {
    settings.defaultQuality = e.target.value;
    saveSettings();
  });

  // Clear history button
  document.getElementById('clear-history')?.addEventListener('click', () => {
    if (confirm('Are you sure you want to clear download history?')) {
      history = [];
      chrome.storage.local.set({ downloadHistory: [] });
      renderHistory();
    }
  });
}

// Update settings UI to match current settings
function updateSettingsUI() {
  // Update toggles
  document.getElementById('toggle-notifications')?.classList.toggle('active', settings.notifications);
  document.getElementById('toggle-autostart')?.classList.toggle('active', settings.autostart);
  document.getElementById('toggle-sounds')?.classList.toggle('active', settings.sounds);
  document.getElementById('toggle-subtitles')?.classList.toggle('active', settings.subtitles);

  // Update selects
  const maxDownloadsEl = document.getElementById('max-downloads');
  if (maxDownloadsEl) maxDownloadsEl.value = settings.maxDownloads.toString();

  const formatEl = document.getElementById('default-format');
  if (formatEl) formatEl.value = settings.defaultFormat;

  const qualityEl = document.getElementById('default-quality');
  if (qualityEl) qualityEl.value = settings.defaultQuality;
}

// Save settings to storage
function saveSettings() {
  chrome.storage.sync.set({
    notifications: settings.notifications,
    autostart: settings.autostart,
    sounds: settings.sounds,
    maxDownloads: settings.maxDownloads,
    format: settings.defaultFormat,
    quality: settings.defaultQuality,
    subs: settings.subtitles
  });
}

// Setup other event listeners
function setupEventListeners() {
  // Refresh button
  document.getElementById('refresh-btn')?.addEventListener('click', () => {
    requestDownloads();
    loadHistory();
  });

  // Settings button (switch to settings tab)
  document.getElementById('settings-btn')?.addEventListener('click', () => {
    document.querySelector('.tab[data-tab="settings"]')?.click();
  });

  // History search
  document.getElementById('history-search')?.addEventListener('input', (e) => {
    renderHistory(e.target.value);
  });
}

// Request download data from background script
function requestDownloads() {
  chrome.runtime.sendMessage({ action: 'getDownloads' }, (response) => {
    if (response) {
      downloads = response;
      renderDownloads();
    }
  });
}

// Listen for progress updates from background
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'progress') {
    if (request.id && request.data) {
      downloads[request.id] = request.data;
      renderDownloads();

      // Save to history when completed
      if (request.data.status === 'finished' || request.data.status === 'completed') {
        saveToHistory(request.data);
      }
    }
  }

  if (request.action === 'nativeError') {
    showNativeError(request.message);
  }
});

// Render downloads in Active tab
function renderDownloads() {
  const container = document.getElementById('active-downloads');
  const downloadArray = Object.entries(downloads);

  // Update badge count
  const badge = document.getElementById('active-count');
  if (badge) badge.textContent = downloadArray.length;

  if (downloadArray.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📥</div>
        <div class="empty-state-text">No active downloads</div>
        <div class="empty-state-subtext">Navigate to a YouTube video and click the download button</div>
      </div>
    `;
    return;
  }

  container.innerHTML = '';

  downloadArray.forEach(([id, dl]) => {
    const item = createDownloadItem(id, dl);
    container.appendChild(item);
  });
}

// Create a download item element
function createDownloadItem(id, dl) {
  const item = document.createElement('div');
  item.className = 'download-item';
  item.dataset.id = id;

  const title = dl.title || 'Unknown';
  const status = dl.status || 'queued';
  const progress = Math.max(0, Math.min(100, Math.round(dl.progress || 0)));

  // Calculate stats
  const speed = formatSpeed(dl.speed || 0);
  const downloaded = formatBytes(dl.downloaded || 0);
  const total = formatBytes(dl.total || dl.fileSize || 0);
  const eta = formatETA(dl.eta || dl.timeRemaining || 0);

  const statusClass = {
    'queued': 'queued',
    'downloading': 'downloading',
    'progress': 'downloading',
    'paused': 'paused',
    'finished': 'completed',
    'completed': 'completed',
    'error': 'error'
  }[status] || 'queued';

  const statusText = {
    'queued': 'Queued',
    'downloading': 'Downloading',
    'progress': 'Downloading',
    'paused': 'Paused',
    'finished': 'Completed',
    'completed': 'Completed',
    'error': 'Error'
  }[status] || 'Unknown';

  // Show progress bar for downloading/queued/paused
  const showProgress = ['queued', 'downloading', 'progress', 'paused'].includes(status);
  const showStats = status === 'downloading' || status === 'progress';

  item.innerHTML = `
    <div class="download-header">
      <div class="download-title" title="${escapeHtml(title)}">${escapeHtml(title)}</div>
      <div class="download-status ${statusClass}">${statusText}</div>
    </div>
    
    ${showProgress ? `
      <div class="progress-container">
        <div class="progress-bar-wrapper">
          <div class="progress-bar ${status === 'downloading' || status === 'progress' ? 'active' : ''}" style="width: ${progress}%"></div>
        </div>
        <div class="progress-text">
          <span>${progress}%</span>
          <span>${downloaded}${total && total !== '0 B' ? ' / ' + total : ''}</span>
        </div>
      </div>
    ` : ''}
    
    ${showStats ? `
      <div class="download-stats">
        <div class="stat-item">
          <div class="stat-label">Speed</div>
          <div class="stat-value">${speed}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">ETA</div>
          <div class="stat-value">${eta}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">Size</div>
          <div class="stat-value">${total || 'Unknown'}</div>
        </div>
      </div>
    ` : ''}
    
    ${status === 'error' ? `
      <div style="color: var(--idm-danger); font-size: 11px; margin-bottom: 10px;">
        ${escapeHtml(dl.error || dl.message || 'Download failed')}
      </div>
    ` : ''}
    
    <div class="download-actions">
      ${status === 'downloading' || status === 'progress' ? `
        <button class="action-btn" data-action="pause" data-id="${id}">⏸ Pause</button>
      ` : ''}
      ${status === 'paused' ? `
        <button class="action-btn primary" data-action="resume" data-id="${id}">▶ Resume</button>
      ` : ''}
      ${status === 'finished' || status === 'completed' ? `
        <button class="action-btn success" data-action="open" data-id="${id}">📂 Open</button>
      ` : ''}
      <button class="action-btn danger" data-action="cancel" data-id="${id}">✕ ${status === 'finished' || status === 'completed' ? 'Remove' : 'Cancel'}</button>
    </div>
  `;

  // Add event listeners for action buttons
  item.querySelectorAll('.action-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const action = btn.dataset.action;
      const downloadId = btn.dataset.id;
      handleDownloadAction(action, downloadId);
    });
  });

  return item;
}

// Handle download actions (pause, resume, cancel, open)
function handleDownloadAction(action, id) {
  chrome.runtime.sendMessage({
    action: 'downloadControl',
    control: action,
    id: id
  });

  if (action === 'cancel') {
    delete downloads[id];
    renderDownloads();
  }
}

// Render history
function renderHistory(searchTerm = '') {
  const container = document.getElementById('history-list');

  if (!history || history.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📜</div>
        <div class="empty-state-text">No download history</div>
        <div class="empty-state-subtext">Your completed downloads will appear here</div>
      </div>
    `;
    return;
  }

  // Filter history by search term
  let filtered = history;
  if (searchTerm) {
    const term = searchTerm.toLowerCase();
    filtered = history.filter(item =>
      item.title?.toLowerCase().includes(term) ||
      item.url?.toLowerCase().includes(term)
    );
  }

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">🔍</div>
        <div class="empty-state-text">No results found</div>
        <div class="empty-state-subtext">Try a different search term</div>
      </div>
    `;
    return;
  }

  container.innerHTML = '';

  filtered.forEach(item => {
    const el = document.createElement('div');
    el.className = 'download-item';

    const date = new Date(item.timestamp);
    const dateStr = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();

    const statusClass = item.status === 'finished' || item.status === 'completed' ? 'completed' : 'error';
    const statusText = item.status === 'finished' || item.status === 'completed' ? 'Completed' : 'Failed';

    el.innerHTML = `
      <div class="download-header">
        <div class="download-title" title="${escapeHtml(item.title)}">${escapeHtml(item.title)}</div>
        <div class="download-status ${statusClass}">${statusText}</div>
      </div>
      <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--text-secondary); margin-top: 6px;">
        <span>📅 ${dateStr}</span>
        <span>💾 ${item.fileSize || 'Unknown'}</span>
      </div>
    `;

    container.appendChild(el);
  });
}

// Show native host error
function showNativeError(message) {
  const container = document.getElementById('native-error-container');
  container.innerHTML = `
    <div class="native-error">
      <div class="native-error-title">⚠ Native Host Connection Error</div>
      <div class="native-error-message">${escapeHtml(message || 'Cannot connect to native app. Please ensure the desktop application is running.')}</div>
    </div>
  `;

  // Auto-hide after 10 seconds
  setTimeout(() => {
    container.innerHTML = '';
  }, 10000);
}

// Utility functions
function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function formatSpeed(bytesPerSecond) {
  if (!bytesPerSecond || bytesPerSecond === 0) return '0 B/s';
  return formatBytes(bytesPerSecond) + '/s';
}

function formatETA(seconds) {
  if (!seconds || seconds === 0 || seconds === Infinity) return '--:--';

  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);

  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}