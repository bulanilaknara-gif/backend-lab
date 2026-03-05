import os, json
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename

from config import UPLOAD_DIR, MAX_UPLOAD_MB
from nexus.auth.firebase_auth import token_required
from nexus.db.auth_db import get_auth_conn, put_auth_conn
from nexus.db.hospital_db import get_hospital_conn, put_hospital_conn

lab_bp = Blueprint("lab_bp", __name__, url_prefix="/api/lab")

def ensure_upload_dir():
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

def lab_is_active(uid: str):
    conn = get_auth_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT role, is_active FROM users WHERE firebase_uid=%s", (uid,))
        row = cur.fetchone()
        if not row:
            return False, "Lab staff not registered. Please register first."
        if row[0] != "LAB":
            return False, "Not a LAB account."
        if not row[1]:
            return False, "Waiting for admin approval."
        return True, ""
    finally:
        cur.close()
        put_auth_conn(conn)

# ---------- Register Lab Staff (backend record) ----------
@lab_bp.post("/register")
@token_required
def register_lab_staff():
    uid = request.user["uid"]
    email = request.user["email"]

    conn = get_auth_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO users (firebase_uid, email, role, is_active)
            VALUES (%s, %s, 'LAB', FALSE)
            ON CONFLICT (firebase_uid) DO NOTHING
        """, (uid, email))
        conn.commit()
    finally:
        cur.close()
        put_auth_conn(conn)

    return jsonify({"message": "Registered ✅ waiting for admin approval."})

# ---------- Manage Lab Profile ----------
@lab_bp.get("/profile")
@token_required
def get_profile():
    ok, msg = lab_is_active(request.user["uid"])
    if not ok: return jsonify({"error": msg}), 403

    uid = request.user["uid"]
    conn = get_hospital_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT lab_name, phone, address, reg_no FROM lab_profiles WHERE lab_uid=%s", (uid,))
        r = cur.fetchone()
        if not r:
            return jsonify({"lab_name":"", "phone":"", "address":"", "reg_no":""})
        return jsonify({"lab_name":r[0], "phone":r[1], "address":r[2], "reg_no":r[3]})
    finally:
        cur.close()
        put_hospital_conn(conn)

@lab_bp.put("/profile")
@token_required
def update_profile():
    ok, msg = lab_is_active(request.user["uid"])
    if not ok: return jsonify({"error": msg}), 403

    uid = request.user["uid"]
    d = request.get_json() or {}

    conn = get_hospital_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
        INSERT INTO lab_profiles (lab_uid, lab_name, phone, address, reg_no)
        VALUES (%s,%s,%s,%s,%s)
        ON CONFLICT (lab_uid) DO UPDATE SET
          lab_name=EXCLUDED.lab_name,
          phone=EXCLUDED.phone,
          address=EXCLUDED.address,
          reg_no=EXCLUDED.reg_no
        """, (uid, d.get("lab_name",""), d.get("phone",""), d.get("address",""), d.get("reg_no","")))
        conn.commit()
    finally:
        cur.close()
        put_hospital_conn(conn)

    return jsonify({"message": "Profile updated ✅"})

# ---------- Offered Tests ----------
@lab_bp.get("/tests")
@token_required
def list_tests():
    ok, msg = lab_is_active(request.user["uid"])
    if not ok: return jsonify({"error": msg}), 403

    uid = request.user["uid"]
    conn = get_hospital_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, test_name, duration, sample_type, category, is_active
            FROM lab_tests WHERE lab_uid=%s ORDER BY id DESC
        """, (uid,))
        rows = cur.fetchall()
        return jsonify([{
            "id":x[0], "test_name":x[1], "duration":x[2],
            "sample_type":x[3], "category":x[4], "is_active":x[5]
        } for x in rows])
    finally:
        cur.close()
        put_hospital_conn(conn)

@lab_bp.post("/tests")
@token_required
def add_test():
    ok, msg = lab_is_active(request.user["uid"])
    if not ok: return jsonify({"error": msg}), 403

    uid = request.user["uid"]
    d = request.get_json() or {}
    name = (d.get("test_name") or "").strip()
    if not name:
        return jsonify({"error": "test_name required"}), 400

    conn = get_hospital_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO lab_tests (lab_uid, test_name, duration, sample_type, category, is_active)
            VALUES (%s,%s,%s,%s,%s,TRUE)
        """, (uid, name, d.get("duration",""), d.get("sample_type",""), d.get("category","")))
        conn.commit()
    finally:
        cur.close()
        put_hospital_conn(conn)

    return jsonify({"message": "Test added ✅"})

