# Architecture

The project follows a layered architecture that separates business logic
from the way it is invoked (a single-item CLI or a batch pipeline).

## Two content sources, one output format

Learning material comes from two independent sources, which converge on
the same output format (see [data-format.md](data-format.md)) so
downstream consumers don't need to know where a given piece of content
came from:

- **YouTube videos** (`url2metadata` -> `audio2script`): extract
  metadata, download audio, transcribe it with Whisper into a
  sentence-segmented, timestamped, pinyin-annotated script.
- **Pre-written scripts** (`script2audio`): synthesize audio for an
  existing script with a TTS model and produce the same
  sentence-segmented, timestamped, pinyin-annotated output — without an
  ASR step, since the text is already known.

A separate step, `export.py`, reads every cached transcript regardless of
source and repackages it into a flat, self-contained dataset under
`outcome/` (see [data-format.md](data-format.md#outcome-dataset)) — one
CSV row and one audio clip per sentence.

## Directory layout

```
configs/
  system.yml                        General configuration, read by every module
  url.yml                           List of URLs to run through the YouTube pipeline
  scripts.yml                       List of script files to run through script2audio

services/generateContents/          Business logic, the main package
  common/
    config.py                       load_config(), load_urls(), load_scripts() (pydantic, fail fast)
    logger.py                       get_logger(name), logs to stdout and to a file
    schema.py                       ScriptSegment, TranscriptResult — shared output format
    transcript_store.py             Reads and writes the JSON transcript cache, shared by every module
    pinyin_converter.py             The only place that imports pypinyin
    sentence_split.py               Splits text into sentences on Chinese/Western punctuation
    audio.py                        The only place that imports pydub (load/slice/concat/export WAV)
  modules/
    url2metadata/
      domain/
        schema.py                   VideoMetadata
        exceptions.py               MetadataExtractionError, AudioDownloadError
      adapters/
        ytdlp_client.py             The only place that imports yt-dlp
        cache_store.py              Reads and writes the JSON cache, path helpers
      service.py                    extract_metadata(), download_audio(), run()
      run.py                        Thin CLI for a single URL, calls service.run()
    audio2script/
      domain/
        exceptions.py               TranscriptionError
      adapters/
        whisper_client.py           The only place that imports faster-whisper
      service.py                    transcribe(), run() (also calls url2metadata.service)
      run.py                        Thin CLI for a single URL, calls service.run()
    script2audio/
      domain/
        exceptions.py               ScriptLoadError, SpeechSynthesisError
      adapters/
        script_loader.py            Reads a script file into a list of sentences
        edge_tts_client.py          The only place that imports edge-tts
        audio_builder.py            The only place that imports pydub; concatenates TTS clips into one WAV
      service.py                    synthesize(), run()
      run.py                        Thin CLI for a single script file, calls service.run()
  pipeline.py                       Batch CLI: runs url.yml through audio2script, and scripts.yml through script2audio
  export.py                         Packages every cached transcript into outcome/ (dataset CSV + per-sentence audio clips)

data/
  metadata/{video_id}.json          Output of url2metadata
  audio_cache/{content_id}.wav      Output of url2metadata (video_id) or script2audio (script filename stem)
  transcripts/{content_id}.json     Output of audio2script or script2audio, the final learning material
  scripts/                          Where pre-written script .txt files live, referenced by scripts.yml

outcome/
  dataset.csv                       One row per sentence, across every content_id, output of export.py
  audio/{content_id}_{index}.wav    One clip per row, cut from that sentence's source audio

logs/
  system.log                        Shared log file
```

## Core rule

`service.py` is the only place that contains business logic for a
module. Both `run.py` (single-item CLI) and `pipeline.py` (batch CLI)
only call into `service.py`; they never contain business logic
themselves and never import `adapters/` directly. A later module calls
into the `service.py` of an earlier module instead of duplicating logic
(for example, `audio2script.service.run()` calls
`url2metadata.service.run()` to obtain the audio before transcribing
it).

Both `audio2script` and `script2audio` produce the same `TranscriptResult`
shape (defined once in `common/schema.py`) and share the transcript
cache, pinyin conversion, and sentence-splitting logic instead of
duplicating it — the only thing that differs between them is how the
audio and text come to exist in the first place (transcription from real
audio vs. TTS from known text).

## Out of scope for now

- There is no API or web layer in this repository. That responsibility
  belongs to a separate repository, which is expected to read from
  `data/` directly (or from a shared storage location in the future).
- Not yet implemented: export to other learning formats (Anki, SRT, and
  so on — `export.py` currently only produces the CSV + audio-clip
  dataset format), parallel processing of multiple items, and progress
  tracking across batch runs (each run of `pipeline.py` walks the full
  URL/script list again; only items that are not yet cached actually
  take meaningful time).
