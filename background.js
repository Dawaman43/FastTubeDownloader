// FastTube Downloader - Background Service Worker (MV3)
// Fixes: Extension persistence, progress tracking, native messaging reliability

let nativePort = null;
let downloads = {};
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

// Keep service worker alive with periodic alarm
chrome.runtime.onInstalled.addListener(() => {
  console.log('FastTube Downloader installed/updated');

  // Create periodic alarm to keep service worker alive
  chrome.alarms.create('keepAlive', { periodInMinutes: 1 });

  // Initialize storage
  chrome.storage.local.get(['downloads'], (data) => {
    if (data.downloads) {
      downloads = data.downloads;
    }
  });
});

// Keep-alive alarm handler (prevents extension from being disabled)
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'keepAlive') {
    // Ping to keep service worker active
    console.log('Keep-alive ping:', new Date().toISOString());

    // Clean up old completed downloads
    cleanupOldDownloads();

    // Check native host connection health
    checkNativeHostHealth();
  }
});

// Startup: restore state and establish native connection
chrome.runtime.onStartup.addListener(() => {
  console.log('Browser started, restoring FastTube state');
  chrome.storage.local.get(['downloads'], (data) => {
    if (data.downloads) {
      downloads = data.downloads;
    }
  });
});

// Handle messages from content scripts and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Received message:', request.action);

  // Probe video formats
  if (request.action === 'probeFormats') {
    const msg = { action: 'probe', url: request.url };
    chrome.runtime.sendNativeMessage('com.fasttube.downloader', msg, (resp) => {
      if (chrome.runtime.lastError) {
        console.error('Native messaging error:', chrome.runtime.lastError);
        sendResponse({ status: 'error', error: chrome.runtime.lastError.message });
      } else {
        sendResponse(resp || { status: 'error' });
      }
    });
    return true; // Keep channel open for async response
  }

  // Enqueue download
  if (request.action === 'download') {
    handleDownloadRequest(request, sendResponse);
    return true;
  }

  // Get current downloads
  if (request.action === 'getDownloads') {
    sendResponse(downloads);
    return false;
  }

  // Download control (pause, resume, cancel)
  if (request.action === 'downloadControl') {
    handleDownloadControl(request.control, request.id);
    sendResponse({ status: 'ok' });
    return false;
  }
});

// Handle download request from content script
function handleDownloadRequest(request, sendResponse) {
  const downloadId = Date.now().toString();

  // Create download entry
  downloads[downloadId] = {
    id: downloadId,
    url: request.url,
    title: request.title || 'Unknown',
    progress: 0,
    status: 'queued',
    speed: 0,
    downloaded: 0,
    total: 0,
    eta: 0,
    timestamp: Date.now()
  };

  // Persist to storage
  saveDownloads();

  // Notify popup of new download
  broadcastProgress(downloadId, downloads[downloadId]);

  // Ensure native port is connected
  ensureNativeConnection();

  // Get user preferences
  chrome.storage.sync.get(['format', 'quality', 'subs'], (prefs) => {
    const message = {
      action: 'enqueue',
      url: request.url,
      title: request.title,
      formatId: request.formatId || '',
      format: request.format || prefs.format || 'Best Video + Audio',
      quality: request.formatId ? '' : (request.quality || prefs.quality || ''),
      subs: (request.subs !== undefined ? request.subs : (prefs.subs !== undefined ? prefs.subs : true)) ? 'y' : 'n',
      confirm: false,
      show: true,
      requestId: downloadId
    };

    // Send to native host
    sendToNativeHost(message, downloadId);

    // Show notification
    chrome.storage.sync.get(['notifications'], (data) => {
      if (data.notifications !== false) {
        showNotification('Download Started', `Downloading: ${request.title}`, downloadId);
      }
    });

    sendResponse({ status: 'queued', id: downloadId });
  });
}

