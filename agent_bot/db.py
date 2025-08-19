import mysql.connector
from config import DefaultConfig

CONFIG = DefaultConfig()

def get_connection():
    return mysql.connector.connect(
        host=CONFIG.DB_HOST,
        user=CONFIG.DB_USER,
        password=CONFIG.DB_PASSWORD,
        database=CONFIG.DB_NAME
    )

def insert_installation(user_id, app, version):
    db = get_connection()
    cursor = db.cursor()
    sql = """
        INSERT INTO installations (user_id, app, version, start_time, end_time)
        VALUES (%s, %s, %s, NOW(), NULL)
    """
    cursor.execute(sql, (user_id, app, version))
    db.commit()
    last_id = cursor.lastrowid
    cursor.close()
    db.close()
    return last_id   # return the row id so we can track it



def update_end_time(installation_id):
    db = get_connection()
    cursor = db.cursor()
    sql = "UPDATE installations SET end_time = NOW() WHERE id = %s"
    cursor.execute(sql, (installation_id,))
    db.commit()
    cursor.close()
    db.close()
