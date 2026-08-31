from database import Database
import api

print('DATABASE_METHODS')
for name in sorted(n for n in dir(Database) if not n.startswith('_')):
    print(name)
print('ROUTES')
for route in api.app.routes:
    path = getattr(route, 'path', '')
    methods = sorted(getattr(route, 'methods', []) or [])
    print(','.join(methods), path)
