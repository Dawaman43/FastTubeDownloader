let nativePort = null;
let downloads = {};

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'probeFormats') {
    const msg = { action: 'probe', url: request.url };
    chrome.runtime.sendNativeMessage('com.fasttube.downloader', msg, (resp) => {
      sendResponse(resp || { status: 'error' });
    });
    return true;
  }
  if (request.action === 'download') {
    const downloadId = Date.now().toString();
    downloads[downloadId] = { url: request.url, title: request.title || 'Unknown', progress: 0, status: 'queued' };

    if (!nativePort || nativePort.disconnected) {
      try {
        nativePort = chrome.runtime.connectNative('com.fasttube.downloader');
      } catch (e) {
        nativePort = null;
      }
      if (nativePort) {
        nativePort.onMessage.addListener((message) => {
          try {
            const rid = message.requestId;
            if (rid && downloads[rid]) {
              // Update by requestId mapping
              if (message.status === 'progress') {
                downloads[rid].progress = Math.max(0, Math.min(100, Math.round(message.percent || 0)));
                downloads[rid].status = 'downloading';
              } else if (message.status === 'finished' || message.status === 'error') {
                downloads[rid].status = message.status;
                setTimeout(() => delete downloads[rid], 5000);
              }
              chrome.runtime.sendMessage({ action: 'progress', id: rid, data: message });
              return;
            }
            // Fallback: try to match by URL
            if (message.url) {
              const matchId = Object.keys(downloads).find(id => downloads[id].url === message.url);
              if (matchId) {
                if (message.status === 'progress') {
                  downloads[matchId].progress = Math.max(0, Math.min(100, Math.round(message.percent || 0)));
                  downloads[matchId].status = 'downloading';
                } else if (message.status === 'finished' || message.status === 'error') {
                  downloads[matchId].status = message.status;
                  setTimeout(() => delete downloads[matchId], 5000);
                }
                chrome.runtime.sendMessage({ action: 'progress', id: matchId, data: message });
              }
            }
          } catch (e) {}
        });
        nativePort.onDisconnect.addListener(() => {
          const lastError = chrome.runtime.lastError?.message || '';
          nativePort = null;
        });
      }
    }

    // Merge options with storage defaults
    chrome.storage.sync.get(['format', 'quality', 'subs'], (prefs) => {
      const message = {
        url: request.url,
        title: request.title,
        format: request.formatId || request.format || prefs.format || 'Best Video + Audio',
        quality: request.formatId ? '' : (request.quality || prefs.quality || ''),
        subs: (request.subs !== undefined ? request.subs : (prefs.subs !== undefined ? prefs.subs : true)) ? 'y' : 'n',
        confirm: false,
        show: true,
        requestId: downloadId
      };
      const postOrFallback = () => {
        if (nativePort) {
          try {
            nativePort.postMessage(message);
            return;
          } catch (e) {
          }
        }
        chrome.runtime.sendNativeMessage('com.fasttube.downloader', message, (resp) => {
          if (chrome.runtime.lastError) {
            const msg = chrome.runtime.lastError.message || 'Unknown native messaging error';
            chrome.runtime.sendMessage({ action: 'nativeError', message: msg });
          }
        });
      };
      postOrFallback();
      chrome.runtime.sendMessage({ action: 'progress', id: downloadId, data: downloads[downloadId] });
      sendResponse({ status: 'queued', id: downloadId });
    });

    return true;
  }
  if (request.action === 'getDownloads') {
    sendResponse(downloads);
  }
});

function handleNativeMessage(message, downloadId) {
  if (message.status === 'progress') {
    downloads[downloadId].progress = message.percent || 0;
    downloads[downloadId].status = 'downloading';
    chrome.runtime.sendMessage({action: 'progress', id: downloadId, data: message});
  } else if (message.status === 'finished' || message.status === 'error') {
    downloads[downloadId].status = message.status;
    setTimeout(() => delete downloads[downloadId], 5000);
  }
}