// Handle download control actions
function handleDownloadControl(control, id) {
  console.log(`Download control: ${control} for ${id}`);

  if (control === 'cancel') {
    // Remove from active downloads
    if (downloads[id]) {
      downloads[id].status = 'cancelled';

      // Send cancel message to native host
      sendToNativeHost({
        action: 'cancel',
        requestId: id
      });

      // Remove after a delay
      setTimeout(() => {
        delete downloads[id];
        saveDownloads();
        broadcastProgress(id, null);
      }, 1000);
    }
  } else if (control === 'pause') {
    if (downloads[id]) {
      downloads[id].status = 'paused';
      sendToNativeHost({
        action: 'pause',
        requestId: id
      });
      broadcastProgress(id, downloads[id]);
    }
  } else if (control === 'resume') {
    if (downloads[id]) {
      downloads[id].status = 'downloading';
      sendToNativeHost({
        action: 'resume',
        requestId: id
      });
      broadcastProgress(id, downloads[id]);
    }
  } else if (control === 'open') {
    // Request native host to open the file
    sendToNativeHost({
      action: 'openFile',
      requestId: id
    });
  }

  saveDownloads();
}

// Ensure native messaging connection is established
function ensureNativeConnection() {
  if (nativePort && !nativePort.disconnected) {
    return nativePort;
  }

  try {
    console.log('Connecting to native host...');
    nativePort = chrome.runtime.connectNative('com.fasttube.downloader');
    reconnectAttempts = 0;

    nativePort.onMessage.addListener(handleNativeMessage);

    nativePort.onDisconnect.addListener(() => {
      const error = chrome.runtime.lastError?.message || 'Unknown error';
      console.error('Native host disconnected:', error);
      nativePort = null;

      // Broadcast error to popup
      chrome.runtime.sendMessage({
        action: 'nativeError',
        message: error
      }).catch(() => { }); // Ignore if popup not open

      // Attempt reconnection
      attemptReconnect();
    });

    console.log('Native host connected');
  } catch (e) {
    console.error('Failed to connect to native host:', e);
    nativePort = null;

    chrome.runtime.sendMessage({
      action: 'nativeError',
      message: e.message || 'Failed to connect to native app'
    }).catch(() => { });
  }

  return nativePort;
}

// Attempt to reconnect to native host
function attemptReconnect() {
  if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
    console.error('Max reconnection attempts reached');
    return;
  }

  reconnectAttempts++;
  const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000); // Exponential backoff

  console.log(`Attempting reconnect in ${delay}ms (attempt ${reconnectAttempts})`);

  setTimeout(() => {
    ensureNativeConnection();
  }, delay);
}

// Send message to native host
function sendToNativeHost(message, downloadId = null) {
  const port = ensureNativeConnection();

  if (!port) {
    console.error('No native connection available');

    // Try sendNativeMessage as fallback
    chrome.runtime.sendNativeMessage('com.fasttube.downloader', message, (resp) => {
      if (chrome.runtime.lastError) {
        console.error('Native message error:', chrome.runtime.lastError);

        if (downloadId && downloads[downloadId]) {
          downloads[downloadId].status = 'error';
          downloads[downloadId].error = 'Cannot connect to native app';
          broadcastProgress(downloadId, downloads[downloadId]);
        }
      } else if (resp && downloadId) {
        handleNativeMessage(resp);
      }
    });

    return;
  }

  try {
    port.postMessage(message);
    console.log('Sent message to native host:', message.action);
  } catch (e) {
    console.error('Failed to send message:', e);

    if (downloadId && downloads[downloadId]) {
      downloads[downloadId].status = 'error';
      downloads[downloadId].error = e.message;
      broadcastProgress(downloadId, downloads[downloadId]);
    }
  }
}

