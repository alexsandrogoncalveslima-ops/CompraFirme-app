import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.clock import mainthread
from kivy.uix.popup import Popup
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
            padding=dp(15), 
            spacing=dp(5)
        )
        
        payments_button = Button(text='Ver Pagamentos', size_hint_y=None, height=dp(40))
        payments_button.bind(on_press=self.go_to_payments_screen)
        main_container.add_widget(payments_button)
        
        main_container.add_widget(Label(text='Valor Total do Imóvel: R$ 280.000,00', font_size='18sp'))
        
        self.total_paid_label = Label(text='Total Pago: R$ 0,00', font_size='16sp')
        main_container.add_widget(self.total_paid_label)
        
        self.remaining_amount_label = Label(text='Valor Restante: R$ 0,00', font_size='22sp', bold=True)
        main_container.add_widget(self.remaining_amount_label)

        main_container.add_widget(Label(text='Adicionar Novo Pagamento', font_size='18sp'))

        # Novo layout para os campos de entrada, usando GridLayout
        input_grid = GridLayout(cols=1, spacing=dp(5), size_hint_y=None, height=dp(80))
        
        self.name_input = TextInput(hint_text='Nome do Pagador', multiline=False, size_hint_y=None, height=dp(35))
        input_grid.add_widget(self.name_input)

        self.value_input = TextInput(hint_text='Valor (ex: 10000.00)', multiline=False, input_type='number', size_hint_y=None, height=dp(35))
        input_grid.add_widget(self.value_input)
        
        main_container.add_widget(input_grid)
        
        self.add_button = Button(text='Registrar Pagamento', size_hint_y=None, height=dp(40))
        self.add_button.bind(on_press=self.register_payment_thread)
        main_container.add_widget(self.add_button)
        
        self.message_label = Label(text='', size_hint_y=None, height=dp(40))
        main_container.add_widget(self.message_label)

        self.add_widget(main_container)

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
                
                self.update_ui_labels(total_pago, valor_restante)
            else:
                self.update_ui_labels_error(f"Erro ao carregar dados. Status: {total_paid_response.status_code}")
        except requests.exceptions.RequestException:
            self.update_ui_labels_error("Erro de conexão com o servidor.")
    
    @mainthread
    def update_ui_labels(self, total_pago, valor_restante):
        self.total_paid_label.text = f'Total Pago: R$ {total_pago:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        self.remaining_amount_label.text = f'Valor Restante: R$ {valor_restante:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    @mainthread
    def update_ui_labels_error(self, message):
        self.total_paid_label.text = message
        self.remaining_amount_label.text = ""

    def register_payment_thread(self, instance):
        self.add_button.disabled = True
        self.message_label.text = "Registrando pagamento..."
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
                    self.clear_inputs_and_show_message("Pagamento registrado com sucesso!")
                else:
                    self.clear_inputs_and_show_message(f"Erro ao registrar: {response.json().get('error', '')}")
            else:
                self.clear_inputs_and_show_message("Por favor, preencha nome e valor corretamente.")
        except ValueError:
            self.clear_inputs_and_show_message("Valor inválido. Use um número (ex: 10000.00).")
        finally:
            self.add_button.disabled = False

    @mainthread
    def clear_inputs_and_show_message(self, message):
        self.name_input.text = ''
        self.value_input.text = ''
        self.message_label.text = message

    def go_to_payments_screen(self, instance):
        self.manager.current = 'payments'

class PaymentsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(5))
        
        header_layout = BoxLayout(size_hint_y=None, height=dp(40))
        header_layout.add_widget(Button(text='Voltar', size_hint_x=0.2, on_press=self.go_back))
        header_layout.add_widget(Label(text='Histórico de Pagamentos', font_size='20sp', size_hint_x=0.8))
        self.layout.add_widget(header_layout)

        self.scroll_view = ScrollView()
        self.payments_list_container = GridLayout(cols=1, spacing=dp(5), size_hint_y=None, row_default_height=dp(50))
        self.payments_list_container.bind(minimum_height=self.payments_list_container.setter('height'))
        self.scroll_view.add_widget(self.payments_list_container)
        
        self.layout.add_widget(self.scroll_view)
        self.add_widget(self.layout)

    def on_enter(self, *args):
        self.load_payments()

    def load_payments(self):
        self.payments_list_container.clear_widgets()
        self.payments_list_container.add_widget(Label(text="Carregando...", size_hint_y=None, height=dp(40)))
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
            
    @mainthread
    def populate_list_on_main_thread(self, pagamentos):
        self.payments_list_container.clear_widgets()
        if not pagamentos:
            self.payments_list_container.add_widget(Label(text="Nenhum pagamento registrado."))
        else:
            for p in pagamentos:
                data_formatada = p['data'].split(' ')[0]
                valor_formatado = f"R$ {p['valor']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                
                # Item da lista com botões
                payment_item = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), padding=dp(5), spacing=dp(5))
                payment_item.add_widget(Label(text=p['nome_pagador'], size_hint_x=0.4))
                payment_item.add_widget(Label(text=valor_formatado, size_hint_x=0.3))
                payment_item.add_widget(Label(text=data_formatada, size_hint_x=0.2))
                
                # Botão de Excluir
                delete_btn = Button(text='X', size_hint_x=0.1, background_color=(1, 0, 0, 1))
                delete_btn.bind(on_press=lambda btn, id=p['id']: self.show_admin_password_popup(id))
                payment_item.add_widget(delete_btn)
                
                self.payments_list_container.add_widget(payment_item)
    
    def show_admin_password_popup(self, payment_id):
        # Layout do popup
        popup_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        popup_layout.add_widget(Label(text='Insira a senha de administrador para excluir:', font_size='16sp'))
        
        password_input = TextInput(password=True, multiline=False, size_hint_y=None, height=dp(35))
        popup_layout.add_widget(password_input)
        
        btn_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        cancel_btn = Button(text='Cancelar')
        confirm_btn = Button(text='Confirmar')
        
        btn_layout.add_widget(cancel_btn)
        btn_layout.add_widget(confirm_btn)
        popup_layout.add_widget(btn_layout)
        
        popup = Popup(title='Excluir Pagamento', content=popup_layout, size_hint=(0.8, 0.4), auto_dismiss=False)

        def dismiss_popup(instance):
            popup.dismiss()
        
        def confirm_and_delete(instance):
            password = password_input.text
            self.delete_payment_thread(payment_id, password)
            popup.dismiss()

        cancel_btn.bind(on_press=dismiss_popup)
        confirm_btn.bind(on_press=confirm_and_delete)
        
        popup.open()

    def delete_payment_thread(self, payment_id, password):
        Thread(target=self.delete_payment, args=(payment_id, password)).start()

    def delete_payment(self, payment_id, password):
        try:
            headers = {'Admin-Password': password}
            response = requests.delete(f"{SERVER_URL}/delete_payment/{payment_id}", headers=headers)
            
            if response.status_code == 200:
                self.load_payments() # Recarrega a lista
                self.add_message_on_main_thread("Pagamento excluído com sucesso!")
                self.manager.get_screen('main').update_values_thread()
            else:
                self.add_message_on_main_thread(f"Erro ao excluir: {response.json().get('error', 'Erro desconhecido')}")
        except requests.exceptions.RequestException:
            self.add_message_on_main_thread("Erro de conexão ao excluir.")

    @mainthread
    def add_message_on_main_thread(self, message):
        # Implementação para exibir mensagens na tela de pagamentos
        popup = Popup(title='Status', content=Label(text=message), size_hint=(0.8, 0.2))
        popup.open()
            
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