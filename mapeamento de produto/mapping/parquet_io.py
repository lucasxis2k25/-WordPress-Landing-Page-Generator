from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable


def _pyarrow():
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:  # pragma: no cover - exercised only in an unprovisioned environment
        raise RuntimeError("Parquet support requires pyarrow; install the project dependency first") from exc
    return pa, pq


def write_parquet(records: Iterable[dict[str, Any]], path: str | Path) -> None:
    pa, pq = _pyarrow()
    rows = list(records)
    table = pa.Table.from_pylist(rows)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, destination, compression="zstd", use_dictionary=True)


def read_parquet(path: str | Path) -> list[dict[str, Any]]:
    _, pq = _pyarrow()
    return pq.read_table(path).to_pylist()
