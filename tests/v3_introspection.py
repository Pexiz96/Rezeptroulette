from pathlib import Path
import sys, base64, gzip, inspect
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

api_b64 = ''.join((ROOT / '.github/upgrade_payload/api.py.gz.b64').read_text().split())
api_source = gzip.decompress(base64.b64decode(api_b64)).decode('utf-8')
needles = [
    'ALLERGENS','allergen_labels','allergens_for_recipe','merge_ingredients',
    'normalize_food_name','recipe_is_safe','score_recipe','structured_ingredients',
    'subtract_pantry','days_until'
]
print('API_USAGES')
for idx, line in enumerate(api_source.splitlines(), 1):
    if any(n in line for n in needles):
        print(f'{idx:04d}: {line}')

from database import Database
import smart_features
print('SMART_SIGNATURES')
for name in ['allergen_catalog','canonicalize_name','detect_allergens','aggregate_ingredients','aggregate_to_categories','parse_ingredient','recipe_profile_conflicts','food_rescue_score','subtract_pantry']:
    obj = getattr(smart_features, name, None)
    print(name, inspect.signature(obj) if callable(obj) else repr(obj))

print('CATALOG_SAMPLE')
try:
    print(smart_features.allergen_catalog())
except Exception as exc:
    print(type(exc).__name__, str(exc))
print('PARSE_SAMPLE')
for sample in ['1 kleine Zwiebel','250 g Möhren','2 Frühlingszwiebeln']:
    try:
        print(sample, '=>', smart_features.parse_ingredient(sample))
    except Exception as exc:
        print(sample, type(exc).__name__, str(exc))

print('DATABASE_METHODS')
for name in sorted(n for n in dir(Database) if not n.startswith('_')):
    print(name)
