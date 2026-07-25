const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const path = require("path");
const fs = require("fs");

function createWindow() {
  const win = new BrowserWindow({
    width: 780,
    height: 720,
    minWidth: 640,
    minHeight: 600,
    backgroundColor: "#14171B",
    title: "MacPuTTY",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  win.setMenuBarVisibility(false);
  win.loadFile("index.html");
}

ipcMain.handle("save-file", async (_event, suggestedName, data) => {
  const { canceled, filePath } = await dialog.showSaveDialog({
    defaultPath: suggestedName,
  });

  if (canceled || !filePath) {
    return { canceled: true };
  }

  fs.writeFileSync(filePath, Buffer.from(data));

  if (suggestedName.includes("id_") && !suggestedName.endsWith(".pub")) {
    try {
      fs.chmodSync(filePath, 0o600);
    } catch (_err) {
      // best-effort; not all filesystems support chmod (e.g. some Windows setups)
    }
  }

  return { canceled: false, filePath };
});

app.whenReady().then(() => {
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});