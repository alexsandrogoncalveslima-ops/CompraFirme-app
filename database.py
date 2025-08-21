import sqlite3

def create_connection():
    """Cria e retorna uma conexão com o banco de dados.
    Cria o arquivo do banco de dados se ele não existir.
    """
    conn = None
    try:
        conn = sqlite3.connect('comprada_imovel.db')
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

def create_table(conn):
    """Cria a tabela de pagamentos no banco de dados.
    """
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pagamentos (
            id INTEGER PRIMARY KEY,
            nome_pagador TEXT NOT NULL,
            valor REAL NOT NULL,
            data TEXT NOT NULL
        )
    ''')
    conn.commit()

if __name__ == '__main__':
    conn = create_connection()
    if conn:
        create_table(conn)
        conn.close()
        print("Banco de dados 'comprada_imovel.db' e tabela 'pagamentos' criados com sucesso!")