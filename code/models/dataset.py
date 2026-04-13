"""
Dataset access helpers.

This avoids intermittent DuckDB HTTPS SSL failures by caching the parquet file locally
and querying the local file thereafter.
"""

from __future__ import annotations

from pathlib import Path
from urllib.request import Request, urlopen


PUZZLE_PARQUET_URL = (
    "https://huggingface.co/api/datasets/jackcai1206/killer-sudoku-puzzles/parquet/default/train/0.parquet"
)

def ensure_local_parquet() -> str:
    """
    Ensure the parquet dataset exists locally and return its absolute path.
    """
    path = (Path(__file__).resolve().parents[2] / "data" / "killer_sudoku_train.parquet").resolve()

    if path.exists():
        return path.as_posix()

    path.parent.mkdir(parents=True, exist_ok=True)
    request = Request(PUZZLE_PARQUET_URL)

    with urlopen(request, timeout=30) as response:
        data = response.read()

    path.write_bytes(data)
    return path.as_posix()
