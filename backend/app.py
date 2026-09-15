import os
import sqlite3
import time
from functools import wraps
from flask import Flask, jsonify, request, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv

from database import get_db, init_db
from models import (
    get_books, get_book, create_book, update_book, delete_book,
    increment_downloads
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads", "pdfs")
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(__name__, static_folder=None)

# API 404
@app.errorhandler(404)
def api_404(e):
    from flask import request, jsonify
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "message": "Route API introuvable", "path": request.path}), 404
    return e

# Toute exception non gérée (erreur 500) doit renvoyer du JSON sur /api/,
# sinon le frontend reçoit une page HTML et échoue sur res.json()
# ("Unexpected token '<' ... is not valid JSON").
@app.errorhandler(Exception)
def api_error(e):
    if request.path.startswith("/api/"):
        if isinstance(e, HTTPException):
            return jsonify({"success": False, "message": e.description or "Erreur"}), e.code
        app.logger.exception("Erreur interne sur %s", request.path)
        return jsonify({"success": False, "message": "Erreur interne du serveur."}), 500
    if isinstance(e, HTTPException):
        return e
    raise e

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_FILE_SIZE_MB", "25")) * 1024 * 1024

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")

# --- Limitation des tentatives de connexion admin ---
MAX_LOGIN_ATTEMPTS = 3
LOGIN_LOCKOUT_SECONDS = 30
# Stockage en mémoire (par IP) : {ip: {"attempts": int, "locked_until": float}}
_login_attempts = {}

def _client_key():
    return request.remote_addr or "unknown"

def _check_lockout():
    """Renvoie le nombre de secondes restantes si l'IP est bloquée, sinon 0."""
    entry = _login_attempts.get(_client_key())
    if not entry:
        return 0
    remaining = entry["locked_until"] - time.time()
    return max(0, round(remaining)) if remaining > 0 else 0

def _register_failed_attempt():
    key = _client_key()
    entry = _login_attempts.setdefault(key, {"attempts": 0, "locked_until": 0})
    entry["attempts"] += 1
    if entry["attempts"] >= MAX_LOGIN_ATTEMPTS:
        entry["locked_until"] = time.time() + LOGIN_LOCKOUT_SECONDS
        entry["attempts"] = 0

def _reset_attempts():
    _login_attempts.pop(_client_key(), None)

ALLOWED_CATEGORIES = {
    "Programmation", "Cybersécurité", "Business", "Éducation",
    "Technologie", "Développement web", "Autres"
}
ALLOWED_EXTENSIONS = {"pdf"}

os.makedirs(UPLOAD_DIR, exist_ok=True)
init_db()

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return jsonify({"error": "Authentification administrateur requise."}), 401
        return fn(*args, **kwargs)
    return wrapper

@app.after_request
def add_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "same-origin"
    return response

@app.route("/")
def root():
    return send_from_directory(os.path.join(BASE_DIR, "..", "frontend"), "index.html")

@app.route("/<path:path>")
def frontend(path):
    frontend_dir = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))
    if os.path.isfile(os.path.join(frontend_dir, path)):
        return send_from_directory(frontend_dir, path)
    return send_from_directory(frontend_dir, "index.html")

@app.get("/api/books")
def api_books():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    sort = request.args.get("sort", "recent")
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(50, max(1, int(request.args.get("per_page", 12))))
    except ValueError:
        return jsonify({"error": "Paramètres de pagination invalides."}), 400

    result = get_books(query=query, category=category, sort=sort,
                       page=page, per_page=per_page)
    return jsonify(result)

@app.get("/api/books/category/<path:category>")
def api_books_category(category):
    result = get_books(category=category, sort="recent", page=1, per_page=50)
    return jsonify(result)

@app.get("/api/books/<int:book_id>")
def api_book(book_id):
    book = get_book(book_id)
    if not book:
        return jsonify({"error": "PDF introuvable."}), 404
    return jsonify(book)

@app.get("/api/books/<int:book_id>/download")
def api_download(book_id):
    book = get_book(book_id)
    if not book:
        return jsonify({"error": "PDF introuvable."}), 404
    filename = book["filename"]
    path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.isfile(path):
        return jsonify({"error": "Fichier PDF indisponible."}), 404
    increment_downloads(book_id)
    return send_from_directory(
        UPLOAD_DIR, filename, as_attachment=True,
        download_name=filename, mimetype="application/pdf"
    )

@app.get("/api/books/<int:book_id>/preview")
def api_preview(book_id):
    book = get_book(book_id)
    if not book:
        return jsonify({"error": "PDF introuvable."}), 404
    path = os.path.join(UPLOAD_DIR, book["filename"])
    if not os.path.isfile(path):
        return jsonify({"error": "Fichier PDF indisponible."}), 404
    return send_from_directory(UPLOAD_DIR, book["filename"], as_attachment=False,
                               mimetype="application/pdf")

