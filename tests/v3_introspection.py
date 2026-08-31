from database import Database
import smart_features

print('SMART_FEATURES')
for name in sorted(n for n in dir(smart_features) if not n.startswith('_')):
    print(name)

print('DATABASE_METHODS')
for name in sorted(n for n in dir(Database) if not n.startswith('_')):
    print(name)

try:
    import api
except Exception as exc:
    print('API_IMPORT_ERROR', type(exc).__name__, str(exc))
    raise

print('ROUTES')
for route in api.app.routes:
    path = getattr(route, 'path', '')
    methods = sorted(getattr(route, 'methods', []) or [])
    print(','.join(methods), path)
