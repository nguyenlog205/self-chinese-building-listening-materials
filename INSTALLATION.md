# Cài đặt app luyện nghe (Listening Practice)

App desktop để luyện nghe tiếng Trung: dán link YouTube, tự động tách audio +
nhận diện giọng nói + pinyin, rồi luyện tập từng câu với video, phụ đề,
pinyin, và chép chính tả.

Có 2 bản cài đặt tương ứng 2 hệ điều hành — chọn đúng bản theo máy bạn đang
dùng:

| Hệ điều hành | Thư mục nguồn | Cách cài |
|---|---|---|
| **Windows** | `app_win/` | Tải installer `.exe` dựng sẵn, double-click cài — không cần cài gì thêm |
| **Linux (Fedora và tương đương)** | `app/` | Build AppImage tại máy (cần Python + ffmpeg có sẵn) |

---

## Windows

### Bước 1 — Tải installer

Installer `.exe` được build tự động qua GitHub Actions mỗi khi có thay đổi
trong `app_win/`. Để tải bản mới nhất:

1. Vào tab **Actions** của repo trên GitHub:
   `https://github.com/nguyenlog205/self-chinese-building-listening-materials/actions/workflows/build-app-win.yml`
2. Bấm vào lần chạy (run) mới nhất có dấu ✅ màu xanh.
3. Kéo xuống phần **Artifacts**, tải file
   `listening-practice-windows-installer.zip`.
4. Giải nén ra sẽ được file installer `.exe`.

Muốn build thủ công thay vì tải từ CI? Xem `app_win/README.md`.

### Bước 2 — Cài đặt

1. Double-click file `.exe` vừa giải nén.
2. Windows SmartScreen sẽ hiện cảnh báo **"Windows protected your PC"** vì
   file chưa được ký số (unsigned) — đây là bình thường với app tự build,
   không phải virus. Bấm **More info** → **Run anyway**.
3. Installer chạy kiểu one-click, tự cài vào profile người dùng — không cần
   quyền admin, không hỏi thêm gì.
4. App tự mở sau khi cài xong.

### Không cần cài thêm gì

Bản Windows đã đóng gói sẵn Python backend (PyInstaller) và ffmpeg bên
trong — máy không cần có sẵn Python, Node.js, hay ffmpeg.

### Lần chạy đầu tiên

Khi bạn thêm link YouTube đầu tiên, app sẽ tự tải model nhận diện giọng nói
(Whisper, ~150MB) từ Hugging Face — cần internet, và lần xử lý video đầu
tiên sẽ chờ lâu hơn các lần sau một chút.

---

## Linux (Fedora)

Bản Linux hiện chưa có installer dựng sẵn tự động (chưa thiết lập CI cho
Linux) — bạn tự build AppImage tại máy, chỉ mất vài phút.

### Yêu cầu trước khi cài

- **Python 3.10+** (`python3 --version` để kiểm tra)
- **Node.js 18+** và npm (`node -v`)
- **ffmpeg**: `sudo dnf install ffmpeg`

### Bước 1 — Build AppImage

```bash
cd app
npm install
npm run build:linux
```

Kết quả nằm ở `app/dist/Listening Practice-0.1.0.AppImage`.

### Bước 2 — Chạy

```bash
chmod +x "app/dist/Listening Practice-0.1.0.AppImage"
"app/dist/Listening Practice-0.1.0.AppImage"
```

Hoặc double-click file đó trong trình quản lý file (đã có quyền thực thi
sau bước `chmod +x`).

### Lần chạy đầu tiên

Khác với bản Windows, bản Linux **cần Python/ffmpeg có sẵn trên máy** —
app tự tạo virtual environment và cài các thư viện cần thiết
(faster-whisper, yt-dlp,...) ở lần chạy đầu tiên, mất vài phút và cần
internet. Từ lần thứ 2 trở đi sẽ khởi động ngay lập tức.

Model Whisper cũng được tải tự động khi thêm link đầu tiên, giống bản
Windows.

---

## Gặp lỗi?

- **Windows SmartScreen chặn không cho "Run anyway"**: vào Windows Security
  → App & browser control → tắt tạm Reputation-based protection, hoặc dùng
  tài khoản admin để cho phép.
- **Linux: `ffmpeg: command not found`**: cài `sudo dnf install ffmpeg` rồi
  chạy lại app.
- **App không mở được / lỗi khi thêm link**: mở app từ terminal
  (`./"Listening Practice-0.1.0.AppImage"` trên Linux, hoặc chạy `.exe` từ
  `cmd`/PowerShell trên Windows) để xem log lỗi in ra console.

Chi tiết kỹ thuật hơn về từng bản xem thêm ở `app/README.md` và
`app_win/README.md`.