@app.post("/api/admin/login")
def admin_login():
    remaining_lock = _check_lockout()
    if remaining_lock > 0:
        return jsonify({
            "error": f"Trop de tentatives. Réessayez dans {remaining_lock} seconde(s).",
            "locked": True,
            "retry_after": remaining_lock
        }), 429

    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    if not ADMIN_PASSWORD_HASH:
        return jsonify({"error": "ADMIN_PASSWORD_HASH n'est pas configuré."}), 500

    try:
        password_ok = check_password_hash(ADMIN_PASSWORD_HASH, password)
    except Exception:
        # Hash mal formé/mal copié dans .env : ne pas planter, traiter comme échec.
        app.logger.exception("ADMIN_PASSWORD_HASH invalide")
        password_ok = False

    if username == ADMIN_USERNAME and password_ok:
        _reset_attempts()
        session.clear()
        session["admin"] = True
        return jsonify({"ok": True})

    _register_failed_attempt()
    remaining_attempts = MAX_LOGIN_ATTEMPTS - _login_attempts.get(_client_key(), {}).get("attempts", 0)
    payload = {"error": "Identifiants incorrects."}
    if 0 < remaining_attempts < MAX_LOGIN_ATTEMPTS:
        payload["remaining_attempts"] = remaining_attempts
    return jsonify(payload), 401

@app.post("/api/admin/logout")
def admin_logout():
    session.clear()
    return jsonify({"ok": True})

@app.get("/api/admin/me")
def admin_me():
    return jsonify({"authenticated": bool(session.get("admin"))})

@app.post("/api/books")
@admin_required
def api_create_book():
    if "file" not in request.files:
        return jsonify({"error": "Fichier PDF requis."}), 400
    uploaded = request.files["file"]
    if not uploaded.filename or not allowed_file(uploaded.filename):
        return jsonify({"error": "Seuls les fichiers PDF sont acceptés."}), 400

    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()
    description = request.form.get("description", "").strip()
    category = request.form.get("category", "").strip()

    if not title or not author or not description:
        return jsonify({"error": "Titre, auteur et description sont requis."}), 400
    if category not in ALLOWED_CATEGORIES:
        return jsonify({"error": "Catégorie invalide."}), 400

    original = secure_filename(uploaded.filename)
    if not original:
        return jsonify({"error": "Nom de fichier invalide."}), 400

    stem, ext = os.path.splitext(original)
    filename = original
    counter = 1
    while os.path.exists(os.path.join(UPLOAD_DIR, filename)):
        filename = f"{stem}_{counter}{ext}"
        counter += 1

    path = os.path.join(UPLOAD_DIR, filename)
    uploaded.save(path)
    filesize = os.path.getsize(path)

    try:
        book = create_book(title, author, description, category, filename, filesize)
    except Exception:
        if os.path.exists(path):
            os.remove(path)
        raise
    return jsonify(book), 201

@app.put("/api/books/<int:book_id>")
@admin_required
def api_update_book(book_id):
    book = get_book(book_id)
    if not book:
        return jsonify({"error": "PDF introuvable."}), 404

    data = request.form if request.form else (request.get_json(silent=True) or {})
    title = str(data.get("title", book["title"])).strip()
    author = str(data.get("author", book["author"])).strip()
    description = str(data.get("description", book["description"])).strip()
    category = str(data.get("category", book["category"])).strip()

    if not title or not author or not description:
        return jsonify({"error": "Titre, auteur et description sont requis."}), 400
    if category not in ALLOWED_CATEGORIES:
        return jsonify({"error": "Catégorie invalide."}), 400

    new_filename = book["filename"]
    new_filesize = book["filesize"]
    uploaded = request.files.get("file")
    old_path = os.path.join(UPLOAD_DIR, book["filename"])

    if uploaded and uploaded.filename:
        if not allowed_file(uploaded.filename):
            return jsonify({"error": "Seuls les fichiers PDF sont acceptés."}), 400
        original = secure_filename(uploaded.filename)
        stem, ext = os.path.splitext(original)
        new_filename = original
        counter = 1
        while os.path.exists(os.path.join(UPLOAD_DIR, new_filename)) and new_filename != book["filename"]:
            new_filename = f"{stem}_{counter}{ext}"
            counter += 1
        new_path = os.path.join(UPLOAD_DIR, new_filename)
        uploaded.save(new_path)
        new_filesize = os.path.getsize(new_path)

    updated = update_book(book_id, title, author, description, category,
                           new_filename, new_filesize)

    if uploaded and uploaded.filename and old_path != os.path.join(UPLOAD_DIR, new_filename):
        if os.path.isfile(old_path):
            os.remove(old_path)

    return jsonify(updated)

@app.delete("/api/books/<int:book_id>")
@admin_required
def api_delete_book(book_id):
    book = get_book(book_id)
    if not book:
        return jsonify({"error": "PDF introuvable."}), 404
    deleted = delete_book(book_id)
    if deleted:
        path = os.path.join(UPLOAD_DIR, book["filename"])
        if os.path.isfile(path):
            os.remove(path)
    return jsonify({"ok": True})

@app.errorhandler(413)
def too_large(_):
    return jsonify({"error": "Fichier trop volumineux."}), 413

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