@lab_bp.delete("/tests/<int:test_id>")
@token_required
def delete_test(test_id):
    ok, msg = lab_is_active(request.user["uid"])
    if not ok: return jsonify({"error": msg}), 403

    uid = request.user["uid"]
    conn = get_hospital_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM lab_tests WHERE id=%s AND lab_uid=%s", (test_id, uid))
        conn.commit()
    finally:
        cur.close()
        put_hospital_conn(conn)
    return jsonify({"message": "Deleted ✅"})

# ---------- Availability ----------
@lab_bp.get("/availability")
@token_required
def get_availability():
    ok, msg = lab_is_active(request.user["uid"])
    if not ok: return jsonify({"error": msg}), 403

    uid = request.user["uid"]
    conn = get_hospital_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT schedule_json FROM lab_availability WHERE lab_uid=%s", (uid,))
        row = cur.fetchone()
        schedule = json.loads(row[0]) if row and row[0] else {}
        return jsonify({"schedule": schedule})
    finally:
        cur.close()
        put_hospital_conn(conn)

@lab_bp.put("/availability")
@token_required
def update_availability():
    ok, msg = lab_is_active(request.user["uid"])
    if not ok: return jsonify({"error": msg}), 403

    uid = request.user["uid"]
    d = request.get_json() or {}
    schedule_json = json.dumps(d.get("schedule", {}))

    conn = get_hospital_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO lab_availability (lab_uid, schedule_json)
            VALUES (%s,%s)
            ON CONFLICT (lab_uid) DO UPDATE SET
              schedule_json=EXCLUDED.schedule_json,
              updated_at=CURRENT_TIMESTAMP
        """, (uid, schedule_json))
        conn.commit()
    finally:
        cur.close()
        put_hospital_conn(conn)

    return jsonify({"message": "Availability updated ✅"})

# ---------- Requests (Accept/Reject + Status) ----------
@lab_bp.get("/requests")
@token_required
def list_requests():
    ok, msg = lab_is_active(request.user["uid"])
    if not ok: return jsonify({"error": msg}), 403

    uid = request.user["uid"]
    status = request.args.get("status", "all")

    conn = get_hospital_conn()
    cur = conn.cursor()
    try:
        if status == "all":
            cur.execute("""
                SELECT id, patient_name, patient_email, test_name, priority, status, created_at
                FROM lab_test_requests WHERE lab_uid=%s ORDER BY created_at DESC
            """, (uid,))
        else:
            cur.execute("""
                SELECT id, patient_name, patient_email, test_name, priority, status, created_at
                FROM lab_test_requests WHERE lab_uid=%s AND status=%s ORDER BY created_at DESC
            """, (uid, status))
        rows = cur.fetchall()
        return jsonify([{
            "id":r[0], "patient_name":r[1], "patient_email":r[2],
            "test_name":r[3], "priority":r[4], "status":r[5],
            "created_at": r[6].isoformat()
        } for r in rows])
    finally:
        cur.close()
        put_hospital_conn(conn)

@lab_bp.put("/requests/<int:req_id>/status")
@token_required
def update_request_status(req_id):
    ok, msg = lab_is_active(request.user["uid"])
    if not ok: return jsonify({"error": msg}), 403

    uid = request.user["uid"]
    d = request.get_json() or {}
    status = d.get("status")
    allowed = ["pending", "accepted", "rejected", "in_progress", "completed", "sent"]
    if status not in allowed:
        return jsonify({"error": "Invalid status"}), 400

    conn = get_hospital_conn()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE lab_test_requests SET status=%s WHERE id=%s AND lab_uid=%s", (status, req_id, uid))
        conn.commit()
    finally:
        cur.close()
        put_hospital_conn(conn)

    return jsonify({"message": "Updated ✅"})

# ---------- Upload Lab Report PDF ----------
@lab_bp.post("/requests/<int:req_id>/upload-report")
@token_required
def upload_report(req_id):
    ok, msg = lab_is_active(request.user["uid"])
    if not ok: return jsonify({"error": msg}), 403

    uid = request.user["uid"]
    ensure_upload_dir()

    if "file" not in request.files:
        return jsonify({"error": "file required"}), 400

    f = request.files["file"]
    if not (f.filename or "").lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF allowed"}), 400

    f.seek(0, os.SEEK_END)
    size = f.tell()
    f.seek(0)
    if size > MAX_UPLOAD_MB * 1024 * 1024:
        return jsonify({"error": f"Max {MAX_UPLOAD_MB}MB"}), 400

    safe_name = secure_filename(f.filename)
    path = os.path.join(UPLOAD_DIR, f"{req_id}_{safe_name}")
    f.save(path)

    conn = get_hospital_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT patient_email FROM lab_test_requests WHERE id=%s AND lab_uid=%s", (req_id, uid))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Request not found"}), 404

        patient_email = row[0]
        cur.execute("""
            INSERT INTO lab_reports (request_id, lab_uid, patient_email, file_name, file_path)
            VALUES (%s,%s,%s,%s,%s)
        """, (req_id, uid, patient_email, os.path.basename(path), path))

        cur.execute("UPDATE lab_test_requests SET status='completed' WHERE id=%s AND lab_uid=%s", (req_id, uid))
        conn.commit()
    finally:
        cur.close()
        put_hospital_conn(conn)

    return jsonify({"message": "Uploaded ✅"})

# ---------- Report History + Download ----------
@lab_bp.get("/reports")
@token_required
def report_history():
    ok, msg = lab_is_active(request.user["uid"])
    if not ok: return jsonify({"error": msg}), 403

    uid = request.user["uid"]
    conn = get_hospital_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, request_id, file_name, uploaded_at
            FROM lab_reports WHERE lab_uid=%s ORDER BY uploaded_at DESC
        """, (uid,))
        rows = cur.fetchall()
        return jsonify([{
            "id":x[0], "request_id":x[1], "file_name":x[2], "uploaded_at":x[3].isoformat()
        } for x in rows])
    finally:
        cur.close()
        put_hospital_conn(conn)

