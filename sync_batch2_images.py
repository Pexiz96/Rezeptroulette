from __future__ import annotations

from sqlalchemy import MetaData, Table, select, update


BATCH2_IMAGE_PATHS = {
    "Cremige Pilzpfanne mit Spätzle": "/generated-images/pilzspaetzle.jpg",
    "Mediterrane Gemüse-Lasagne": "/generated-images/gemueselasagne.jpg",
    "Knusprige Ofenkartoffeln mit Kräuterquark": "/generated-images/ofenkartoffeln_kraeuterquark.jpg",
    "Gebratene Gnocchi mit Spinat und Tomaten": "/generated-images/gnocchi_spinat_tomaten.jpg",
    "Apfel-Zimt-Porridge": "/generated-images/apfel_zimt_porridge.jpg",
    "Couscous-Salat mit Feta": "/generated-images/couscous_salat_feta.jpg",
    "Hähnchen-Gemüse-Wrap mit Joghurt-Dressing": "/generated-images/haehnchen_gemuese_wrap.jpg",
    "Tomaten-Mozzarella-Pasta": "/generated-images/tomaten_mozzarella_pasta.jpg",
    "Beeren-Pancakes mit Joghurt": "/generated-images/beeren_pancakes.jpg",
    "Tomate-Mozzarella-Salat": "/generated-images/tomate_mozzarella_salat.jpg",
    "Pilzrisotto": "/generated-images/pilzrisotto.jpg",
    "Chili sin Carne": "/generated-images/chili_sin_carne.jpg",
    "French Toast mit Beeren": "/generated-images/french_toast_beeren.jpg",
    "Thunfisch-Nudel-Salat": "/generated-images/thunfisch_nudelsalat.jpg",
    "Gemüseomelett": "/generated-images/gemueseomelett.jpg",
}


def sync_batch2_recipe_images(engine) -> int:
    """Ensure every Batch-2 recipe uses a same-origin image URL."""
    metadata = MetaData()
    recipes = Table("recipes", metadata, autoload_with=engine)
    changed = 0

    with engine.begin() as conn:
        existing = {
            row.name: row.bild
            for row in conn.execute(select(recipes.c.name, recipes.c.bild)).all()
        }
        for name, image in BATCH2_IMAGE_PATHS.items():
            if name not in existing or existing[name] == image:
                continue
            conn.execute(
                update(recipes)
                .where(recipes.c.name == name)
                .values(bild=image)
            )
            changed += 1
    return changed
