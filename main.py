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
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.image import Image
import requests
import json
from threading import Thread
import re
from datetime import datetime

# Importa a URL do servidor e o modelo de contrato
from app_logic import SERVER_URL, CONTRATO_TEMPLATE

# Torna a janela menor para um visual mais compacto
Window.size = (400, 600)

# Define as cores
BG_COLOR = (0.95, 0.96, 0.97, 1)  # Cinza muito claro
CARD_BG_COLOR = (1, 1, 1, 1)  # Branco
PRIMARY_COLOR = (0.2, 0.5, 0.8, 1)  # Azul
SECONDARY_COLOR = (0.8, 0.8, 0.8, 1) # Cinza para botões
SUCCESS_COLOR = (0.16, 0.65, 0.32, 1) # Verde para sucesso
ACCENT_COLOR = (0.9, 0.3, 0.3, 1) # Vermelho para destaque
TEXT_COLOR_DARK = (0.2, 0.2, 0.2, 1) # Texto escuro
TEXT_COLOR_LIGHT = (0.5, 0.5, 0.5, 1) # Texto claro

# Configura a cor de fundo da janela
Window.clearcolor = BG_COLOR

# Função auxiliar para exibir balão de alerta
def show_popup(title, message, is_success=True):
    popup = Popup(
        title=title,
        content=Label(text=message, halign='center', valign='middle', color=TEXT_COLOR_DARK),
        size_hint=(0.8, 0.2)
    )
    popup.open()

class RoundedButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        with self.canvas.before:
            self.rect_color = Color(self.background_color[0], self.background_color[1], self.background_color[2], self.background_color[3])
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[dp(10)])
            self.bind(pos=self.update_rect, size=self.update_rect)
            
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_press(self):
        self.rect_color.a = 0.7 
    
    def on_release(self):
        self.rect_color.a = 1.0

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
        
        cancel_btn = RoundedButton(text='Cancelar', background_color=SECONDARY_COLOR, color=TEXT_COLOR_DARK)
        confirm_btn = RoundedButton(text='Confirmar Edição', background_color=PRIMARY_COLOR, color=(1, 1, 1, 1))
        
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

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        root_layout = BoxLayout(
            orientation='vertical',
            padding=dp(25), 
            spacing=dp(20)
        )
        
        # Adiciona o logo
        logo = Image(source='assets/logo.png', size_hint_y=None, height=dp(80))
        root_layout.add_widget(logo)
        
        # Seção de valores dentro de um card
        values_card = BoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(10),
            size_hint_y=None,
            height=dp(200)
        )
        with values_card.canvas.before:
            Color(CARD_BG_COLOR[0], CARD_BG_COLOR[1], CARD_BG_COLOR[2], CARD_BG_COLOR[3])
            self.values_card_rect = RoundedRectangle(size=values_card.size, pos=values_card.pos, radius=[dp(15)])
            values_card.bind(pos=self.update_card_rect, size=self.update_card_rect)
        
        values_card.add_widget(Label(text='VALOR TOTAL DO IMÓVEL', font_size='16sp', bold=True, color=TEXT_COLOR_DARK))
        values_card.add_widget(Label(text='R$ 280.000,00', font_size='24sp', bold=True, color=PRIMARY_COLOR))
        self.total_paid_label = Label(text='Total Pago: R$ 0,00', font_size='16sp', color=TEXT_COLOR_LIGHT)
        values_card.add_widget(self.total_paid_label)
        self.remaining_amount_label = Label(text='Valor Restante: R$ 0,00', font_size='22sp', bold=True, color=ACCENT_COLOR)
        values_card.add_widget(self.remaining_amount_label)
        
        root_layout.add_widget(values_card)

        # Seção para adicionar pagamento
        input_card = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15), size_hint_y=None, height=dp(200))
        with input_card.canvas.before:
            Color(CARD_BG_COLOR[0], CARD_BG_COLOR[1], CARD_BG_COLOR[2], CARD_BG_COLOR[3])
            self.input_card_rect = RoundedRectangle(size=input_card.size, pos=input_card.pos, radius=[dp(15)])
            input_card.bind(pos=self.update_input_card_rect, size=self.update_input_card_rect)

        input_card.add_widget(Label(text='ADICIONAR NOVO PAGAMENTO', font_size='16sp', bold=True, color=TEXT_COLOR_DARK))
        
        self.name_input = TextInput(hint_text='Nome do Pagador', multiline=False, size_hint_y=None, height=dp(45), font_size='16sp', padding=dp(10), background_color=(1, 1, 1, 1), foreground_color=TEXT_COLOR_DARK, cursor_color=PRIMARY_COLOR, hint_text_color=TEXT_COLOR_LIGHT)
        input_card.add_widget(self.name_input)

        self.value_input = TextInput(hint_text='Valor (ex: 10000.00)', multiline=False, input_type='number', size_hint_y=None, height=dp(45), font_size='16sp', padding=dp(10), background_color=(1, 1, 1, 1), foreground_color=TEXT_COLOR_DARK, cursor_color=PRIMARY_COLOR, hint_text_color=TEXT_COLOR_LIGHT)
        input_card.add_widget(self.value_input)
        
        root_layout.add_widget(input_card)
        
        self.add_button = RoundedButton(text='Registrar Pagamento', size_hint_y=None, height=dp(50), font_size='18sp', background_color=SUCCESS_COLOR, color=(1, 1, 1, 1))
        self.add_button.bind(on_press=self.register_payment_thread)
        root_layout.add_widget(self.add_button)

        # Layout para os dois botões na parte inferior
        button_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10)
        )

        payments_button = RoundedButton(text='Ver Pagamentos', size_hint_y=1, font_size='18sp', background_color=PRIMARY_COLOR, color=(1, 1, 1, 1))
        payments_button.bind(on_press=self.go_to_payments_screen)
        
        contract_button = RoundedButton(text='Contrato', size_hint_y=1, font_size='18sp', background_color=SECONDARY_COLOR, color=TEXT_COLOR_DARK)
        contract_button.bind(on_press=self.go_to_contract_screen)

        button_layout.add_widget(payments_button)
        button_layout.add_widget(contract_button)
        
        root_layout.add_widget(button_layout)

        self.add_widget(root_layout)

    def update_card_rect(self, instance, value):
        self.values_card_rect.pos = instance.pos
        self.values_card_rect.size = instance.size
        
    def update_input_card_rect(self, instance, value):
        self.input_card_rect.pos = instance.pos
        self.input_card_rect.size = instance.size

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
        show_popup("Sucesso", message, is_success=True)

    def go_to_payments_screen(self, instance):
        self.manager.current = 'payments'
    
    def go_to_contract_screen(self, instance):
        self.manager.current = 'contract'

class PaymentsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        root_layout = BoxLayout(
            orientation='vertical',
            padding=dp(10),
            spacing=dp(10)
        )
        
        # Cabeçalho com o botão Voltar
        header = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10),
            padding=(dp(10), 0)
        )
        self.back_button = RoundedButton(
            text='Voltar',
            size_hint_x=0.2,
            background_color=SECONDARY_COLOR,
            color=TEXT_COLOR_DARK
        )
        self.back_button.bind(on_press=self.go_back)
        header.add_widget(self.back_button)
        
        header.add_widget(Label(
            text='Histórico de Pagamentos',
            font_size='22sp',
            bold=True,
            size_hint_x=0.8,
            color=TEXT_COLOR_DARK
        ))
        
        root_layout.add_widget(header)

        # Cabeçalho da tabela de pagamentos
        table_header = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            padding=(dp(20), 0),
            spacing=dp(10)
        )
        table_header.add_widget(Label(text='Nome', font_size='16sp', bold=True, color=TEXT_COLOR_DARK, halign='left', valign='middle', size_hint_x=0.4))
        table_header.add_widget(Label(text='Valor', font_size='16sp', bold=True, color=TEXT_COLOR_DARK, halign='right', valign='middle', size_hint_x=0.3))
        table_header.add_widget(Label(text='Data', font_size='16sp', bold=True, color=TEXT_COLOR_DARK, halign='right', valign='middle', size_hint_x=0.3))
        # Widget para alinhar com os botões de ação
        table_header.add_widget(Widget(size_hint_x=0.2, width=dp(50))) 
        root_layout.add_widget(table_header)
        
        # ScrollView para a lista de pagamentos
        self.scroll_view = ScrollView()
        self.payments_list_container = BoxLayout(
            orientation='vertical',
            spacing=dp(10),
            size_hint_y=None,
            padding=dp(10)
        )
        self.payments_list_container.bind(minimum_height=self.payments_list_container.setter('height'))
        self.scroll_view.add_widget(self.payments_list_container)
        
        root_layout.add_widget(self.scroll_view)
        self.add_widget(root_layout)
        
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
        self.payments_list_container.add_widget(Label(text="Carregando...", size_hint_y=None, height=dp(40), color=TEXT_COLOR_LIGHT))
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
            self.payments_list_container.add_widget(Label(text="Nenhum pagamento registrado.", color=TEXT_COLOR_LIGHT))
        else:
            for p in pagamentos:
                data_formatada = p['data'].split('T')[0]
                valor_formatado = f"R$ {p['valor']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                
                # Container para o item da lista com fundo de card
                list_item_container = BoxLayout(
                    orientation='horizontal',
                    size_hint_y=None,
                    height=dp(60),
                    padding=(dp(15), dp(10)),
                    spacing=dp(10)
                )

                # Cria um retângulo arredondado para o fundo
                with list_item_container.canvas.before:
                    Color(CARD_BG_COLOR[0], CARD_BG_COLOR[1], CARD_BG_COLOR[2], CARD_BG_COLOR[3])
                    self.rect = RoundedRectangle(size=list_item_container.size, pos=list_item_container.pos, radius=[dp(15)])
                
                list_item_container.bind(pos=self.update_rect, size=self.update_rect)

                # Layout interno para os detalhes do pagamento e botões
                
                name_label = Label(
                    text=p['nome_pagador'],
                    font_size='16sp',
                    bold=True,
                    color=TEXT_COLOR_DARK,
                    halign='left',
                    valign='middle',
                    text_size=(self.scroll_view.width * 0.4, None),
                    size_hint_x=0.4
                )
                value_label = Label(
                    text=valor_formatado,
                    font_size='14sp',
                    color=SUCCESS_COLOR,
                    bold=True,
                    halign='center',
                    valign='middle',
                    size_hint_x=0.25
                )
                date_label = Label(
                    text=data_formatada,
                    font_size='14sp',
                    color=TEXT_COLOR_LIGHT,
                    halign='center',
                    valign='middle',
                    size_hint_x=0.25
                )
                
                buttons_layout = BoxLayout(
                    orientation='horizontal',
                    size_hint_x=0.1,
                    spacing=dp(5)
                )
                
                edit_btn = RoundedButton(text='E', background_color=PRIMARY_COLOR, color=(1,1,1,1))
                edit_btn.bind(on_press=lambda btn, p_id=p['id'], p_nome=p['nome_pagador'], p_valor=p['valor']: self.show_edit_popup(p_id, p_nome, p_valor))
                
                delete_btn = RoundedButton(text='X', background_color=ACCENT_COLOR, color=(1,1,1,1))
                delete_btn.bind(on_press=lambda btn, id=p['id']: self.show_admin_password_popup(id))
                
                buttons_layout.add_widget(edit_btn)
                buttons_layout.add_widget(delete_btn)
                
                list_item_container.add_widget(name_label)
                list_item_container.add_widget(value_label)
                list_item_container.add_widget(date_label)
                list_item_container.add_widget(buttons_layout)
                
                self.payments_list_container.add_widget(list_item_container)
    
    def update_rect(self, instance, value):
        instance.canvas.before.children[-1].pos = instance.pos
        instance.canvas.before.children[-1].size = instance.size

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
        
        cancel_btn = RoundedButton(text='Cancelar', background_color=SECONDARY_COLOR, color=TEXT_COLOR_DARK)
        confirm_btn = RoundedButton(text='Confirmar', background_color=ACCENT_COLOR, color=(1, 1, 1, 1))
        
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

class NewContractScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root_layout = BoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(20)
        )
        
        header = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50)
        )
        
        back_button = RoundedButton(
            text='Voltar',
            size_hint_x=0.2,
            background_color=SECONDARY_COLOR,
            color=TEXT_COLOR_DARK
        )
        back_button.bind(on_press=self.go_back)
        header.add_widget(back_button)
        header.add_widget(Label(text='Novo Contrato', font_size='22sp', bold=True, color=TEXT_COLOR_DARK, size_hint_x=0.8))

        root_layout.add_widget(header)
        
        self.scroll_view = ScrollView()
        
        self.input_container = GridLayout(
            cols=1,
            spacing=dp(10),
            size_hint_y=None,
            padding=dp(10)
        )
        self.input_container.bind(minimum_height=self.input_container.setter('height'))
        
        self.create_input_fields()
        
        self.scroll_view.add_widget(self.input_container)
        root_layout.add_widget(self.scroll_view)

        generate_button = RoundedButton(
            text='Gerar Contrato',
            size_hint_y=None,
            height=dp(50),
            font_size='18sp',
            background_color=PRIMARY_COLOR
        )
        generate_button.bind(on_press=self.generate_contract)
        root_layout.add_widget(generate_button)

        self.add_widget(root_layout)
        
    def add_input(self, label_text, **kwargs):
        box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(70), spacing=dp(5))
        # Ajustado para alinhar o texto do Label à esquerda
        box.add_widget(Label(text=label_text, halign='left', valign='bottom', size_hint_y=None, height=dp(20), text_size=(Window.width - dp(40), None), color=TEXT_COLOR_DARK))
        text_input = TextInput(multiline=kwargs.get('multiline', False), size_hint_y=None, height=dp(40), background_color=CARD_BG_COLOR, foreground_color=TEXT_COLOR_DARK, hint_text=label_text)
        box.add_widget(text_input)
        self.input_container.add_widget(box)
        return text_input

    def add_section_title(self, title_text):
        self.input_container.add_widget(Label(text=title_text, font_size='16sp', bold=True, size_hint_y=None, height=dp(30), color=PRIMARY_COLOR))


    def create_input_fields(self):
        # Campos do Vendedor
        self.add_section_title('DADOS DO VENDEDOR')
        self.vendedor_nome = self.add_input('Nome:')
        self.vendedor_nacionalidade = self.add_input('Nacionalidade:')
        self.vendedor_profissao = self.add_input('Profissão:')
        self.vendedor_estado_civil = self.add_input('Estado Civil:')
        self.vendedor_rg = self.add_input('RG:')
        self.vendedor_cpf = self.add_input('CPF:')
        self.vendedor_rua = self.add_input('Rua:')
        self.vendedor_numero = self.add_input('Número:')
        self.vendedor_bairro = self.add_input('Bairro:')
        self.vendedor_estado = self.add_input('Estado:')
        
        # Campos do Comprador
        self.add_section_title('DADOS DO COMPRADOR')
        self.comprador_nome = self.add_input('Nome:')
        self.comprador_nacionalidade = self.add_input('Nacionalidade:')
        self.comprador_profissao = self.add_input('Profissão:')
        self.comprador_estado_civil = self.add_input('Estado Civil:')
        self.comprador_rg = self.add_input('RG:')
        self.comprador_cpf = self.add_input('CPF:')
        self.comprador_rua = self.add_input('Rua:')
        self.comprador_numero = self.add_input('Número:')
        self.comprador_bairro = self.add_input('Bairro:')
        self.comprador_estado = self.add_input('Estado:')

        # Campos do Imóvel
        self.add_section_title('DADOS DO IMÓVEL')
        self.imovel_rua = self.add_input('Rua do Imóvel:')
        self.imovel_numero = self.add_input('Número do Imóvel:')
        self.imovel_bairro = self.add_input('Bairro do Imóvel:')
        self.imovel_estado = self.add_input('Estado do Imóvel:')
        self.imovel_descricao = self.add_input('Descrição Completa do Imóvel:', multiline=True)
        self.imovel_aquisicao = self.add_input('Forma de Aquisição:')
        self.imovel_registro = self.add_input('Registro do Imóvel:')
        self.imovel_matricula = self.add_input('Matrícula do Imóvel:')

        # Campos de Valores
        self.add_section_title('VALORES E PAGAMENTOS')
        self.valor_total = self.add_input('Valor Total (R$):', input_type='number')
        self.sinal = self.add_input('Valor do Sinal (R$):', input_type='number')
        self.cheque_sinal = self.add_input('Cheque do Sinal:')
        self.banco_sinal = self.add_input('Banco do Sinal:')
        self.valor_parcela_1 = self.add_input('Valor 1ª Parcela (R$):', input_type='number')
        self.data_parcela_1 = self.add_input('Data 1ª Parcela (DD/MM/AAAA):')
        self.saldo_restante = self.add_input('Saldo Restante (R$):', input_type='number')
        self.data_lavratura_escritura = self.add_input('Data Lavratura Escritura (DD/MM/AAAA):')
        self.porcentagem_multa = self.add_input('Multa (%):', input_type='number')
        self.indice_reajuste = self.add_input('Índice de Reajuste:')
        self.data_transferencia_posse = self.add_input('Data Transferência Posse (DD/MM/AAAA):')
        self.aluguel_diario = self.add_input('Aluguel Diário (R$):', input_type='number')
        self.local_assinatura = self.add_input('Local de Assinatura:')
        self.data_assinatura = self.add_input('Data da Assinatura (DD/MM/AAAA):')
        self.foro = self.add_input('Foro:')

    def generate_contract(self, instance):
        try:
            # Coleta os dados dos campos de entrada
            dados_contrato = {
                "vendedor_nome": self.vendedor_nome.text,
                "vendedor_nacionalidade": self.vendedor_nacionalidade.text,
                "vendedor_profissao": self.vendedor_profissao.text,
                "vendedor_estado_civil": self.vendedor_estado_civil.text,
                "vendedor_rg": self.vendedor_rg.text,
                "vendedor_cpf": self.vendedor_cpf.text,
                "vendedor_rua": self.vendedor_rua.text,
                "vendedor_numero": self.vendedor_numero.text,
                "vendedor_bairro": self.vendedor_bairro.text,
                "vendedor_estado": self.vendedor_estado.text,
                "comprador_nome": self.comprador_nome.text,
                "comprador_nacionalidade": self.comprador_nacionalidade.text,
                "comprador_profissao": self.comprador_profissao.text,
                "comprador_estado_civil": self.comprador_estado_civil.text,
                "comprador_rg": self.comprador_rg.text,
                "comprador_cpf": self.comprador_cpf.text,
                "comprador_rua": self.comprador_rua.text,
                "comprador_numero": self.comprador_numero.text,
                "comprador_bairro": self.comprador_bairro.text,
                "comprador_estado": self.comprador_estado.text,
                "imovel_rua": self.imovel_rua.text,
                "imovel_numero": self.imovel_numero.text,
                "imovel_bairro": self.imovel_bairro.text,
                "imovel_estado": self.imovel_estado.text,
                "imovel_descricao": self.imovel_descricao.text,
                "imovel_aquisicao": self.imovel_aquisicao.text,
                "imovel_registro": self.imovel_registro.text,
                "imovel_matricula": self.imovel_matricula.text,
                "valor_total": self.valor_total.text,
                "valor_total_extenso": self.number_to_words(self.valor_total.text),
                "sinal": self.sinal.text,
                "sinal_extenso": self.number_to_words(self.sinal.text),
                "cheque_sinal": self.cheque_sinal.text,
                "banco_sinal": self.banco_sinal.text,
                "valor_parcela_1": self.valor_parcela_1.text,
                "valor_parcela_1_extenso": self.number_to_words(self.valor_parcela_1.text),
                "data_parcela_1": self.data_parcela_1.text,
                "saldo_restante": self.saldo_restante.text,
                "saldo_restante_extenso": self.number_to_words(self.saldo_restante.text),
                "data_lavratura_escritura": self.data_lavratura_escritura.text,
                "porcentagem_multa": self.porcentagem_multa.text,
                "porcentagem_multa_extenso": self.number_to_words(self.porcentagem_multa.text),
                "indice_reajuste": self.indice_reajuste.text,
                "data_transferencia_posse": self.data_transferencia_posse.text,
                "aluguel_diario": self.aluguel_diario.text,
                "aluguel_diario_extenso": self.number_to_words(self.aluguel_diario.text),
                "local_assinatura": self.local_assinatura.text,
                "dia_assinatura": self.data_assinatura.text.split('/')[0] if self.data_assinatura.text else '',
                "mes_assinatura": self.data_assinatura.text.split('/')[1] if self.data_assinatura.text else '',
                "ano_assinatura": self.data_assinatura.text.split('/')[2] if self.data_assinatura.text else '',
                "foro": self.foro.text
            }

            contrato_gerado = CONTRATO_TEMPLATE.format(**dados_contrato)
            self.manager.get_screen('contract').update_contract_text(contrato_gerado)
            self.manager.current = 'contract'
            show_popup("Sucesso", "Contrato gerado com sucesso!")

        except KeyError as e:
            show_popup("Erro", f"Campo ausente no template: {e}. Verifique se todos os campos foram preenchidos.")
        except Exception as e:
            show_popup("Erro", f"Ocorreu um erro: {e}")
            
    def number_to_words(self, number_str):
        # Esta é uma função placeholder. Para a implementação real,
        # você precisaria de uma biblioteca como `num2words` ou uma função personalizada.
        # Por exemplo: `from num2words import num2words; return num2words(float(number_str), lang='pt_BR')`
        try:
            return str(float(number_str))
        except (ValueError, TypeError):
            return ""

    def go_back(self, instance):
        self.manager.current = 'contract'

