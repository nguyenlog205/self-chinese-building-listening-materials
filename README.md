# generateContents

`generateContents` produces Chinese listening learning materials from
two sources: YouTube videos (transcribed with Whisper) and pre-written
scripts (synthesized with a TTS model). Both produce the same
sentence-segmented, timestamped, pinyin-annotated JSON output under
`data/transcripts/`.

This project is a batch pipeline, not a web service — there is no API or
web layer here. For architecture, configuration reference, the output
JSON schema, and coding conventions, see [docs/](docs/).

## Installation

```bash
./scripts/setup_venv.sh
source .venv/bin/activate
```

This creates `.venv`, installs the project, and patches
`LD_LIBRARY_PATH` in `.venv/bin/activate` so that faster-whisper can find
`libcublas` and `libcudnn` (installed via the `nvidia-cublas-cu12` and
`nvidia-cudnn-cu12` pip wheels, without requiring a system-wide CUDA
toolkit installation). Always run `source .venv/bin/activate` before
using the pipeline; otherwise faster-whisper will fail with
`Library libcublas.so.12 is not found`.

Additional requirements:
- `ffmpeg` must be available on the machine (used to convert audio to
  WAV, and by `pydub` to decode/concatenate the MP3 clips edge-tts
  produces).
- An NVIDIA GPU is expected by default (`device: cuda` in
  `configs/system.yml`). On a machine without a GPU, set `device: cpu`
  and `compute_type: int8` instead.
- `script2audio` calls the edge-tts service over the network at
  synthesis time; it does not run offline.

## Configuring what to process

- `configs/url.yml` — list of YouTube URLs to transcribe. See
  [docs/configuration.md](docs/configuration.md#configsurlyml).
- `configs/scripts.yml` — list of pre-written script files (dropped
  under `data/scripts/`) to synthesize. See
  [docs/configuration.md](docs/configuration.md#configsscriptsyml).
- `configs/system.yml` — model/device/voice settings for every module.
  See [docs/configuration.md](docs/configuration.md#configssystemyml).

## Running the pipeline

### Batch: everything in `configs/url.yml` and `configs/scripts.yml`

```bash
python -m generateContents.pipeline
```

Runs every URL through metadata -> audio -> transcript, then every
script through script2audio. A failing item (a private video, a
transcription failure, a TTS error, and so on) is logged and skipped; it
does not stop the rest of its batch. At the end, a combined summary of
the form `N succeeded, M failed` is printed, and the process exits with
status code `1` if anything failed.

### A single URL

```bash
# Metadata and audio only
python -m generateContents.modules.url2metadata.run "<youtube_url>"

# Metadata, audio, and transcript (Chinese script with pinyin and timestamps)
python -m generateContents.modules.audio2script.run "<youtube_url>"
```

### A single script

```bash
python -m generateContents.modules.script2audio.run "data/scripts/example.txt"
```

All commands respect the cache: if a `content_id` already has a cached
transcript and `overwrite_existing` is `false` in `configs/system.yml`,
the cached result is returned instead of fetching, downloading,
transcribing, or synthesizing again.

## Output

Learning material is written to `data/transcripts/{content_id}.json`.
See [docs/data-format.md](docs/data-format.md) for the full schema.

### Packaging a dataset

Once you have cached transcripts (from either source), package them into
a flat CSV + per-sentence audio clips under `outcome/`:

```bash
python -m generateContents.export
```

This is a separate, repeatable step — it only reads what's already in
`data/`, so it's safe to re-run any time to rebuild `outcome/` after
adding more videos or scripts. See
[docs/data-format.md](docs/data-format.md#outcome-dataset) for the CSV
schema.
