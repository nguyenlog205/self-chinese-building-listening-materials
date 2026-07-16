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

## Word vocabulary dataset

`python -m generateContents.word_export` reads the same cached
transcripts under `data/transcripts/*.json`, segments every sentence into
words, and produces a second, additive dataset under `outcome/`:

```
outcome/
  word.csv
  word_audio/
    e164c5dd00a6.wav
    6b2db7797ea8.wav
    ...
```

`word.csv` has one row per unique `(word, pinyin)` pair, across every
content item — the same word recurring in many sentences is deduplicated
into a single row. Words are segmented with `jieba`
(`common/segmentation.py`) and their pinyin comes from the same
`pinyin_converter.to_pinyin()` used for sentence-level transcripts:

| Column | Meaning |
|---|---|
| `word` | The segmented word, in Chinese |
| `pinyin` | Space-separated pinyin for the word, in the style set by `modules.word_export.pinyin_style` |
| `meaning` | English translation, looked up from `data/word_hsk/hsk_*.csv`; empty if the word isn't found in any HSK level |
| `hsk_level` | HSK level (`"1"`–`"6"`, or `"7-9"` for the combined advanced band), looked up the same way; empty if not found — never guessed |
| `audio_path` | Path, relative to `outcome/`, to a standalone audio clip of the word being spoken on its own |
| `audio_source` | How `audio_path` was produced. Currently always `"tts"` (edge-tts synthesizing the word in isolation); reserved for a future `"sliced"` value (cut from the word's position inside its sentence's natural audio) without a schema change |

Lookup against `data/word_hsk/` first tries an exact `(word, pinyin)`
match (pinyin compared ignoring whitespace, since 多音字 like 还
(huán/hái) or 得 (dé/děi/de) read differently depending on context), and
falls back to a word-only match if no exact reading is found. The HSK
level for each `hsk_*.csv` file comes from its filename (`hsk_04.csv` ->
`"4"`, `hsk_79.csv` -> `"7-9"`).

`audio_path` clips are synthesized once per unique `(word, pinyin)` and
cached under `word_audio/` by a hash of that pair — re-running
`word_export.py` reuses existing clips instead of re-synthesizing them,
unless `modules.word_export.overwrite_existing` is set. `word_export.py`
never modifies `outcome/dataset.csv` or `outcome/audio/`.
