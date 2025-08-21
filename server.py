from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Configurações do banco de dados (ainda local)
DATABASE = 'comprada_imovel.db'

def connect_db():
    """Cria e retorna uma conexão com o banco de dados."""
    return sqlite3.connect(DATABASE)

# --- ROTAS DE AUTENTICAÇÃO E PAGAMENTO ---

@app.route('/login', methods=['POST'])
def login():
    """Endpoint para autenticação de usuário."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username == 'admin' and password == '12345':
        return jsonify({"message": "Login bem-sucedido!"}), 200
    else:
        return jsonify({"error": "Credenciais inválidas"}), 401

@app.route('/add_payment', methods=['POST'])
def add_payment():
    """Endpoint para adicionar um novo pagamento."""
    data = request.get_json()
    nome_pagador = data.get('nome_pagador')
    valor = data.get('valor')

    if not nome_pagador or not valor:
        return jsonify({"error": "Dados de pagamento incompletos"}), 400

    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO pagamentos (nome_pagador, valor, data) VALUES (?, ?, datetime('now'))",
                       (nome_pagador, valor))
        conn.commit()
        conn.close()
        return jsonify({"message": "Pagamento registrado com sucesso!"}), 201
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

@app.route('/total_paid', methods=['GET'])
def get_total_paid():
    """Endpoint para calcular e retornar o total de pagamentos."""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(valor) FROM pagamentos")
        total = cursor.fetchone()[0]
        conn.close()
        return jsonify({"total": total if total is not None else 0}), 200
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    from database import create_connection, create_table
    conn = create_connection()
    if conn:
        create_table(conn)
        conn.close()
    app.run(host='0.0.0.0', port=10000)