// Handle messages from native host
function handleNativeMessage(message) {
  console.log('Native message received:', message);

  try {
    const rid = message.requestId;

    if (!rid) {
      // Try to match by URL
      if (message.url) {
        const matchId = Object.keys(downloads).find(id => downloads[id].url === message.url);
        if (matchId) {
          return handleNativeMessage({ ...message, requestId: matchId });
        }
      }
      console.warn('No requestId in native message');
      return;
    }

    if (!downloads[rid]) {
      console.warn('Unknown download ID:', rid);
      return;
    }

    // Update download status based on message
    if (message.status === 'progress' || message.status === 'downloading') {
      downloads[rid].progress = Math.max(0, Math.min(100, Math.round(message.percent || message.progress || 0)));
      downloads[rid].status = 'downloading';
      downloads[rid].speed = message.speed || message.downloadSpeed || 0;
      downloads[rid].downloaded = message.downloaded || message.downloadedBytes || 0;
      downloads[rid].total = message.total || message.totalBytes || message.fileSize || 0;
      downloads[rid].eta = message.eta || message.timeRemaining || 0;
    } else if (message.status === 'finished' || message.status === 'completed') {
      downloads[rid].status = 'finished';
      downloads[rid].progress = 100;
      downloads[rid].fileSize = message.fileSize || downloads[rid].total;
      downloads[rid].filePath = message.filePath || message.path;

      // Show completion notification
      chrome.storage.sync.get(['notifications'], (data) => {
        if (data.notifications !== false) {
          showNotification(
            'Download Complete',
            `${downloads[rid].title}`,
            rid,
            true
          );
        }
      });

      // Remove from active downloads after 5 seconds
      setTimeout(() => {
        delete downloads[rid];
        saveDownloads();
      }, 5000);

    } else if (message.status === 'error' || message.status === 'failed') {
      downloads[rid].status = 'error';
      downloads[rid].error = message.error || message.message || 'Download failed';

      // Show error notification
      showNotification(
        'Download Failed',
        `${downloads[rid].title}: ${downloads[rid].error}`,
        rid
      );

      // Remove from active downloads after 10 seconds
      setTimeout(() => {
        delete downloads[rid];
        saveDownloads();
      }, 10000);
    }

    // Broadcast update to popup
    broadcastProgress(rid, downloads[rid]);

    // Save state
    saveDownloads();

  } catch (e) {
    console.error('Error handling native message:', e);
  }
}

// Broadcast progress update to all extension pages
function broadcastProgress(id, data) {
  chrome.runtime.sendMessage({
    action: 'progress',
    id: id,
    data: data
  }).catch(() => {
    // Popup may not be open, that's fine
  });
}

// Save downloads to storage
function saveDownloads() {
  chrome.storage.local.set({ downloads: downloads });
}

// Clean up old completed/failed downloads
function cleanupOldDownloads() {
  const now = Date.now();
  const maxAge = 60 * 60 * 1000; // 1 hour

  let cleaned = false;

  Object.keys(downloads).forEach(id => {
    const dl = downloads[id];
    const age = now - (dl.timestamp || 0);

    if (age > maxAge && (dl.status === 'finished' || dl.status === 'error' || dl.status === 'cancelled')) {
      delete downloads[id];
      cleaned = true;
    }
  });

  if (cleaned) {
    saveDownloads();
  }
}

// Check native host health
function checkNativeHostHealth() {
  if (Object.keys(downloads).length > 0 && (!nativePort || nativePort.disconnected)) {
    console.log('Active downloads but no native connection, attempting reconnect...');
    ensureNativeConnection();
  }
}

// Show browser notification
function showNotification(title, message, id, requireInteraction = false) {
  chrome.notifications.create(id || `notif-${Date.now()}`, {
    type: 'basic',
    iconUrl: 'icon128.png',
    title: title,
    message: message,
    priority: 2,
    requireInteraction: requireInteraction
  });

  // Play sound if enabled
  chrome.storage.sync.get(['sounds'], (data) => {
    if (data.sounds) {
      // Browser will play default notification sound
    }
  });
}

// Update badge with download count
function updateBadge() {
  const activeCount = Object.values(downloads).filter(
    dl => dl.status === 'downloading' || dl.status === 'queued'
  ).length;

  if (activeCount > 0) {
    chrome.action.setBadgeText({ text: activeCount.toString() });
    chrome.action.setBadgeBackgroundColor({ color: '#0d6efd' });
  } else {
    chrome.action.setBadgeText({ text: '' });
  }
}

// Update badge periodically
setInterval(updateBadge, 2000);

console.log('FastTube Downloader background script loaded');