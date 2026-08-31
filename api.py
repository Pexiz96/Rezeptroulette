from __future__ import annotations

from pathlib import Path

from fastapi.staticfiles import StaticFiles

from payload_loader import exec_gzip_base64_payload

exec_gzip_base64_payload(
    globals(),
    [".github/upgrade_payload/api.py.gz.b64"],
    "api.py",
)

# Die bestehenden Rezeptbilder liegen historisch im Repository-Ordner
# "bilder". V3 referenziert sie unter /bilder/<dateiname>. Den Ordner
# deshalb zusätzlich als statische Route bereitstellen.
_images_dir = Path(__file__).resolve().parent / "bilder"
if _images_dir.is_dir() and not any(getattr(route, "path", None) == "/bilder" for route in app.routes):
    app.mount("/bilder", StaticFiles(directory=str(_images_dir)), name="bilder")
