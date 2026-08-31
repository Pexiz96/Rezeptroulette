from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import api

print('ROUTES_AND_MOUNTS')
for route in api.app.routes:
    print(type(route).__name__, getattr(route, 'path', ''), getattr(route, 'name', ''))

print('SAMPLE_RECIPES')
try:
    rows = api.db.all_recipes(None)
    for row in rows[:10]:
        print(row.get('id'), row.get('name'), 'bild=', repr(row.get('bild')), 'image=', repr(row.get('image')), 'image_url=', repr(row.get('image_url')))
except Exception as exc:
    print(type(exc).__name__, str(exc))
