import requests

SERVER_URL = "https://comprafirme-app.onrender.com"

def add_payment(nome_pagador, valor):
    """Envia um novo pagamento para o servidor online."""
    payload = {
        "nome_pagador": nome_pagador,
        "valor": valor
    }
    response = requests.post(f"{SERVER_URL}/add_payment", json=payload)
    if response.status_code == 201:
        print("Pagamento registrado com sucesso no servidor!")
    else:
        print(f"Erro ao registrar pagamento: {response.status_code}")
        try:
            print(response.json())
        except requests.exceptions.JSONDecodeError:
            print("Resposta do servidor não é JSON.")

def get_total_paid():
    """Obtém o total de pagamentos do servidor online."""
    try:
        response = requests.get(f"{SERVER_URL}/total_paid")
        if response.status_code == 200:
            return response.json().get('total', 0)
        print(f"Erro ao obter total: {response.status_code}")
        return 0
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão: {e}")
        return 0

def get_remaining_amount(total_imovel=280000):
    """Calcula o valor restante a ser pago."""
    total_pago = get_total_paid()
    return total_imovel - total_pago

if __name__ == '__main__':
    print("--- Testando a lógica da aplicação contra o servidor online ---")
    add_payment("Teste API", 5000)
    print(f"Total pago: R${get_total_paid():.2f}")
    print("--- Teste concluído ---")