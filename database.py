from __future__ import annotations

from payload_loader import exec_gzip_base64_payload

exec_gzip_base64_payload(
    globals(),
    [
        ".github/upgrade_payload/database.00",
        ".github/upgrade_payload/database.01",
        ".github/upgrade_payload/database.02",
        ".github/upgrade_payload/database.03",
    ],
    "database.py",
)

# Zusätzliche kuratierte Rezepte werden idempotent ergänzt. Die Funktionen
# prüfen jeweils den Rezeptnamen und verändern bereits vorhandene Rezepte nicht.
try:
    from extra_recipes import ensure_extra_recipes

    ensure_extra_recipes(engine)
except Exception as exc:
    print(f"[Rezeptroulette] Extra-Rezepte Batch 1 konnten nicht ergänzt werden: {exc}")

try:
    from extra_recipes_batch2 import ensure_extra_recipes_batch2

    ensure_extra_recipes_batch2(engine)
except Exception as exc:
    print(f"[Rezeptroulette] Extra-Rezepte Batch 2 konnten nicht ergänzt werden: {exc}")
