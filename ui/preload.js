const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  saveFile: (suggestedName, data) =>
    ipcRenderer.invoke("save-file", suggestedName, data),
  getBackendToken: () => ipcRenderer.invoke("get-backend-token"),
});