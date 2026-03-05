from flask import Blueprint, jsonify, send_file, request
from nexus.auth.firebase_auth import token_required
from nexus.db.hospital_db import get_hospital_conn, put_hospital_conn

patient_bp = Blueprint("patient_bp", __name__, url_prefix="/api/patient")

@patient_bp.get("/recommended-lab-tests")
@token_required
def patient_recommended_tests():
    conn = get_hospital_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT test_name, COUNT(*) as c
            FROM lab_test_requests
            GROUP BY test_name
            ORDER BY c DESC
            LIMIT 10
        """)
        rows = cur.fetchall()
        return jsonify([{"test_name":x[0], "count":int(x[1])} for x in rows])
    finally:
        cur.close()
        put_hospital_conn(conn)

@patient_bp.get("/lab-reports")
@token_required
def patient_reports():
    email = (request.user.get("email") or "").lower()
    conn = get_hospital_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, request_id, file_name, uploaded_at
            FROM lab_reports
            WHERE patient_email=%s
            ORDER BY uploaded_at DESC
        """, (email,))
        rows = cur.fetchall()
        return jsonify([{
            "id":x[0], "request_id":x[1], "file_name":x[2], "uploaded_at":x[3].isoformat()
        } for x in rows])
    finally:
        cur.close()
        put_hospital_conn(conn)

@patient_bp.get("/lab-reports/<int:report_id>/download")
@token_required
def patient_download(report_id):
    email = (request.user.get("email") or "").lower()
    conn = get_hospital_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT file_path, file_name
            FROM lab_reports
            WHERE id=%s AND patient_email=%s
        """, (report_id, email))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        return send_file(row[0], as_attachment=True, download_name=row[1])
    finally:
        cur.close()
        put_hospital_conn(conn)