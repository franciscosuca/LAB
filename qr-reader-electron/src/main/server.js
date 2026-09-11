const path = require('path');
const fs = require('fs');
const http = require('http');
const crypto = require('crypto');
const { EventEmitter } = require('events');
const express = require('express');
const multer = require('multer');
const { WebSocketServer } = require('ws');

const SESSION_TTL_MS = 30 * 60 * 1000; // sessions (and their QR codes) expire after 30 minutes
const MAX_PHOTO_BYTES = 20 * 1024 * 1024; // 20MB per photo
const SWEEP_INTERVAL_MS = 30 * 1000;
const HEARTBEAT_INTERVAL_MS = 20 * 1000;

const MOBILE_DIR = path.join(__dirname, '..', 'mobile');

function expiredPageHtml() {
  return `<!doctype html>
<html><head><meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Link expired</title>
<style>
  body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
    background:#0f1115;color:#eef1f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;text-align:center;padding:24px;}
  .card{max-width:360px;}
  h1{font-size:20px;margin-bottom:8px;}
  p{color:#9399ab;font-size:14px;line-height:1.5;}
</style></head>
<body><div class="card">
  <h1>This link expired \u{1F4F7}</h1>
  <p>Go back to the desktop app and scan the current QR code &mdash; each session is refreshed for security.</p>
</div></body></html>`;
}

/**
 * PairingServer hosts:
 *  - A tiny web app served to the phone (GET /m/:sessionId) that lets the
 *    user take/choose a photo and upload it (POST /api/sessions/:id/photos).
 *  - A WebSocket endpoint (/ws) the phone page uses to announce "I'm here"
 *    so the desktop can show a live "phone connected" status, and that the
 *    desktop can use to (optionally) ask the phone to snap a photo remotely.
 *
 * Sessions are short-lived, random, capability-style tokens: whoever holds
 * the URL (normally obtained only by scanning the QR code) can upload to
 * that session until it expires or is rotated.
 */
class PairingServer extends EventEmitter {
  constructor({ photosDir }) {
    super();
    this.photosDir = photosDir;
    this.sessions = new Map();
    this.port = null;

    this.app = express();
    this._configureRoutes();

    this.httpServer = http.createServer(this.app);
    this.wss = new WebSocketServer({ server: this.httpServer, path: '/ws' });
    this._configureWebSocket();

    this._sweepTimer = setInterval(() => this._sweepExpiredSessions(), SWEEP_INTERVAL_MS);
    this._heartbeatTimer = setInterval(() => this._heartbeat(), HEARTBEAT_INTERVAL_MS);
  }

  // ---- lifecycle -----------------------------------------------------

  start(preferredPort, maxAttempts = 15) {
    return new Promise((resolve, reject) => {
      const tryPort = (port, attemptsLeft) => {
        const onError = (err) => {
          this.httpServer.removeListener('error', onError);
          if (err.code === 'EADDRINUSE' && attemptsLeft > 0) {
            tryPort(port + 1, attemptsLeft - 1);
          } else {
            reject(err);
          }
        };
        this.httpServer.once('error', onError);
        this.httpServer.listen(port, '0.0.0.0', () => {
          this.httpServer.removeListener('error', onError);
          this.port = this.httpServer.address().port;
          resolve(this.port);
        });
      };
      tryPort(preferredPort, maxAttempts);
    });
  }

  stop() {
    clearInterval(this._sweepTimer);
    clearInterval(this._heartbeatTimer);
    for (const session of this.sessions.values()) {
      session.mobileSocket?.close(1001, 'server shutting down');
    }
    this.wss.close();
    this.httpServer.close();
  }

  // ---- sessions --------------------------------------------------------

  createSession() {
    const sessionId = crypto.randomBytes(9).toString('hex');
    const now = Date.now();
    const session = {
      sessionId,
      createdAt: now,
      expiresAt: now + SESSION_TTL_MS,
      status: 'pending',
      mobileSocket: null
    };
    this.sessions.set(sessionId, session);
    return { sessionId, expiresAt: session.expiresAt };
  }

  invalidateSession(sessionId) {
    const session = this.sessions.get(sessionId);
    if (!session) return;
    session.mobileSocket?.close(4000, 'session rotated');
    this.sessions.delete(sessionId);
  }

