from __future__ import annotations

import json

from sqlalchemy import MetaData, Table, select


EXTRA_RECIPES = [
    {
        "name": "Lachs-Spinat-Pasta",
        "kueche": "Italienisch",
        "bild": "/generated-images/lachs_spinat_pasta.jpg",
        "portionen": 2,
        "kochzeit": 30,
        "schwierigkeit": "Einfach",
        "tags": ["Pasta", "Fisch", "Schnell", "Protein"],
        "description": "Cremige Pasta mit gebratenem Lachs, frischem Spinat und Parmesan – schnell, herzhaft und alltagstauglich.",
        "zutaten": [
            "250 g Tagliatelle oder andere Pasta",
            "250 g Lachsfilet ohne Haut",
            "150 g frischer Blattspinat",
            "1 kleine Zwiebel",
            "1 Knoblauchzehe",
            "150 ml Sahne",
            "40 g Parmesan",
            "1 EL Olivenöl",
            "1 TL Zitronensaft",
            "Salz",
            "Pfeffer"
        ],
        "anleitung": "1. Pasta in Salzwasser bissfest kochen und etwas Nudelwasser auffangen.\n2. Lachs trocken tupfen, würfeln, salzen und pfeffern.\n3. Olivenöl in einer großen Pfanne erhitzen und den Lachs rundherum 3–4 Minuten anbraten. Herausnehmen und beiseitestellen.\n4. Zwiebel fein würfeln, Knoblauch hacken und beides in derselben Pfanne glasig anschwitzen.\n5. Spinat zugeben und zusammenfallen lassen.\n6. Sahne angießen, Parmesan einrühren und mit Zitronensaft, Salz und Pfeffer abschmecken. Bei Bedarf etwas Nudelwasser zugeben.\n7. Pasta und Lachs vorsichtig unterheben, kurz erwärmen und direkt servieren."
    },
    {
        "name": "Ofengemüse mit Feta",
        "kueche": "Mediterran",
        "bild": "/generated-images/ofengemuese_mit_feta.jpg",
        "portionen": 4,
        "kochzeit": 45,
        "schwierigkeit": "Einfach",
        "tags": ["Vegetarisch", "Ofengericht", "Gemüse", "Familie"],
        "description": "Buntes Ofengemüse mit Kartoffeln, Paprika und Zucchini, dazu würziger Feta und mediterrane Kräuter.",
        "zutaten": [
            "600 g Kartoffeln",
            "2 Paprika",
            "1 Zucchini",
            "2 Karotten",
            "1 rote Zwiebel",
            "200 g Feta",
            "3 EL Olivenöl",
            "1 TL Oregano",
            "1 TL Thymian",
            "1 Knoblauchzehe",
            "Salz",
            "Pfeffer"
        ],
        "anleitung": "1. Backofen auf 200 °C Ober-/Unterhitze vorheizen.\n2. Kartoffeln und Karotten in kleine Stücke schneiden. Paprika, Zucchini und Zwiebel ebenfalls grob schneiden.\n3. Gemüse mit Olivenöl, gehacktem Knoblauch, Oregano, Thymian, Salz und Pfeffer vermengen.\n4. Alles auf einem Blech oder in einer großen Auflaufform verteilen und 25 Minuten backen.\n5. Feta mittig auf das Gemüse legen und weitere 15–20 Minuten backen, bis Gemüse und Käse leicht gebräunt sind.\n6. Vor dem Servieren kurz durchziehen lassen und nach Wunsch mit frischen Kräutern bestreuen."
    },
    {
        "name": "Linsencurry mit Kokosmilch",
        "kueche": "Indisch",
        "bild": "/generated-images/linsencurry_kokosmilch.jpg",
        "portionen": 4,
        "kochzeit": 35,
        "schwierigkeit": "Einfach",
        "tags": ["Vegan", "Vegetarisch", "Curry", "Low Budget", "Meal Prep"],
        "description": "Cremiges rotes Linsencurry mit Kokosmilch, Tomaten und Gemüse – sättigend, günstig und ideal zum Vorkochen.",
        "zutaten": [
            "250 g rote Linsen",
            "1 Zwiebel",
            "2 Knoblauchzehen",
            "1 Stück Ingwer, ca. 2 cm",
            "1 Paprika",
            "1 Karotte",
            "400 g gehackte Tomaten",
            "400 ml Kokosmilch",
            "400 ml Gemüsebrühe",
            "2 TL Currypulver",
            "1 TL Kreuzkümmel",
            "1 EL Pflanzenöl",
            "150 g Blattspinat",
            "Salz",
            "Pfeffer",
            "optional: 250 g Reis"
        ],
        "anleitung": "1. Zwiebel, Knoblauch und Ingwer fein hacken. Paprika und Karotte klein schneiden.\n2. Öl in einem Topf erhitzen und Zwiebel, Knoblauch und Ingwer 2 Minuten anschwitzen.\n3. Currypulver und Kreuzkümmel kurz mitrösten.\n4. Paprika, Karotte und rote Linsen zugeben.\n5. Tomaten, Kokosmilch und Gemüsebrühe angießen und gut verrühren.\n6. Bei mittlerer Hitze 20–25 Minuten köcheln lassen, bis die Linsen weich sind. Gelegentlich umrühren.\n7. Spinat unterheben und 2 Minuten zusammenfallen lassen. Mit Salz und Pfeffer abschmecken.\n8. Nach Wunsch mit gekochtem Reis servieren."
    },
    {
        "name": "Hähnchen Teriyaki mit Reis",
        "kueche": "Asiatisch",
        "bild": "/generated-images/haehnchen_teriyaki_reis.jpg",
        "portionen": 4,
        "kochzeit": 35,
        "schwierigkeit": "Einfach",
        "tags": ["Hähnchen", "Reis", "Asiatisch", "Protein", "Pfanne"],
        "description": "Saftiges Hähnchen in würziger Teriyaki-Sauce mit Reis und knackigem Gemüse.",
        "zutaten": [
            "500 g Hähnchenbrust",
            "300 g Reis",
            "1 Brokkoli",
            "2 Karotten",
            "1 Paprika",
            "2 Frühlingszwiebeln",
            "5 EL Sojasauce",
            "2 EL Honig",
            "1 EL Reisessig",
            "1 TL Sesamöl",
            "1 TL Speisestärke",
            "1 Knoblauchzehe",
            "1 Stück Ingwer, ca. 2 cm",
            "1 EL Pflanzenöl",
            "1 EL Sesam"
        ],
        "anleitung": "1. Reis nach Packungsangabe garen.\n2. Hähnchen in mundgerechte Stücke schneiden. Brokkoli in Röschen teilen, Karotten und Paprika schneiden.\n3. Sojasauce, Honig, Reisessig, Sesamöl, Speisestärke, fein gehackten Knoblauch und Ingwer verrühren.\n4. Pflanzenöl in einer großen Pfanne erhitzen und das Hähnchen kräftig anbraten.\n5. Gemüse zugeben und 5–7 Minuten unter Rühren braten, sodass es noch etwas Biss hat.\n6. Teriyaki-Sauce angießen und 2–3 Minuten einkochen lassen, bis sie glänzend bindet.\n7. Mit Reis anrichten und mit Frühlingszwiebeln und Sesam bestreuen."
    },
    {
        "name": "Kartoffel-Brokkoli-Auflauf",
        "kueche": "Deutsch",
        "bild": "/generated-images/kartoffel_brokkoli_auflauf.jpg",
        "portionen": 4,
        "kochzeit": 55,
        "schwierigkeit": "Einfach",
        "tags": ["Auflauf", "Vegetarisch", "Kartoffeln", "Familie"],
        "description": "Cremiger Kartoffel-Brokkoli-Auflauf mit goldbrauner Käsekruste – unkomplizierte Familienküche aus dem Ofen.",
        "zutaten": [
            "800 g Kartoffeln",
            "500 g Brokkoli",
            "1 Zwiebel",
            "200 ml Sahne",
            "200 ml Milch",
            "180 g geriebener Käse",
            "1 EL Butter",
            "1 TL Senf",
            "Salz",
            "Pfeffer",
            "Muskat"
        ],
        "anleitung": "1. Backofen auf 190 °C Ober-/Unterhitze vorheizen und eine Auflaufform mit Butter einfetten.\n2. Kartoffeln schälen, in dünne Scheiben schneiden und 8 Minuten in Salzwasser vorgaren.\n3. Brokkoli in Röschen teilen und für die letzten 3 Minuten zu den Kartoffeln geben. Anschließend abgießen.\n4. Zwiebel fein würfeln. Sahne, Milch, Senf, Salz, Pfeffer und Muskat verrühren.\n5. Kartoffeln, Brokkoli und Zwiebel in der Form verteilen und die Sahnemischung darübergeben.\n6. Mit geriebenem Käse bestreuen.\n7. 30–35 Minuten backen, bis die Oberfläche goldbraun ist und die Kartoffeln weich sind."
    },
    {
        "name": "Caesar Salat mit Hähnchen",
        "kueche": "Amerikanisch",
        "bild": "/generated-images/caesar_salat_haehnchen.jpg",
        "portionen": 2,
        "kochzeit": 25,
        "schwierigkeit": "Einfach",
        "tags": ["Salat", "Hähnchen", "Protein", "Schnell"],
        "description": "Knackiger Romanasalat mit gebratenem Hähnchen, Parmesan, Croûtons und einem cremigen Caesar-Dressing.",
        "zutaten": [
            "300 g Hähnchenbrust",
            "1 Romanasalat",
            "80 g Weißbrot",
            "40 g Parmesan",
            "1 EL Olivenöl",
            "100 g Naturjoghurt",
            "1 EL Mayonnaise",
            "1 TL Senf",
            "1 TL Zitronensaft",
            "1 kleine Knoblauchzehe",
            "Salz",
            "Pfeffer"
        ],
        "anleitung": "1. Hähnchenbrust mit Salz und Pfeffer würzen und in einer Pfanne mit etwas Olivenöl von beiden Seiten vollständig durchbraten. Anschließend in Streifen schneiden.\n2. Weißbrot würfeln und in derselben Pfanne goldbraun rösten.\n3. Romanasalat waschen, trocken schleudern und grob schneiden.\n4. Für das Dressing Joghurt, Mayonnaise, Senf, Zitronensaft und fein geriebenen Knoblauch verrühren. Mit Salz und Pfeffer abschmecken.\n5. Salat mit Dressing vermengen, Hähnchen und Croûtons darauf verteilen.\n6. Parmesan darüberhobeln und sofort servieren."
    },
    {
        "name": "Shakshuka",
        "kueche": "Orientalisch",
        "bild": "/generated-images/shakshuka.jpg",
        "portionen": 2,
        "kochzeit": 30,
        "schwierigkeit": "Einfach",
        "tags": ["Vegetarisch", "Frühstück", "Pfanne", "Protein"],
        "description": "Eier in einer würzigen Tomaten-Paprika-Sauce – perfekt zum Frühstück, Brunch oder als schnelles Abendessen.",
        "zutaten": [
            "4 Eier",
            "1 rote Paprika",
            "1 Zwiebel",
            "2 Knoblauchzehen",
            "400 g gehackte Tomaten",
            "1 EL Tomatenmark",
            "1 EL Olivenöl",
            "1 TL Kreuzkümmel",
            "1 TL Paprikapulver",
            "0,5 TL Chiliflocken",
            "Salz",
            "Pfeffer",
            "2 EL gehackte Petersilie"
        ],
        "anleitung": "1. Zwiebel und Paprika klein schneiden, Knoblauch fein hacken.\n2. Olivenöl in einer großen Pfanne erhitzen und Zwiebel sowie Paprika 5 Minuten anbraten.\n3. Knoblauch, Tomatenmark, Kreuzkümmel, Paprikapulver und Chiliflocken kurz mitrösten.\n4. Gehackte Tomaten zugeben, mit Salz und Pfeffer würzen und 10 Minuten offen köcheln lassen.\n5. Vier Mulden in die Sauce drücken und die Eier hineinschlagen.\n6. Pfanne abdecken und die Eier bei kleiner Hitze 6–9 Minuten stocken lassen, bis das Eiweiß fest und das Eigelb nach Wunsch gegart ist.\n7. Mit Petersilie bestreuen und direkt aus der Pfanne servieren."
    },
    {
        "name": "Quarkbowl mit Beeren",
        "kueche": "Frühstück",
        "bild": "/generated-images/quarkbowl_beeren.jpg",
        "portionen": 1,
        "kochzeit": 10,
        "schwierigkeit": "Einfach",
        "tags": ["Frühstück", "Protein", "Schnell", "Süß"],
        "description": "Cremige Quarkbowl mit frischen Beeren, knusprigen Haferflocken und Nüssen – in wenigen Minuten fertig.",
        "zutaten": [
            "250 g Magerquark",
            "50 ml Milch",
            "100 g Erdbeeren",
            "50 g Heidelbeeren",
            "50 g Himbeeren",
            "30 g Haferflocken",
            "15 g Walnüsse",
            "1 TL Honig",
            "optional: frische Minze"
        ],
        "anleitung": "1. Magerquark mit Milch glatt und cremig rühren.\n2. Erdbeeren waschen und in Stücke schneiden. Heidelbeeren und Himbeeren ebenfalls waschen.\n3. Quark in eine Schüssel geben und die Beeren darauf verteilen.\n4. Haferflocken und grob gehackte Walnüsse darüberstreuen.\n5. Mit Honig beträufeln und nach Wunsch mit frischer Minze garnieren."
    }
]


def ensure_extra_recipes(engine) -> int:
    """Insert the curated V3 recipes once, without overwriting user data."""
    metadata = MetaData()
    table = Table("recipes", metadata, autoload_with=engine)
    inserted = 0
    with engine.begin() as conn:
        existing = set(conn.execute(select(table.c.name)).scalars().all())
        for recipe in EXTRA_RECIPES:
            if recipe["name"] in existing:
                continue
            row = {
                "name": recipe["name"],
                "kueche": recipe["kueche"],
                "bild": recipe["bild"],
                "portionen": recipe["portionen"],
                "kochzeit": recipe["kochzeit"],
                "schwierigkeit": recipe["schwierigkeit"],
                "tags_json": json.dumps(recipe["tags"], ensure_ascii=False),
                "zutaten_json": json.dumps(recipe["zutaten"], ensure_ascii=False),
                "anleitung": recipe["anleitung"],
                "description": recipe["description"],
                "owner_user_id": None,
                "source_url": "",
            }
            row = {key: value for key, value in row.items() if key in table.c}
            conn.execute(table.insert().values(**row))
            existing.add(recipe["name"])
            inserted += 1
    return inserted
