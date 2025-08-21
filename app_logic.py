import sqlite3
import datetime

DATABASE = 'comprada_imovel.db'

def connect_db():
    """Conecta ao banco de dados e retorna o objeto de conexão."""
    return sqlite3.connect(DATABASE)

def add_payment(nome_pagador, valor):
    """Adiciona um novo pagamento à tabela."""
    conn = connect_db()
    cursor = conn.cursor()
    data_hoje = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO pagamentos (nome_pagador, valor, data) VALUES (?, ?, ?)",
        (nome_pagador, valor, data_hoje)
    )
    conn.commit()
    conn.close()
    print(f"Pagamento de R${valor:.2f} por {nome_pagador} adicionado com sucesso!")

def get_total_paid():
    """Calcula a soma de todos os pagamentos realizados."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(valor) FROM pagamentos")
    total = cursor.fetchone()[0]
    conn.close()
    return total if total is not None else 0

def get_remaining_amount(total_imovel=280000):
    """Calcula o valor restante a ser pago."""
    total_pago = get_total_paid()
    return total_imovel - total_pago

if __name__ == '__main__':
    # Exemplo de uso das funções
    print("--- Testando a lógica da aplicação ---")

    # Adicionar alguns pagamentos de exemplo
    add_payment("João", 10000)
    add_payment("Maria", 5000)

    # Obter o total pago
    total_pago_atual = get_total_paid()
    print(f"Total já pago: R${total_pago_atual:.2f}")

    # Obter o valor restante
    valor_restante = get_remaining_amount()
    print(f"Valor restante a pagar: R${valor_restante:.2f}")

    print("--- Teste concluído ---")