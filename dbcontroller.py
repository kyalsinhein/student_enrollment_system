import sqlite3

def query_db(query, args=(), one=False):
    con = sqlite3.connect('advweb.db')
    cur = con.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    con.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    con = sqlite3.connect('advweb.db')
    cur = con.cursor()
    cur.execute(query, args)
    con.commit()
    cur.close()
    con.close()
