from pathlib import Path
import sys, json
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import api

spec = api.app.openapi()
print('MODELS')
for name, schema in sorted(spec.get('components', {}).get('schemas', {}).items()):
    if any(k in name.lower() for k in ['household','profile','register','login','pantry','recipe','rating','items']):
        print(name, json.dumps(schema, ensure_ascii=False, sort_keys=True))

print('ROUTES')
for path, methods in spec.get('paths', {}).items():
    if any(k in path for k in ['/auth','/household','/favorites','/ratings','/eaten','/rezepte/{recipe_id}/scale']):
        print(path, json.dumps(methods, ensure_ascii=False, sort_keys=True))
