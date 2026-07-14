# Error handling and logging conventions

- Every public function logs at `INFO` level on start and success, and at
  `ERROR` level on failure.
- There are no bare `except` clauses. Every function catches specific
  exceptions and wraps them in the module's own exception type
  (`raise XxxError(...) from e`), which preserves the original traceback
  and prevents exceptions from third-party libraries (yt-dlp,
  faster-whisper, edge-tts, pydub) from leaking out of the module.
