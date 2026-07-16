"""Dictation web app: serves the packaged outcome/ dataset (dataset.csv +
audio/) to the static frontend under frontend/, and exposes a small JSON
API for it to read.

This is a read-only viewer over outcome/ — it never writes to data/ or
outcome/, and does not touch the generation pipeline. Run export.py first
so outcome/dataset.csv exists.
"""

from __future__ import annotations

import csv
from pathlib import Path

from flask import Flask, abort, jsonify, send_from_directory

from generateContents.common.config import SystemConfig, load_config
from generateContents.common.logger import get_logger

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

logger = get_logger(__name__)


def _load_sentences(outcome_dir: Path) -> list[dict]:
    csv_path = outcome_dir / "dataset.csv"
    if not csv_path.is_file():
        return []
    with csv_path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def create_app(config: SystemConfig | None = None) -> Flask:
    config = config or load_config()
    outcome_dir = Path(config.paths.outcome_dir).resolve()

    app = Flask(__name__, static_folder=None)

    @app.get("/api/contents")
    def list_contents():
        rows = _load_sentences(outcome_dir)
        counts: dict[str, int] = {}
        for row in rows:
            counts[row["content_id"]] = counts.get(row["content_id"], 0) + 1
        contents = [
            {"content_id": content_id, "sentence_count": count}
            for content_id, count in counts.items()
        ]
        return jsonify(contents)

    @app.get("/api/contents/<content_id>/sentences")
    def list_sentences(content_id: str):
        rows = _load_sentences(outcome_dir)
        sentences = [row for row in rows if row["content_id"] == content_id]
        if not sentences:
            abort(404, description=f"No sentences found for content_id={content_id}")
        sentences.sort(key=lambda row: int(row["index"]))
        return jsonify(sentences)

    @app.get("/audio/<path:filename>")
    def serve_audio(filename: str):
        return send_from_directory(outcome_dir / "audio", filename)

    @app.get("/")
    def serve_index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.get("/<path:filename>")
    def serve_static(filename: str):
        return send_from_directory(FRONTEND_DIR, filename)

    return app


def main() -> None:
    config = load_config()
    app = create_app(config)
    logger.info(
        "Starting dictation web app on %s:%d", config.web.host, config.web.port
    )
    app.run(host=config.web.host, port=config.web.port, debug=config.web.debug)


if __name__ == "__main__":
    main()
