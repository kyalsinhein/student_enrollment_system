import os
import shutil
import sqlite3

SRC_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'advweb.db')
DB_NAME = SRC_DB

if os.environ.get('VERCEL'):
    DB_NAME = '/tmp/advweb.db'
    if not os.path.exists(DB_NAME) and os.path.exists(SRC_DB):
        shutil.copy(SRC_DB, DB_NAME)

def query_db(query, args=()):
    con = None
    try:
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        cur.execute(query, args)
        rv = cur.fetchall()
        return rv
    except sqlite3.Error as e:
        print(f"[query_db error] {e}")
        raise
    finally:
        if con:
            con.close()

def execute_db(query, args=()):
    con = None
    try:
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        cur.execute(query, args)
        con.commit()
    except sqlite3.Error as e:
        print(f"[execute_db error] {e}")
        raise
    finally:
        if con:
            con.close()