@lab_bp.get("/reports/<int:report_id>/download")
@token_required
def download_report(report_id):
    ok, msg = lab_is_active(request.user["uid"])
    if not ok: return jsonify({"error": msg}), 403

    uid = request.user["uid"]
    conn = get_hospital_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT file_path, file_name FROM lab_reports WHERE id=%s AND lab_uid=%s", (report_id, uid))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        return send_file(row[0], as_attachment=True, download_name=row[1])
    finally:
        cur.close()
        put_hospital_conn(conn)

# ---------- Performance Stats ----------
@lab_bp.get("/stats")
@token_required
def stats():
    ok, msg = lab_is_active(request.user["uid"])
    if not ok: return jsonify({"error": msg}), 403

    uid = request.user["uid"]
    conn = get_hospital_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
        SELECT
          COUNT(*),
          SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END),
          SUM(CASE WHEN status='in_progress' THEN 1 ELSE 0 END),
          SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END),
          SUM(CASE WHEN status='sent' THEN 1 ELSE 0 END)
        FROM lab_test_requests WHERE lab_uid=%s
        """, (uid,))
        r = cur.fetchone()
        return jsonify({
            "total": int(r[0] or 0),
            "pending": int(r[1] or 0),
            "in_progress": int(r[2] or 0),
            "completed": int(r[3] or 0),
            "sent": int(r[4] or 0),
        })
    finally:
        cur.close()
        put_hospital_conn(conn)

# ---------- Recommended Tests ----------
@lab_bp.get("/recommended-tests")
@token_required
def recommended_tests():
    ok, msg = lab_is_active(request.user["uid"])
    if not ok: return jsonify({"error": msg}), 403

    uid = request.user["uid"]
    conn = get_hospital_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT test_name, COUNT(*) as c
            FROM lab_test_requests
            WHERE lab_uid=%s
            GROUP BY test_name
            ORDER BY c DESC
            LIMIT 10
        """, (uid,))
        rows = cur.fetchall()
        return jsonify([{"test_name":x[0], "count":int(x[1])} for x in rows])
    finally:
        cur.close()
        put_hospital_conn(conn)