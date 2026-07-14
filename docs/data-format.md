# Learning material format

Output location: `data/transcripts/{content_id}.json`.

```json
{
  "content_id": "hBPECevVz-k",
  "source_type": "youtube",
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

| Field | Meaning |
|---|---|
| `content_id` | YouTube `video_id` for `audio2script` output, or the script's filename stem for `script2audio` output |
| `source_type` | `"youtube"` (produced by `audio2script`) or `"tts"` (produced by `script2audio`) — everything else about the format is identical between the two |
| `source_audio_path` | Path to the WAV file the segments' timestamps refer to |
| `segments[].index` | 0-based sentence order |
| `segments[].start_sec` / `end_sec` | Sentence boundaries in the audio, in seconds |
| `segments[].text_zh` | The sentence in Chinese |
| `segments[].pinyin` | Space-separated pinyin for the sentence |

Each entry in `segments` represents a single sentence:

- **`audio2script`**: Whisper produces segments bounded by pauses in the
  audio, and `service.py` further splits each segment on Chinese
  sentence-final punctuation (`。！？`), redistributing the timestamps in
  proportion to the character count of each resulting piece.
- **`script2audio`**: sentences come directly from the script file (split
  the same way, via `common/sentence_split.py`), and timestamps come from
  the actual duration of each sentence's synthesized audio clip as it is
  concatenated into the final track — there is no ASR step, since the
  text is already known.

## Outcome dataset

`python -m generateContents.export` reads every cached transcript under
`data/transcripts/*.json` (from both sources) and repackages them into a
flat dataset under `outcome/`:

```
outcome/
  dataset.csv
  audio/
    hBPECevVz-k_000.wav
    hBPECevVz-k_001.wav
    example_000.wav
    ...
```

`dataset.csv` has one row per sentence (not per content item):

| Column | Meaning |
|---|---|
| `content_id` | Same `content_id` as the source transcript |
| `source_type` | `"youtube"` or `"tts"` |
| `source_url` | The original YouTube URL for `youtube` rows; empty for `tts` rows (self-generated, no real-world source to link to) |
| `index` | The sentence's index within its content item |
| `start_sec` / `end_sec` | The sentence's position in its *original* source audio. For `youtube` rows this doubles as a real-world timestamp into that video (e.g. append `&t={start_sec}s` to `source_url`); for `tts` rows it's just an internal offset into the synthesized track |
| `text_zh` | The sentence in Chinese |
| `pinyin` | Space-separated pinyin for the sentence |
| `audio_path` | Path, relative to `outcome/`, to that sentence's own audio clip — already cut to `[start_sec, end_sec]`, playable on its own with no further seeking needed |

Each `audio_path` clip is cut fresh from the source recording every time
`export.py` runs, so `outcome/` can always be rebuilt from `data/`
without re-fetching, re-transcribing, or re-synthesizing anything.
