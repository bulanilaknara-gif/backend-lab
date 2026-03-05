from psycopg2.pool import SimpleConnectionPool
from config import HOSPITAL_DB

_hospital_pool = SimpleConnectionPool(1, 10, **HOSPITAL_DB)

def get_hospital_conn():
    return _hospital_pool.getconn()

def put_hospital_conn(conn):
    _hospital_pool.putconn(conn)