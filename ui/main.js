const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const path = require("path");
const fs = require("fs");
const http = require("http");
const { spawn } = require("child_process");

const BACKEND_HOST = "127.0.0.1";
const BACKEND_PORT = 5050;
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;

let backendProcess = null;
let mainWindow = null;

function backendExecutablePath() {
  // Matches extraResources "to": "backend" in package.json's build config,
  // and the --onedir layout produced by scripts/build-backend.sh
  // (dist folder name == executable name == "macputty-backend").
  return path.join(
    process.resourcesPath,
    "backend",
    "macputty-backend",
    "macputty-backend"
  );
}

function startBackend() {
  return new Promise((resolve, reject) => {
    const exePath = backendExecutablePath();

    if (!fs.existsSync(exePath)) {
      reject(new Error(`Backend executable not found at ${exePath}`));
      return;
    }

    backendProcess = spawn(exePath, [], { stdio: ["ignore", "pipe", "pipe"] });

    backendProcess.stdout.on("data", (d) => console.log(`[backend] ${d}`));
    backendProcess.stderr.on("data", (d) => console.error(`[backend] ${d}`));
    backendProcess.on("error", (err) => reject(err));
    backendProcess.on("exit", (code, signal) => {
      console.log(`[backend] exited code=${code} signal=${signal}`);
      backendProcess = null;
    });

    resolve();
  });
}

function waitForHealth(timeoutMs = 15000, intervalMs = 250) {
  const deadline = Date.now() + timeoutMs;

  return new Promise((resolve, reject) => {
    const attempt = () => {
      const req = http.get(`${BACKEND_URL}/health`, (res) => {
        res.resume();
        if (res.statusCode === 200) resolve();
        else retry();
      });
      req.on("error", retry);
      req.setTimeout(2000, () => {
        req.destroy();
        retry();
      });
    };
    const retry = () => {
      if (Date.now() > deadline) {
        reject(new Error("Backend did not become healthy in time"));
        return;
      }
      setTimeout(attempt, intervalMs);
    };
    attempt();
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
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

  mainWindow.setMenuBarVisibility(false);
  mainWindow.loadFile("index.html");
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

app.whenReady().then(async () => {
  if (app.isPackaged) {
    try {
      await startBackend();
      await waitForHealth();
    } catch (err) {
      dialog.showErrorBox(
        "MacPuTTY failed to start",
        `The bundled backend could not be started or did not respond in time.\n\n${err.message}\n\nPlease relaunch the app.`
      );
      app.quit();
      return;
    }
  }
  // Dev mode (app.isPackaged === false): unchanged — assumes `make build`
  // (docker compose) has already started the Flask backend on 127.0.0.1:5050.

  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", () => {
  if (backendProcess) {
    backendProcess.kill("SIGTERM");
    backendProcess = null;
  }
});

app.on("will-quit", () => {
  if (backendProcess) backendProcess.kill("SIGKILL");
});