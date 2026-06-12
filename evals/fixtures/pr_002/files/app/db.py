import sqlite3


def find_user(conn: sqlite3.Connection, username: str):
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchone()
