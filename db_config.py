import os
import MySQLdb

def connect_db():
    url = os.environ.get('JAWSDB_URL')
    return MySQLdb.connect(url)
