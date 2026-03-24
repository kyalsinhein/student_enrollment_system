import sqlite3

DB_NAME = 'advweb.db'

def init_db():
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS student (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name  TEXT NOT NULL,
            email      TEXT NOT NULL UNIQUE,
            phone      TEXT,
            address    TEXT,
            password   TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS course (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            image       TEXT,
            description TEXT,
            credits     INTEGER,
            lecturer    TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS enrollment (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  INTEGER NOT NULL,
            course_id   INTEGER NOT NULL,
            enroll_date TEXT,
            FOREIGN KEY (student_id) REFERENCES student(id),
            FOREIGN KEY (course_id)  REFERENCES course(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS schedule (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id   INTEGER NOT NULL,
            day_of_week TEXT,
            start_time  TEXT,
            end_time    TEXT,
            FOREIGN KEY (course_id) REFERENCES course(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name  TEXT NOT NULL,
            email      TEXT NOT NULL UNIQUE,
            password   TEXT NOT NULL
        )
    """)

    con.commit()
    con.close()
    print("[init_db] Database and tables created successfully.")

if __name__ == "__main__":
    init_db()
