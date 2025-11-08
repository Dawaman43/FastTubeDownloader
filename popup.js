let downloads = {};

chrome.runtime.onMessage.addListener((request, sender, tab) => {
  if (request.action === 'progress') {
    downloads[request.id] = request.data;
    renderDownloads();
  }
});

function renderDownloads() {
  const list = document.getElementById('downloads-list');
  list.innerHTML = '';
  Object.entries(downloads).forEach(([id, dl]) => {
    const div = document.createElement('div');
    div.className = 'download';
    div.innerHTML = `
      <strong>${dl.title || 'Unknown'}</strong><br>
      <progress value="${dl.progress || 0}" max="100"></progress> ${dl.progress || 0}%
      <br><small>${dl.status}</small>
    `;
    list.appendChild(div);
  });
  if (Object.keys(downloads).length === 0) {
    list.innerHTML = '<p>No active downloads</p>';
  }
}

chrome.runtime.sendMessage({action: 'getDownloads'}, (data) => {
  downloads = data;
  renderDownloads();
});
chrome.runtime.onMessage.addListener((request) => {
  if (request.action === 'nativeError') {
    const list = document.getElementById('downloads-list');
    const warn = document.createElement('div');
    warn.className = 'download';
    warn.style.borderColor = '#e67e22';
    warn.innerHTML = `<strong>Native host error</strong><br><small>${request.message || 'Check setup.sh and extension ID.'}</small>`;
    list.prepend(warn);
  }
});