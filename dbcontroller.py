import sqlite3

def query_db(query, args=()):
    con = sqlite3.connect('advweb.db')
    cur = con.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()  
    cur.close()
    con.close()
    return rv 

def execute_db(query, args=()):
    con = sqlite3.connect('advweb.db')
    cur = con.cursor()
    cur.execute(query, args)
    con.commit()
    cur.close()
    con.close()
