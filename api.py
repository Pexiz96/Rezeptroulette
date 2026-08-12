import os
import random
import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from dataclasses import asdict

from fastapi import FastAPI, HTTPException, Request, Response, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from database import Database
from models import Rezept

import re

def clean_text(text):
    if not text:
        return ""

    text = str(text)

    replacements = {
        "Ã¤": "ä",
        "Ã¶": "ö",
        "Ã¼": "ü",
        "ÃŸ": "ß",
        "â€“": "-",
        "â€œ": "\"",
        "â€": "\"",
    }

    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)

    text = re.sub(r'\s+', ' ', text)

    return text.strip()

def normalize_ingredient_name(text):
    text = str(text).lower().strip()

    text = clean_text(text)

    text = text.replace("–", "-")
    text = text.replace("oder", " ")
    text = text.replace("nach wahl", "")
    text = text.replace("optional", "")
    text = text.replace("belieben", "")

    text = re.sub(r"\d+\s*[-–]\s*\d+", "", text)
    text = re.sub(r"\d+[.,]?\d*", "", text)

    text = re.sub(
        r"\b(g|kg|ml|l|el|tl|stück|stk|dose|dosen|tüte|packung|päckchen|prise|bund|glas|becher)\b",
        "",
        text
    )

    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"[^a-zäöüß\s-]", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    replacements = {
        "tomaten": "tomate",
        "gehackte tomaten": "tomate",
        "tomatensauce": "tomate",
        "tomatenmark": "tomatenmark",

        "zwiebel": "zwiebel",
        "zwiebeln": "zwiebel",

        "eier": "ei",
        "eigelb": "ei",

        "hähnchenbrust": "hähnchen",
        "hähnchen": "hähnchen",
        "hähnchen oder hackfleisch": "hähnchen/hackfleisch",

        "käse": "käse",
        "geriebener käse": "käse",
        "light-reibekäse": "käse",

        "skyr": "skyr",
        "magerquark": "magerquark",
        "frischkäse": "frischkäse",

        "nudeln": "nudeln",
        "wraps": "wrap",
        "low-carb-wrap": "wrap",
        "bagels": "bagel",

        "olivenöl": "öl",
        "öl": "öl",

        "zucker": "zucker",
        "erythrit": "zuckerersatz",

        "mehl": "mehl",
        "dinkelmehl": "mehl",

        "backpulver": "backpulver",
        "zimt": "zimt",
        "salz": "salz",
        "pfeffer": "pfeffer",
        "oregano": "oregano",
    }

    return replacements.get(text, text)

class RezeptCreate(BaseModel):
    name: str
    kueche: str = "Unbekannt"
    bild: str = ""
    portionen: int = 2
    kochzeit: int = 30
    schwierigkeit: str = "Einfach"
    tags: list[str] = Field(default_factory=list)
    zutaten: list[str] = Field(default_factory=list)
    anleitung: str = "Keine Anleitung vorhanden."


class WeeklyPlanEntry(BaseModel):
    day: str
    slot: int = Field(ge=1, le=3)
    recipe_id: int | None = None


class WeeklyPlanBulk(BaseModel):
    entries: list[WeeklyPlanEntry] = Field(default_factory=list)


class AuthCredentials(BaseModel):
    email: str
    password: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class RatingPayload(BaseModel):
    rating: int = Field(ge=1, le=5)


class ItemsPayload(BaseModel):
    items: list[str] = Field(default_factory=list)


app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
BILDER_DIR = os.path.join(BASE_DIR, "bilder")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/bilder", StaticFiles(directory=BILDER_DIR), name="bilder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSION_COOKIE = "rr_session"
SESSION_DAYS = 30
PBKDF2_ITERATIONS = 310_000


def get_db():
    return Database()


def normalize_email(email: str) -> str:
    return str(email or "").strip().lower()


def validate_email(email: str) -> str:
    email = normalize_email(email)
    if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise HTTPException(status_code=400, detail="Bitte eine gültige E-Mail-Adresse eingeben")
    return email


def validate_password(password: str) -> str:
    password = str(password or "")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Das Passwort muss mindestens 8 Zeichen lang sein")
    if len(password) > 256:
        raise HTTPException(status_code=400, detail="Das Passwort ist zu lang")
    return password


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS,
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = stored.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_b64.encode("ascii"))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def is_https(request: Request) -> bool:
    forwarded = request.headers.get("x-forwarded-proto", "").split(",")[0].strip().lower()
    return forwarded == "https" or request.url.scheme == "https"


