from nexus.db.auth_db import get_auth_conn, put_auth_conn
from nexus.db.hospital_db import get_hospital_conn, put_hospital_conn

def init_auth_tables():
    conn = get_auth_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
          id SERIAL PRIMARY KEY,
          firebase_uid VARCHAR(128) UNIQUE NOT NULL,
          email VARCHAR(255) UNIQUE NOT NULL,
          role VARCHAR(30) NOT NULL DEFAULT 'LAB',
          is_active BOOLEAN DEFAULT FALSE,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()
    finally:
        cur.close()
        put_auth_conn(conn)

def init_hospital_tables():
    conn = get_hospital_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS lab_profiles (
            id SERIAL PRIMARY KEY,
            lab_uid VARCHAR(128) UNIQUE NOT NULL,
            lab_name VARCHAR(255) DEFAULT '',
            phone VARCHAR(50) DEFAULT '',
            address VARCHAR(255) DEFAULT '',
            reg_no VARCHAR(100) DEFAULT ''
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS lab_availability (
            id SERIAL PRIMARY KEY,
            lab_uid VARCHAR(128) UNIQUE NOT NULL,
            schedule_json TEXT DEFAULT '{}',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS lab_tests (
            id SERIAL PRIMARY KEY,
            lab_uid VARCHAR(128) NOT NULL,
            test_name VARCHAR(255) NOT NULL,
            duration VARCHAR(80) DEFAULT '',
            sample_type VARCHAR(120) DEFAULT '',
            category VARCHAR(120) DEFAULT '',
            is_active BOOLEAN DEFAULT TRUE
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS lab_test_requests (
            id SERIAL PRIMARY KEY,
            lab_uid VARCHAR(128) NOT NULL,
            doctor_uid VARCHAR(128) DEFAULT '',
            patient_uid VARCHAR(128) DEFAULT '',
            patient_name VARCHAR(255) NOT NULL,
            patient_email VARCHAR(255) NOT NULL,
            test_name VARCHAR(255) NOT NULL,
            priority VARCHAR(30) DEFAULT 'normal',
            status VARCHAR(30) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS lab_reports (
            id SERIAL PRIMARY KEY,
            request_id INT NOT NULL,
            lab_uid VARCHAR(128) NOT NULL,
            patient_email VARCHAR(255) NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        conn.commit()
    finally:
        cur.close()
        put_hospital_conn(conn)