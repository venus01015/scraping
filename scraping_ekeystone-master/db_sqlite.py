import sqlite3
from sqlite3 import Error

def update_query(conn, query):
    try:
        cur = conn.cursor()
        cur.execute(query)
        conn.commit()
        return True
    except Error:
        print(Error)
        return None

def select_query(conn, query):
    try:
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        return rows
    except Error:
        print(Error)
        return None

def exist_check_query(conn, query):
    try:
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        if len(rows) > 0:
            return True
        else:
            return False
    except Error:
        print(Error)
        return None

def run_query(con, query):
    try:
        return con.cursor().execute(query)
    except Error:
        print(Error)
        return None

def insert_query(con, query):
    try:
        con.cursor().execute(query)
        con.commit()
        return True
    except Error:
        print(Error)
        return False

def create_table(con, query):
    try:
        cursorObj = con.cursor()
        cursorObj.execute(query)
        con.commit()
        return True
    except Error:
        print(Error)
        return False

def create_db(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
        return True
    except Error as e:
        print(e)
        return False
    finally:
        if conn:
            conn.close()

def connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error:
        print(Error)
        return None

def close(connect):
    try:
        return connect.close()
    except Error:
        print(Error)

if __name__ == '__main__':
    DB_Name = "scraping.db"
    create_db(DB_Name)
    con = connection(DB_Name)
    query = "create table if not exists employees(id integer PRIMARY KEY, name text, salary real, department text, position text, hireDate text)"
    create_table(con,query)
    query = "INSERT INTO employees VALUES(11, 'John', 700, 'HR', 'Manager', '2017-01-04')"
    insert_query(con,query)
    query = "Select * FROM employees WHERE name='John'"
    rows = select_query(con,query)
    print(rows)
    # query = "UPDATE employees SET name = 'Rogers' where name='John'"
    # print(update_query(con,query))
    for row in rows :
        print(row[0], row[1], row[2])