from __future__ import annotations

import base64
import io
import re
from pathlib import Path
from urllib.request import Request, urlopen

from fastapi import HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image

from payload_loader import exec_gzip_base64_payload

exec_gzip_base64_payload(
    globals(),
    [".github/upgrade_payload/api.py.gz.b64"],
    "api.py",
)

_base_dir = Path(__file__).resolve().parent
_images_dir = _base_dir / "bilder"
_static_images_dir = _base_dir / "static" / "images"
if _images_dir.is_dir() and not any(getattr(route, "path", None) == "/bilder" for route in app.routes):
    app.mount("/bilder", StaticFiles(directory=str(_images_dir)), name="bilder")

_generated_image_dir = _base_dir / ".github" / "generated_images"
_generated_name_re = re.compile(r"^[a-z0-9_\-]+\.jpg$")
_safe_filename_re = re.compile(r"^[^/\\]+$")

# Die 15 Bilder des zweiten Rezept-Batches liegen zusätzlich gemeinsam in
# einem 5x3-Sprite. Einzeldateien haben Vorrang; das Sprite bleibt als Fallback.
_BATCH2_SPRITE_TILES = {
    "pilzspaetzle.jpg": 0,
    "gemueselasagne.jpg": 1,
    "ofenkartoffeln_kraeuterquark.jpg": 2,
    "gnocchi_spinat_tomaten.jpg": 3,
    "apfel_zimt_porridge.jpg": 4,
    "couscous_salat_feta.jpg": 5,
    "haehnchen_gemuese_wrap.jpg": 6,
    "tomaten_mozzarella_pasta.jpg": 7,
    "beeren_pancakes.jpg": 8,
    "tomate_mozzarella_salat.jpg": 9,
    "pilzrisotto.jpg": 10,
    "chili_sin_carne.jpg": 11,
    "french_toast_beeren.jpg": 12,
    "thunfisch_nudelsalat.jpg": 13,
    "gemueseomelett.jpg": 14,
}

_REMOTE_GENERATED_IMAGES = {
    "gemueselasagne.jpg": "https://itsonly.recipes/images/recipeimages/garden-veggie-lasagna.webp",
    "ofenkartoffeln_kraeuterquark.jpg": "https://vegnews.com/media/W1siZiIsIjU0MzM4L1VudGl0bGVkIGRlc2lnbiAtIDIwMjUtMDgtMjVUMTQ0NTU2LjE2Mi5wbmciXSxbInAiLCJjcm9wX3Jlc2l6ZWQiLCIxNTk5eDk0NSswKzAiLCIxNjAweDk0Nl4iLHsiZm9ybWF0IjoianBnIn1dLFsicCIsIm9wdGltaXplIl1d/Untitled%20design%20-%202025-08-25T144556.162.png?sha=90f99779aa88195b",
    "gnocchi_spinat_tomaten.jpg": "https://img.chefkoch-cdn.de/rezepte/3508451522698641/bilder/1229293/crop-640x427/gnocchi-mit-spinat-und-tomaten.jpg",
    "apfel_zimt_porridge.jpg": "https://itsonly.recipes/images/recipeimages/apple-cinnamon-porridge.webp",
    "couscous_salat_feta.jpg": "https://s7g10.scene7.com/is/image/aldi/202205050000",
    "haehnchen_gemuese_wrap.jpg": "https://images.mrcook.app/recipe-image/0198ab6d-3e66-7afb-a3d0-2ef6fb0fd8c5?cacheKey=RnJpLCAxNSBBdWcgMjAyNSAwMTo1MjowMiBHTVQ%3D",
    "tomaten_mozzarella_pasta.jpg": "https://cdn.gutekueche.de/media/recipe/69297/tomaten-mozzarella-sosse.jpg",
    "beeren_pancakes.jpg": "https://itesco.cz/imgglobal/content_platform/recipes/main/67/6755f984a73bd34fff082dbc8f7490fe.jpg",
    "tomate_mozzarella_salat.jpg": "https://api.bulmag.org/images/342b0fa92ab581373f0f8e4bf7e4afdf.jpeg",
    "pilzrisotto.jpg": "https://www.datocms-assets.com/20941/1756899974-mushroom-guide-mushroom-risotto.jpeg?auto=format&dpr=0.18&fit=max&w=4763",
    "chili_sin_carne.jpg": "https://i.pinimg.com/originals/4f/79/ec/4f79ec53a5031e02da786aff478ce9fd.jpg",
    "french_toast_beeren.jpg": "https://food.fnr.sndimg.com/content/dam/images/food/fullset/2013/12/9/0/FNK_French-Toast-with-Mixed-Berries_s4x3.jpg.rend.hgtvcom.1280.960.suffix/1387416657918.webp",
    "thunfisch_nudelsalat.jpg": "https://ip.index.hr/remote/bucket.index.hr/b/index/2a3127a4-c4b0-4c39-9bbd-ab23dff50802.jpg?width=500",
    "gemueseomelett.jpg": "https://www.gutekueche.at/storage/media/recipe/166532/gemueseomelette.jpg",
}


