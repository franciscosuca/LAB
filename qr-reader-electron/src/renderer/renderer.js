(function () {
  const state = {
    session: null,
    phoneConnected: false,
    photos: [],
    selectedId: null
  };

  const $ = (selector) => document.querySelector(selector);

  const els = {
    qrImg: $('#qrImage'),
    linkText: $('#linkText'),
    copyBtn: $('#copyLinkBtn'),
    networkField: $('#networkField'),
    networkSelect: $('#networkSelect'),
    expiryText: $('#expiryText'),
    newSessionBtn: $('#newSessionBtn'),
    testLocallyBtn: $('#testLocallyBtn'),
    requestCaptureBtn: $('#requestCaptureBtn'),
    openFolderBtn: $('#openFolderBtn'),
    statusPill: $('#statusPill'),
    bigPreview: $('#bigPreview'),
    bigPreviewImg: $('#bigPreview img'),
    previewMeta: $('#bigPreview .preview-meta'),
    revealBtn: $('#revealBtn'),
    emptyState: $('#emptyState'),
    gallery: $('#gallery'),
    toastContainer: $('#toastContainer')
  };

  let countdownTimer = null;

  function formatBytes(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function showToast(text) {
    const el = document.createElement('div');
    el.className = 'toast';
    el.textContent = text;
    els.toastContainer.appendChild(el);
    requestAnimationFrame(() => el.classList.add('toast--visible'));
    setTimeout(() => {
      el.classList.remove('toast--visible');
      setTimeout(() => el.remove(), 300);
    }, 3200);
  }

  function renderStatus() {
    if (!state.session) return;
    const expired = state.session.expiresAt <= Date.now();

    if (expired) {
      els.statusPill.textContent = 'Session expired';
      els.statusPill.className = 'pill pill--expired';
    } else if (state.phoneConnected) {
      els.statusPill.textContent = 'Phone connected';
      els.statusPill.className = 'pill pill--connected';
    } else {
      els.statusPill.textContent = 'Waiting for phone\u2026';
      els.statusPill.className = 'pill pill--pending';
    }

    els.requestCaptureBtn.disabled = !state.phoneConnected || expired;
  }

  function renderExpiry() {
    if (!state.session) return;
    const remaining = state.session.expiresAt - Date.now();

    if (remaining <= 0) {
      els.expiryText.textContent = 'Expired \u2014 click "New session" for a fresh QR code.';
      renderStatus();
      return;
    }

    const mins = Math.floor(remaining / 60000);
    const secs = Math.floor((remaining % 60000) / 1000);
    els.expiryText.textContent = `Expires in ${mins}m ${String(secs).padStart(2, '0')}s`;
  }

  function applySession(session) {
    state.session = session;
    state.phoneConnected = false;

    els.qrImg.src = session.qrDataUrl;
    els.linkText.textContent = session.url;

    els.networkSelect.innerHTML = '';
    session.addresses.forEach((entry) => {
      const option = document.createElement('option');
      option.value = entry.address;
      option.textContent = `${entry.address} (${entry.name})`;
      if (entry.address === session.address) option.selected = true;
      els.networkSelect.appendChild(option);
    });
    els.networkField.hidden = session.addresses.length <= 1;

    renderStatus();
    renderExpiry();

    clearInterval(countdownTimer);
    countdownTimer = setInterval(renderExpiry, 1000);
  }

  function renderGallery() {
    els.emptyState.hidden = state.photos.length > 0;
    els.gallery.innerHTML = '';

    for (const photo of state.photos) {
      const thumb = document.createElement('button');
      thumb.type = 'button';
      thumb.className = 'thumb';
      thumb.title = new Date(photo.receivedAt).toLocaleString();

      const img = document.createElement('img');
      img.src = photo.dataUrl;
      img.alt = 'Received photo thumbnail';
      thumb.appendChild(img);

      thumb.addEventListener('click', () => selectPhoto(photo.id));
      els.gallery.appendChild(thumb);
    }
  }

  function selectPhoto(id) {
    const photo = state.photos.find((p) => p.id === id);
    if (!photo) return;

    state.selectedId = id;
    els.bigPreview.hidden = false;
    els.bigPreviewImg.src = photo.dataUrl;
    els.previewMeta.textContent =
      `Received ${new Date(photo.receivedAt).toLocaleTimeString()} \u2022 ${formatBytes(photo.size)}`;
    els.revealBtn.disabled = false;
  }

  function addPhoto(photo) {
    state.photos.unshift(photo);
    renderGallery();
    selectPhoto(photo.id);
    showToast('New photo received from phone \u{1F4F8}');
  }

  // ---- wire up main-process events ----------------------------------

  window.api.onSession(applySession);

  window.api.onPhoneStatus(({ status }) => {
    state.phoneConnected = status === 'connected';
    renderStatus();
    showToast(state.phoneConnected ? 'Phone connected \u2705' : 'Phone disconnected');
  });

  window.api.onPhoto(addPhoto);

  // ---- wire up UI controls -------------------------------------------

  els.copyBtn.addEventListener('click', async () => {
    if (!state.session) return;
    try {
      await navigator.clipboard.writeText(state.session.url);
      showToast('Link copied to clipboard');
    } catch {
      showToast('Could not copy link');
    }
  });

  els.newSessionBtn.addEventListener('click', () => window.api.newSession());
  els.testLocallyBtn.addEventListener('click', () => window.api.openLocalTest());
  els.requestCaptureBtn.addEventListener('click', async () => {
    const ok = await window.api.requestCapture();
    showToast(ok ? 'Asked your phone for a photo' : 'Phone is not connected right now');
  });

  els.networkSelect.addEventListener('change', (event) => {
    window.api.setAddress(event.target.value);
  });

  els.openFolderBtn.addEventListener('click', () => window.api.openFolder());

  els.revealBtn.addEventListener('click', () => {
    const photo = state.photos.find((p) => p.id === state.selectedId);
    if (photo) window.api.revealPhoto(photo.filePath);
  });
})();
