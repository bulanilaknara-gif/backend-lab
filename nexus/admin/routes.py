from flask import Blueprint, request, jsonify
from config import ADMIN_SECRET
from nexus.db.auth_db import get_auth_conn, put_auth_conn

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/api/admin")

@admin_bp.post("/approve")
def approve_lab():
    secret = request.headers.get("X-ADMIN-SECRET", "")
    if not ADMIN_SECRET or secret != ADMIN_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "email required"}), 400

    conn = get_auth_conn()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET is_active=TRUE WHERE email=%s", (email,))
        conn.commit()
    finally:
        cur.close()
        put_auth_conn(conn)

    return jsonify({"message": "Approved ✅"})