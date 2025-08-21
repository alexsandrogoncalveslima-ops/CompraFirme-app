import sqlite3
import bcrypt

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

def create_tables(conn):
    """Cria as tabelas de pagamentos e de usuários no banco de dados.
    """
    cursor = conn.cursor()

    # Tabela para os pagamentos (a que você já tinha)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pagamentos (
            id INTEGER PRIMARY KEY,
            nome_pagador TEXT NOT NULL,
            valor REAL NOT NULL,
            data TEXT NOT NULL
        )
    ''')

    # Tabela para os usuários (nova)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()

def add_admin_user(conn):
    """Adiciona um usuário administrador se ele não existir."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if cursor.fetchone() is None:
        # Criptografa a senha antes de salvar
        hashed_password = bcrypt.hashpw('12345'.encode('utf-8'), bcrypt.gensalt())
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                       ('admin', hashed_password.decode('utf-8')))
        conn.commit()
        print("Usuário 'admin' com senha '12345' criado com sucesso!")

if __name__ == '__main__':
    conn = create_connection()
    if conn:
        create_tables(conn)
        add_admin_user(conn)
        conn.close()
        print("Banco de dados e tabelas criados com sucesso!")