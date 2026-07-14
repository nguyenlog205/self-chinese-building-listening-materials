# Configuration reference

Every path and setting is read through `SystemConfig`
(`services/generateContents/common/config.py`, pydantic, fail fast); no
value is hardcoded anywhere else in the codebase.

## `configs/system.yml`

```yaml
paths:
  metadata_dir: data/metadata
  audio_cache_dir: data/audio_cache
  transcript_dir: data/transcripts
  outcome_dir: outcome
  log_file: logs/system.log

modules:
  url2metadata:
    enabled: true
    download_audio: true       # if false, only metadata is fetched, audio is not downloaded
    audio_format: wav
    sample_rate: 16000
    channels: 1
    overwrite_existing: false  # if true, always re-fetch and re-download, ignoring the cache

  audio2script:
    enabled: true
    model_size: medium         # tiny | base | small | medium | large-v3, larger is more accurate but slower
    device: cuda                # cuda | cpu
    compute_type: float16       # float16 for GPU, int8 for CPU
    language: zh
    pinyin_style: tone_marks    # tone_marks (ni hao with tone marks) | numeric (ni3 hao3)
    overwrite_existing: false

  script2audio:
    enabled: true
    voice: zh-CN-XiaoxiaoNeural       # any edge-tts voice, e.g. zh-CN-YunxiNeural
    rate: "+0%"                       # edge-tts speaking rate, e.g. "-10%", "+15%"
    pause_between_sentences_sec: 0.5
    language: zh
    pinyin_style: tone_marks          # tone_marks | numeric
    overwrite_existing: false

logging:
  level: INFO
```

| Section | Field | Meaning |
|---|---|---|
| `paths` | `metadata_dir` | Where `url2metadata` writes `{video_id}.json` |
| `paths` | `audio_cache_dir` | Where downloaded/synthesized audio (`{content_id}.wav`) is stored |
| `paths` | `transcript_dir` | Where the final learning material (`{content_id}.json`) is stored |
| `paths` | `outcome_dir` | Where `export.py` writes the packaged dataset (`dataset.csv` + `audio/`) |
| `paths` | `log_file` | Shared log file path |
| `modules.url2metadata` | `download_audio` | Skip audio download if you only need metadata |
| `modules.url2metadata` | `overwrite_existing` | Ignore the metadata/audio cache and re-fetch |
| `modules.audio2script` | `model_size` | Whisper model size — bigger is slower but more accurate |
| `modules.audio2script` | `device` / `compute_type` | GPU (`cuda`/`float16`) or CPU (`cpu`/`int8`) |
| `modules.audio2script` | `overwrite_existing` | Ignore the transcript cache and re-transcribe |
| `modules.script2audio` | `voice` | edge-tts voice name (run `edge-tts --list-voices` to see options) |
| `modules.script2audio` | `rate` | edge-tts speaking-rate adjustment |
| `modules.script2audio` | `pause_between_sentences_sec` | Silence inserted between synthesized sentences |
| `modules.script2audio` | `overwrite_existing` | Ignore the transcript cache and re-synthesize |

## `configs/url.yml`

The list of URLs to run through the YouTube pipeline, processed in the
order they are listed:

```yaml
urls:
  - https://www.youtube.com/watch?v=hBPECevVz-k
  - https://www.youtube.com/watch?v=xxxxxxxxxxx
```

## `configs/scripts.yml`

The list of pre-written script files to run through `script2audio`,
processed in the order they are listed:

```yaml
scripts:
  - data/scripts/example.txt
```

Each script is a plain UTF-8 text file dropped under `data/scripts/`:
- One sentence or paragraph per line.
- Blank lines and lines starting with `#` are ignored (comments).
- Longer lines are further split into sentences on sentence-final
  punctuation (`。！？!?`).
- The `content_id` for a script is its filename stem — `example.txt`
  produces `content_id: example`.
