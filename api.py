from __future__ import annotations

import base64
import re
from pathlib import Path
from urllib.request import Request, urlopen

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

# Neue kuratierte Rezeptbilder liegen teilweise als Base64-Text im Repository.
# Für Batch 2 werden die Bilder über denselben lokalen Endpunkt ausgeliefert.
# Dadurch lädt das Frontend ausschließlich same-origin URLs und ist nicht von
# Hotlink-Sperren fremder Webseiten abhängig.
_generated_image_dir = Path(__file__).resolve().parent / ".github" / "generated_images"
_generated_name_re = re.compile(r"^[a-z0-9_\-]+\.jpg$")

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


@app.get("/generated-images/{filename}", include_in_schema=False)
def generated_recipe_image(filename: str):
    if not _generated_name_re.fullmatch(filename):
        raise HTTPException(status_code=404, detail="Bild nicht gefunden")

    source = _generated_image_dir / f"{filename}.b64"
    if source.is_file():
        try:
            payload = base64.b64decode("".join(source.read_text(encoding="ascii").split()), validate=True)
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Bild konnte nicht geladen werden") from exc
        return Response(
            content=payload,
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=31536000, immutable"},
        )

    remote_url = _REMOTE_GENERATED_IMAGES.get(filename)
    if not remote_url:
        raise HTTPException(status_code=404, detail="Bild nicht gefunden")

    try:
        request = Request(
            remote_url,
            headers={
                "User-Agent": "Mozilla/5.0 Rezeptroulette/3.0",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            },
        )
        with urlopen(request, timeout=10) as remote:
            payload = remote.read(8 * 1024 * 1024)
            media_type = remote.headers.get_content_type() or "image/jpeg"
        if not payload or not media_type.startswith("image/"):
            raise ValueError("Remote response is not an image")
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Rezeptbild konnte nicht geladen werden") from exc

    return Response(
        content=payload,
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )
