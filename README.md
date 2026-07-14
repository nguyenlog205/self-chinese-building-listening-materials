# generateContents

Content pipeline sinh học liệu nghe (listening) tiếng Trung từ danh sách
video YouTube: lấy metadata → tải audio → transcribe thành script tiếng
Trung có timestamp + pinyin, ngắt theo câu. Chạy như một pipeline/batch
job, output là file JSON/WAV trong `data/` — **không có API trong repo
này**, việc phục vụ dữ liệu này qua HTTP thuộc về một repo khác.

## Kiến trúc

Project theo layered architecture, tách biệt business logic khỏi cách nó
được gọi:

```
configs/
  system.yml                        # config chung, mọi module đọc từ đây
  url.yml                           # danh sách URL sẽ chạy qua pipeline

services/generateContents/          # business logic — package chính
  common/
    config.py                       # load_config(), load_urls() (pydantic, fail-fast)
    logger.py                       # get_logger(name) -> ghi log ra stdout + file
  modules/
    url2metadata/
      domain/
        schema.py                   # VideoMetadata
        exceptions.py               # MetadataExtractionError, AudioDownloadError
      adapters/
        ytdlp_client.py             # nơi DUY NHẤT import yt-dlp
        cache_store.py              # đọc/ghi JSON cache, path helpers
      service.py                    # extract_metadata(), download_audio(), run()
      run.py                        # CLI mỏng cho 1 URL, gọi service.run()
    audio2script/
      domain/
        schema.py                   # ScriptSegment, TranscriptResult
        exceptions.py               # TranscriptionError
      adapters/
        whisper_client.py           # nơi DUY NHẤT import faster-whisper
        pinyin_converter.py         # nơi DUY NHẤT import pypinyin
        cache_store.py              # đọc/ghi JSON cache transcript
      service.py                    # transcribe(), run() (gọi cả url2metadata.service)
      run.py                        # CLI mỏng cho 1 URL, gọi service.run()
  pipeline.py                       # CLI batch: chạy tuần tự mọi URL trong url.yml

data/
  metadata/{video_id}.json           # output của url2metadata
  audio_cache/{video_id}.wav          # output của url2metadata
  transcripts/{video_id}.json          # output của audio2script — học liệu cuối cùng

logs/
  system.log                          # log file dùng chung
```

**Quy tắc cốt lõi:** `service.py` là nơi duy nhất chứa business logic của
mỗi module — `run.py` (CLI 1 URL) và `pipeline.py` (CLI batch) đều chỉ gọi
vào `service.py`, không viết logic riêng, không import `adapters/` trực
tiếp. Module sau gọi lại `service.py` của module trước thay vì lặp code
(`audio2script.service.run()` gọi `url2metadata.service.run()` để lấy audio
trước khi transcribe).

## Cài đặt

```bash
./scripts/setup_venv.sh
source .venv/bin/activate
```

Script này tạo `.venv`, cài project, và vá `LD_LIBRARY_PATH` trong
`.venv/bin/activate` để faster-whisper tìm thấy `libcublas`/`libcudnn` (cài
qua pip wheel `nvidia-cublas-cu12` / `nvidia-cudnn-cu12`, không cần cài CUDA
toolkit hệ thống). **Luôn `source .venv/bin/activate` trước khi chạy** —
nếu không, faster-whisper sẽ báo lỗi `Library libcublas.so.12 is not
found`.

Yêu cầu khác:
- `ffmpeg` có sẵn trên máy (convert audio sang WAV).
- GPU NVIDIA (mặc định `device: cuda` trong config). Không có GPU thì đổi
  `device: cpu` và `compute_type: int8` trong `configs/system.yml`.

## Cấu hình

### `configs/system.yml`

