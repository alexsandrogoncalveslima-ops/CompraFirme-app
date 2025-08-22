from flask import Flask, request, jsonify, g
import sqlite3
import bcrypt
import os
import uuid

# --- CONFIGURAÇÕES ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'uma_chave_secreta_padrao')
DATABASE = 'comprada_imovel.db'
SESSIONS = {} # Simulação de sessões com um dicionário

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- ROTAS DA API ---

@app.route('/add_payment', methods=['POST'])
def add_payment():
    data = request.get_json()
    nome_pagador = data.get('nome_pagador')
    valor = data.get('valor')

    if not nome_pagador or not valor:
        return jsonify({"error": "Dados de pagamento incompletos"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO pagamentos (nome_pagador, valor, data) VALUES (?, ?, datetime('now'))",
                   (nome_pagador, valor))
    conn.commit()
    return jsonify({"message": "Pagamento registrado com sucesso!"}), 201

@app.route('/total_paid', methods=['GET'])
def get_total_paid():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(valor) FROM pagamentos")
    total = cursor.fetchone()[0]
    return jsonify({"total": total if total is not None else 0}), 200

@app.route('/payments', methods=['GET'])
def get_payments():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome_pagador, valor, data FROM pagamentos ORDER BY data DESC")
    pagamentos = cursor.fetchall()

    pagamentos_list = []
    for p in pagamentos:
        pagamentos_list.append({
            "id": p[0],
            "nome_pagador": p[1],
            "valor": p[2],
            "data": p[3]
        })
    return jsonify(pagamentos_list), 200

# NOVO ENDPOINT: Rota para excluir um pagamento
@app.route('/delete_payment/<int:payment_id>', methods=['DELETE'])
def delete_payment(payment_id):
    # Verificação de senha de administrador (simples e temporária)
    admin_password = request.headers.get('Admin-Password')
    if admin_password != "admin123":
        return jsonify({"error": "Acesso negado. Senha de administrador incorreta."}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM pagamentos WHERE id = ?", (payment_id,))
    if cursor.fetchone()[0] == 0:
        return jsonify({"error": "Pagamento não encontrado."}), 404
        
    cursor.execute("DELETE FROM pagamentos WHERE id = ?", (payment_id,))
    conn.commit()
    return jsonify({"message": "Pagamento excluído com sucesso!"}), 200

# Endpoint de login mantido para referência futura, mas não usado pelo app
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
    user_data = cursor.fetchone()

    if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data[1].encode('utf-8')):
        session_key = str(uuid.uuid4())
        SESSIONS[session_key] = user_data[0]
        return jsonify({"message": "Login bem-sucedido!", "session_key": session_key}), 200
    else:
        return jsonify({"error": "Credenciais inválidas"}), 401

if __name__ == '__main__':
    from database import create_connection, create_tables, add_admin_user
    conn = create_connection()
    if conn:
        create_tables(conn)
        add_admin_user(conn)
        conn.close()
    app.run(host='0.0.0.0', port=10000)