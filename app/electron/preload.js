const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("listeningApp", {
  getBackendPort: () => ipcRenderer.invoke("get-backend-port"),
});
