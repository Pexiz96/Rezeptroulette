from __future__ import annotations

import base64
import gzip
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent


def _read_payload(parts: Iterable[str]) -> str:
    chunks: list[str] = []
    for relative in parts:
        path = ROOT / relative
        if not path.exists():
            raise RuntimeError(f"Upgrade-Payload fehlt: {relative}")
        chunks.append("".join(path.read_text(encoding="utf-8").split()))
    return "".join(chunks)


def exec_gzip_base64_payload(namespace: dict, parts: Iterable[str], logical_filename: str) -> None:
    encoded = _read_payload(parts)
    try:
        compressed = base64.b64decode(encoded, validate=True)
        source = gzip.decompress(compressed).decode("utf-8")
    except Exception as exc:
        raise RuntimeError(f"Upgrade-Payload für {logical_filename} ist beschädigt") from exc

    filename = str(ROOT / logical_filename)
    code = compile(source, filename, "exec")
    namespace["__file__"] = filename
    exec(code, namespace, namespace)
