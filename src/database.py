#database.py

import sqlite3
#makore
def create_table(conn):
    try:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_topic ON knowledge_base(topic)')
    except sqlite3.Error as e:
        print(f"Error creating table: {e}")

def insert_knowledge(conn, topic, content):
    sql = '''
        INSERT INTO knowledge_base(topic, content)
        VALUES(?, ?)
    '''
    cur = conn.cursor()
    cur.execute(sql, (topic, content))
    conn.commit()
    return cur.lastrowid

def update_knowledge(conn, id, topic, content):
    sql = '''
        UPDATE knowledge_base
        SET topic = ?, content = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    '''
    cur = conn.cursor()
    cur.execute(sql, (topic, content, id))
    conn.commit()