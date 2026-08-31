from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Iterable

SIZE_WORDS = {
    "klein", "kleine", "kleiner", "kleines", "kleinen",
    "mittel", "mittlere", "mittlerer", "mittleres", "mittleren",
    "gross", "große", "großer", "großes", "großen", "grosse", "grosser", "grosses", "grossen",
}

UNIT_ALIASES = {
    "g": "g", "gramm": "g",
    "kg": "kg", "kilogramm": "kg",
    "ml": "ml", "milliliter": "ml",
    "l": "l", "liter": "l",
    "el": "EL", "esslöffel": "EL", "essloeffel": "EL",
    "tl": "TL", "teelöffel": "TL", "teeloeffel": "TL",
    "stk": "Stück", "stk.": "Stück", "stück": "Stück", "stueck": "Stück",
    "dose": "Dose", "dosen": "Dose",
    "packung": "Packung", "packungen": "Packung", "päckchen": "Packung", "paeckchen": "Packung",
    "becher": "Becher", "bund": "Bund", "prise": "Prise", "prisen": "Prise",
    "scheibe": "Scheibe", "scheiben": "Scheibe", "zehe": "Zehe", "zehen": "Zehe",
    "glas": "Glas", "gläser": "Glas", "glaeser": "Glas", "flasche": "Flasche", "flaschen": "Flasche",
}

ALIASES = {
    "möhren": "karotte", "möhre": "karotte", "moehren": "karotte", "moehre": "karotte",
    "karotten": "karotte", "karotte": "karotte",
    "zwiebeln": "zwiebel", "zwiebel": "zwiebel",
    "kartoffeln": "kartoffel", "kartoffel": "kartoffel",
    "tomaten": "tomate", "tomate": "tomate",
    "paprikaschoten": "paprika", "paprikaschote": "paprika", "paprika": "paprika",
    "gurken": "gurke", "gurke": "gurke", "eier": "ei", "ei": "ei",
    "äpfel": "apfel", "apfel": "apfel", "aepfel": "apfel", "bananen": "banane", "banane": "banane",
    "champignons": "champignon", "champignon": "champignon", "pilze": "pilz", "pilz": "pilz",
    "knoblauchzehen": "knoblauch", "knoblauchzehe": "knoblauch", "knoblauch": "knoblauch",
    "frühlingszwiebeln": "frühlingszwiebel", "frühlingszwiebel": "frühlingszwiebel",
    "fruehlingszwiebeln": "frühlingszwiebel", "fruehlingszwiebel": "frühlingszwiebel",
}

DISPLAY_NAMES = {
    "karotte": "Karotten", "zwiebel": "Zwiebeln", "kartoffel": "Kartoffeln", "tomate": "Tomaten",
    "paprika": "Paprika", "gurke": "Gurken", "ei": "Eier", "apfel": "Äpfel", "banane": "Bananen",
    "champignon": "Champignons", "pilz": "Pilze", "knoblauch": "Knoblauch", "frühlingszwiebel": "Frühlingszwiebeln",
}

CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Obst & Gemüse", ("zwiebel", "karotte", "kartoffel", "tomate", "paprika", "gurke", "apfel", "banane", "champignon", "pilz", "knoblauch", "brokkoli", "blumenkohl", "zucchini", "aubergine", "salat", "spinat", "lauch", "sellerie", "zitrone", "limette", "orange", "beere", "erdbeer")),
    ("Kühlregal", ("milch", "sahne", "joghurt", "skyr", "quark", "käse", "kaese", "butter", "creme fraiche", "schmand", "mozzarella", "feta", "ei")),
    ("Fleisch & Fisch", ("hähnchen", "haehnchen", "hackfleisch", "rind", "schwein", "speck", "schinken", "lachs", "thunfisch", "kabeljau", "fisch", "garnelen")),
    ("Backwaren & Frühstück", ("brot", "brötchen", "broetchen", "toast", "wrap", "tortilla", "müsli", "muesli", "haferflocken")),
    ("Nudeln, Reis & Hülsenfrüchte", ("nudel", "pasta", "spaghetti", "reis", "couscous", "bulgur", "linse", "bohne", "kichererbse")),
    ("Konserven & Gläser", ("mais", "passierte tomate", "gehackte tomate", "tomatenmark", "kokosmilch")),
    ("Gewürze & Vorrat", ("salz", "pfeffer", "paprika pulver", "paprikapulver", "oregano", "basilikum", "curry", "chili", "mehl", "zucker", "öl", "oel", "essig", "brühe", "bruehe", "senf", "honig")),
]

