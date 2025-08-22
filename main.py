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
from kivy.uix.widget import Widget
from kivy.uix.progressbar import ProgressBar
from kivy.clock import mainthread, Clock
from kivy.uix.popup import Popup
import requests
import json
from threading import Thread
import re

# Importa a URL do servidor
from app_logic import SERVER_URL

# Torna a janela menor para um visual mais compacto
Window.size = (400, 600)

# Função auxiliar para exibir balão de alerta
def show_popup(title, message):
    popup = Popup(
        title=title,
        content=Label(text=message, halign='center', valign='middle'),
        size_hint=(0.8, 0.2)
    )
    popup.open()

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        main_container = BoxLayout(
            orientation='vertical',
            padding=dp(25), 
            spacing=dp(20),
            size_hint_y=None,
            pos_hint={'center_y': 0.5}
        )
        main_container.bind(minimum_height=main_container.setter('height'))
        
        # Seção de valores
        values_section = BoxLayout(
            orientation='vertical',
            padding=dp(10),
            spacing=dp(5)
        )
        values_section.add_widget(Label(text='VALOR TOTAL DO IMÓVEL', font_size='16sp', bold=True, color=(0.2, 0.6, 0.8, 1)))
        values_section.add_widget(Label(text='R$ 280.000,00', font_size='20sp', bold=True))
        self.total_paid_label = Label(text='Total Pago: R$ 0,00', font_size='16sp')
        values_section.add_widget(self.total_paid_label)
        self.remaining_amount_label = Label(text='Valor Restante: R$ 0,00', font_size='22sp', bold=True, color=(1, 0.4, 0.4, 1))
        values_section.add_widget(self.remaining_amount_label)
        main_container.add_widget(values_section)

        # Seção para adicionar pagamento
        main_container.add_widget(Label(text='ADICIONAR NOVO PAGAMENTO', font_size='16sp', bold=True, color=(0.8, 0.8, 0.8, 1)))
        
        input_box = BoxLayout(orientation='vertical', spacing=dp(15), size_hint_y=None, height=dp(100))
        
        self.name_input = TextInput(hint_text='Nome do Pagador', multiline=False, size_hint_y=None, height=dp(45), font_size='16sp', padding=dp(10))
        input_box.add_widget(self.name_input)

        self.value_input = TextInput(hint_text='Valor (ex: 10000.00)', multiline=False, input_type='number', size_hint_y=None, height=dp(45), font_size='16sp', padding=dp(10))
        input_box.add_widget(self.value_input)
        
        main_container.add_widget(input_box)
        
        self.add_button = Button(text='Registrar Pagamento', size_hint_y=None, height=dp(50), font_size='18sp', background_color=(0.3, 0.7, 0.3, 1))
        self.add_button.bind(on_press=self.register_payment_thread)
        main_container.add_widget(self.add_button)

        payments_button = Button(text='Ver Pagamentos', size_hint_y=None, height=dp(50), font_size='18sp', background_color=(0.2, 0.6, 0.8, 1))
        payments_button.bind(on_press=self.go_to_payments_screen)
        main_container.add_widget(payments_button)

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
        Thread(target=self.register_payment, args=(instance,)).start()

    def register_payment(self, instance):
        nome = self.name_input.text
        valor_str = self.value_input.text

        if not re.match("^[a-zA-Z\s]+$", nome):
            self.show_message_on_main_thread("Nome inválido. Use apenas letras e espaços.")
            self.add_button.disabled = False
            return
        
        try:
            valor = float(valor_str.replace(',', '.'))
            if valor <= 0:
                self.show_message_on_main_thread("Valor inválido. Use um número maior que zero.")
                self.add_button.disabled = False
                return
        except ValueError:
            self.show_message_on_main_thread("Valor inválido. Use um número.")
            self.add_button.disabled = False
            return
        
        try:
            payload = {"nome_pagador": nome, "valor": valor}
            response = requests.post(f"{SERVER_URL}/add_payment", json=payload)
            
            if response.status_code == 201:
                self.update_values()
                self.clear_inputs_and_show_message_on_main_thread("Pagamento registrado com sucesso!")
                self.manager.get_screen('payments').load_payments_from_main_screen()
            else:
                self.show_message_on_main_thread(f"Erro ao registrar: {response.json().get('error', '')}")
        except requests.exceptions.RequestException:
            self.show_message_on_main_thread("Erro de conexão com o servidor.")
        finally:
            self.add_button.disabled = False

    @mainthread
    def show_message_on_main_thread(self, message):
        show_popup("Aviso", message)

    @mainthread
    def clear_inputs_and_show_message_on_main_thread(self, message):
        self.name_input.text = ''
        self.value_input.text = ''
        show_popup("Sucesso", message)

    def go_to_payments_screen(self, instance):
        self.manager.current = 'payments'

