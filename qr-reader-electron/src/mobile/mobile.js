(function () {
  const sessionId = location.pathname.split('/').filter(Boolean).pop();

  const statusEl = document.getElementById('status');
  const messageEl = document.getElementById('message');
  const video = document.getElementById('preview');
  const canvas = document.getElementById('canvas');
  const shotImg = document.getElementById('shot');
  const liveBtn = document.getElementById('liveBtn');
  const captureBtn = document.getElementById('captureBtn');
  const fileLabel = document.getElementById('fileLabel');
  const fileInput = document.getElementById('fileInput');
  const retakeBtn = document.getElementById('retakeBtn');
  const sendBtn = document.getElementById('sendBtn');

  let stream = null;
  let blobToSend = null;
  let ws = null;
  let reconnectDelay = 1000;
  let stopReconnecting = false;
  let autoSendOnCapture = false;

  function setStatus(text, kind) {
    statusEl.textContent = text;
    statusEl.className = `status status--${kind}`;
  }

  function setMessage(text, kind) {
    messageEl.textContent = text;
    messageEl.className = kind ? `message message--${kind}` : 'message';
  }

  function canUseLiveCamera() {
    return Boolean(window.isSecureContext && navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
  }

  function stopStream() {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }
  }

  // ---- capture flow: file/camera input (default) or live preview -----

  function resetCapture() {
    blobToSend = null;
    autoSendOnCapture = false;
    stopStream();

    video.hidden = true;
    shotImg.hidden = true;
    shotImg.src = '';
    canvas.hidden = true;

    captureBtn.hidden = true;
    retakeBtn.hidden = true;
    sendBtn.hidden = true;
    fileInput.value = '';

    fileLabel.hidden = false;
    liveBtn.hidden = !canUseLiveCamera();

    setMessage('');
  }

  function showPreview(src) {
    shotImg.src = src;
    shotImg.hidden = false;
    video.hidden = true;

    captureBtn.hidden = true;
    liveBtn.hidden = true;
    fileLabel.hidden = true;
    retakeBtn.hidden = false;
    sendBtn.hidden = false;

    stopStream();
  }

  liveBtn.addEventListener('click', async () => {
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
        audio: false
      });
      video.srcObject = stream;
      video.hidden = false;
      liveBtn.hidden = true;
      fileLabel.hidden = true;
      captureBtn.hidden = false;
    } catch (err) {
      setMessage(`Camera error: ${err.message}`, 'error');
    }
  });

  function captureFrame() {
    if (!stream) return;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    canvas.toBlob(
      (blob) => {
        blobToSend = blob;
        showPreview(URL.createObjectURL(blob));
        if (autoSendOnCapture) {
          autoSendOnCapture = false;
          sendPhoto();
        }
      },
      'image/jpeg',
      0.92
    );
  }

  captureBtn.addEventListener('click', captureFrame);

  fileInput.addEventListener('change', () => {
    const file = fileInput.files && fileInput.files[0];
    if (!file) return;
    blobToSend = file;
    const reader = new FileReader();
    reader.onload = () => showPreview(reader.result);
    reader.readAsDataURL(file);
  });

  retakeBtn.addEventListener('click', resetCapture);

  async function sendPhoto() {
    if (!blobToSend) return;
    sendBtn.disabled = true;
    sendBtn.textContent = 'Sending\u2026';
    try {
      const form = new FormData();
      form.append('photo', blobToSend, blobToSend.name || 'photo.jpg');
      const res = await fetch(`/api/sessions/${sessionId}/photos`, { method: 'POST', body: form });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.ok) throw new Error(data.error || 'Upload failed');

      setMessage('Sent! Check your desktop screen. \u2705', 'ok');
      setTimeout(resetCapture, 1200);
    } catch (err) {
      setMessage(`Could not send photo: ${err.message}`, 'error');
    } finally {
      sendBtn.disabled = false;
      sendBtn.textContent = 'Send to desktop';
    }
  }

  sendBtn.addEventListener('click', sendPhoto);

  // ---- WebSocket: lets the desktop know we're here, and lets it -----
  // ---- (optionally) ask us to snap a photo remotely ------------------

  function connectSocket() {
    if (stopReconnecting) return;
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
    ws = new WebSocket(`${protocol}://${location.host}/ws?session=${sessionId}`);

    ws.addEventListener('open', () => {
      reconnectDelay = 1000;
      setStatus('Connected to desktop \u2713', 'ok');
    });

    ws.addEventListener('message', (event) => {
      let data;
      try {
        data = JSON.parse(event.data);
      } catch {
        return;
      }
      if (data.type === 'request-capture') {
        handleCaptureRequest();
      }
    });

    ws.addEventListener('close', (event) => {
      if (event.code === 4001 || event.code === 4004) {
        stopReconnecting = true;
        setStatus('Link expired \u2014 ask desktop for a new QR code', 'error');
        return;
      }
      setStatus('Disconnected \u2014 reconnecting\u2026', 'warn');
      setTimeout(connectSocket, reconnectDelay);
      reconnectDelay = Math.min(reconnectDelay * 1.5, 8000);
    });

    ws.addEventListener('error', () => ws.close());
  }

  function handleCaptureRequest() {
    if (navigator.vibrate) navigator.vibrate(200);

    if (stream && !video.hidden) {
      // Live camera is active: capture and send automatically.
      autoSendOnCapture = true;
      captureFrame();
      setMessage('Desktop asked for a photo \u2014 capturing\u2026', 'ok');
    } else {
      setMessage('Desktop is asking for a photo \u2014 please take one! \u{1F4F8}', 'ok');
    }
  }

  resetCapture();
  connectSocket();
})();
