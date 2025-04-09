import MySQLdb

def connect_db():
    return MySQLdb.connect(
        host="localhost",
        user="root",
        passwd="2508",
        db="kingsleague",
        charset='utf8mb4'
    )
