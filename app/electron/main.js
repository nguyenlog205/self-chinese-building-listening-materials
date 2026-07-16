const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const fs = require("fs");

let backendProcess = null;
let mainWindow = null;
let backendPort = null;

const BACKEND_DIR = path.join(__dirname, "..", "backend");

function isWindows() {
  return process.platform === "win32";
}

function spawnBackend() {
  return new Promise((resolve, reject) => {
    const scriptPath = isWindows()
      ? path.join(BACKEND_DIR, "scripts", "run.ps1")
      : path.join(BACKEND_DIR, "scripts", "run.sh");

    const command = isWindows() ? "powershell.exe" : "bash";
    const args = isWindows()
      ? ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", scriptPath]
      : [scriptPath];

    backendProcess = spawn(command, args, { cwd: BACKEND_DIR });

    let resolved = false;
    let stdoutBuf = "";

    backendProcess.stdout.on("data", (data) => {
      stdoutBuf += data.toString();
      const match = stdoutBuf.match(/READY (\d+)/);
      if (match && !resolved) {
        resolved = true;
        resolve(parseInt(match[1], 10));
      }
      console.log(`[backend] ${data}`.trim());
    });

    backendProcess.stderr.on("data", (data) => {
      console.error(`[backend] ${data}`.trim());
    });

    backendProcess.on("exit", (code) => {
      if (!resolved) {
        reject(new Error(`Backend exited before becoming ready (code ${code})`));
      }
    });
  });
}

async function createWindow() {
  try {
    backendPort = await spawnBackend();
  } catch (err) {
    console.error("Failed to start backend:", err);
    app.quit();
    return;
  }

  mainWindow = new BrowserWindow({
    width: 1280,
    height: 860,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadFile(path.join(__dirname, "..", "frontend", "index.html"));
}

ipcMain.handle("get-backend-port", () => backendPort);

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", () => {
  if (backendProcess) {
    backendProcess.kill();
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