def set_session_cookie(response: Response, request: Request, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=SESSION_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=is_https(request),
        samesite="lax",
        path="/",
    )


def optional_user(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    db = get_db()
    return db.get_session_user(token_hash(token), now_utc().isoformat())


def require_user(request: Request):
    user = optional_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Bitte zuerst anmelden")
    return user



@app.post("/auth/register")
def register(credentials: AuthCredentials, request: Request, response: Response):
    email = validate_email(credentials.email)
    password = validate_password(credentials.password)
    db = get_db()
    if db.get_user_by_email(email):
        raise HTTPException(status_code=409, detail="Für diese E-Mail gibt es bereits ein Konto")
    try:
        user_id = db.create_user(email, hash_password(password))
    except Exception as exc:
        if "UNIQUE constraint failed" in str(exc):
            raise HTTPException(status_code=409, detail="Für diese E-Mail gibt es bereits ein Konto")
        raise
    token = secrets.token_urlsafe(32)
    expires = now_utc() + timedelta(days=SESSION_DAYS)
    db.create_session(user_id, token_hash(token), expires.isoformat())
    set_session_cookie(response, request, token)
    return {"id": user_id, "email": email}


@app.post("/auth/login")
def login(credentials: AuthCredentials, request: Request, response: Response):
    email = validate_email(credentials.email)
    db = get_db()
    user = db.get_user_by_email(email)
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="E-Mail oder Passwort ist falsch")
    token = secrets.token_urlsafe(32)
    expires = now_utc() + timedelta(days=SESSION_DAYS)
    db.create_session(int(user["id"]), token_hash(token), expires.isoformat())
    set_session_cookie(response, request, token)
    return {"id": int(user["id"]), "email": user["email"]}


@app.post("/auth/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        get_db().delete_session(token_hash(token))
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True}

@app.delete("/admin/reset-users")
def reset_users(x_admin_key: str = Header(default="")):
    expected_key = os.getenv("ADMIN_RESET_KEY", "")

    if not expected_key or x_admin_key != expected_key:
        raise HTTPException(
            status_code=403,
            detail="Nicht erlaubt"
        )

    db = get_db()

    try:
        db.conn.execute("PRAGMA foreign_keys = ON")
        db.conn.execute("DELETE FROM users")
        db.conn.commit()

        return {
            "ok": True,
            "message": "Alle Benutzerkonten wurden gelöscht."
        }
    finally:
        db.conn.close()

@app.get("/auth/me")
def me(user=Depends(require_user)):
    return {"id": int(user["id"]), "email": user["email"], "created_at": user["created_at"]}


@app.post("/auth/password")
def change_password(payload: PasswordChange, request: Request, response: Response, user=Depends(require_user)):
    db = get_db()
    full_user = db.get_user(int(user["id"]))
    if not full_user or not verify_password(payload.current_password, full_user["password_hash"]):
        raise HTTPException(status_code=400, detail="Aktuelles Passwort ist falsch")
    new_password = validate_password(payload.new_password)
    db.update_user_password(int(user["id"]), hash_password(new_password))
    token = secrets.token_urlsafe(32)
    expires = now_utc() + timedelta(days=SESSION_DAYS)
    db.create_session(int(user["id"]), token_hash(token), expires.isoformat())
    set_session_cookie(response, request, token)
    return {"ok": True}


@app.delete("/auth/account")
def delete_account(request: Request, response: Response, user=Depends(require_user)):
    get_db().delete_user(int(user["id"]))
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True}


@app.get("/user-state")
def user_state(user=Depends(require_user)):
    db = get_db()
    uid = int(user["id"])
    return {
        "favorites": db.favorite_ids(uid),
        "ratings": db.ratings(uid),
        "pantry": db.get_user_items("user_pantry", uid),
        "at_home": db.get_user_items("user_at_home", uid),
    }


@app.get("/favorites")
def get_favorites(user=Depends(require_user)):
    return {"ids": get_db().favorite_ids(int(user["id"]))}


@app.post("/favorites/{recipe_id}/toggle")
def toggle_favorite(recipe_id: int, user=Depends(require_user)):
    db = get_db()
    if not db.get_recipe(recipe_id):
        raise HTTPException(status_code=404, detail="Rezept nicht gefunden")
    favorite = db.toggle_user_favorite(int(user["id"]), recipe_id)
    return {"favorite": favorite, "ids": db.favorite_ids(int(user["id"]))}


