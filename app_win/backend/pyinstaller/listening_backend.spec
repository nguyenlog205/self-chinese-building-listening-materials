# PyInstaller spec for the frozen backend exe.
#
# onedir (not onefile): onefile self-extracts into a temp dir on every
# launch, which is slow and more likely to trip antivirus heuristics for an
# unsigned exe. onedir starts instantly after install.
#
# yt-dlp, faster-whisper, ctranslate2, and pypinyin all ship extra data
# and/or native binaries that PyInstaller's static analysis won't find on its
# own -- collect_all() pulls in everything each package needs.
#
# Run from app_win/backend/: pyinstaller pyinstaller/listening_backend.spec

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []

for pkg in ("yt_dlp", "faster_whisper", "ctranslate2", "pypinyin", "uvicorn"):
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

a = Analysis(
    ["../listening_backend/main.py"],
    pathex=["../"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="listening-backend",
    console=True,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="listening-backend",
)
