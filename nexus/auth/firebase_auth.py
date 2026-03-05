import firebase_admin
from firebase_admin import credentials, auth as fb_auth
from functools import wraps
from flask import request, jsonify
from config import FIREBASE_KEY_PATH

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    firebase_admin.initialize_app(cred)

def token_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify({"error": "Missing Bearer token"}), 401
        token = header.split(" ", 1)[1]

        try:
            decoded = fb_auth.verify_id_token(token)
            request.user = {
                "uid": decoded["uid"],
                "email": (decoded.get("email") or "").lower()
            }
        except Exception:
            return jsonify({"error": "Invalid token"}), 401

        return fn(*args, **kwargs)
    return wrapper