class EditPaymentPopup(Popup):
    def __init__(self, payment_id, current_nome, current_valor, on_edit_callback, **kwargs):
        super().__init__(**kwargs)
        self.payment_id = payment_id
        self.on_edit_callback = on_edit_callback
        
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        layout.add_widget(Label(text='Editar Pagamento', font_size='20sp'))
        
        self.name_input = TextInput(text=current_nome, multiline=False, hint_text='Nome do Pagador', size_hint_y=None, height=dp(35))
        layout.add_widget(self.name_input)
        
        self.value_input = TextInput(text=str(current_valor), multiline=False, hint_text='Valor', input_type='number', size_hint_y=None, height=dp(35))
        layout.add_widget(self.value_input)
        
        self.password_input = TextInput(password=True, multiline=False, hint_text='Senha de Administrador', size_hint_y=None, height=dp(35))
        layout.add_widget(self.password_input)
        
        btn_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        cancel_btn = Button(text='Cancelar')
        confirm_btn = Button(text='Confirmar Edição')
        
        btn_layout.add_widget(cancel_btn)
        btn_layout.add_widget(confirm_btn)
        layout.add_widget(btn_layout)
        
        self.content = layout
        self.title = 'Editar Pagamento'
        self.size_hint = (0.9, 0.6)
        self.auto_dismiss = False
        
        def dismiss_popup(instance):
            self.dismiss()
        
        def confirm_edit(instance):
            new_nome = self.name_input.text
            new_valor = self.value_input.text
            password = self.password_input.text
            self.on_edit_callback(self.payment_id, new_nome, new_valor, password)
            self.dismiss()

        cancel_btn.bind(on_press=dismiss_popup)
        confirm_btn.bind(on_press=confirm_edit)

class PaymentsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(5))
        
        top_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        top_layout.add_widget(Button(text='Voltar', size_hint_x=0.2, on_press=self.go_back))
        top_layout.add_widget(Label(text='Histórico de Pagamentos', font_size='20sp', size_hint_x=0.8))
        self.layout.add_widget(top_layout)

        # Cabeçalho da Tabela
        header_row = GridLayout(cols=5, size_hint_y=None, height=dp(30), padding=dp(5), spacing=dp(5))
        header_row.add_widget(Label(text='Nome', font_size='14sp', bold=True, size_hint_x=0.4))
        header_row.add_widget(Label(text='Valor', font_size='14sp', bold=True, size_hint_x=0.25))
        header_row.add_widget(Label(text='Data', font_size='14sp', bold=True, size_hint_x=0.2))
        header_row.add_widget(Label(text='E', font_size='14sp', bold=True, size_hint_x=0.075))
        header_row.add_widget(Label(text='X', font_size='14sp', bold=True, size_hint_x=0.075))
        self.layout.add_widget(header_row)

        self.scroll_view = ScrollView()
        self.payments_list_container = GridLayout(cols=1, spacing=dp(5), size_hint_y=None, row_default_height=dp(50))
        self.payments_list_container.bind(minimum_height=self.payments_list_container.setter('height'))
        self.scroll_view.add_widget(self.payments_list_container)
        
        self.layout.add_widget(self.scroll_view)
        self.add_widget(self.layout)

    def on_enter(self, *args):
        self.load_payments()
        self.update_event = Clock.schedule_interval(self.load_payments, 10)
        
    def on_leave(self, *args):
        if hasattr(self, 'update_event'):
            self.update_event.cancel()
        
    def load_payments_from_main_screen(self):
        self.load_payments()

    def load_payments(self, dt=None):
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
                data_formatada = p['data'].split('T')[0]
                valor_formatado = f"R$ {p['valor']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                
                payment_item = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), padding=dp(5), spacing=dp(5))
                payment_item.add_widget(Label(text=p['nome_pagador'], size_hint_x=0.4))
                payment_item.add_widget(Label(text=valor_formatado, size_hint_x=0.25))
                payment_item.add_widget(Label(text=data_formatada, size_hint_x=0.2))

                edit_btn = Button(text='E', size_hint_x=0.075, background_color=(0, 0.5, 1, 1))
                edit_btn.bind(on_press=lambda btn, p_id=p['id'], p_nome=p['nome_pagador'], p_valor=p['valor']: self.show_edit_popup(p_id, p_nome, p_valor))
                payment_item.add_widget(edit_btn)
                
                delete_btn = Button(text='X', size_hint_x=0.075, background_color=(1, 0, 0, 1))
                delete_btn.bind(on_press=lambda btn, id=p['id']: self.show_admin_password_popup(id))
                payment_item.add_widget(delete_btn)
                
                self.payments_list_container.add_widget(payment_item)
    
    def show_edit_popup(self, payment_id, nome, valor):
        popup = EditPaymentPopup(payment_id, nome, valor, self.edit_payment_thread)
        popup.open()

    def edit_payment_thread(self, payment_id, new_nome, new_valor, password):
        Thread(target=self.edit_payment, args=(payment_id, new_nome, new_valor, password)).start()

    def edit_payment(self, payment_id, new_nome, new_valor, password):
        try:
            headers = {'Admin-Password': password}
            payload = {'nome_pagador': new_nome, 'valor': float(new_valor)}
            response = requests.put(f"{SERVER_URL}/edit_payment/{payment_id}", json=payload, headers=headers)
            
            if response.status_code == 200:
                self.load_payments()
                self.add_message_on_main_thread("Pagamento editado com sucesso!")
                self.manager.get_screen('main').update_values_thread()
            else:
                self.add_message_on_main_thread(f"Erro ao editar: {response.json().get('error', 'Erro desconhecido')}")
        except requests.exceptions.RequestException:
            self.add_message_on_main_thread("Erro de conexão ao editar.")
        except ValueError:
            self.add_message_on_main_thread("Valor inválido. Use um número.")
    
    def show_admin_password_popup(self, payment_id):
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
                self.load_payments()
                self.add_message_on_main_thread("Pagamento excluído com sucesso!")
                self.manager.get_screen('main').update_values_thread()
            else:
                self.add_message_on_main_thread(f"Erro ao excluir: {response.json().get('error', 'Erro desconhecido')}")
        except requests.exceptions.RequestException:
            self.add_message_on_main_thread("Erro de conexão ao excluir.")

    @mainthread
    def add_message_on_main_thread(self, message):
        show_popup("Status", message)
            
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