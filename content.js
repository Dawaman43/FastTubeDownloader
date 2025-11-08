(function() {
  const BTN_ID = 'fasttube-overlay-btn';
  const PANEL_ID = 'fasttube-panel';
  const STYLE_ID = 'fasttube-style';
  let lastHref = location.href;
  function hasChrome() { try { return typeof chrome !== 'undefined' && !!chrome; } catch(e) { return false; } }

  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    const s = document.createElement('style');
    s.id = STYLE_ID;
    let iconURL = '';
    try { iconURL = chrome.runtime?.getURL?.('icon48.png') || ''; } catch(e) { iconURL = ''; }
    const bg = iconURL ? `linear-gradient(135deg,#e41616,#a50707) url(${iconURL}) center/24px 24px no-repeat` : 'linear-gradient(135deg,#e41616,#a50707)';
    s.textContent = `
  #${BTN_ID} { position: absolute; top: 8px; right: 8px; z-index: 2147483647; width: 44px; height: 44px; border-radius: 12px; background: ${bg} !important; background-color:#cf1515 !important; cursor: pointer; border: 1px solid #7a0b0b; box-shadow: 0 8px 22px rgba(0,0,0,.6); transition: transform .18s ease, box-shadow .18s ease; opacity:1 !important; pointer-events:auto !important; mix-blend-mode: normal !important; filter: none !important; backdrop-filter: none !important; isolation:isolate; background-clip: padding-box; }
  #${BTN_ID}:hover { transform: scale(1.06) translateY(-2px); box-shadow: 0 10px 28px rgba(0,0,0,.6); }
  #${PANEL_ID} { position: fixed; top: 64px; right: 20px; width: 420px; max-width: calc(100% - 40px); background: #121417 !important; background-color:#121417 !important; color: #f2f5f8; z-index: 2147483647; border: 1px solid #262d33; border-radius: 14px; box-shadow: 0 16px 40px rgba(0,0,0,.65); resize: both; overflow: hidden; font-family: system-ui, Arial, sans-serif; opacity:1 !important; pointer-events:auto !important; mix-blend-mode: normal !important; filter: none !important; backdrop-filter: none !important; isolation:isolate; background-clip: padding-box; contain: paint; }
      #${PANEL_ID} * { mix-blend-mode: normal !important; filter: none !important; backdrop-filter: none !important; }
      #${PANEL_ID} .ft-header { padding: 10px 14px; background: #181d22 !important; background-color:#181d22 !important; cursor: move; user-select: none; display: flex; justify-content: space-between; align-items: center; border-top-left-radius: 14px; border-top-right-radius: 14px; font-size:13px; letter-spacing:.4px; border-bottom: 1px solid #242a30; }
      #${PANEL_ID} .ft-body { padding: 16px 14px 18px; animation: none !important; background:#121417 !important; background-color:#121417 !important; }
      #${PANEL_ID} label { display:block; margin: 8px 0 4px; font-size: 12px; font-weight:600; text-transform:uppercase; letter-spacing:.5px; opacity:1; }
      #${PANEL_ID} select, #${PANEL_ID} input[type="text"] { width: 100%; padding: 8px 10px; border-radius: 8px; border: 1px solid #2e363d; background: #161b21; color: #e8eef4; font-size:12px; transition: border-color .2s, background .2s; }
      #${PANEL_ID} select:focus, #${PANEL_ID} input[type="text"]:focus { outline:none; border-color:#3e4a55; background:#1b2229; }
      #${PANEL_ID} .ft-actions { display: flex; gap: 10px; margin-top: 14px; }
      #${PANEL_ID} .ft-btn { background: #e42e2e; color:#fff; border: 1px solid #9d2626; padding: 9px 14px; border-radius: 8px; cursor: pointer; font-size:12px; font-weight:700; letter-spacing:.5px; box-shadow: 0 6px 14px rgba(0,0,0,.45); transition: background .18s, transform .18s; }
      #${PANEL_ID} .ft-btn:hover { background: linear-gradient(180deg,#ff3d32,#c62828); transform: translateY(-2px); }
      #${PANEL_ID} .ft-btn:active { transform: translateY(0); }
      #${PANEL_ID} .ft-btn.secondary { background: #2e2e2e; box-shadow:none; }
      #${PANEL_ID} .ft-btn.secondary:hover { background:#3a3a3a; }
      #${PANEL_ID} #ft-download[disabled] { background:#444 !important; opacity:.6; cursor:default; transform:none; }
      #${PANEL_ID} .ft-format-grid { display:grid; grid-template-columns: 1fr 1fr; gap:8px; }
      #${PANEL_ID} .ft-pill { display:inline-block; padding:2px 6px; background:#222; border-radius:12px; font-size:10px; margin-left:6px; opacity:.8; }
      @keyframes ftFade { from { opacity:0; transform:translateY(6px);} to { opacity:1; transform:translateY(0);} }
    `;
    document.documentElement.appendChild(s);
  }

  function getPlayerContainer() {
    return document.getElementById('movie_player') || document.querySelector('#ytd-player #container');
  }

  function enhanceThumbnails() {
    const thumbs = document.querySelectorAll([
      'ytd-rich-item-renderer',
      'ytd-rich-grid-media',
      'ytd-video-renderer',
      'ytd-grid-video-renderer',
      'ytd-compact-video-renderer',
      'ytd-reel-video-renderer',
      'ytd-reel-item-renderer',
      'ytd-playlist-video-renderer',
      'ytd-playlist-panel-video-renderer'
    ].join(','));
    thumbs.forEach(th => {
      if (th.querySelector('.fasttube-thumb-hover')) return;

      const link = th.querySelector('a#thumbnail, ytd-thumbnail a#thumbnail, a#video-title-link, a.yt-simple-endpoint[href*="/watch?"], a[href*="/watch?"], a[href^="/shorts/"], a[href^="https://www.youtube.com/shorts/"]');
      if (!link) return;
      let raw = link.getAttribute('href') || link.href || '';
      try { raw = new URL(raw, location.origin).href; } catch(e) {}
      if (!( /watch\?v=/.test(raw) || /\/shorts\//.test(raw) )) return;

      const wrapper = th.querySelector('ytd-thumbnail') || link.closest('ytd-thumbnail') || link;
      if (!wrapper) return;
      try { if (getComputedStyle(wrapper).position === 'static') wrapper.style.position = 'relative'; } catch(e) {}

      if (wrapper.querySelector('.fasttube-thumb-hover')) return;

      const hoverBtn = document.createElement('div');
      hoverBtn.className = 'fasttube-thumb-hover';
      hoverBtn.title = 'Download';
      hoverBtn.style.cssText = 'position:absolute;right:6px;bottom:6px;width:38px;height:38px;background:#cf1515 !important;background-color:#cf1515 !important;color:#fff;font-size:18px;display:flex;align-items:center;justify-content:center;border-radius:10px;cursor:pointer;opacity:0;transition:opacity .14s,transform .14s;transform:scale(.9);z-index:2147483647;box-shadow:0 8px 20px rgba(0,0,0,.6);pointer-events:auto !important;font-weight:800;letter-spacing:.2px;border:1px solid #7a0b0b;mix-blend-mode: normal !important; filter: none !important; backdrop-filter: none !important; isolation:isolate; background-clip: padding-box;';
      hoverBtn.textContent = '↓';
      try { wrapper.appendChild(hoverBtn); } catch(e) { return; }

      wrapper.addEventListener('mouseenter', () => { hoverBtn.style.opacity = '1'; hoverBtn.style.transform='scale(1)'; hoverBtn.style.background='#cf1515'; });
      wrapper.addEventListener('mouseleave', () => { hoverBtn.style.opacity = '0'; hoverBtn.style.transform='scale(.85)'; });
      hoverBtn.addEventListener('click', (e) => {
        e.preventDefault(); e.stopPropagation();
        const titleEl = th.querySelector('#video-title') || th.querySelector('#video-title-link') || th.querySelector('h3 a');
        const title = (titleEl?.textContent || document.title || 'Unknown').trim();
        openPanel({ anchorEl: wrapper, url: raw, title });
      });
    });
  }

  function getVideoInfo() {
    const url = location.href.includes('/watch') ? location.href : document.querySelector('link[rel="canonical"]')?.href || location.href;
    const title = document.querySelector('h1 yt-formatted-string')?.textContent?.trim() || document.title.replace(/ - YouTube$/,'');
    return { url, title };
  }

  function ensureOverlay() {
    injectStyles();
    const player = getPlayerContainer();
    if (!player) return;
    if (document.getElementById(BTN_ID)) return;
    const btn = document.createElement('button');
    btn.id = BTN_ID;
    btn.title = 'Download with FastTube';
    btn.addEventListener('click', togglePanel);
    // Position within player
    player.style.position = player.style.position || 'relative';
    player.appendChild(btn);
  }

  function togglePanel() {
    const panel = document.getElementById(PANEL_ID);
    if (panel) { panel.remove(); return; }
    openPanel({});
  }

  function openPanel(opts) {
    const { url: passedUrl, title: passedTitle, anchorEl } = opts || {};
    const { url, title } = passedUrl ? { url: passedUrl, title: (passedTitle || document.title) } : getVideoInfo();
    try { const existing = document.getElementById(PANEL_ID); if (existing) existing.remove(); } catch(e) {}
    const panel = document.createElement('div');
    panel.id = PANEL_ID;
    panel.innerHTML = `
      <div class="ft-header">
        <div style="font-weight:600;">FastTube Downloader</div>
        <div>
          <button class="ft-btn secondary" id="ft-close">✕</button>
        </div>
      </div>
      <div class="ft-body">
  <div style="font-size: 13px; margin-bottom: 10px; opacity:.92; font-weight:600; line-height:1.3;">${title}</div>
        <label>Format</label>
        <div class="ft-format-grid">
          <select id="ft-format">
            <option>Best Video + Audio</option>
            <option>Audio Only</option>
            <option>Best (default)</option>
          </select>
          <select id="ft-formatid"><option value="">Exact format…</option></select>
        </div>
        <label>Quality</label>
        <span id="ft-quality-wrap">
          <select id="ft-quality-select">
            <option value="">Best</option>
            <option value="2160">2160p</option>
            <option value="1440">1440p</option>
            <option value="1080">1080p</option>
            <option value="720">720p</option>
            <option value="480">480p</option>
            <option value="360">360p</option>
          </select>
        </span>
        <div id="ft-quality-loading" style="font-size:11px; opacity:.65; margin:4px 0 2px;">Loading formats…</div>
  <label style="margin-top:10px;"><input type="checkbox" id="ft-subs" checked /> Subtitles <span class="ft-pill">EN</span></label>
        <div class="ft-actions">
          <button class="ft-btn" id="ft-download">Download</button>
        </div>
      </div>`;
    (document.body || document.documentElement).appendChild(panel);

    try {
      panel.style.setProperty('background', '#121417', 'important');
      panel.style.setProperty('background-color', '#121417', 'important');
      panel.style.setProperty('opacity', '1', 'important');
      panel.style.setProperty('mix-blend-mode', 'normal', 'important');
      panel.style.setProperty('filter', 'none', 'important');
      panel.style.setProperty('backdrop-filter', 'none', 'important');
      panel.style.setProperty('z-index', '2147483647', 'important');
      panel.style.setProperty('pointer-events', 'auto', 'important');
      panel.style.setProperty('isolation', 'isolate');
      panel.style.setProperty('contain', 'paint');
      const headerEl = panel.querySelector('.ft-header');
      const bodyEl = panel.querySelector('.ft-body');
      if (headerEl) {
        headerEl.style.setProperty('background', '#181d22', 'important');
        headerEl.style.setProperty('background-color', '#181d22', 'important');
      }
      if (bodyEl) {
        bodyEl.style.setProperty('background', '#121417', 'important');
        bodyEl.style.setProperty('background-color', '#121417', 'important');
      }
    } catch(e) {}
    try {
      if (anchorEl) {
        const r = anchorEl.getBoundingClientRect();
        panel.style.position = 'fixed';
        panel.style.left = '-9999px';
        panel.style.top = '-9999px';
        requestAnimationFrame(() => {
          const pw = panel.offsetWidth || 380;
          const ph = panel.offsetHeight || 260;
          let left = Math.min(window.innerWidth - pw - 12, Math.max(12, r.right + 8));
          let top = Math.min(window.innerHeight - ph - 12, Math.max(12, r.top));
          if (left + pw + 12 > window.innerWidth) {
            left = Math.max(12, r.left - pw - 8);
          }
          panel.style.left = left + 'px';
          panel.style.top = top + 'px';
        });
      }
    } catch(e) {}

    chrome.storage.sync.get(['format','quality','subs'], (prefs) => {
      if (prefs.format) panel.querySelector('#ft-format').value = prefs.format;
      if (prefs.quality) {
        const qSel = panel.querySelector('#ft-quality-select');
        if (qSel) qSel.value = prefs.quality;
      }
      if (prefs.subs !== undefined) panel.querySelector('#ft-subs').checked = prefs.subs;
    });

    try {
      if (hasChrome() && chrome.runtime?.sendMessage) {
        chrome.runtime.sendMessage({ action: 'probeFormats', url }, (resp) => {
          const loading = panel.querySelector('#ft-quality-loading');
          if (loading) loading.remove();
          if (!resp || resp.status !== 'ok' || !Array.isArray(resp.qualities)) return;
          const sel = panel.querySelector('#ft-quality-select');
          if (sel) {
            const current = sel.value;
            sel.innerHTML = '<option value="">Best</option>' + resp.qualities.map(h => `<option value="${h}">${h}p</option>`).join('');
            // Restore previous choice if still available
            if ([...sel.options].some(o => o.value === current)) sel.value = current;
          }

          // Populate exact format list with sizes
          const fmtWrap = panel.querySelector('#ft-formatid');
          if (fmtWrap && Array.isArray(resp.formats)) {
            // Clear old options except first placeholder
            fmtWrap.innerHTML = '<option value="">Exact format…</option>';
            const progressive = resp.formats.filter(f => f.progressive && f.height);
            const others = resp.formats.filter(f => !f.progressive && f.height);
            const audio = resp.formats.filter(f => (f.vcodec === null || f.vcodec === 'none'));
            const addOptions = (arr, labelSuffix) => arr.forEach(f => {
              const size = (typeof f.sizeMB === 'number') ? ` (~${f.sizeMB}MB)` : '';
              const h = f.height ? `${f.height}p` : '';
              const fps = f.fps ? `${f.fps}fps` : '';
              const v = f.vcodec && f.vcodec !== 'none' ? f.vcodec : '';
              const a = f.acodec && f.acodec !== 'none' ? f.acodec : '';
              const xa = [h, fps, f.ext || '', v, a].filter(Boolean).join(' · ');
              const txt = `${xa}${labelSuffix ? ' ' + labelSuffix : ''}${size} [${f.id}]`.trim();
              const opt = document.createElement('option');
              opt.value = f.id;
              opt.textContent = txt;
              fmtWrap.appendChild(opt);
            });
            if (progressive.length) {
              const grp = document.createElement('optgroup'); grp.label = 'Progressive (video+audio)';
              fmtWrap.appendChild(grp);
              progressive.forEach(f => {
                const size = (typeof f.sizeMB === 'number') ? ` (~${f.sizeMB}MB)` : '';
                const h = f.height ? `${f.height}p` : '';
                const fps = f.fps ? `${f.fps}fps` : '';
                const xa = [h, fps, f.ext || ''].filter(Boolean).join(' · ');
                const opt = document.createElement('option');
                opt.value = f.id; opt.textContent = `${xa}${size} [${f.id}]`;
                grp.appendChild(opt);
              });
            }
            if (others.length) {
              const grp = document.createElement('optgroup'); grp.label = 'Video only';
              fmtWrap.appendChild(grp);
              others.forEach(f => {
                const size = (typeof f.sizeMB === 'number') ? ` (~${f.sizeMB}MB)` : '';
                const h = f.height ? `${f.height}p` : '';
                const fps = f.fps ? `${f.fps}fps` : '';
                const xa = [h, fps, f.ext || '', f.vcodec || ''].filter(Boolean).join(' · ');
                const opt = document.createElement('option');
                opt.value = f.id; opt.textContent = `${xa}${size} [${f.id}]`;
                grp.appendChild(opt);
              });
            }
            if (audio.length) {
              const grp = document.createElement('optgroup'); grp.label = 'Audio only';
              fmtWrap.appendChild(grp);
              audio.forEach(f => {
                const size = (typeof f.sizeMB === 'number') ? ` (~${f.sizeMB}MB)` : '';
                const xa = [f.ext || '', f.acodec || ''].filter(Boolean).join(' · ');
                const opt = document.createElement('option');
                opt.value = f.id; opt.textContent = `${xa}${size} [${f.id}]`;
                grp.appendChild(opt);
              });
            }
          }
        });
      }
    } catch (e) { /* ignore */ }

    const header = panel.querySelector('.ft-header');
    let dragging = false, sx=0, sy=0, ox=0, oy=0;
    const onHeaderMouseDown = (e) => {
      if (e.button !== 0) return;
      if (e.target && (e.target.id === 'ft-close' || e.target.closest('#ft-close'))) return;
      dragging = true; sx = e.clientX; sy = e.clientY; const r = panel.getBoundingClientRect(); ox = r.left; oy = r.top; e.preventDefault();
    };
    const onHeaderMouseMove = (e) => {
      if (!dragging) return; const dx = e.clientX - sx, dy = e.clientY - sy; panel.style.left = (ox+dx)+"px"; panel.style.top = (oy+dy)+"px"; panel.style.right = 'auto';
    };
    const onHeaderMouseUp = () => { dragging = false; };
    header.addEventListener('mousedown', onHeaderMouseDown);
    document.addEventListener('mousemove', onHeaderMouseMove);
    document.addEventListener('mouseup', onHeaderMouseUp);

    const closeBtn = panel.querySelector('#ft-close');
    const doClose = () => {
      try { panel.remove(); } catch(e) {}
      document.removeEventListener('mousedown', onDocClick, true);
      document.removeEventListener('mousemove', onHeaderMouseMove);
      document.removeEventListener('mouseup', onHeaderMouseUp);
      document.removeEventListener('keydown', onKey);
    };
    closeBtn.addEventListener('click', (e) => { e.stopPropagation(); doClose(); });
    const triggerDownload = () => {
      const format = panel.querySelector('#ft-format').value;
      const qualitySel = panel.querySelector('#ft-quality-select');
      const quality = qualitySel ? qualitySel.value : (panel.querySelector('#ft-quality')?.value || '');
      const formatIdSel = panel.querySelector('#ft-formatid');
      const formatId = formatIdSel ? formatIdSel.value : '';
      const subs = panel.querySelector('#ft-subs').checked;
      // Save prefs
      chrome.storage.sync.set({format, quality, subs});
      // Trigger background/native
      try {
        chrome.runtime.sendMessage({ action: 'download', url, title, format, quality, subs, formatId, confirm: false, show: false });
      } catch (e) {
        console.warn('Extension context lost; please refresh');
        alert('FastTube reloaded. Refresh the page and try again.');
      }
      panel.querySelector('#ft-download').textContent = 'Queued';
      panel.querySelector('#ft-download').disabled = true;
      setTimeout(doClose, 800);
    };
    panel.querySelector('#ft-download').onclick = triggerDownload;
    panel.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        triggerDownload();
      }
    });
    const onDocClick = (e) => { if (!panel.contains(e.target)) { doClose(); } };
    document.addEventListener('mousedown', onDocClick, true);
    const onKey = (e) => { if (e.key === 'Escape') { doClose(); } };
    document.addEventListener('keydown', onKey, true);
  }

  function initObservers() {
    const app = document.querySelector('ytd-app') || document.body;
    const obs = new MutationObserver(() => {
      if (location.href !== lastHref) {
        lastHref = location.href;
        const p = document.getElementById(PANEL_ID); if (p) p.remove();
        const b = document.getElementById(BTN_ID); if (b) b.remove();
      }
      if (location.href.includes('/watch')) ensureOverlay();
      enhanceThumbnails();
    });
    obs.observe(app, { childList: true, subtree: true });
    if (location.href.includes('/watch')) ensureOverlay();
    enhanceThumbnails();
    let tries = 0; const timer = setInterval(() => {
      enhanceThumbnails(); tries += 1; if (tries > 30) clearInterval(timer);
    }, 1000);
    window.addEventListener('scroll', () => { enhanceThumbnails(); }, { passive: true });
  }

  initObservers();
})();