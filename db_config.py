import os
import MySQLdb
from urllib.parse import urlparse

def connect_db():
    # Tenta pegar a variável de ambiente JAWSDB_URL (pode ser 'JAWSDB_AQUA_URL' também)
    db_url = os.environ.get('JAWSDB_URL') or os.environ.get('JAWSDB_AQUA_URL')
    
    # Caso não encontre a variável de ambiente, lança um erro
    if not db_url:
        raise ValueError("A URL do banco de dados não foi encontrada nas variáveis de ambiente.")
    
    # Conectar ao banco de dados usando a URL de conexão
    return MySQLdb.connect(db_url)
