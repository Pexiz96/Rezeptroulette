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

# Zusätzliche kuratierte Rezepte werden idempotent ergänzt. Die Funktion
# prüft den Rezeptnamen und verändert bereits vorhandene Rezepte nicht.
try:
    from extra_recipes import ensure_extra_recipes

    ensure_extra_recipes(engine)
except Exception as exc:
    # Die App soll auch dann starten, wenn beim optionalen Seed ein einzelner
    # Datenbankfehler auftritt; der Fehler bleibt im Log sichtbar.
    print(f"[Rezeptroulette] Extra-Rezepte konnten nicht ergänzt werden: {exc}")
