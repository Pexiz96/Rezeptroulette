from pathlib import Path
import sys, json
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import api

print('V3_ROUTES')
for route in api.app.routes:
    path = getattr(route, 'path', '')
    if path and any(key in path for key in ['/profile','/pantry','/food-rescue','/household','/wochenplan','/einkaufsliste','/recipe-notes','/auth/sessions','/auth/export','/roulette','/rezepte']):
        print(','.join(sorted(getattr(route, 'methods', []) or [])), path, getattr(route, 'name', ''))

print('V3_MODELS')
for name in ['FoodProfilePayload','PantryItemPayload','PantryV2Payload','HouseholdPayload','JoinHouseholdPayload','HouseholdProfilePayload','RecipeNotePayload','ShoppingCheckPayload','WeeklyPlanBulk']:
    cls = getattr(api, name, None)
    if cls is not None and hasattr(cls, 'model_json_schema'):
        print(name, json.dumps(cls.model_json_schema(), ensure_ascii=False, sort_keys=True))

print('OPENAPI_PATHS')
spec = api.app.openapi()
for path, methods in spec.get('paths', {}).items():
    if any(key in path for key in ['/profile','/pantry','/food-rescue','/household','/wochenplan','/einkaufsliste','/recipe-notes','/auth/sessions','/auth/export','/roulette']):
        print(path, json.dumps(methods, ensure_ascii=False, sort_keys=True))
