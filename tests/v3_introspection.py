from pathlib import Path
import sys, base64, gzip
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

api_b64 = ''.join((ROOT / '.github/upgrade_payload/api.py.gz.b64').read_text().split())
api_source = gzip.decompress(base64.b64decode(api_b64)).decode('utf-8')
print('API_HEAD')
for idx, line in enumerate(api_source.splitlines()[:80], 1):
    print(f'{idx:03d}: {line}')

from database import Database
import smart_features
print('SMART_FEATURES')
for name in sorted(n for n in dir(smart_features) if not n.startswith('_')):
    print(name)
print('DATABASE_METHODS')
for name in sorted(n for n in dir(Database) if not n.startswith('_')):
    print(name)

import api
print('ROUTES')
for route in api.app.routes:
    path = getattr(route, 'path', '')
    methods = sorted(getattr(route, 'methods', []) or [])
    print(','.join(methods), path)
