import sqlite3
import threading
conn = sqlite3.connect('database.db',check_same_thread=False)

c = conn.cursor()
lock = threading.Lock()

def create_table():
    try:
        lock.acquire(True)
        with conn:
            c.execute("""CREATE TABLE IF NOT EXISTS CONFIG (
                UID TEXT PRIMARY KEY NOT NULL,
                YEAR INTEGER,
                MONTH INTEGER,
                START CHAR(20),
                END CHAR(20),
                K INTEGER,
                COUNTRY CHAR(3),
                SUBDIV TEXT,
                HOLIDAYS TEXT
            )""")
    finally:
        lock.release()



def insert_into_table(config_obj):
    try:
        lock.acquire(True)
        with conn:
            c.execute("INSERT INTO CONFIG VALUES (?,?,?,?,?,?,?,?,?)",config_obj)
    finally:
        lock.release()
    
def update_holidays(config_obj):
    try:
        lock.acquire(True)
        with conn:
            c.execute("""UPDATE CONFIG SET YEAR=?,MONTH=?,START=?,END=?,K=?,COUNTRY=?,SUBDIV=?,HOLIDAYS=?
                        WHERE UID=?""",config_obj)
    finally:
        lock.release()

def get_holidays_by_uid(uid):
    c.execute("SELECT * FROM CONFIG WHERE UID=:UID", {'UID': uid})
    return c.fetchone()


create_table()