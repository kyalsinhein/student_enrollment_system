import sqlite3
from contextlib import closing

DATABASE = 'advweb.db'

def get_db_connection():
    return sqlite3.connect(DATABASE)

def query_db(query, args=(), one=False):
    con = get_db_connection()
    with closing(con.cursor()) as cur:
        cur.execute(query, args)
        rv = cur.fetchall()
        if one:
            return rv[0] if rv else None
        return rv

def execute_db(query, args=()):
    con = get_db_connection()
    with closing(con.cursor()) as cur:
        cur.execute(query, args)
        con.commit()
