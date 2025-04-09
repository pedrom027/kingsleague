import os
import MySQLdb

# Pega a variável de ambiente JAWSDB_URL
DATABASE_URL = os.environ.get('JAWSDB_URL')

def connect_db():
    # Conecta ao banco de dados MySQL
    return MySQLdb.connect(
        host=DATABASE_URL.split('@')[1].split(':')[0],
        user=DATABASE_URL.split(':')[1].split('//')[1],
        passwd=DATABASE_URL.split(':')[2].split('@')[0],
        db=DATABASE_URL.split('/')[-1],
        charset='utf8mb4'
    )