@app.get("/ratings")
def get_ratings(user=Depends(require_user)):
    return get_db().ratings(int(user["id"]))


@app.put("/ratings/{recipe_id}")
def put_rating(recipe_id: int, payload: RatingPayload, user=Depends(require_user)):
    db = get_db()
    if not db.get_recipe(recipe_id):
        raise HTTPException(status_code=404, detail="Rezept nicht gefunden")
    db.set_rating(int(user["id"]), recipe_id, payload.rating)
    return {"ok": True, "rating": payload.rating}


@app.get("/pantry")
def get_pantry(user=Depends(require_user)):
    return {"items": get_db().get_user_items("user_pantry", int(user["id"]))}


@app.put("/pantry")
def put_pantry(payload: ItemsPayload, user=Depends(require_user)):
    db = get_db()
    db.replace_user_items("user_pantry", int(user["id"]), payload.items)
    return {"items": db.get_user_items("user_pantry", int(user["id"]))}


@app.get("/at-home")
def get_at_home(user=Depends(require_user)):
    return {"items": get_db().get_user_items("user_at_home", int(user["id"]))}


@app.put("/at-home")
def put_at_home(payload: ItemsPayload, user=Depends(require_user)):
    db = get_db()
    db.replace_user_items("user_at_home", int(user["id"]), payload.items)
    return {"items": db.get_user_items("user_at_home", int(user["id"]))}


@app.delete("/delete-pdf-recipes")
def delete_pdf_recipes():
    db = get_db()
    deleted = db.delete_pdf_imports()
    return {"deleted": deleted}

@app.get("/")
def home():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/rezepte")
def get_rezepte():
    db = get_db()
    return [asdict(r) for r in db.all_recipes()]

@app.post("/rezept-erstellen")
def rezept_erstellen(daten: RezeptCreate):
    db = get_db()

    if not daten.name.strip():
        return {"error": "Name fehlt"}

    rezept = Rezept(
        name=daten.name.strip(),
        kueche=daten.kueche.strip() or "Unbekannt",
        bild=daten.bild.strip(),
        portionen=max(1, daten.portionen),
        kochzeit=max(1, daten.kochzeit),
        schwierigkeit=daten.schwierigkeit or "Einfach",
        tags=daten.tags,
        favorit=False,
        zutaten=daten.zutaten,
        anleitung=daten.anleitung.strip() or "Keine Anleitung vorhanden.",
    )

    recipe_id = db.save_recipe(rezept)
    saved = db.get_recipe(recipe_id)

    return asdict(saved)
@app.post("/rezept-aus-link")
def rezept_aus_link(daten: dict):
    db = get_db()
    url = daten.get("url", "").strip()

    if not url:
        return {"error": "Kein Link angegeben"}

    rezept = Rezept(
        name="Importiertes Rezept",
        kueche="Link Import",
        bild="",
        portionen=2,
        kochzeit=30,
        schwierigkeit="Einfach",
        tags=["Import"],
        favorit=False,
        zutaten=["Bitte Zutaten prüfen"],
        anleitung=f"Quelle:\n{url}\n\nBitte Zutaten und Anleitung ergänzen."
    )

    recipe_id = db.save_recipe(rezept)
    saved = db.get_recipe(recipe_id)

    return asdict(saved)
@app.delete("/rezepte/{recipe_id}")
def rezept_loeschen(recipe_id: int):
    db = get_db()
    db.delete_recipe(recipe_id)
    return {"message": "Rezept gelöscht"}

@app.delete("/rezepte/importierte")
def importierte_rezepte_loeschen():
    db = get_db()
    db.conn.execute("DELETE FROM recipes WHERE kueche = ?", ("Link Import",))
    db.conn.commit()
    return {"message": "Importierte Rezepte gelöscht"}
    
@app.get("/roulette")
def roulette():
    db = get_db()
    rezepte = db.all_recipes()

    if not rezepte:
        return {"error": "Keine Rezepte vorhanden"}

    rezept = random.choice(rezepte)
    daten = asdict(rezept)

    daten["bild_url"] = f"/bilder/{daten['bild']}"

    return daten


VALID_DAYS = [
    "Montag", "Dienstag", "Mittwoch", "Donnerstag",
    "Freitag", "Samstag", "Sonntag"
]


