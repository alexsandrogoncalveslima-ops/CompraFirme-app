import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
import requests
import json
from threading import Thread

# Importa a URL do servidor
from app_logic import SERVER_URL

# Torna a janela menor para um visual mais compacto
Window.size = (400, 600)

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        main_container = BoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(10)
        )
        
        # Botão para visualizar os pagamentos
        payments_button = Button(text='Ver Pagamentos', size_hint_y=None, height=dp(44))
        payments_button.bind(on_press=self.go_to_payments_screen)
        main_container.add_widget(payments_button)
        
        main_container.add_widget(Label(text='Valor Total do Imóvel: R$ 280.000,00', font_size='20sp'))
        
        self.total_paid_label = Label(text='Total Pago: R$ 0,00', font_size='18sp')
        main_container.add_widget(self.total_paid_label)
        
        self.remaining_amount_label = Label(text='Valor Restante: R$ 0,00', font_size='24sp', bold=True)
        main_container.add_widget(self.remaining_amount_label)

        main_container.add_widget(Label(text='Adicionar Novo Pagamento', font_size='18sp'))

        self.name_input = TextInput(hint_text='Nome do Pagador', multiline=False, size_hint_y=None, height=dp(40), on_text_validate=self.focus_value)
        main_container.add_widget(self.name_input)

        self.value_input = TextInput(hint_text='Valor (ex: 10000.00)', multiline=False, input_type='number', size_hint_y=None, height=dp(40), on_text_validate=self.register_payment_thread)
        main_container.add_widget(self.value_input)

        self.add_button = Button(text='Registrar Pagamento', size_hint_y=None, height=dp(44))
        self.add_button.bind(on_press=self.register_payment_thread)
        main_container.add_widget(self.add_button)
        
        self.add_widget(main_container)

    def focus_value(self, instance):
        self.value_input.focus = True

    def on_enter(self, *args):
        self.update_values_thread()

    def update_values_thread(self, instance=None):
        self.total_paid_label.text = "Carregando..."
        Thread(target=self.update_values).start()

    def update_values(self):
        try:
            total_paid_response = requests.get(f"{SERVER_URL}/total_paid")
            if total_paid_response.status_code == 200:
                total_pago = total_paid_response.json().get('total', 0)
                valor_restante = 280000 - total_pago
                
                self.total_paid_label.text = f'Total Pago: R$ {total_pago:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
                self.remaining_amount_label.text = f'Valor Restante: R$ {valor_restante:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
            else:
                self.total_paid_label.text = f"Erro ao carregar dados. Status: {total_paid_response.status_code}"
                self.remaining_amount_label.text = ""
        except requests.exceptions.RequestException:
            self.total_paid_label.text = "Erro de conexão com o servidor."
            self.remaining_amount_label.text = ""

    def register_payment_thread(self, instance):
        self.add_button.disabled = True
        Thread(target=self.register_payment, args=(instance,)).start()

    def register_payment(self, instance):
        nome = self.name_input.text
        try:
            valor = float(self.value_input.text.replace(',', '.'))
            if nome and valor > 0:
                payload = {"nome_pagador": nome, "valor": valor}
                
                response = requests.post(f"{SERVER_URL}/add_payment", json=payload)
                
                if response.status_code == 201:
                    self.update_values()
                    self.name_input.text = ''
                    self.value_input.text = ''
                else:
                    self.total_paid_label.text = f"Erro ao registrar: {response.json().get('error', '')}"
            else:
                self.total_paid_label.text = "Por favor, preencha nome e valor corretamente."
        except ValueError:
            self.total_paid_label.text = "Valor inválido. Use um número (ex: 10000.00)."
        finally:
            self.add_button.disabled = False
            
    def go_to_payments_screen(self, instance):
        self.manager.current = 'payments'

class PaymentsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        header_layout = BoxLayout(size_hint_y=None, height=dp(50))
        header_layout.add_widget(Button(text='Voltar', size_hint_x=0.2, on_press=self.go_back))
        header_layout.add_widget(Label(text='Histórico de Pagamentos', font_size='24sp', size_hint_x=0.8))
        self.layout.add_widget(header_layout)

        self.scroll_view = ScrollView()
        self.payments_list_container = GridLayout(cols=1, spacing=dp(10), size_hint_y=None, row_default_height=dp(50))
        self.payments_list_container.bind(minimum_height=self.payments_list_container.setter('height'))
        self.scroll_view.add_widget(self.payments_list_container)
        
        self.layout.add_widget(self.scroll_view)
        self.add_widget(self.layout)

    def on_enter(self, *args):
        self.load_payments()

    def load_payments(self):
        # Limpa a lista antes de carregar
        self.payments_list_container.clear_widgets()
        
        # Chama a API de forma assíncrona
        Thread(target=self.fetch_payments_data).start()

    def fetch_payments_data(self):
        try:
            response = requests.get(f"{SERVER_URL}/payments")
            if response.status_code == 200:
                pagamentos = response.json()
                self.populate_list_on_main_thread(pagamentos)
            else:
                self.add_message_on_main_thread("Erro ao carregar pagamentos.")
        except requests.exceptions.RequestException:
            self.add_message_on_main_thread("Erro de conexão com o servidor.")
            
    def populate_list_on_main_thread(self, pagamentos):
        # Acesso seguro aos widgets da UI
        from kivy.clock import mainthread
        @mainthread
        def populate_widgets():
            if not pagamentos:
                self.payments_list_container.add_widget(Label(text="Nenhum pagamento registrado."))
            else:
                for p in pagamentos:
                    # Formata a data e o valor
                    data_formatada = p['data'].split(' ')[0]
                    valor_formatado = f"R$ {p['valor']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    
                    # Cria a linha do pagamento
                    payment_item = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), padding=dp(5), spacing=dp(5))
                    payment_item.add_widget(Label(text=p['nome_pagador'], size_hint_x=0.4))
                    payment_item.add_widget(Label(text=valor_formatado, size_hint_x=0.3))
                    payment_item.add_widget(Label(text=data_formatada, size_hint_x=0.3))
                    
                    self.payments_list_container.add_widget(payment_item)
        populate_widgets()
        
    def add_message_on_main_thread(self, message):
        from kivy.clock import mainthread
        @mainthread
        def add_message():
            self.payments_list_container.add_widget(Label(text=message))
        add_message()
            
    def go_back(self, instance):
        self.manager.current = 'main'

class CompraFirmeApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(PaymentsScreen(name='payments'))
        return sm

if __name__ == '__main__':
    CompraFirmeApp().run()