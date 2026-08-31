from __future__ import annotations

import os as _os

from fastapi.responses import FileResponse as _FileResponse

from payload_loader import exec_gzip_base64_payload

exec_gzip_base64_payload(
    globals(),
    [".github/upgrade_payload/api.py.gz.b64"],
    "api.py",
)

# The generated API payload intentionally remains self-contained. Replace only its
# legacy home route here so production serves the tested V3 frontend while all API
# routes keep their original behavior.
app.router.routes[:] = [
    route
    for route in app.router.routes
    if not (
        getattr(route, "path", None) == "/"
        and "GET" in (getattr(route, "methods", None) or set())
    )
]


def v3_home():
    return _FileResponse(_os.path.join(STATIC_DIR, "index-v3.html"))


app.add_api_route("/", v3_home, methods=["GET"], include_in_schema=False)
