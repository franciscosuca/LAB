const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  onSession: (callback) => {
    ipcRenderer.on('session', (_event, payload) => callback(payload));
  },
  onPhoneStatus: (callback) => {
    ipcRenderer.on('phone-status', (_event, payload) => callback(payload));
  },
  onPhoto: (callback) => {
    ipcRenderer.on('photo', (_event, payload) => callback(payload));
  },

  newSession: () => ipcRenderer.invoke('session:new'),
  setAddress: (address) => ipcRenderer.invoke('session:setAddress', address),
  openLocalTest: () => ipcRenderer.invoke('session:openLocalTest'),
  requestCapture: () => ipcRenderer.invoke('session:requestCapture'),
  revealPhoto: (filePath) => ipcRenderer.invoke('photo:reveal', filePath),
  openFolder: () => ipcRenderer.invoke('folder:open')
});