```yaml
paths:
  metadata_dir: data/metadata
  audio_cache_dir: data/audio_cache
  transcript_dir: data/transcripts
  log_file: logs/system.log

modules:
  url2metadata:
    enabled: true
    download_audio: true       # false thì chỉ lấy metadata, không tải audio
    audio_format: wav
    sample_rate: 16000
    channels: 1
    overwrite_existing: false  # true thì luôn fetch/download lại, bỏ qua cache

  audio2script:
    enabled: true
    model_size: medium         # tiny | base | small | medium | large-v3 — model càng lớn càng chính xác, càng chậm
    device: cuda                # cuda | cpu
    compute_type: float16       # float16 (GPU) | int8 (CPU)
    language: zh
    pinyin_style: tone_marks    # tone_marks (nǐ hǎo) | numeric (ni3 hao3)
    overwrite_existing: false

logging:
  level: INFO
```

Mọi path/setting đều đọc từ file này qua `SystemConfig` — không hardcode ở
nơi khác.

### `configs/url.yml`

Danh sách URL sẽ chạy qua pipeline, theo thứ tự liệt kê:

```yaml
urls:
  - https://www.youtube.com/watch?v=hBPECevVz-k
  - https://www.youtube.com/watch?v=xxxxxxxxxxx
```

## Chạy

### Batch — toàn bộ danh sách trong `configs/url.yml`

```bash
python -m generateContents.pipeline
```

Chạy tuần tự từng URL, mỗi URL đi qua đủ 3 bước (metadata → audio →
transcript). URL nào lỗi (video private, transcribe fail...) sẽ được ghi
log và bỏ qua — không làm dừng cả batch. Cuối cùng in ra bảng tổng kết
`N succeeded, M failed` và exit code `1` nếu có lỗi.

### Một URL đơn lẻ

```bash
# Chỉ lấy metadata + audio
python -m generateContents.modules.url2metadata.run "<youtube_url>"

# Lấy metadata + audio + transcript (script tiếng Trung + pinyin + timestamp)
python -m generateContents.modules.audio2script.run "<youtube_url>"
```

Cả 2 lệnh đều tôn trọng cache: nếu `video_id` đã có cache và
`overwrite_existing: false`, không fetch/download/transcribe lại.

### Định dạng học liệu — `data/transcripts/{video_id}.json`

```json
{
  "video_id": "hBPECevVz-k",
  "source_audio_path": "data/audio_cache/hBPECevVz-k.wav",
  "language": "zh",
  "segments": [
    {
      "index": 0,
      "start_sec": 6.06,
      "end_sec": 11.06,
      "text_zh": "大家好,欢迎收听新一期的《每天中门》,我是李明。",
      "pinyin": "dà jiā hǎo huān yíng shōu tīng xīn yī qī de měi tiān zhōng mén wǒ shì lǐ míng"
    }
  ],
  "transcribed_at": "2026-07-14T20:41:30Z"
}
```

Mỗi `segment` là **một câu** (whisper transcribe theo đoạn tạm dừng, sau đó
`service.py` tách tiếp theo dấu câu tiếng Trung `。！？`, chia lại
timestamp theo tỉ lệ số ký tự trong đoạn gốc).

## Quy ước lỗi & log

- Mỗi hàm public log `INFO` khi bắt đầu/thành công, `ERROR` khi thất bại.
- Không có `except:` trần — luôn bắt exception cụ thể, wrap lại thành
  exception riêng của module (`raise XxxError(...) from e`) để giữ traceback
  gốc và không để lộ exception của thư viện ngoài (yt-dlp, faster-whisper)
  ra ngoài module.

## Ngoài phạm vi hiện tại

- Không có API/web layer trong repo này — sẽ nằm ở repo khác, đọc trực
  tiếp từ `data/` (hoặc một storage chung sau này).
- Chưa có: export sang định dạng học tập (Anki, SRT...), xử lý song song
  nhiều video, hoặc theo dõi tiến độ giữa các lần chạy batch (mỗi lần
  `pipeline.py` chạy lại toàn bộ danh sách, chỉ URL nào chưa cache mới thực
  sự tốn thời gian).