def validate_plan_target(day: str, slot: int) -> None:
    if day not in VALID_DAYS:
        raise HTTPException(status_code=400, detail="Ungültiger Wochentag")
    if slot not in (1, 2, 3):
        raise HTTPException(status_code=400, detail="Ungültiger Mahlzeiten-Slot")


@app.get("/wochenplan")
def wochenplan(request: Request):
    db = get_db()
    user = optional_user(request)
    return db.user_weekly_plan(int(user["id"])) if user else db.weekly_plan()


@app.post("/wochenplan/reset")
def reset_wochenplan(request: Request):
    db = get_db()
    user = optional_user(request)
    if user:
        db.reset_user_weekly_plan(int(user["id"]))
    else:
        db.reset_weekly_plan()
    return {"message": "Wochenplan geleert"}


@app.post("/wochenplan/clear/{day}")
def loesche_tag(day: str, request: Request):
    if day not in VALID_DAYS:
        raise HTTPException(status_code=400, detail="Ungültiger Wochentag")

    db = get_db()
    user = optional_user(request)
    entries = [(day, slot, None) for slot in (1, 2, 3)]
    if user:
        db.set_user_weekly_plan_bulk(int(user["id"]), entries)
    else:
        db.set_weekly_plan_bulk(entries)
    return {"message": f"{day} wurde gelöscht"}


@app.post("/wochenplan/bulk")
def set_weekly_plan_bulk(payload: WeeklyPlanBulk, request: Request):
    db = get_db()
    entries = []

    for entry in payload.entries:
        validate_plan_target(entry.day, entry.slot)

        recipe_id = entry.recipe_id
        if recipe_id in (None, 0):
            recipe_id = None
        elif not db.get_recipe(int(recipe_id)):
            raise HTTPException(status_code=404, detail=f"Rezept {recipe_id} nicht gefunden")

        entries.append((entry.day, entry.slot, recipe_id))

    user = optional_user(request)
    if user:
        db.set_user_weekly_plan_bulk(int(user["id"]), entries)
    else:
        db.set_weekly_plan_bulk(entries)
    return {"ok": True, "saved": len(entries)}


@app.post("/wochenplan/{day}/{slot}/{recipe_id}")
def set_weekly_plan(day: str, slot: int, recipe_id: int, request: Request):
    validate_plan_target(day, slot)
    db = get_db()

    if recipe_id != 0 and not db.get_recipe(recipe_id):
        raise HTTPException(status_code=404, detail="Rezept nicht gefunden")

    user = optional_user(request)
    if user:
        db.set_user_weekly_plan_slot(int(user["id"]), day, slot, recipe_id)
    else:
        db.set_weekly_plan_slot(day, slot, recipe_id)
    return {"ok": True}

