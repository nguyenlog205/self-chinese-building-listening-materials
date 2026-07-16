const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");
const fs = require("fs");
const { spawn } = require("child_process");

let backendProcess = null;
let mainWindow = null;
let backendPort = null;

function backendExePath() {
  // Packaged app: electron-builder copies backend/dist/listening-backend
  // into resources/backend/listening-backend (see package.json extraResources).
  const packaged = path.join(
    process.resourcesPath,
    "backend",
    "listening-backend",
    "listening-backend.exe"
  );
  if (fs.existsSync(packaged)) return packaged;

  // Dev (pre-package): built locally via backend/scripts/build_exe.ps1.
  const devBuilt = path.join(
    __dirname,
    "..",
    "backend",
    "dist",
    "listening-backend",
    "listening-backend.exe"
  );
  return devBuilt;
}

function ffmpegPath() {
  const packaged = path.join(process.resourcesPath, "ffmpeg", "ffmpeg.exe");
  if (fs.existsSync(packaged)) return packaged;

  const devDownloaded = path.join(__dirname, "..", "resources", "ffmpeg", "ffmpeg.exe");
  if (fs.existsSync(devDownloaded)) return devDownloaded;

  return null;
}

function spawnBackend() {
  return new Promise((resolve, reject) => {
    const exePath = backendExePath();
    if (!fs.existsSync(exePath)) {
      reject(
        new Error(
          `Backend exe not found at ${exePath}. Run backend/scripts/build_exe.ps1 first.`
        )
      );
      return;
    }

    const env = { ...process.env };
    const ffmpeg = ffmpegPath();
    if (ffmpeg) env.LISTENING_FFMPEG_PATH = ffmpeg;

    backendProcess = spawn(exePath, [], { env });

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
  app.quit();
});

app.on("before-quit", () => {
  if (backendProcess) {
    backendProcess.kill();
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