def _decode_b64_file(path: Path) -> bytes:
    return base64.b64decode("".join(path.read_text(encoding="ascii").split()), validate=True)


def _batch2_sprite_image(filename: str) -> bytes | None:
    index = _BATCH2_SPRITE_TILES.get(filename)
    sprite_source = _generated_image_dir / "batch2_sprite.jpg.b64"
    if index is None or not sprite_source.is_file():
        return None

    try:
        sprite_bytes = _decode_b64_file(sprite_source)
        with Image.open(io.BytesIO(sprite_bytes)) as sprite:
            sprite = sprite.convert("RGB")
            cols, rows = 5, 3
            tile_w = sprite.width // cols
            tile_h = sprite.height // rows
            col = index % cols
            row = index // cols
            tile = sprite.crop((col * tile_w, row * tile_h, (col + 1) * tile_w, (row + 1) * tile_h))
            out = io.BytesIO()
            tile.save(out, format="JPEG", quality=92, optimize=True)
            return out.getvalue()
    except Exception:
        return None


def _serve_generated_image(filename: str) -> Response:
    if not _generated_name_re.fullmatch(filename):
        raise HTTPException(status_code=404, detail="Bild nicht gefunden")

    # Eine eigene Datei ist immer die beste Quelle und hat Vorrang vor dem
    # komprimierten Sprite. Dadurch können hochwertige Bilder einzeln ersetzt werden.
    source = _generated_image_dir / f"{filename}.b64"
    if source.is_file():
        try:
            payload = _decode_b64_file(source)
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Bild konnte nicht geladen werden") from exc
        return Response(content=payload, media_type="image/jpeg", headers={"Cache-Control": "no-cache"})

    sprite_payload = _batch2_sprite_image(filename)
    if sprite_payload:
        return Response(content=sprite_payload, media_type="image/jpeg", headers={"Cache-Control": "no-cache"})

    remote_url = _REMOTE_GENERATED_IMAGES.get(filename)
    if not remote_url:
        raise HTTPException(status_code=404, detail="Bild nicht gefunden")

    try:
        request = Request(remote_url, headers={
            "User-Agent": "Mozilla/5.0 Rezeptroulette/3.0",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        })
        with urlopen(request, timeout=10) as remote:
            payload = remote.read(8 * 1024 * 1024)
            media_type = remote.headers.get_content_type() or "image/jpeg"
        if not payload or not media_type.startswith("image/"):
            raise ValueError("Remote response is not an image")
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Rezeptbild konnte nicht geladen werden") from exc

    return Response(content=payload, media_type=media_type, headers={"Cache-Control": "no-cache"})


@app.get("/generated-images/{filename}", include_in_schema=False)
def generated_recipe_image(filename: str):
    return _serve_generated_image(filename)


# Das alte Frontend setzt bei allen lokalen Bildern pauschal /static/images/
# davor. Hier korrigieren wir die historischen Sonderfälle serverseitig, damit
# die Bilder auch ohne installierten Service Worker funktionieren.
@app.middleware("http")
async def repair_legacy_recipe_image_paths(request, call_next):
    path = request.url.path

    marker = "generated-images/"
    if path.startswith("/static/images//generated-images/") or path.startswith("/static/images/generated-images/"):
        filename = path[path.index(marker) + len(marker):]
        if _generated_name_re.fullmatch(filename):
            return _serve_generated_image(filename)

    if path.startswith("/static/images/"):
        filename = path[len("/static/images/"):].lstrip("/")

        # Manche Datensätze enthalten bereits 'bilder/' im Feld, andere nur
        # den pdf_*.png-Dateinamen. Beide Varianten liegen physisch in /bilder.
        if filename.startswith("bilder/"):
            filename = filename[len("bilder/"):]

        if _safe_filename_re.fullmatch(filename):
            static_candidate = _static_images_dir / filename
            if not static_candidate.is_file():
                legacy_candidate = _images_dir / filename
                if legacy_candidate.is_file():
                    return FileResponse(legacy_candidate, headers={"Cache-Control": "no-cache"})

    return await call_next(request)