def parse_ingredient(text):
    original = str(text).strip()
    cleaned = clean_text(original).lower()
    cleaned = cleaned.replace("½", "0.5")
    cleaned = cleaned.replace("optional:", "")
    cleaned = cleaned.replace("optional", "")
    cleaned = cleaned.replace("nach wahl", "")
    cleaned = cleaned.replace("nach belieben", "")
    cleaned = cleaned.replace("zum servieren", "")
    cleaned = cleaned.replace("oder gemüse", "")
    cleaned = cleaned.strip()

    cleaned = cleaned.replace("–", "-")
    cleaned = cleaned.replace(" ca. ", " ")
    cleaned = cleaned.replace("ca. ", "")
    cleaned = cleaned.replace("optional", "")
    cleaned = cleaned.replace("nach wahl", "")
    cleaned = cleaned.replace("nach belieben", "")
    cleaned = cleaned.replace("nach belieben", "")

    match = re.match(
        r"^(\d+(?:[.,]\d+)?)(?:\s*-\s*\d+(?:[.,]\d+)?)?\s*(g|kg|ml|l|el|tl|stück|stk|dose|dosen|scheiben|tüte|packung|päckchen)?\s+(.+)$",
        cleaned
    )

    if not match:
        name = normalize_ingredient_name(cleaned)
        return {
            "original": original,
            "amount": None,
            "unit": "",
            "name": name,
        }

    amount = float(match.group(1).replace(",", "."))
    unit = match.group(2) or ""
    name = normalize_ingredient_name(match.group(3))

    unit_map = {
        "stk": "stück",
        "dose": "dose",
        "dosen": "dose",
        "tl": "TL",
        "el": "EL",
        "päckchen": "Päckchen",
        "dose": "Dose",
        "dosen": "Dose",
        "tüte": "Tüte",
        "scheiben": "Scheiben",
    }

    unit = unit_map.get(unit, unit)

    name_map = {
    # Eier
    "ei": "ei",
    "eier": "ei",
    "eigelb": "ei",

    "frühlingszwiebeln": "frühlingszwiebel",
    "frühlingszwiebel": "frühlingszwiebel",

    "gurken": "gurke",
    "gurke": "gurke",

    "parmesan": "parmesan",

    "mozzarella light": "mozzarella",
    "mozzarella": "mozzarella",

    "päckchen backpulver": "backpulver",

    # Zwiebeln
    "zwiebel": "zwiebel",
    "zwiebeln": "zwiebel",
    "rote zwiebel": "zwiebel",
    "kleine zwiebel": "zwiebel",

    # Knoblauch
    "knoblauch": "knoblauch",
    "knoblauchzehe": "knoblauch",
    "knoblauchzehen": "knoblauch",

    # Tomaten
    "tomate": "tomate",
    "tomaten": "tomate",
    "gehackte tomaten": "tomate",
    "dose tomaten": "tomate",

    # Paprika
    "paprika": "paprika",
    "rote paprika": "paprika",
    "kleine paprika": "paprika",

    # Käse
    "käse": "käse",
    "geriebener käse": "käse",
    "scheiben käse": "käse",
    "light-reibekäse": "käse",

    # Backwaren
    "wrap": "wrap",
    "wraps": "wrap",
    "low-carb-wrap": "wrap",

    "bagel": "bagel",
    "bagels": "bagel",

    # Gewürze
    "salz": "salz",
    "pfeffer": "pfeffer",
    "muskat": "muskat",
    "oregano": "oregano",

    # Öle
    "öl": "öl",
    "olivenöl": "öl",
    "butter": "butter",

    # Backzutaten
    "backpulver": "backpulver",
    "mehl": "mehl",
    "dinkelmehl": "mehl",
    "weizenmehl": "mehl",

    # Milchprodukte
    "skyr": "skyr",
    "magerquark": "magerquark",
    "frischkäse": "frischkäse",
    "hüttenkäse": "hüttenkäse",
    "sahne": "sahne",
    "milch": "milch",
}
    name = name_map.get(name, name)

    return {
        "original": original,
        "amount": amount,
        "unit": unit,
        "name": name,
    }

def ingredient_category(name):
    text = normalize_ingredient_name(name).lower()

    category_map = {
        "🥦 Obst & Gemüse": [
            "apfel", "äpfel", "banane", "bananen", "beeren", "erdbeere", "erdbeeren",
            "himbeere", "himbeeren", "blaubeere", "blaubeeren",
            "tomate", "tomaten", "tomatensauce", "tomatenmark",
            "paprika", "zucchini", "gurke", "gurken", "karotte", "karotten",
            "möhre", "möhren", "zwiebel", "zwiebeln", "lauchzwiebel",
            "frühlingszwiebel", "knoblauch", "kartoffel", "kartoffeln",
            "brokkoli", "weißkohl", "kohl", "salat", "eisbergsalat", "erbsen"
        ],

        "🥛 Milchprodukte & Eier": [
            "milch", "mandelmilch", "sahne", "protein-sahne", "joghurt",
            "skyr", "quark", "magerquark", "frischkäse", "kräuterfrischkäse",
            "hüttenkäse", "käse", "mozzarella", "parmesan", "schmand",
            "butter", "ei", "eier"
        ],

        "🥩 Fleisch & Fisch": [
            "hähnchen", "hähnchenbrust", "hähnchenbrüste", "hackfleisch",
            "gyrosfleisch", "rind", "rindergulasch", "kassler", "speck",
            "speckwürfel", "putenbrust", "würstchen", "fischstäbchen",
            "thunfisch", "schweineschnitzel"
        ],

        "🍝 Trockenwaren & Beilagen": [
            "reis", "milchreis", "nudeln", "spaghetti", "pasta", "tortellini",
            "gnocchi", "mehl", "dinkelmehl", "weizenmehl", "maismehl",
            "haferflocken", "wrap", "wraps", "bagel", "bagels", "toast",
            "brot", "brötchen", "burgerbrötchen", "eiweißbrot", "brezel",
            "brezeln", "paniermehl", "protein-biskuit"
        ],

        "🧂 Gewürze & Backen": [
            "salz", "pfeffer", "paprikapulver", "oregano", "zimt", "muskat",
            "italienische kräuter", "kräuter", "kümmel", "chili",
            "backpulver", "sahnesteif", "vanillepuddingpulver",
            "vanillezucker", "vanilleextrakt", "zucker", "zuckerersatz",
            "erythrit", "honig", "öl", "olivenöl", "speisestärke"
        ],

        "🥫 Konserven & Soßen": [
            "kidneybohnen", "mais", "tomaten", "gehackte tomaten",
            "brühe", "rinderbrühe", "pesto", "sojasauce", "ketchup",
            "mayonnaise", "miracle whip", "salsa", "tzatziki", "joghurtsoße"
        ],

        "🍫 Süßes & Toppings": [
            "chunky flavour", "granola", "keksbrösel", "schokodrops",
            "light-schokodrops", "schokolade", "trockenfrüchte",
            "walnüsse", "chiasamen", "sonnenblumenkerne", "mohn",
            "erdnussbutter", "salatkernmischung", "körner"
        ],

        "📦 Sonstiges": []
    }

    for category, keywords in category_map.items():
        if category == "📦 Sonstiges":
            continue

        for keyword in keywords:
            if keyword in text:
                return category

    return "📦 Sonstiges"