class ContractScreen(Screen):
    # A propriedade deve ser definida aqui, fora de __init__
    contract_text = StringProperty(CONTRATO_TEMPLATE)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root_layout = BoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(20)
        )

        header = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50)
        )

        back_button = RoundedButton(
            text='Voltar',
            size_hint_x=0.2,
            background_color=SECONDARY_COLOR,
            color=TEXT_COLOR_DARK
        )
        back_button.bind(on_press=self.go_back)
        header.add_widget(back_button)
        header.add_widget(Label(text='Contrato de Compra', font_size='22sp', bold=True, color=TEXT_COLOR_DARK, size_hint_x=0.8))
        
        root_layout.add_widget(header)

        # ScrollView para o conteúdo do contrato
        self.scroll_view = ScrollView()
        
        contract_content_layout = BoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(15),
            size_hint_y=None
        )
        contract_content_layout.bind(minimum_height=contract_content_layout.setter('height'))

        # Adicionando um Label para exibir o contrato
        self.contract_label = Label(
            font_size='14sp',
            halign='left',
            valign='top',
            color=TEXT_COLOR_DARK,
            text_size=(Window.width - dp(40), None),
            size_hint_y=None
        )

        # Vincule a propriedade de texto do Label à sua StringProperty
        # A propriedade 'contract_text' agora existe quando este bind é chamado
        self.bind(contract_text=self.contract_label.setter('text'))
        self.contract_label.bind(texture_size=self.contract_label.setter('size'))

        contract_content_layout.add_widget(self.contract_label)
        self.scroll_view.add_widget(contract_content_layout)
        root_layout.add_widget(self.scroll_view)

        # Botões para Criar Contrato e Gerar PDF
        button_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10)
        )
        
        create_new_button = RoundedButton(text='Criar Novo Contrato', background_color=PRIMARY_COLOR)
        create_new_button.bind(on_press=self.go_to_new_contract_screen)
        
        generate_pdf_button = RoundedButton(text='Gerar PDF', background_color=SUCCESS_COLOR)
        # Note: Esta funcionalidade precisa de bibliotecas adicionais, por isso é um placeholder.
        # generate_pdf_button.bind(on_press=self.generate_pdf)

        button_layout.add_widget(create_new_button)
        button_layout.add_widget(generate_pdf_button)
        root_layout.add_widget(button_layout)
        self.add_widget(root_layout)
        
    def update_contract_text(self, new_text):
        self.contract_text = new_text

    def go_to_new_contract_screen(self, instance):
        self.manager.current = 'new_contract'

    def go_back(self, instance):
        self.manager.current = 'main'

class CompraFirmeApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(PaymentsScreen(name='payments'))
        sm.add_widget(ContractScreen(name='contract'))
        sm.add_widget(NewContractScreen(name='new_contract'))
        return sm

if __name__ == '__main__':
    CompraFirmeApp().run()