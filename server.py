from flask import Flask, request, jsonify, g
import os
from database import get_connection, create_tables, add_admin_user
import bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'uma_chave_secreta_padrao')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = get_connection()
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
    cursor.execute("INSERT INTO pagamentos (nome_pagador, valor) VALUES (%s, %s)",
                   (nome_pagador, valor))
    conn.commit()
    return jsonify({"message": "Pagamento registrado com sucesso!"}), 201

@app.route('/total_paid', methods=['GET'])
def get_total_paid():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(valor) FROM pagamentos")
    total = cursor.fetchone()[0]
    return jsonify({"total": float(total) if total is not None else 0}), 200

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
            "valor": float(p[2]),
            "data": p[3].isoformat()
        })
    return jsonify(pagamentos_list), 200

@app.route('/delete_payment/<int:payment_id>', methods=['DELETE'])
def delete_payment(payment_id):
    admin_password = request.headers.get('Admin-Password')
    if admin_password != "admin123":
        return jsonify({"error": "Acesso negado. Senha de administrador incorreta."}), 401
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM pagamentos WHERE id = %s", (payment_id,))
    if cursor.fetchone()[0] == 0:
        return jsonify({"error": "Pagamento não encontrado."}), 404
    cursor.execute("DELETE FROM pagamentos WHERE id = %s", (payment_id,))
    conn.commit()
    return jsonify({"message": "Pagamento excluído com sucesso!"}), 200

@app.route('/edit_payment/<int:payment_id>', methods=['PUT'])
def edit_payment(payment_id):
    admin_password = request.headers.get('Admin-Password')
    if admin_password != "admin123":
        return jsonify({"error": "Acesso negado. Senha de administrador incorreta."}), 401
    data = request.get_json()
    new_nome_pagador = data.get('nome_pagador')
    new_valor = data.get('valor')
    if not new_nome_pagador or not new_valor:
        return jsonify({"error": "Dados de pagamento incompletos."}), 400
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM pagamentos WHERE id = %s", (payment_id,))
    if cursor.fetchone()[0] == 0:
        return jsonify({"error": "Pagamento não encontrado."}), 404
    cursor.execute("UPDATE pagamentos SET nome_pagador = %s, valor = %s, data = CURRENT_TIMESTAMP WHERE id = %s", 
                   (new_nome_pagador, new_valor, payment_id))
    conn.commit()
    return jsonify({"message": "Pagamento editado com sucesso!"}), 200

if __name__ == '__main__':
    create_tables()
    add_admin_user()
    app.run(host='0.0.0.0', port=10000)