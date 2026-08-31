from __future__ import annotations

from sqlalchemy import MetaData, Table, select, update


def sync_batch2_recipe_images(engine) -> int:
    """Update image paths of existing Batch-2 recipes to the paths in the seed file."""
    from extra_recipes_batch2 import EXTRA_RECIPES_BATCH2

    metadata = MetaData()
    recipes = Table("recipes", metadata, autoload_with=engine)
    changed = 0

    with engine.begin() as conn:
        existing = {
            row.name: row.bild
            for row in conn.execute(select(recipes.c.name, recipes.c.bild)).all()
        }
        for recipe in EXTRA_RECIPES_BATCH2:
            name = recipe.get("name")
            image = recipe.get("bild")
            if not name or not image or name not in existing:
                continue
            if existing[name] == image:
                continue
            conn.execute(
                update(recipes)
                .where(recipes.c.name == name)
                .values(bild=image)
            )
            changed += 1
    return changed