EU14_ALLERGENS: dict[str, dict[str, Any]] = {
    "gluten": {"de": "Glutenhaltiges Getreide", "en": "Cereals containing gluten", "terms": ("weizen", "roggen", "gerste", "hafer", "dinkel", "kamut", "mehl", "brot", "brötchen", "toast", "nudel", "pasta", "spaghetti", "tortellini", "couscous", "bulgur")},
    "crustaceans": {"de": "Krebstiere", "en": "Crustaceans", "terms": ("garnele", "garnelen", "shrimp", "krabbe", "krebs", "languste")},
    "eggs": {"de": "Eier", "en": "Eggs", "terms": ("ei", "eier", "eipulver", "mayonnaise", "mayo")},
    "fish": {"de": "Fisch", "en": "Fish", "terms": ("fisch", "lachs", "thunfisch", "kabeljau", "seelachs", "forelle", "sardine", "anchovis")},
    "peanuts": {"de": "Erdnüsse", "en": "Peanuts", "terms": ("erdnuss", "erdnüsse", "erdnussbutter", "erdnusssauce")},
    "soy": {"de": "Soja", "en": "Soybeans", "terms": ("soja", "sojasauce", "tofu", "tempeh", "edamame")},
    "milk": {"de": "Milch", "en": "Milk", "terms": ("milch", "sahne", "butter", "käse", "kaese", "quark", "joghurt", "skyr", "mozzarella", "feta", "parmesan", "schmand", "creme fraiche")},
    "nuts": {"de": "Schalenfrüchte", "en": "Tree nuts", "terms": ("mandel", "mandeln", "haselnuss", "walnuss", "cashew", "pistazie", "pekannuss", "macadamia", "paranuss")},
    "celery": {"de": "Sellerie", "en": "Celery", "terms": ("sellerie", "knollensellerie", "stangensellerie")},
    "mustard": {"de": "Senf", "en": "Mustard", "terms": ("senf", "senfkorn")},
    "sesame": {"de": "Sesam", "en": "Sesame", "terms": ("sesam", "tahini")},
    "sulphites": {"de": "Schwefeldioxid / Sulfite", "en": "Sulphur dioxide / sulphites", "terms": ("sulfit", "sulfite", "schwefeldioxid")},
    "lupin": {"de": "Lupinen", "en": "Lupin", "terms": ("lupine", "lupinen")},
    "molluscs": {"de": "Weichtiere", "en": "Molluscs", "terms": ("muschel", "muscheln", "auster", "tintenfisch", "calamari", "oktopus", "schnecke")},
}

MEAT_TERMS = ("hähnchen", "haehnchen", "huhn", "rind", "schwein", "hackfleisch", "speck", "schinken", "wurst", "salami", "pute", "lamm", "kalb", "fleisch")
FISH_TERMS = ("fisch", "lachs", "thunfisch", "kabeljau", "forelle", "garnele", "garnelen", "krabbe")
ANIMAL_TERMS = MEAT_TERMS + FISH_TERMS + ("milch", "sahne", "butter", "käse", "kaese", "quark", "joghurt", "skyr", "ei", "eier", "honig", "feta", "mozzarella", "parmesan")
PORK_TERMS = ("schwein", "speck", "schinken", "salami", "bacon", "mett")

@dataclass(frozen=True)
class Ingredient:
    raw: str
    quantity: float | None
    unit: str | None
    name: str
    canonical: str
    display_name: str
    category: str

def _ascii_fold(value: str) -> str:
    value = value.replace("ß", "ss")
    return "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c)).lower()

def _clean_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" ,;:-")

def _number(token: str) -> float | None:
    token = token.strip().replace(",", ".")
    if not token: return None
    try:
        if " " in token and "/" in token:
            whole, frac = token.split(None, 1); return float(whole) + float(Fraction(frac))
        if "/" in token: return float(Fraction(token))
        return float(token)
    except (ValueError, ZeroDivisionError): return None

def canonicalize_name(name: str) -> str:
    original = _clean_spaces(name.lower().replace("–", "-").replace("—", "-"))
    words = [w for w in re.split(r"\s+", original) if w and w not in SIZE_WORDS]
    cleaned = _clean_spaces(" ".join(words)); cleaned = re.sub(r"\bca\.?\b", "", cleaned); cleaned = _clean_spaces(cleaned)
    if cleaned in ALIASES: return ALIASES[cleaned]
    parts = cleaned.split()
    if len(parts) == 1: return ALIASES.get(parts[0], parts[0])
    return cleaned

def display_food_name(canonical: str, fallback: str | None = None) -> str:
    if canonical in DISPLAY_NAMES: return DISPLAY_NAMES[canonical]
    value = fallback or canonical
    return value[:1].upper() + value[1:]

def food_category(canonical: str) -> str:
    folded = _ascii_fold(canonical)
    for category, terms in CATEGORY_RULES:
        if any(_ascii_fold(term) in folded for term in terms): return category
    return "Sonstiges"

