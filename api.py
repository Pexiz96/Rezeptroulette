from __future__ import annotations

import base64
import hashlib
import hmac
import io
import os
import random
import re
import secrets
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import (
    FastAPI, HTTPException, Request, Response, Depends, Header, UploadFile, File
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from PIL import Image, UnidentifiedImageError

from database import Database

SESSION_COOKIE = "rr_session"
SESSION_DAYS = 30
PBKDF2_ITERATIONS = 310_000
MAX_AVATAR_BYTES = 5 * 1024 * 1024
ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp"}
VALID_DAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
BILDER_DIR = os.path.join(BASE_DIR, "bilder")

db = Database(initialize=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Database(initialize=True)
    yield


app = FastAPI(
    title="Rezeptroulette API",
    version="2.0.0",
    docs_url="/api/docs" if os.getenv("ENABLE_API_DOCS", "false").lower() == "true" else None,
    redoc_url=None,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
if os.path.isdir(BILDER_DIR):
    app.mount("/bilder", StaticFiles(directory=BILDER_DIR), name="bilder")

allowed_origins = [
    value.strip() for value in os.getenv("ALLOWED_ORIGINS", "").split(",") if value.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or [],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-Admin-Key"],
)
app.add_middleware(GZipMiddleware, minimum_size=800)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    if is_https(request):
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# -------------------- Models --------------------

class RegisterPayload(BaseModel):
    username: str
    email: str
    password: str
    display_name: str = ""


class LoginPayload(BaseModel):
    identifier: str
    password: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class ProfileUpdate(BaseModel):
    username: str
    display_name: str = ""
    bio: str = ""


class RatingPayload(BaseModel):
    rating: int = Field(ge=1, le=5)


class ItemsPayload(BaseModel):
    items: list[str] = Field(default_factory=list)


class PreferencesPayload(BaseModel):
    preferences: dict[str, Any] = Field(default_factory=dict)


class RecipeCreate(BaseModel):
    name: str
    kueche: str = "Unbekannt"
    bild: str = ""
    portionen: int = Field(default=2, ge=1, le=100)
    kochzeit: int = Field(default=30, ge=1, le=1440)
    schwierigkeit: str = "Einfach"
    tags: list[str] = Field(default_factory=list)
    zutaten: list[str] = Field(default_factory=list)
    anleitung: str = "Keine Anleitung vorhanden."
    description: str = ""
    source_url: str = ""


class RecipeLinkPayload(BaseModel):
    url: str
    name: str = "Gespeichertes Rezept"


class WeeklyPlanEntry(BaseModel):
    day: str
    slot: int = Field(ge=1, le=3)
    recipe_id: int | None = None


class WeeklyPlanBulk(BaseModel):
    entries: list[WeeklyPlanEntry] = Field(default_factory=list)


# -------------------- Helpers --------------------

def normalize_email(value: str) -> str:
    return str(value or "").strip().lower()


def validate_email(value: str) -> str:
    email = normalize_email(value)
    if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise HTTPException(status_code=400, detail="Bitte eine gültige E-Mail-Adresse eingeben.")
    return email


def normalize_username(value: str) -> str:
    username = str(value or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9._-]{3,30}", username):
        raise HTTPException(
            status_code=400,
            detail="Benutzername: 3–30 Zeichen, nur Buchstaben, Zahlen, Punkt, Unterstrich oder Bindestrich."
        )
    return username


def validate_password(password: str) -> str:
    password = str(password or "")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Das Passwort muss mindestens 8 Zeichen lang sein.")
    if len(password) > 256:
        raise HTTPException(status_code=400, detail="Das Passwort ist zu lang.")
    return password


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS,
        base64.urlsafe_b64encode(salt).decode(),
        base64.urlsafe_b64encode(digest).decode(),
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = stored.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_b64.encode())
        expected = base64.urlsafe_b64decode(digest_b64.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def is_https(request: Request) -> bool:
    forwarded = request.headers.get("x-forwarded-proto", "").split(",")[0].strip().lower()
    return forwarded == "https" or request.url.scheme == "https"


def set_session_cookie(response: Response, request: Request, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_DAYS * 86400,
        httponly=True,
        secure=is_https(request),
        samesite="lax",
        path="/",
    )


def public_user(row: Any) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "username": row["username"],
        "email": row["email"],
        "display_name": row.get("display_name") or row["username"],
        "bio": row.get("bio") or "",
        "created_at": row["created_at"],
        "avatar_url": f"/users/{int(row['id'])}/avatar",
    }


def current_user_optional(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    return db.get_session_user(token_hash(token), now_utc().isoformat())


def current_user(request: Request):
    user = current_user_optional(request)
    if not user:
        raise HTTPException(status_code=401, detail="Bitte zuerst anmelden.")
    return user


def validate_plan_target(day: str, slot: int) -> None:
    if day not in VALID_DAYS:
        raise HTTPException(status_code=400, detail="Ungültiger Wochentag.")
    if slot not in (1, 2, 3):
        raise HTTPException(status_code=400, detail="Ungültiger Mahlzeiten-Slot.")


def user_recipe(recipe_id: int, user_id: int | None):
    recipe = db.get_recipe(recipe_id, user_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Rezept nicht gefunden.")
    return recipe


# Einfache Login-Drosselung. Für mehrere Serverinstanzen später Redis verwenden.
_attempts: dict[str, deque[float]] = defaultdict(deque)


def enforce_login_rate_limit(request: Request) -> None:
    key = request.client.host if request.client else "unknown"
    now = time.monotonic()
    q = _attempts[key]
    while q and now - q[0] > 600:
        q.popleft()
    if len(q) >= 12:
        raise HTTPException(status_code=429, detail="Zu viele Anmeldeversuche. Bitte später erneut versuchen.")
    q.append(now)


def clear_login_attempts(request: Request) -> None:
    key = request.client.host if request.client else "unknown"
    _attempts.pop(key, None)


# -------------------- Health / App --------------------

@app.get("/health")
def health():
    return {"ok": True, "service": "rezeptroulette", "version": "2.0.0"}


@app.get("/")
def home():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


# -------------------- Auth / Profil --------------------

@app.post("/auth/register")
def register(payload: RegisterPayload, request: Request, response: Response):
    enforce_login_rate_limit(request)
    username = normalize_username(payload.username)
    email = validate_email(payload.email)
    password = validate_password(payload.password)

    if db.get_user_by_username(username):
        raise HTTPException(status_code=409, detail="Dieser Benutzername ist bereits vergeben.")
    if db.get_user_by_email(email):
        raise HTTPException(status_code=409, detail="Für diese E-Mail-Adresse gibt es bereits ein Konto.")

    try:
        user_id = db.create_user(
            username=username,
            email=email,
            password_hash=hash_password(password),
            display_name=(payload.display_name or username).strip()[:80],
        )
    except Exception:
        # Eindeutige Indizes fangen parallele Registrierungen ab.
        if db.get_user_by_username(username):
            raise HTTPException(status_code=409, detail="Dieser Benutzername ist bereits vergeben.")
        if db.get_user_by_email(email):
            raise HTTPException(status_code=409, detail="Für diese E-Mail-Adresse gibt es bereits ein Konto.")
        raise

    token = secrets.token_urlsafe(32)
    db.create_session(user_id, token_hash(token), (now_utc() + timedelta(days=SESSION_DAYS)).isoformat())
    set_session_cookie(response, request, token)
    clear_login_attempts(request)
    return public_user(db.get_user(user_id))


@app.post("/auth/login")
def login(payload: LoginPayload, request: Request, response: Response):
    enforce_login_rate_limit(request)
    identifier = str(payload.identifier or "").strip().lower()
    user = db.get_user_by_email(identifier) if "@" in identifier else db.get_user_by_username(identifier)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Benutzername/E-Mail oder Passwort ist falsch.")

    token = secrets.token_urlsafe(32)
    db.create_session(int(user["id"]), token_hash(token), (now_utc() + timedelta(days=SESSION_DAYS)).isoformat())
    set_session_cookie(response, request, token)
    clear_login_attempts(request)
    return public_user(user)


@app.post("/auth/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        db.delete_session(token_hash(token))
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True}


@app.post("/auth/logout-all")
def logout_all(request: Request, response: Response, user=Depends(current_user)):
    db.delete_all_sessions(int(user["id"]))
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True}


@app.get("/auth/me")
def me(user=Depends(current_user)):
    return public_user(user)


@app.patch("/auth/profile")
def update_profile(payload: ProfileUpdate, user=Depends(current_user)):
    uid = int(user["id"])
    username = normalize_username(payload.username)
    other = db.get_user_by_username(username)
    if other and int(other["id"]) != uid:
        raise HTTPException(status_code=409, detail="Dieser Benutzername ist bereits vergeben.")
    display_name = (payload.display_name or username).strip()[:80]
    bio = str(payload.bio or "").strip()[:280]
    db.update_profile(uid, username, display_name, bio)
    return public_user(db.get_user(uid))


@app.post("/auth/avatar")
async def upload_avatar(file: UploadFile = File(...), user=Depends(current_user)):
    if file.content_type not in ALLOWED_AVATAR_TYPES:
        raise HTTPException(status_code=415, detail="Erlaubt sind JPG, PNG und WebP.")
    raw = await file.read(MAX_AVATAR_BYTES + 1)
    if len(raw) > MAX_AVATAR_BYTES:
        raise HTTPException(status_code=413, detail="Das Profilbild darf maximal 5 MB groß sein.")
    try:
        image = Image.open(io.BytesIO(raw))
        image.thumbnail((512, 512))
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")
        output = io.BytesIO()
        image.save(output, format="WEBP", quality=86, method=6)
        data = output.getvalue()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=400, detail="Ungültige Bilddatei.")
    db.set_avatar(int(user["id"]), "image/webp", data)
    return {"ok": True, "avatar_url": f"/users/{int(user['id'])}/avatar?t={int(time.time())}"}


@app.delete("/auth/avatar")
def delete_avatar(user=Depends(current_user)):
    db.set_avatar(int(user["id"]), None, None)
    return {"ok": True}


@app.get("/users/{user_id}/avatar")
def avatar(user_id: int):
    row = db.get_avatar(user_id)
    if not row or not row.get("avatar_data"):
        raise HTTPException(status_code=404, detail="Kein Profilbild vorhanden.")
    return StreamingResponse(io.BytesIO(row["avatar_data"]), media_type=row.get("avatar_mime") or "image/webp")


@app.post("/auth/password")
def change_password(payload: PasswordChange, request: Request, response: Response, user=Depends(current_user)):
    full = db.get_user(int(user["id"]))
    if not full or not verify_password(payload.current_password, full["password_hash"]):
        raise HTTPException(status_code=400, detail="Aktuelles Passwort ist falsch.")
    new_password = validate_password(payload.new_password)
    db.update_user_password(int(user["id"]), hash_password(new_password))
    token = secrets.token_urlsafe(32)
    db.create_session(int(user["id"]), token_hash(token), (now_utc() + timedelta(days=SESSION_DAYS)).isoformat())
    set_session_cookie(response, request, token)
    return {"ok": True}


@app.delete("/auth/account")
def delete_account(response: Response, user=Depends(current_user)):
    db.delete_user(int(user["id"]))
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True}


@app.delete("/admin/reset-users")
def reset_users(x_admin_key: str = Header(default="")):
    expected = os.getenv("ADMIN_RESET_KEY", "")
    if not expected or not hmac.compare_digest(x_admin_key, expected):
        raise HTTPException(status_code=403, detail="Nicht erlaubt.")
    count = db.reset_all_users()
    return {"ok": True, "deleted_users": count}


# -------------------- User state --------------------

@app.get("/user-state")
def user_state(user=Depends(current_user)):
    uid = int(user["id"])
    return {
        "favorites": db.favorite_ids(uid),
        "ratings": db.ratings(uid),
        "pantry": db.get_user_items("user_pantry", uid),
        "at_home": db.get_user_items("user_at_home", uid),
        "eaten": db.eaten_history(uid, 30),
        "preferences": db.get_preferences(uid),
    }


@app.get("/favorites")
def get_favorites(user=Depends(current_user)):
    return {"ids": db.favorite_ids(int(user["id"]))}


@app.post("/favorites/{recipe_id}/toggle")
def toggle_favorite(recipe_id: int, user=Depends(current_user)):
    uid = int(user["id"])
    user_recipe(recipe_id, uid)
    favorite = db.toggle_user_favorite(uid, recipe_id)
    return {"favorite": favorite, "ids": db.favorite_ids(uid)}


@app.get("/ratings")
def get_ratings(user=Depends(current_user)):
    return db.ratings(int(user["id"]))


@app.put("/ratings/{recipe_id}")
def put_rating(recipe_id: int, payload: RatingPayload, user=Depends(current_user)):
    uid = int(user["id"])
    user_recipe(recipe_id, uid)
    db.set_rating(uid, recipe_id, payload.rating)
    return {"ok": True, "rating": payload.rating}


@app.get("/pantry")
def get_pantry(user=Depends(current_user)):
    return {"items": db.get_user_items("user_pantry", int(user["id"]))}


@app.put("/pantry")
def put_pantry(payload: ItemsPayload, user=Depends(current_user)):
    uid = int(user["id"])
    db.replace_user_items("user_pantry", uid, payload.items)
    return {"items": db.get_user_items("user_pantry", uid)}


@app.get("/at-home")
def get_at_home(user=Depends(current_user)):
    return {"items": db.get_user_items("user_at_home", int(user["id"]))}


@app.put("/at-home")
def put_at_home(payload: ItemsPayload, user=Depends(current_user)):
    uid = int(user["id"])
    db.replace_user_items("user_at_home", uid, payload.items)
    return {"items": db.get_user_items("user_at_home", uid)}


@app.get("/eaten")
def get_eaten(user=Depends(current_user)):
    return {"items": db.eaten_history(int(user["id"]), 30)}


@app.post("/eaten/{recipe_id}")
def mark_eaten(recipe_id: int, user=Depends(current_user)):
    uid = int(user["id"])
    user_recipe(recipe_id, uid)
    db.add_eaten(uid, recipe_id)
    return {"ok": True}


@app.delete("/eaten")
def clear_eaten(user=Depends(current_user)):
    db.clear_eaten(int(user["id"]))
    return {"ok": True}


@app.put("/preferences")
def save_preferences(payload: PreferencesPayload, user=Depends(current_user)):
    allowed = {
        key: value for key, value in payload.preferences.items()
        if key in {"avoid_recent", "theme", "default_max_time", "diet"}
    }
    db.set_preferences(int(user["id"]), allowed)
    return {"preferences": allowed}


# -------------------- Rezepte --------------------

@app.get("/rezepte")
def get_rezepte(request: Request):
    user = current_user_optional(request)
    uid = int(user["id"]) if user else None
    return db.all_recipes(uid)


@app.post("/rezept-erstellen")
def create_recipe(payload: RecipeCreate, user=Depends(current_user)):
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Name fehlt.")
    uid = int(user["id"])
    rid = db.create_user_recipe(uid, payload.model_dump())
    return user_recipe(rid, uid)


@app.post("/rezept-aus-link")
def recipe_from_link(payload: RecipeLinkPayload, user=Depends(current_user)):
    url = payload.url.strip()
    if not re.fullmatch(r"https?://[^\s]+", url):
        raise HTTPException(status_code=400, detail="Bitte eine gültige http(s)-URL eingeben.")
    uid = int(user["id"])
    data = {
        "name": (payload.name or "Gespeichertes Rezept").strip(),
        "kueche": "Eigener Link",
        "bild": "",
        "portionen": 2,
        "kochzeit": 30,
        "schwierigkeit": "Einfach",
        "tags": ["Eigener Link"],
        "zutaten": ["Zutaten bitte ergänzen"],
        "anleitung": "Öffne die Quelle und ergänze anschließend Zutaten und Zubereitung.",
        "description": "Ein von dir gespeicherter Rezept-Link.",
        "source_url": url,
    }
    rid = db.create_user_recipe(uid, data)
    return user_recipe(rid, uid)


@app.delete("/rezepte/{recipe_id}")
def delete_recipe(recipe_id: int, user=Depends(current_user)):
    if not db.delete_user_recipe(recipe_id, int(user["id"])):
        raise HTTPException(status_code=403, detail="Nur eigene Rezepte können gelöscht werden.")
    return {"ok": True}


@app.get("/roulette")
def roulette(request: Request):
    user = current_user_optional(request)
    uid = int(user["id"]) if user else None
    items = db.all_recipes(uid)
    if not items:
        raise HTTPException(status_code=404, detail="Keine Rezepte vorhanden.")
    return random.choice(items)


# -------------------- Wochenplan --------------------

@app.get("/wochenplan")
def get_weekly_plan(request: Request):
    user = current_user_optional(request)
    return db.user_weekly_plan(int(user["id"])) if user else db.weekly_plan()


@app.post("/wochenplan/reset")
def reset_weekly_plan(request: Request):
    user = current_user_optional(request)
    if user:
        db.reset_user_weekly_plan(int(user["id"]))
    else:
        db.reset_weekly_plan()
    return {"ok": True}


@app.post("/wochenplan/bulk")
def set_weekly_plan_bulk(payload: WeeklyPlanBulk, request: Request):
    user = current_user_optional(request)
    uid = int(user["id"]) if user else None
    entries: list[tuple[str, int, int | None]] = []
    for item in payload.entries:
        validate_plan_target(item.day, item.slot)
        rid = item.recipe_id or None
        if rid is not None:
            user_recipe(rid, uid)
        entries.append((item.day, item.slot, rid))
    if uid is not None:
        db.set_user_weekly_plan_bulk(uid, entries)
    else:
        db.set_weekly_plan_bulk(entries)
    return {"ok": True, "saved": len(entries)}


@app.post("/wochenplan/{day}/{slot}/{recipe_id}")
def set_weekly_plan(day: str, slot: int, recipe_id: int, request: Request):
    validate_plan_target(day, slot)
    user = current_user_optional(request)
    uid = int(user["id"]) if user else None
    rid = None if recipe_id == 0 else recipe_id
    if rid:
        user_recipe(rid, uid)
    if uid is not None:
        db.set_user_weekly_plan_slot(uid, day, slot, rid)
    else:
        db.set_weekly_plan_slot(day, slot, rid)
    return {"ok": True}


# -------------------- Einkaufsliste --------------------

def clean_ingredient_name(text: str) -> str:
    value = str(text or "").lower()
    value = re.sub(r"\([^)]*\)", "", value)
    value = re.sub(r"\d+(?:[.,]\d+)?(?:\s*[-–]\s*\d+(?:[.,]\d+)?)?", "", value)
    value = re.sub(
        r"\b(g|kg|ml|l|el|tl|stück|stk|dose|dosen|scheiben|tüte|packung|päckchen|prise|bund|glas|becher)\b",
        "", value
    )
    value = re.sub(r"[^\wäöüß -]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def ingredient_category(item: str) -> str:
    text = clean_ingredient_name(item)
    groups = {
        "🥦 Obst & Gemüse": ["apfel", "banane", "beere", "erdbeere", "himbeere", "blaubeere", "tomate", "paprika", "zucchini", "gurke", "karotte", "möhre", "zwiebel", "lauch", "knoblauch", "kartoffel", "brokkoli", "kohl", "salat", "erbsen"],
        "🥛 Milchprodukte & Eier": ["milch", "sahne", "joghurt", "skyr", "quark", "frischkäse", "hüttenkäse", "käse", "mozzarella", "parmesan", "schmand", "butter", "ei"],
        "🥩 Fleisch & Fisch": ["hähnchen", "hackfleisch", "gyros", "rind", "kassler", "speck", "pute", "würstchen", "fisch", "thunfisch", "schnitzel"],
        "🍝 Trockenwaren & Beilagen": ["reis", "nudel", "spaghetti", "pasta", "tortellini", "gnocchi", "mehl", "hafer", "wrap", "bagel", "toast", "brot", "paniermehl"],
        "🧂 Gewürze & Backen": ["salz", "pfeffer", "paprika", "oregano", "zimt", "muskat", "kräuter", "kümmel", "chili", "backpulver", "vanille", "zucker", "erythrit", "honig", "öl"],
        "🥫 Konserven & Soßen": ["bohnen", "mais", "brühe", "pesto", "sojasauce", "ketchup", "mayonnaise", "salsa", "tzatziki"],
    }
    for category, words in groups.items():
        if any(word in text for word in words):
            return category
    return "📦 Sonstiges"


def shopping_list(recipes_: list[dict[str, Any]]) -> dict[str, list[str]]:
    # Bewusst konservativ: Mengen mit unterschiedlichen Einheiten werden nicht falsch zusammengerechnet.
    collected: dict[str, list[str]] = {}
    seen: set[str] = set()
    for recipe in recipes_:
        for item in recipe.get("zutaten", []) or []:
            raw = str(item).strip()
            if not raw:
                continue
            key = re.sub(r"\s+", " ", raw.casefold())
            if key in seen:
                continue
            seen.add(key)
            category = ingredient_category(raw)
            collected.setdefault(category, []).append(raw)
    for category in collected:
        collected[category].sort(key=str.casefold)
    return collected


@app.get("/einkaufsliste")
def get_shopping_list(request: Request):
    user = current_user_optional(request)
    uid = int(user["id"]) if user else None
    plan = db.user_weekly_plan(uid) if uid is not None else db.weekly_plan()
    recipe_items: list[dict[str, Any]] = []
    for slots in plan.values():
        for rid in slots.values():
            if rid:
                recipe = db.get_recipe(int(rid), uid)
                if recipe:
                    recipe_items.append(recipe)
    return {"categories": shopping_list(recipe_items)}