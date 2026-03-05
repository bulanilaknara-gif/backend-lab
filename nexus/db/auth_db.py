from psycopg2.pool import SimpleConnectionPool
from config import AUTH_DB

_auth_pool = SimpleConnectionPool(1, 10, **AUTH_DB)

def get_auth_conn():
    return _auth_pool.getconn()

def put_auth_conn(conn):
    _auth_pool.putconn(conn)