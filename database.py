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

# Zusätzliche kuratierte Rezepte werden beim Initialisieren der Datenbank
# idempotent ergänzt. Dadurch funktioniert das sowohl lokal als auch auf
# Render/PostgreSQL und bereits vorhandene Rezepte werden nicht dupliziert.
_OriginalDatabase = Database


class Database(_OriginalDatabase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from extra_recipes import ensure_extra_recipes
            from extra_recipes_batch2 import ensure_extra_recipes_batch2

            ensure_extra_recipes(self.engine)
            ensure_extra_recipes_batch2(self.engine)
        except Exception as exc:
            # Bei initialize=False können die Tabellen beim ersten Import noch
            # fehlen. Der reguläre Startup-Lauf mit initialize=True ergänzt die
            # Rezepte anschließend automatisch.
            print(f"[Rezeptroulette] Zusatzrezepte konnten noch nicht ergänzt werden: {exc}")
