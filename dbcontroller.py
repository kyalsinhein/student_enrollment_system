import sqlite3

DB_NAME = 'advweb.db'

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