def parse_ingredient(raw: str) -> Ingredient:
    raw = _clean_spaces(str(raw or "")); working = raw; quantity: float | None = None; unit: str | None = None
    m = re.match(r"^\s*(\d+(?:[.,]\d+)?(?:\s+\d+/\d+)?|\d+/\d+)\s*(.*)$", working)
    if m: quantity = _number(m.group(1)); working = m.group(2).strip()
    if working:
        first, *rest = working.split(maxsplit=1); unit_candidate = UNIT_ALIASES.get(first.lower().rstrip("."))
        if unit_candidate: unit = unit_candidate; working = rest[0] if rest else ""
    if quantity is not None and unit is None: unit = "Stück"
    words = [w for w in working.split() if w.lower().strip(".,") not in SIZE_WORDS]
    name = _clean_spaces(" ".join(words)) or _clean_spaces(working) or raw; canonical = canonicalize_name(name)
    return Ingredient(raw, quantity, unit, name, canonical, display_food_name(canonical, name), food_category(canonical))

def _base_amount(quantity: float, unit: str) -> tuple[float, str]:
    if unit == "kg": return quantity * 1000.0, "g"
    if unit == "l": return quantity * 1000.0, "ml"
    return quantity, unit

def _pretty_number(value: float) -> str:
    if math.isclose(value, round(value), abs_tol=1e-9): return str(int(round(value)))
    return f"{value:.2f}".rstrip("0").rstrip(".").replace(".", ",")

def _pretty_amount(value: float, unit: str) -> str:
    if unit == "g" and value >= 1000 and math.isclose(value % 1000, 0, abs_tol=1e-9): return f"{_pretty_number(value / 1000)} kg"
    if unit == "ml" and value >= 1000 and math.isclose(value % 1000, 0, abs_tol=1e-9): return f"{_pretty_number(value / 1000)} l"
    if unit == "Stück": return _pretty_number(value)
    return f"{_pretty_number(value)} {unit}".strip()

def scale_ingredient(ingredient: Ingredient, factor: float) -> Ingredient:
    if ingredient.quantity is None: return ingredient
    quantity = ingredient.quantity * max(factor, 0)
    if ingredient.unit == "Stück": quantity = float(math.ceil(quantity - 1e-9))
    return Ingredient(**{**ingredient.__dict__, "quantity": quantity})

def aggregate_ingredients(recipe_ingredients: Iterable[tuple[Iterable[str], float]], pantry_items: Iterable[str] = ()) -> list[dict[str, Any]]:
    pantry_keys = {parse_ingredient(x).canonical for x in pantry_items if str(x).strip()}; buckets: dict[str, dict[str, Any]] = {}
    for raw_items, factor in recipe_ingredients:
        for raw in raw_items:
            ing = scale_ingredient(parse_ingredient(str(raw)), factor)
            if not ing.canonical or ing.canonical in pantry_keys: continue
            bucket = buckets.setdefault(ing.canonical, {"key": ing.canonical, "name": ing.display_name, "category": ing.category, "amounts": {}, "unquantified": 0, "sources": []})
            bucket["sources"].append(ing.raw)
            if ing.quantity is None: bucket["unquantified"] += 1; continue
            qty, unit = _base_amount(ing.quantity, ing.unit or "Stück"); bucket["amounts"][unit] = bucket["amounts"].get(unit, 0.0) + qty
    result: list[dict[str, Any]] = []
    for bucket in buckets.values():
        amounts = [_pretty_amount(qty, unit) for unit, qty in sorted(bucket["amounts"].items())]
        if bucket["unquantified"]: amounts.append("nach Bedarf")
        amount_text = " + ".join(amounts); label = f"{amount_text} {bucket['name']}".strip() if amount_text else bucket["name"]
        result.append({**bucket, "amount_text": amount_text, "label": label})
    return sorted(result, key=lambda x: (x["category"].casefold(), x["name"].casefold()))

def aggregate_to_categories(items: Iterable[dict[str, Any]]) -> dict[str, list[str]]:
    categories: dict[str, list[str]] = {}
    for item in items: categories.setdefault(item["category"], []).append(item["label"])
    for rows in categories.values(): rows.sort(key=str.casefold)
    return categories

def detect_allergens(ingredients: Iterable[str]) -> list[str]:
    folded = _ascii_fold(" ".join(str(x) for x in ingredients).lower()); found: list[str] = []
    for code, meta in EU14_ALLERGENS.items():
        if any(_ascii_fold(term) in folded for term in meta["terms"]): found.append(code)
    return found

def allergen_catalog() -> list[dict[str, str]]:
    return [{"code": code, "name_de": meta["de"], "name_en": meta["en"]} for code, meta in EU14_ALLERGENS.items()]

