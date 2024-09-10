import sqlite3

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('knowledge_base.db')
        print(f"Successfully connected to SQLite version {sqlite3.version}")
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
    return conn

def create_table(conn):
    try: 
        c = conn.cursor()
        c.execute(
            '''
                CREATE TABLE IF NOT EXIST knowledge_base(
                    id INTEGER PRIMERY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            '''
        )
        c.execute('CREATE INDEX IF NOT EXIST idx_topic ON knowledge_base(topic)')
    except sqlite3.Error as e:
        print(f"error creating table: {e}")
        

def insert_knowledge(conn, topic, content):
    sql = '''
        INSERT INTO knowledge_base(topic, content)
        VALUES(?, ?)
    '''
    cur = conn.curser()
    cur.execute(sql, ())