const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const QRCode = require('qrcode');

const { PairingServer } = require('./server');
const { listAddresses } = require('./network');

const PREFERRED_PORT = 17321;

let mainWindow = null;
let server = null;
let currentSession = null; // { sessionId, expiresAt }
let preferredAddress = null;
let photosDir = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1120,
    height: 780,
    minWidth: 900,
    minHeight: 620,
    backgroundColor: '#0f1115',
    title: 'QR Photo Bridge',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  mainWindow.loadFile(path.join(__dirname, '..', 'renderer', 'index.html'));

  mainWindow.webContents.on('did-finish-load', async () => {
    if (!currentSession) {
      await startNewSession();
    } else {
      await broadcastSession();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function pickAddress(addresses) {
  if (preferredAddress && addresses.some((a) => a.address === preferredAddress)) {
    return preferredAddress;
  }
  return addresses[0]?.address ?? '127.0.0.1';
}

function buildPairingUrl(address) {
  return `http://${address}:${server.port}/m/${currentSession.sessionId}`;
}

async function broadcastSession() {
  if (!mainWindow || !currentSession) return;

  const addresses = listAddresses();
  const address = pickAddress(addresses);
  preferredAddress = address;

  const url = buildPairingUrl(address);
  const qrDataUrl = await QRCode.toDataURL(url, {
    margin: 1,
    width: 320,
    color: { dark: '#111111', light: '#ffffff' }
  });

  mainWindow.webContents.send('session', {
    sessionId: currentSession.sessionId,
    expiresAt: currentSession.expiresAt,
    url,
    qrDataUrl,
    address,
    addresses,
    port: server.port
  });
}

async function startNewSession() {
  if (currentSession) {
    server.invalidateSession(currentSession.sessionId);
  }
  currentSession = server.createSession();
  await broadcastSession();
}

function registerIpcHandlers() {
  ipcMain.handle('session:new', async () => {
    await startNewSession();
    return true;
  });

  ipcMain.handle('session:setAddress', async (_event, address) => {
    preferredAddress = address;
    await broadcastSession();
    return true;
  });

  ipcMain.handle('session:openLocalTest', () => {
    if (!currentSession) return false;
    // 127.0.0.1 is treated as a "secure context" by browsers, so opening the
    // pairing page locally lets you test the full live-camera flow using
    // this computer's own webcam, no phone required.
    const url = `http://127.0.0.1:${server.port}/m/${currentSession.sessionId}`;
    shell.openExternal(url);
    return true;
  });

  ipcMain.handle('session:requestCapture', () => {
    if (!currentSession) return false;
    return server.requestCapture(currentSession.sessionId);
  });

  ipcMain.handle('photo:reveal', (_event, filePath) => {
    shell.showItemInFolder(filePath);
  });

  ipcMain.handle('folder:open', () => {
    shell.openPath(photosDir);
  });
}

async function bootstrap() {
  photosDir = path.join(app.getPath('userData'), 'received-photos');
  fs.mkdirSync(photosDir, { recursive: true });

  server = new PairingServer({ photosDir });
  await server.start(PREFERRED_PORT);

  server.on('mobile-status', (payload) => {
    mainWindow?.webContents.send('phone-status', payload);
  });

  server.on('photo', (photo) => {
    mainWindow?.webContents.send('photo', {
      id: photo.id,
      sessionId: photo.sessionId,
      dataUrl: photo.dataUrl,
      filePath: photo.filePath,
      receivedAt: photo.receivedAt,
      size: photo.size
    });
  });

  registerIpcHandlers();
  createWindow();
}

const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  app.whenReady().then(bootstrap);

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });

  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
  });

  app.on('will-quit', () => {
    server?.stop();
  });
}
