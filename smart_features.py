from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timezone
from typing import Any, Iterable

from payload_loader import exec_gzip_base64_payload

# Keep the generated V3 implementation isolated. This is important because the API
# expects dictionary-oriented helper functions while the lower-level implementation
# intentionally works with an Ingredient dataclass.
_impl: dict[str, Any] = {"__name__": "rezeptroulette_v3_features_impl"}
exec_gzip_base64_payload(
    _impl,
    [
        ".github/upgrade_payload/v3_features.00",
        ".github/upgrade_payload/v3_features.01",
    ],
    "smart_features_impl.py",
)

allergen_catalog = _impl["allergen_catalog"]
canonicalize_name = _impl["canonicalize_name"]
detect_allergens = _impl["detect_allergens"]
aggregate_ingredients = _impl["aggregate_ingredients"]
aggregate_to_categories = _impl["aggregate_to_categories"]
recipe_profile_conflicts = _impl["recipe_profile_conflicts"]
food_rescue_score = _impl["food_rescue_score"]
register_v3 = _impl["register_v3"]
V3_METADATA = _impl.get("V3_METADATA")

_raw_parse_ingredient = _impl["parse_ingredient"]
_raw_subtract_pantry = _impl["subtract_pantry"]

_CATALOG = allergen_catalog()
ALLERGENS = [str(item["code"]) for item in _CATALOG]
_ALLERGEN_DE = {str(item["code"]): str(item["name_de"]) for item in _CATALOG}
_ALLERGEN_EN = {str(item["code"]): str(item["name_en"]) for item in _CATALOG}


def normalize_food_name(value: str) -> str:
    return canonicalize_name(str(value or ""))


def _ingredient_dict(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        row = asdict(value)
    elif isinstance(value, dict):
        row = dict(value)
    else:
        row = dict(vars(value)) if hasattr(value, "__dict__") else {}
    quantity = row.get("quantity", row.get("amount"))
    canonical = row.get("canonical", row.get("food")) or normalize_food_name(row.get("name", ""))
    display_name = row.get("display_name") or row.get("name") or canonical
    return {
        "raw": row.get("raw", ""),
        "amount": quantity,
        "quantity": quantity,
        "unit": row.get("unit") or "",
        "name": row.get("name") or display_name,
        "food": canonical,
        "canonical": canonical,
        "display_name": display_name,
        "category": row.get("category") or "📦 Sonstiges",
    }


def parse_ingredient(raw: str) -> dict[str, Any]:
    return _ingredient_dict(_raw_parse_ingredient(str(raw or "")))


def allergens_for_recipe(recipe: dict[str, Any]) -> list[str]:
    ingredients = [str(item) for item in (recipe.get("zutaten") or [])]
    return list(detect_allergens(ingredients))


def allergen_labels(codes: Iterable[str], language: str = "de") -> list[str]:
    labels = _ALLERGEN_EN if str(language).lower().startswith("en") else _ALLERGEN_DE
    return [labels.get(str(code), str(code)) for code in codes]


def _format_number(value: float) -> str:
    value = float(value)
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return (f"{value:.2f}").rstrip("0").rstrip(".").replace(".", ",")


def structured_ingredients(recipe: dict[str, Any], portions: int | None = None) -> list[dict[str, Any]]:
    base_portions = max(1, int(recipe.get("portionen") or 1))
    requested = int(portions or recipe.get("requested_portions") or base_portions)
    factor = requested / base_portions
    rows: list[dict[str, Any]] = []
    for raw in recipe.get("zutaten") or []:
        parsed = parse_ingredient(str(raw))
        amount = parsed.get("amount")
        if amount is not None:
            amount = float(amount) * factor
        row = dict(parsed)
        row["amount"] = amount
        row["quantity"] = amount
        if amount is None:
            row["display"] = str(raw)
        else:
            unit = str(row.get("unit") or "").strip()
            label = str(row.get("display_name") or row.get("name") or "").strip()
            row["display"] = " ".join(x for x in [_format_number(amount), unit, label] if x).strip()
        rows.append(row)
    return rows


def _decorate_aggregate(item: dict[str, Any]) -> dict[str, Any]:
    row = dict(item)
    row["food"] = row.get("key") or normalize_food_name(row.get("name", ""))
    row["display_name"] = row.get("name") or row.get("food") or ""
    row["display"] = row.get("label") or row.get("display_name") or ""
    return row


def merge_ingredients(recipes: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    batches: list[tuple[Iterable[str], float]] = []
    for recipe in recipes:
        base = max(1, int(recipe.get("portionen") or 1))
        requested = recipe.get("requested_portions") or recipe.get("servings") or base
        try:
            factor = max(0.0, float(requested) / base)
        except (TypeError, ValueError):
            factor = 1.0
        batches.append((recipe.get("zutaten") or [], factor))
    return [_decorate_aggregate(item) for item in aggregate_ingredients(batches)]


def subtract_pantry(items: list[dict[str, Any]], pantry: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    remaining = _raw_subtract_pantry(items, pantry)
    return [_decorate_aggregate(item) for item in remaining]


def recipe_is_safe(recipe: dict[str, Any], profile: dict[str, Any] | None) -> tuple[bool, dict[str, Any]]:
    conflicts = recipe_profile_conflicts(recipe, profile or {})
    return (not bool(conflicts.get("blocked"))), conflicts


def _pantry_keys(pantry: Iterable[dict[str, Any]]) -> set[str]:
    result: set[str] = set()
    for item in pantry or []:
        key = normalize_food_name(str(item.get("food_key") or item.get("name") or ""))
        if key:
            result.add(key)
    return result


def score_recipe(
    recipe: dict[str, Any],
    profile: dict[str, Any] | None,
    pantry: Iterable[dict[str, Any]],
    ratings: dict[Any, Any] | None,
    favorites: Iterable[int] | None,
    recent: Iterable[int] | None,
    *,
    max_time: int = 0,
) -> float:
    """Deterministic recommendation score; safety remains a hard filter in the API."""
    conflicts = recipe_profile_conflicts(recipe, profile or {})
    if conflicts.get("blocked"):
        return -10000.0

    score = 0.0
    rid = int(recipe.get("id") or 0)
    rating_map = ratings or {}
    rating = rating_map.get(rid, rating_map.get(str(rid), 0))
    try:
        score += float(rating or 0) * 2.0
    except (TypeError, ValueError):
        pass
    if rid and rid in {int(x) for x in (favorites or [])}:
        score += 3.0
    if rid and rid in {int(x) for x in (recent or [])}:
        score -= 5.0

    score -= float(conflicts.get("soft_penalty") or 0) * 2.5
    pantry_keys = _pantry_keys(pantry)
    recipe_keys = {parse_ingredient(str(x)).get("food") for x in (recipe.get("zutaten") or [])}
    score += len({x for x in recipe_keys if x and x in pantry_keys}) * 1.5

    cooking_time = int(recipe.get("kochzeit") or 0)
    if max_time and cooking_time > max_time:
        score -= 100.0
    elif cooking_time and cooking_time <= 30:
        score += 0.5
    return score


def days_until(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        if isinstance(value, datetime):
            target = value.date()
        elif isinstance(value, date):
            target = value
        else:
            text = str(value).strip()
            if not text:
                return None
            try:
                target = datetime.fromisoformat(text.replace("Z", "+00:00")).date()
            except ValueError:
                target = date.fromisoformat(text[:10])
        return (target - datetime.now(timezone.utc).date()).days
    except (TypeError, ValueError, OverflowError):
        return None
