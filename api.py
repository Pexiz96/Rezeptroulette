from __future__ import annotations

import base64
import re
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import Response
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

# Neue kuratierte Rezeptbilder liegen als Base64-Text im Repository, damit
# sie mit dem GitHub-Contents-Workflow versioniert werden können. Nach außen
# werden sie wie normale JPEG-Dateien ausgeliefert.
_generated_image_dir = Path(__file__).resolve().parent / ".github" / "generated_images"
_generated_name_re = re.compile(r"^[a-z0-9_\-]+\.jpg$")


@app.get("/generated-images/{filename}", include_in_schema=False)
def generated_recipe_image(filename: str):
    if not _generated_name_re.fullmatch(filename):
        raise HTTPException(status_code=404, detail="Bild nicht gefunden")
    source = _generated_image_dir / f"{filename}.b64"
    if not source.is_file():
        raise HTTPException(status_code=404, detail="Bild nicht gefunden")
    try:
        payload = base64.b64decode("".join(source.read_text(encoding="ascii").split()), validate=True)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Bild konnte nicht geladen werden") from exc
    return Response(
        content=payload,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
