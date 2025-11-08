document.addEventListener('DOMContentLoaded', () => {
  const popupBody = document.querySelector('body');
  const settingsDiv = document.createElement('div');
  settingsDiv.innerHTML = `
    <label>Format: <select id="format">
      <option>Best Video + Audio</option>
      <option>Audio Only</option>
      <option>Best (default)</option>
    </select></label>
    <label>Quality: <input id="quality" placeholder="1080" /></label>
    <label><input type="checkbox" id="subs" checked> Subtitles</label>
  `;
  settingsDiv.style.cssText = 'margin-bottom: 10px; font-size: 12px;';
  popupBody.insertBefore(settingsDiv, document.querySelector('h3'));

  const savePrefs = () => {
    chrome.storage.sync.set({
      format: document.getElementById('format').value,
      quality: document.getElementById('quality').value,
      subs: document.getElementById('subs').checked
    });
  };
  document.getElementById('format').addEventListener('change', savePrefs);
  document.getElementById('quality').addEventListener('input', savePrefs);
  document.getElementById('subs').addEventListener('change', savePrefs);

  chrome.storage.sync.get(['format', 'quality', 'subs'], (data) => {
    if (data.format) document.getElementById('format').value = data.format;
    if (data.quality) document.getElementById('quality').value = data.quality;
    if (data.subs !== undefined) document.getElementById('subs').checked = data.subs;
  });
});