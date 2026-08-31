from pathlib import Path
import sys, base64, gzip, inspect
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

api_b64 = ''.join((ROOT / '.github/upgrade_payload/api.py.gz.b64').read_text().split())
api_source = gzip.decompress(base64.b64decode(api_b64)).decode('utf-8')
lines = api_source.splitlines()
for start, end in [(300,365),(540,565),(650,745),(900,945),(1000,1070)]:
    print(f'API_RANGE_{start}_{end}')
    for idx in range(start, min(end, len(lines))+1):
        print(f'{idx:04d}: {lines[idx-1]}')

from database import Database
import smart_features
print('SMART_SIGNATURES')
for name in ['allergen_catalog','canonicalize_name','detect_allergens','aggregate_ingredients','aggregate_to_categories','parse_ingredient','recipe_profile_conflicts','food_rescue_score','subtract_pantry']:
    obj = getattr(smart_features, name, None)
    print(name, inspect.signature(obj) if callable(obj) else repr(obj))

samples = ['1 kleine Zwiebel','1 Zwiebel','250 g Möhren','500 g Karotten','2 Frühlingszwiebeln']
print('AGGREGATE_SAMPLE')
try:
    print(smart_features.aggregate_ingredients([(samples, 1.0)]))
except Exception as exc:
    print(type(exc).__name__, str(exc))
print('CONFLICT_SAMPLES')
recipe={'zutaten':['200 ml Milch','1 Ei','1 Zwiebel'],'tags':['Vegetarisch'],'kochzeit':20}
for profile in [{},{'allergies':['milk']},{'diet':'vegan'},{'dietary':['vegan']},{'dislikes':['zwiebel']}]:
    try:
        print(profile, '=>', smart_features.recipe_profile_conflicts(recipe, profile))
    except Exception as exc:
        print(profile, type(exc).__name__, str(exc))
