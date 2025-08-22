import os
import sqlite3
from flask import Flask, jsonify, request
import bcrypt
from datetime import datetime

app = Flask(__name__)

# Configuração do banco de dados
DATABASE = 'comprada_imovel.db'
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS pagamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_pagador TEXT NOT NULL,
                valor REAL NOT NULL,
                data TEXT NOT NULL
            )
        ''')

@app.route('/add_payment', methods=['POST'])
def add_payment():
    try:
        data = request.json
        nome = data['nome_pagador']
        valor = float(data['valor'])
        
        with get_db() as conn:
            conn.execute('INSERT INTO pagamentos (nome_pagador, valor, data) VALUES (?, ?, ?)', (nome, valor, datetime.now().isoformat()))
            conn.commit()
            
        return jsonify({"message": "Pagamento adicionado com sucesso!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/payments', methods=['GET'])
def get_payments():
    try:
        with get_db() as conn:
            pagamentos = conn.execute('SELECT * FROM pagamentos ORDER BY data DESC').fetchall()
            
            # Converte as linhas do banco de dados em uma lista de dicionários
            pagamentos_list = []
            for p in pagamentos:
                pagamentos_list.append({
                    "id": p["id"],
                    "nome_pagador": p["nome_pagador"],
                    "valor": p["valor"],
                    "data": datetime.fromisoformat(p["data"]).isoformat()
                })
            
            return jsonify(pagamentos_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/total_paid', methods=['GET'])
def get_total_paid():
    try:
        with get_db() as conn:
            total = conn.execute('SELECT SUM(valor) FROM pagamentos').fetchone()[0]
            if total is None:
                total = 0
            
            return jsonify({"total": total}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/edit_payment/<int:payment_id>', methods=['PUT'])
def edit_payment(payment_id):
    try:
        if not ADMIN_PASSWORD_HASH:
            return jsonify({"error": "Admin password not set."}), 403

        password = request.headers.get('Admin-Password')
        if not bcrypt.checkpw(password.encode('utf-8'), ADMIN_PASSWORD_HASH.encode('utf-8')):
            return jsonify({"error": "Unauthorized."}), 401

        data = request.json
        nome = data.get('nome_pagador')
        valor = float(data.get('valor'))
        
        with get_db() as conn:
            conn.execute('UPDATE pagamentos SET nome_pagador = ?, valor = ? WHERE id = ?', (nome, valor, payment_id))
            conn.commit()
            
        return jsonify({"message": "Pagamento editado com sucesso!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delete_payment/<int:payment_id>', methods=['DELETE'])
def delete_payment(payment_id):
    try:
        if not ADMIN_PASSWORD_HASH:
            return jsonify({"error": "Admin password not set."}), 403

        password = request.headers.get('Admin-Password')
        if not bcrypt.checkpw(password.encode('utf-8'), ADMIN_PASSWORD_HASH.encode('utf-8')):
            return jsonify({"error": "Unauthorized."}), 401

        with get_db() as conn:
            conn.execute('DELETE FROM pagamentos WHERE id = ?', (payment_id,))
            conn.commit()
            
        return jsonify({"message": "Pagamento excluído com sucesso!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True)