  requestCapture(sessionId) {
    const session = this.sessions.get(sessionId);
    if (!session || !session.mobileSocket || session.mobileSocket.readyState !== 1) {
      return false;
    }
    session.mobileSocket.send(JSON.stringify({ type: 'request-capture' }));
    return true;
  }

  _sweepExpiredSessions() {
    const now = Date.now();
    for (const [sessionId, session] of this.sessions) {
      if (session.expiresAt <= now) {
        session.mobileSocket?.close(4001, 'session expired');
        this.sessions.delete(sessionId);
      }
    }
  }

  _heartbeat() {
    for (const session of this.sessions.values()) {
      const socket = session.mobileSocket;
      if (!socket) continue;
      if (socket.isAlive === false) {
        socket.terminate();
        continue;
      }
      socket.isAlive = false;
      socket.ping();
    }
  }

  // ---- HTTP routes -------------------------------------------------------

  _configureRoutes() {
    this.app.use('/static', express.static(MOBILE_DIR));

    this.app.get('/m/:sessionId', (req, res) => {
      const session = this.sessions.get(req.params.sessionId);
      if (!session || session.expiresAt <= Date.now()) {
        return res.status(404).send(expiredPageHtml());
      }
      res.sendFile(path.join(MOBILE_DIR, 'mobile.html'));
    });

    const upload = multer({
      storage: multer.memoryStorage(),
      limits: { fileSize: MAX_PHOTO_BYTES },
      fileFilter: (req, file, cb) => {
        if (file.mimetype.startsWith('image/')) return cb(null, true);
        cb(new Error('Only image files are allowed'));
      }
    });

    this.app.post('/api/sessions/:sessionId/photos', (req, res) => {
      upload.single('photo')(req, res, (err) => {
        if (err) {
          const message = err.code === 'LIMIT_FILE_SIZE' ? 'Photo is too large (max 20MB).' : err.message;
          return res.status(400).json({ ok: false, error: message });
        }
        this._handleUpload(req, res);
      });
    });

    this.app.get('/', (_req, res) => {
      res.type('text/plain').send('QR Photo Bridge server is running. Scan the QR code shown on the desktop app.');
    });
  }

  _handleUpload(req, res) {
    const session = this.sessions.get(req.params.sessionId);
    if (!session || session.expiresAt <= Date.now()) {
      return res.status(404).json({ ok: false, error: 'Session not found or expired' });
    }
    if (!req.file) {
      return res.status(400).json({ ok: false, error: 'No image received' });
    }

    const id = crypto.randomUUID();
    const ext = (req.file.mimetype.split('/')[1] || 'jpg').replace('jpeg', 'jpg');
    const sessionDir = path.join(this.photosDir, req.params.sessionId);
    fs.mkdirSync(sessionDir, { recursive: true });
    const filePath = path.join(sessionDir, `${Date.now()}-${id}.${ext}`);
    fs.writeFileSync(filePath, req.file.buffer);

    const photo = {
      id,
      sessionId: req.params.sessionId,
      filePath,
      mimeType: req.file.mimetype,
      size: req.file.buffer.length,
      receivedAt: Date.now(),
      dataUrl: `data:${req.file.mimetype};base64,${req.file.buffer.toString('base64')}`
    };

    this.emit('photo', photo);
    res.json({ ok: true, id });
  }

  // ---- WebSocket (phone <-> server "sync" channel) ------------------------

  _configureWebSocket() {
    this.wss.on('connection', (socket, req) => {
      const { searchParams } = new URL(req.url, 'http://localhost');
      const sessionId = searchParams.get('session');
      const session = this.sessions.get(sessionId);

      if (!session || session.expiresAt <= Date.now()) {
        socket.close(4004, 'unknown or expired session');
        return;
      }

      session.mobileSocket?.close(4003, 'replaced by new connection');
      session.mobileSocket = socket;
      session.status = 'connected';
      socket.isAlive = true;

      this.emit('mobile-status', { sessionId, status: 'connected' });

      socket.on('pong', () => {
        socket.isAlive = true;
      });

      socket.on('close', () => {
        if (session.mobileSocket === socket) {
          session.mobileSocket = null;
          session.status = 'pending';
          this.emit('mobile-status', { sessionId, status: 'disconnected' });
        }
      });
    });
  }
}

module.exports = { PairingServer };