def shopping_list(recipes):
    categories = {}
    pantry = []
    ingredient_map = {}

    for recipe in recipes:
        zutaten = getattr(recipe, "zutaten", None) or getattr(recipe, "ingredients", None) or []

        if isinstance(zutaten, str):
            zutaten = [z.strip() for z in zutaten.split(",") if z.strip()]

        for zutat in zutaten:
            parsed = parse_ingredient(zutat)

            key = f'{parsed["name"]}|{parsed["unit"]}'

            if key not in ingredient_map:
                ingredient_map[key] = {
                    "name": parsed["name"],
                    "unit": parsed["unit"],
                    "amount": parsed["amount"],
                    "examples": [parsed["original"]],
                    "count": 1
                }
            else:
                existing = ingredient_map[key]

                if existing["amount"] is not None and parsed["amount"] is not None:
                    existing["amount"] += parsed["amount"]
                else:
                    existing["amount"] = None

                existing["examples"].append(parsed["original"])
                existing["count"] += 1

    result = []

    for item in ingredient_map.values():
        name = item["name"]
        unit = item["unit"]
        amount = item["amount"]

        if amount is not None:
            if amount.is_integer():
                amount = int(amount)

            if unit in ["", "stück"]:
                if name == "ei":
                    label = "Ei" if amount == 1 else "Eier"
                elif name == "zwiebel":
                    label = "Zwiebel" if amount == 1 else "Zwiebeln"
                elif name == "tomate":
                    label = "Tomate" if amount == 1 else "Tomaten"
                elif name == "knoblauch":
                    label = "Knoblauchzehe" if amount == 1 else "Knoblauchzehen"
                elif name == "frühlingszwiebel":
                    label = "Frühlingszwiebel" if amount == 1 else "Frühlingszwiebeln"
                else:
                    label = name.capitalize()

                result.append(f"{amount} {label}")
            else:
                result.append(f"{amount} {unit} {name}")
        else:
            if item["count"] > 1:
                result.append(f'{item["examples"][0]} ({item["count"]}x)')
            else:
                result.append(item["examples"][0])

    categories = {}

    for item in result:
        category = ingredient_category(item)

        if category not in categories:
            categories[category] = []

        categories[category].append(item)

    for category in categories:
        categories[category] = sorted(
            categories[category],
            key=lambda x: x.lower()
        )

    return categories, pantry


@app.get("/einkaufsliste")
def einkaufsliste(request: Request):
    db = get_db()
    user = optional_user(request)
    plan = db.user_weekly_plan(int(user["id"])) if user else db.weekly_plan()

    recipes = []

    for day_slots in plan.values():
        if isinstance(day_slots, dict):
            for recipe_id in day_slots.values():
                if recipe_id:
                    recipe = db.get_recipe(int(recipe_id))
                    if recipe:
                        recipes.append(recipe)
        elif day_slots:
            recipe = db.get_recipe(int(day_slots))
            if recipe:
                recipes.append(recipe)

    categories, pantry = shopping_list(recipes)

    return {
        "categories": categories,
        "pantry": pantry,
    }