from __future__ import annotations

import json
from sqlalchemy import MetaData, Table, select

EXTRA_RECIPES_BATCH2 = [
    {
        "name": "Cremige Pilzpfanne mit Spätzle",
        "kueche": "Deutsch",
        "bild": "/generated-images/pilzspaetzle.jpg",
        "portionen": 4,
        "kochzeit": 30,
        "schwierigkeit": "Einfach",
        "tags": ["Vegetarisch", "Spätzle", "Pilze", "Schnell", "Pfanne"],
        "description": "Cremige Spätzle mit gebratenen Champignons, Zwiebeln und Petersilie – unkompliziertes Wohlfühlessen aus einer Pfanne.",
        "zutaten": ["500 g frische Spätzle", "400 g Champignons", "1 Zwiebel", "1 Knoblauchzehe", "200 ml Sahne", "100 ml Gemüsebrühe", "50 g Parmesan", "1 EL Butter", "1 EL Öl", "2 EL gehackte Petersilie", "Salz", "Pfeffer", "Muskat"],
        "anleitung": "1. Champignons putzen und in Scheiben schneiden. Zwiebel fein würfeln, Knoblauch hacken.\n2. Öl und Butter in einer großen Pfanne erhitzen und die Champignons kräftig anbraten, bis sie Farbe bekommen.\n3. Zwiebel und Knoblauch zugeben und 2 Minuten mitbraten.\n4. Spätzle in die Pfanne geben und kurz mitrösten.\n5. Mit Gemüsebrühe und Sahne ablöschen und 5 Minuten sanft köcheln lassen.\n6. Parmesan einrühren und mit Salz, Pfeffer und Muskat abschmecken.\n7. Mit Petersilie bestreuen und direkt servieren."
    },
    {
        "name": "Mediterrane Gemüse-Lasagne",
        "kueche": "Italienisch",
        "bild": "https://itsonly.recipes/images/recipeimages/garden-veggie-lasagna.webp",
        "portionen": 4,
        "kochzeit": 65,
        "schwierigkeit": "Mittel",
        "tags": ["Vegetarisch", "Lasagne", "Ofengericht", "Gemüse", "Familie"],
        "description": "Saftige Lasagne mit Zucchini, Aubergine, Paprika, Tomatensauce und einer goldbraunen Käsekruste.",
        "zutaten": ["9 Lasagneplatten", "1 Zucchini", "1 kleine Aubergine", "1 rote Paprika", "1 Zwiebel", "2 Knoblauchzehen", "500 g passierte Tomaten", "200 g Crème fraîche", "200 g Mozzarella", "50 g Parmesan", "2 EL Olivenöl", "1 TL Oregano", "1 TL Basilikum", "Salz", "Pfeffer"],
        "anleitung": "1. Backofen auf 190 °C Ober-/Unterhitze vorheizen.\n2. Zucchini, Aubergine und Paprika klein schneiden. Zwiebel und Knoblauch hacken.\n3. Olivenöl erhitzen und das Gemüse 8 Minuten anbraten. Zwiebel und Knoblauch kurz mitbraten.\n4. Passierte Tomaten zugeben, mit Oregano, Basilikum, Salz und Pfeffer würzen und 8 Minuten köcheln lassen.\n5. Eine dünne Schicht Sauce in eine Auflaufform geben, dann abwechselnd Lasagneplatten, Gemüsesauce und kleine Kleckse Crème fraîche schichten.\n6. Mit Mozzarella und Parmesan abschließen.\n7. 35–40 Minuten backen und vor dem Anschneiden 5 Minuten ruhen lassen."
    },
    {
        "name": "Knusprige Ofenkartoffeln mit Kräuterquark",
        "kueche": "Deutsch",
        "bild": "https://vegnews.com/media/W1siZiIsIjU0MzM4L1VudGl0bGVkIGRlc2lnbiAtIDIwMjUtMDgtMjVUMTQ0NTU2LjE2Mi5wbmciXSxbInAiLCJjcm9wX3Jlc2l6ZWQiLCIxNTk5eDk0NSswKzAiLCIxNjAweDk0Nl4iLHsiZm9ybWF0IjoianBnIn1dLFsicCIsIm9wdGltaXplIl1d/Untitled%20design%20-%202025-08-25T144556.162.png?sha=90f99779aa88195b",
        "portionen": 4,
        "kochzeit": 45,
        "schwierigkeit": "Einfach",
        "tags": ["Vegetarisch", "Kartoffeln", "Ofengericht", "Low Budget"],
        "description": "Würzige Kartoffelspalten aus dem Ofen mit cremigem Kräuterquark – günstig, einfach und perfekt als Hauptgericht oder Beilage.",
        "zutaten": ["1 kg Kartoffeln", "2 EL Olivenöl", "1 TL Paprikapulver", "1 TL Knoblauchpulver", "1 TL getrocknete Kräuter", "250 g Magerquark", "100 g Naturjoghurt", "2 EL Schnittlauch", "1 EL Petersilie", "1 TL Zitronensaft", "Salz", "Pfeffer"],
        "anleitung": "1. Backofen auf 210 °C Ober-/Unterhitze vorheizen.\n2. Kartoffeln gründlich waschen und in Spalten schneiden.\n3. Mit Olivenöl, Paprikapulver, Knoblauchpulver, Kräutern, Salz und Pfeffer vermengen.\n4. Auf einem Blech verteilen und 35–40 Minuten goldbraun backen, nach der Hälfte der Zeit wenden.\n5. Quark und Joghurt verrühren. Schnittlauch, Petersilie und Zitronensaft unterheben.\n6. Kräuterquark mit Salz und Pfeffer abschmecken und zu den heißen Kartoffeln servieren."
    },
    {
        "name": "Gebratene Gnocchi mit Spinat und Tomaten",
        "kueche": "Italienisch",
        "bild": "https://img.chefkoch-cdn.de/rezepte/3508451522698641/bilder/1229293/crop-640x427/gnocchi-mit-spinat-und-tomaten.jpg",
        "portionen": 2,
        "kochzeit": 20,
        "schwierigkeit": "Einfach",
        "tags": ["Vegetarisch", "Gnocchi", "Schnell", "Pfanne"],
        "description": "Goldbraun gebratene Gnocchi mit Babyspinat, Cherrytomaten und Parmesan – in nur 20 Minuten fertig.",
        "zutaten": ["500 g Gnocchi aus dem Kühlregal", "200 g Cherrytomaten", "150 g Babyspinat", "1 Knoblauchzehe", "40 g Parmesan", "1 EL Butter", "1 EL Olivenöl", "Salz", "Pfeffer"],
        "anleitung": "1. Cherrytomaten halbieren und Knoblauch fein hacken.\n2. Butter und Olivenöl in einer großen Pfanne erhitzen.\n3. Gnocchi 6–8 Minuten unter gelegentlichem Wenden goldbraun braten.\n4. Knoblauch und Tomaten zugeben und weitere 3 Minuten braten.\n5. Spinat portionsweise unterheben und zusammenfallen lassen.\n6. Mit Salz und Pfeffer abschmecken und Parmesan darüberreiben."
    },
    {
        "name": "Apfel-Zimt-Porridge",
        "kueche": "Frühstück",
        "bild": "https://itsonly.recipes/images/recipeimages/apple-cinnamon-porridge.webp",
        "portionen": 2,
        "kochzeit": 15,
        "schwierigkeit": "Einfach",
        "tags": ["Frühstück", "Vegetarisch", "Süß", "Schnell"],
        "description": "Warmes Haferporridge mit Apfel, Zimt und Walnüssen – ein schnelles, sättigendes Frühstück.",
        "zutaten": ["100 g Haferflocken", "400 ml Milch oder Pflanzendrink", "1 Apfel", "1 TL Zimt", "1 TL Honig oder Ahornsirup", "20 g Walnüsse", "1 Prise Salz"],
        "anleitung": "1. Apfel waschen, entkernen und die Hälfte grob raspeln, den Rest in dünne Spalten schneiden.\n2. Haferflocken, Milch, geriebenen Apfel, Zimt und eine Prise Salz in einen Topf geben.\n3. Unter Rühren 5–7 Minuten cremig köcheln lassen.\n4. Porridge auf zwei Schalen verteilen.\n5. Mit Apfelspalten, gehackten Walnüssen und Honig oder Ahornsirup servieren."
    },
    {
        "name": "Couscous-Salat mit Feta",
        "kueche": "Mediterran",
        "bild": "https://s7g10.scene7.com/is/image/aldi/202205050000",
        "portionen": 4,
        "kochzeit": 20,
        "schwierigkeit": "Einfach",
        "tags": ["Vegetarisch", "Salat", "Schnell", "Meal Prep"],
        "description": "Frischer Couscous-Salat mit Gurke, Tomaten, Paprika, Petersilie und Feta – ideal für Meal Prep und warme Tage.",
        "zutaten": ["250 g Couscous", "300 ml Gemüsebrühe", "1 Gurke", "250 g Cherrytomaten", "1 gelbe Paprika", "1 kleine rote Zwiebel", "200 g Feta", "3 EL Olivenöl", "2 EL Zitronensaft", "3 EL gehackte Petersilie", "Salz", "Pfeffer"],
        "anleitung": "1. Couscous in eine Schüssel geben, mit heißer Gemüsebrühe übergießen und 8 Minuten quellen lassen. Anschließend mit einer Gabel auflockern.\n2. Gurke, Tomaten, Paprika und Zwiebel klein schneiden.\n3. Gemüse und Petersilie unter den abgekühlten Couscous mischen.\n4. Olivenöl und Zitronensaft verrühren und unterheben.\n5. Feta darüberbröseln und mit Salz und Pfeffer abschmecken."
    },
    {
        "name": "Hähnchen-Gemüse-Wrap mit Joghurt-Dressing",
        "kueche": "Mexikanisch",
        "bild": "https://images.mrcook.app/recipe-image/0198ab6d-3e66-7afb-a3d0-2ef6fb0fd8c5?cacheKey=RnJpLCAxNSBBdWcgMjAyNSAwMTo1MjowMiBHTVQ%3D",
        "portionen": 4,
        "kochzeit": 25,
        "schwierigkeit": "Einfach",
        "tags": ["Wrap", "Hähnchen", "Schnell", "Protein"],
        "description": "Saftiges Hähnchen, knackiger Salat und frisches Gemüse in warmen Wraps mit leichtem Joghurt-Dressing.",
        "zutaten": ["4 große Weizentortillas", "400 g Hähnchenbrust", "1 Romanasalat", "1 Gurke", "2 Tomaten", "1 Paprika", "150 g Naturjoghurt", "1 TL Zitronensaft", "1 TL Paprikapulver", "1 EL Öl", "Salz", "Pfeffer"],
        "anleitung": "1. Hähnchen in Streifen schneiden und mit Paprikapulver, Salz und Pfeffer würzen.\n2. Öl in einer Pfanne erhitzen und das Hähnchen 6–8 Minuten vollständig durchbraten.\n3. Salat, Gurke, Tomaten und Paprika klein schneiden.\n4. Joghurt mit Zitronensaft, Salz und Pfeffer zu einem Dressing verrühren.\n5. Tortillas kurz erwärmen und mit Dressing, Salat, Gemüse und Hähnchen belegen.\n6. Seiten einschlagen, fest aufrollen und nach Wunsch halbieren."
    },
    {
        "name": "Tomaten-Mozzarella-Pasta",
        "kueche": "Italienisch",
        "bild": "https://cdn.gutekueche.de/media/recipe/69297/tomaten-mozzarella-sosse.jpg",
        "portionen": 4,
        "kochzeit": 25,
        "schwierigkeit": "Einfach",
        "tags": ["Pasta", "Vegetarisch", "Schnell", "Familie"],
        "description": "Fruchtige Tomatenpasta mit schmelzendem Mozzarella, Cherrytomaten und frischem Basilikum.",
        "zutaten": ["400 g Penne", "500 g passierte Tomaten", "250 g Cherrytomaten", "200 g Mozzarella", "1 Zwiebel", "2 Knoblauchzehen", "2 EL Olivenöl", "1 TL Oregano", "1 Bund Basilikum", "Salz", "Pfeffer"],
        "anleitung": "1. Pasta in Salzwasser bissfest kochen.\n2. Zwiebel und Knoblauch fein hacken und in Olivenöl glasig anbraten.\n3. Cherrytomaten halbieren, kurz mitbraten und passierte Tomaten angießen.\n4. Mit Oregano, Salz und Pfeffer würzen und 8 Minuten köcheln lassen.\n5. Pasta unter die Sauce mischen.\n6. Mozzarella würfeln und unterheben, bis er leicht schmilzt.\n7. Mit frischem Basilikum servieren."
    },
    {
        "name": "Beeren-Pancakes mit Joghurt",
        "kueche": "Frühstück",
        "bild": "https://itesco.cz/imgglobal/content_platform/recipes/main/67/6755f984a73bd34fff082dbc8f7490fe.jpg",
        "portionen": 2,
        "kochzeit": 25,
        "schwierigkeit": "Einfach",
        "tags": ["Frühstück", "Vegetarisch", "Süß", "Pancakes"],
        "description": "Fluffige Pancakes mit cremigem Joghurt und frischen Beeren – perfekt für Frühstück oder Brunch.",
        "zutaten": ["180 g Mehl", "2 TL Backpulver", "2 Eier", "220 ml Milch", "1 EL Zucker", "1 Prise Salz", "1 EL Butter oder Öl", "150 g Naturjoghurt", "200 g gemischte Beeren", "2 TL Honig oder Ahornsirup"],
        "anleitung": "1. Mehl, Backpulver, Zucker und Salz vermischen.\n2. Eier und Milch verquirlen und zu den trockenen Zutaten geben. Nur kurz zu einem glatten Teig verrühren.\n3. Eine Pfanne leicht fetten und kleine Pancakes bei mittlerer Hitze von beiden Seiten goldbraun backen.\n4. Pancakes stapeln und mit Joghurt sowie Beeren anrichten.\n5. Mit Honig oder Ahornsirup beträufeln."
    },
    {
        "name": "Tomate-Mozzarella-Salat",
        "kueche": "Italienisch",
        "bild": "https://api.bulmag.org/images/342b0fa92ab581373f0f8e4bf7e4afdf.jpeg",
        "portionen": 2,
        "kochzeit": 10,
        "schwierigkeit": "Einfach",
        "tags": ["Vegetarisch", "Salat", "Schnell", "Low Carb"],
        "description": "Klassischer Caprese-Salat mit reifen Tomaten, Mozzarella, Basilikum und gutem Olivenöl.",
        "zutaten": ["4 große Tomaten", "250 g Mozzarella", "1 Bund Basilikum", "2 EL Olivenöl", "1 EL Balsamico", "Salz", "Pfeffer"],
        "anleitung": "1. Tomaten und Mozzarella in gleichmäßige Scheiben schneiden.\n2. Abwechselnd auf einem Teller anrichten.\n3. Basilikumblätter darauf verteilen.\n4. Mit Olivenöl und Balsamico beträufeln.\n5. Mit Salz und frisch gemahlenem Pfeffer abschmecken und sofort servieren."
    },
    {
        "name": "Pilzrisotto",
        "kueche": "Italienisch",
        "bild": "https://www.datocms-assets.com/20941/1756899974-mushroom-guide-mushroom-risotto.jpeg?auto=format&dpr=0.18&fit=max&w=4763",
        "portionen": 4,
        "kochzeit": 40,
        "schwierigkeit": "Mittel",
        "tags": ["Vegetarisch", "Reis", "Pilze", "Comfort Food"],
        "description": "Cremiges Risotto mit gebratenen Champignons, Parmesan und Petersilie.",
        "zutaten": ["300 g Risottoreis", "400 g Champignons", "1 Zwiebel", "1 Knoblauchzehe", "1 l Gemüsebrühe", "100 ml trockener Weißwein oder zusätzliche Brühe", "60 g Parmesan", "2 EL Butter", "1 EL Olivenöl", "2 EL Petersilie", "Salz", "Pfeffer"],
        "anleitung": "1. Gemüsebrühe erhitzen und warm halten. Champignons in Scheiben schneiden.\n2. Die Hälfte der Butter mit Olivenöl in einer Pfanne erhitzen und die Pilze kräftig anbraten. Herausnehmen.\n3. Zwiebel und Knoblauch fein hacken und in derselben Pfanne glasig dünsten.\n4. Risottoreis zugeben und 1 Minute mitrösten. Mit Weißwein oder etwas Brühe ablöschen.\n5. Nach und nach heiße Brühe zugeben und regelmäßig rühren. Erst neue Brühe nachgießen, wenn die vorherige fast aufgenommen ist.\n6. Nach etwa 20 Minuten Pilze, restliche Butter und Parmesan unterheben.\n7. Mit Salz, Pfeffer und Petersilie abschmecken."
    },
    {
        "name": "Chili sin Carne",
        "kueche": "Mexikanisch",
        "bild": "https://i.pinimg.com/originals/4f/79/ec/4f79ec53a5031e02da786aff478ce9fd.jpg",
        "portionen": 4,
        "kochzeit": 35,
        "schwierigkeit": "Einfach",
        "tags": ["Vegan", "Vegetarisch", "Eintopf", "Low Budget", "Meal Prep"],
        "description": "Würziges vegetarisches Chili mit Kidneybohnen, schwarzen Bohnen, Mais und Paprika – sättigend und perfekt zum Vorkochen.",
        "zutaten": ["1 Dose Kidneybohnen", "1 Dose schwarze Bohnen", "1 Dose Mais", "1 rote Paprika", "1 Zwiebel", "2 Knoblauchzehen", "400 g gehackte Tomaten", "300 ml Gemüsebrühe", "1 EL Tomatenmark", "1 EL Öl", "1 TL Kreuzkümmel", "1 TL Paprikapulver", "0,5 TL Chiliflocken", "Salz", "Pfeffer"],
        "anleitung": "1. Bohnen und Mais abspülen und abtropfen lassen. Paprika würfeln, Zwiebel und Knoblauch hacken.\n2. Öl in einem Topf erhitzen und Zwiebel sowie Paprika 5 Minuten anbraten.\n3. Knoblauch, Tomatenmark, Kreuzkümmel, Paprikapulver und Chili kurz mitrösten.\n4. Gehackte Tomaten und Gemüsebrühe zugeben.\n5. Bohnen und Mais unterrühren und 20 Minuten ohne Deckel köcheln lassen.\n6. Mit Salz und Pfeffer abschmecken. Nach Wunsch mit Limette oder Koriander servieren."
    },
    {
        "name": "French Toast mit Beeren",
        "kueche": "Frühstück",
        "bild": "https://food.fnr.sndimg.com/content/dam/images/food/fullset/2013/12/9/0/FNK_French-Toast-with-Mixed-Berries_s4x3.jpg.rend.hgtvcom.1280.960.suffix/1387416657918.webp",
        "portionen": 2,
        "kochzeit": 20,
        "schwierigkeit": "Einfach",
        "tags": ["Frühstück", "Süß", "Vegetarisch", "Schnell"],
        "description": "Goldbrauner French Toast mit frischen Beeren und Ahornsirup – ein unkompliziertes Frühstück für besondere Morgen.",
        "zutaten": ["4 dicke Scheiben Toast oder Brioche", "2 Eier", "120 ml Milch", "1 TL Vanillezucker", "0,5 TL Zimt", "1 EL Butter", "200 g gemischte Beeren", "2 EL Ahornsirup"],
        "anleitung": "1. Eier, Milch, Vanillezucker und Zimt in einem tiefen Teller verquirlen.\n2. Brotscheiben nacheinander in der Eiermilch wenden und kurz vollsaugen lassen.\n3. Butter in einer Pfanne erhitzen.\n4. Brotscheiben bei mittlerer Hitze von beiden Seiten jeweils 2–3 Minuten goldbraun braten.\n5. Mit Beeren anrichten und Ahornsirup darübergeben."
    },
    {
        "name": "Thunfisch-Nudel-Salat",
        "kueche": "Salat",
        "bild": "https://ip.index.hr/remote/bucket.index.hr/b/index/2a3127a4-c4b0-4c39-9bbd-ab23dff50802.jpg?width=500",
        "portionen": 4,
        "kochzeit": 25,
        "schwierigkeit": "Einfach",
        "tags": ["Pasta", "Fisch", "Salat", "Meal Prep", "Schnell"],
        "description": "Cremiger Nudelsalat mit Thunfisch, Gurke und Erbsen – schnell vorbereitet und ideal für Mittagspause oder Grillabend.",
        "zutaten": ["300 g kurze Nudeln", "2 Dosen Thunfisch im eigenen Saft", "150 g Erbsen", "0,5 Gurke", "150 g Naturjoghurt", "2 EL Mayonnaise", "1 TL Senf", "1 EL Zitronensaft", "2 EL Dill oder Petersilie", "Salz", "Pfeffer"],
        "anleitung": "1. Nudeln in Salzwasser bissfest kochen, abgießen und vollständig abkühlen lassen.\n2. Thunfisch abtropfen lassen. Gurke klein würfeln.\n3. Joghurt, Mayonnaise, Senf und Zitronensaft zu einem Dressing verrühren.\n4. Nudeln mit Thunfisch, Gurke und Erbsen vermengen.\n5. Dressing und Kräuter unterheben.\n6. Mit Salz und Pfeffer abschmecken und vor dem Servieren möglichst 15 Minuten ziehen lassen."
    },
    {
        "name": "Gemüseomelett",
        "kueche": "Frühstück",
        "bild": "https://www.gutekueche.at/storage/media/recipe/166532/gemueseomelette.jpg",
        "portionen": 2,
        "kochzeit": 20,
        "schwierigkeit": "Einfach",
        "tags": ["Frühstück", "Vegetarisch", "Protein", "Low Carb", "Schnell"],
        "description": "Fluffiges Omelett mit Paprika, Tomaten, Zwiebeln und Spinat – proteinreich und schnell gemacht.",
        "zutaten": ["5 Eier", "1 kleine Paprika", "1 Tomate", "0,5 Zwiebel", "50 g Babyspinat", "40 g geriebener Käse", "1 EL Butter", "2 EL Milch", "Salz", "Pfeffer"],
        "anleitung": "1. Paprika, Tomate und Zwiebel klein schneiden.\n2. Eier mit Milch, Salz und Pfeffer verquirlen.\n3. Butter in einer beschichteten Pfanne erhitzen und Zwiebel sowie Paprika 3 Minuten anbraten.\n4. Tomate und Spinat zugeben und kurz zusammenfallen lassen.\n5. Eiermasse darübergeben und bei kleiner bis mittlerer Hitze stocken lassen.\n6. Käse auf einer Hälfte verteilen, Omelett zusammenklappen und weitere 1–2 Minuten garen."
    }
]


def ensure_extra_recipes_batch2(engine) -> int:
    metadata = MetaData()
    table = Table("recipes", metadata, autoload_with=engine)
    inserted = 0
    with engine.begin() as conn:
        existing = set(conn.execute(select(table.c.name)).scalars().all())
        for recipe in EXTRA_RECIPES_BATCH2:
            if recipe["name"] in existing:
                continue
            values = {
                "name": recipe["name"],
                "kueche": recipe["kueche"],
                "bild": recipe["bild"],
                "portionen": recipe["portionen"],
                "kochzeit": recipe["kochzeit"],
                "schwierigkeit": recipe["schwierigkeit"],
                "tags_json": json.dumps(recipe["tags"], ensure_ascii=False),
                "zutaten_json": json.dumps(recipe["zutaten"], ensure_ascii=False),
                "anleitung": recipe["anleitung"],
            }
            if "description" in table.c:
                values["description"] = recipe["description"]
            if "owner_user_id" in table.c:
                values["owner_user_id"] = None
            if "source_url" in table.c:
                values["source_url"] = None
            conn.execute(table.insert().values(**values))
            existing.add(recipe["name"])
            inserted += 1
    return inserted