def recipe_profile_conflicts(recipe: dict[str, Any], profile: dict[str, Any] | None) -> dict[str, Any]:
    profile = profile or {}; ingredients = [str(x) for x in recipe.get("zutaten", [])]
    text = " ".join([str(recipe.get("name", "")), *ingredients, *(str(x) for x in recipe.get("tags", []))]).lower(); folded = _ascii_fold(text)
    detected = set(detect_allergens(ingredients)); allergies = {str(x) for x in profile.get("allergies", [])}; intolerances = {str(x) for x in profile.get("intolerances", [])}
    conflicts = sorted(detected & allergies); intolerance_conflicts = sorted(detected & intolerances)
    dislikes = [canonicalize_name(str(x)) for x in profile.get("dislikes", []) if str(x).strip()]; dislike_hits = sorted({d for d in dislikes if d and _ascii_fold(d) in folded})
    diets = {str(x).lower() for x in profile.get("diets", []) if str(x).strip()}; diet_conflicts: list[str] = []
    if "vegetarian" in diets or "vegetarisch" in diets:
        if any(_ascii_fold(t) in folded for t in MEAT_TERMS + FISH_TERMS): diet_conflicts.append("vegetarian")
    if "vegan" in diets:
        if any(_ascii_fold(t) in folded for t in ANIMAL_TERMS): diet_conflicts.append("vegan")
    if "pescatarian" in diets or "pescetarisch" in diets:
        if any(_ascii_fold(t) in folded for t in MEAT_TERMS): diet_conflicts.append("pescatarian")
    if "no_pork" in diets or "kein_schwein" in diets or "kein schweinefleisch" in diets:
        if any(_ascii_fold(t) in folded for t in PORK_TERMS): diet_conflicts.append("no_pork")
    strict_intolerances = bool(profile.get("exclude_intolerances", True)); hard_blocked = bool(conflicts or diet_conflicts or (strict_intolerances and intolerance_conflicts))
    return {"allergens": sorted(detected), "allergy_conflicts": conflicts, "intolerance_conflicts": intolerance_conflicts, "diet_conflicts": sorted(set(diet_conflicts)), "dislike_hits": dislike_hits, "blocked": hard_blocked, "soft_penalty": len(dislike_hits) + (0 if strict_intolerances else len(intolerance_conflicts))}

def food_rescue_score(recipe: dict[str, Any], available: Iterable[str], expiring: Iterable[str] = ()) -> dict[str, Any]:
    recipe_keys = [parse_ingredient(str(x)).canonical for x in recipe.get("zutaten", [])]; available_keys = {parse_ingredient(str(x)).canonical for x in available if str(x).strip()}; expiring_keys = {parse_ingredient(str(x)).canonical for x in expiring if str(x).strip()}
    matches = sorted({key for key in recipe_keys if key in available_keys}); urgent = sorted({key for key in recipe_keys if key in expiring_keys}); coverage = len(matches) / max(len(set(recipe_keys)), 1); score = len(matches) * 3 + len(urgent) * 8 + coverage
    return {"score": score, "matches": matches, "urgent_matches": urgent, "coverage": round(coverage, 3)}

def subtract_pantry(items: list[dict[str, Any]], pantry: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[str, list[dict[str, Any]]] = {}
    for row in pantry:
        key = canonicalize_name(str(row.get("canonical") or row.get("name") or row.get("display_name") or ""))
        if key: by_key.setdefault(key, []).append(row)
    out: list[dict[str, Any]] = []
    for original in items:
        item = {**original, "amounts": dict(original.get("amounts", {}))}; pantry_rows = by_key.get(item["key"], []); remove_all = False
        for row in pantry_rows:
            qty = row.get("quantity"); unit = str(row.get("unit") or "Stück")
            if qty in (None, ""): remove_all = True; break
            try: base_qty, base_unit = _base_amount(float(qty), UNIT_ALIASES.get(unit.lower().rstrip("."), unit))
            except (TypeError, ValueError): continue
            if base_unit in item["amounts"]: item["amounts"][base_unit] = max(0.0, float(item["amounts"][base_unit]) - base_qty)
        if remove_all: continue
        item["amounts"] = {u: q for u, q in item["amounts"].items() if q > 1e-9}
        if not item["amounts"] and not item.get("unquantified"): continue
        amounts = [_pretty_amount(qty, unit) for unit, qty in sorted(item["amounts"].items())]
        if item.get("unquantified"): amounts.append("nach Bedarf")
        amount_text = " + ".join(amounts); item["amount_text"] = amount_text; item["label"] = f"{amount_text} {item['name']}".strip() if amount_text else item["name"]; out.append(item)
    return out
