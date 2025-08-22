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
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, RoundedRectangle
import requests
import re
from threading import Thread
from os.path import exists

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

# Stubs para as classes que faltam, para evitar o erro de 'not defined'
# Você precisará preencher a lógica dessas classes.
class EditPaymentPopup(Popup):
    def __init__(self, payment_id, name, value, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Editar Pagamento'
        self.size_hint = (0.9, 0.5)
        self.payment_id = payment_id
        
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        
        self.name_input = TextInput(text=name, multiline=False, size_hint_y=None, height=dp(45))
        self.value_input = TextInput(text=str(value), multiline=False, input_type='number', size_hint_y=None, height=dp(45))
        
        button_layout = BoxLayout(spacing=dp(10))
        confirm_button = Button(text='Salvar', on_press=self.confirm_edit)
        cancel_button = Button(text='Cancelar', on_press=self.dismiss)
        button_layout.add_widget(confirm_button)
        button_layout.add_widget(cancel_button)
        
        content.add_widget(self.name_input)
        content.add_widget(self.value_input)
        content.add_widget(button_layout)
        
        self.content = content
    
    def confirm_edit(self, instance):
        # Implementar a lógica para enviar a requisição PUT para o servidor
        # e fechar o popup
        self.dismiss()

class AdminPasswordPopup(Popup):
    def __init__(self, payment_id, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Excluir Pagamento'
        self.size_hint = (0.9, 0.4)
        self.payment_id = payment_id
        
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        content.add_widget(Label(text='Insira a senha de administrador para excluir:', size_hint_y=None, height=dp(30)))
        
        self.password_input = TextInput(password=True, multiline=False, size_hint_y=None, height=dp(45))
        
        button_layout = BoxLayout(spacing=dp(10))
        confirm_button = Button(text='Confirmar', on_press=self.confirm_delete)
        cancel_button = Button(text='Cancelar', on_press=self.dismiss)
        button_layout.add_widget(confirm_button)
        button_layout.add_widget(cancel_button)
        
        content.add_widget(self.password_input)
        content.add_widget(button_layout)
        
        self.content = content
    
    def confirm_delete(self, instance):
        # Implementar a lógica para verificar a senha e enviar a requisição DELETE
        # para o servidor, e fechar o popup.
        self.dismiss()

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

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        root_layout = BoxLayout(
            orientation='vertical',
            padding=dp(25), 
            spacing=dp(20)
        )
        
        logo = Image(source='assets/logo.png', size_hint_y=None, height=dp(80))
        root_layout.add_widget(logo)
        
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

        input_card = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15), size_hint_y=None, height=dp(200))
        with input_card.canvas.before:
            Color(CARD_BG_COLOR[0], CARD_BG_COLOR[1], CARD_BG_COLOR[2], CARD_BG_COLOR[3])
            self.input_card_rect = RoundedRectangle(size=input_card.size, pos=input_card.pos, radius=[dp(15)])
            input_card.bind(pos=self.update_input_card_rect, size=self.update_input_card_rect)

        input_card.add_widget(Label(text='ADICIONAR NOVO PAGAMENTO', font_size='16sp', bold=True, color=TEXT_COLOR_DARK))
        
        self.name_input = TextInput(hint_text='Ex: João da Silva', multiline=False, size_hint_y=None, height=dp(45), font_size='16sp', padding=dp(10), background_color=(1, 1, 1, 1), foreground_color=TEXT_COLOR_DARK, cursor_color=PRIMARY_COLOR, hint_text_color=TEXT_COLOR_LIGHT)
        input_card.add_widget(self.name_input)

        self.value_input = TextInput(hint_text='Ex: 10000.00', multiline=False, input_type='number', size_hint_y=None, height=dp(45), font_size='16sp', padding=dp(10), background_color=(1, 1, 1, 1), foreground_color=TEXT_COLOR_DARK, cursor_color=PRIMARY_COLOR, hint_text_color=TEXT_COLOR_LIGHT)
        input_card.add_widget(self.value_input)
        
        root_layout.add_widget(input_card)
        
        self.add_button = RoundedButton(text='Registrar Pagamento', size_hint_y=None, height=dp(50), font_size='18sp', background_color=SUCCESS_COLOR, color=(1, 1, 1, 1))
        self.add_button.bind(on_press=self.register_payment_thread)
        root_layout.add_widget(self.add_button)

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

    def go_to_contract_screen(self, instance):
        self.manager.current = 'contract'

    def update_card_rect(self, instance, value):
        self.values_card_rect.pos = instance.pos
        self.values_card_rect.size = instance.size
        
    def update_input_card_rect(self, instance, value):
        self.input_card_rect.pos = instance.pos
        self.input_card_rect.size = instance.size

    def on_enter(self, *args):
        self.update_values_thread()

    def update_values_thread(self, instance=None):
        Thread(target=self.update_values).start()

    def update_values(self):
        try:
            total_paid_response = requests.get(f"http://127.0.0.1:5000/total_paid")
            if total_paid_response.status_code == 200:
                total_pago = total_paid_response.json().get('total', 0)
                valor_restante = 280000 - total_pago
                self.update_ui_labels(total_pago, valor_restante)
            else:
                self.update_ui_labels_error(f"Erro ao carregar dados. Status: {total_paid_response.status_code}")
        except requests.exceptions.RequestException:
            self.update_ui_labels_error("Erro de conexão com o servidor.")

    @kivy.clock.mainthread
    def update_ui_labels(self, total_pago, valor_restante):
        self.total_paid_label.text = f'Total Pago: R$ {total_pago:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        self.remaining_amount_label.text = f'Valor Restante: R$ {valor_restante:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    @kivy.clock.mainthread
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
            response = requests.post(f"http://127.0.0.1:5000/add_payment", json=payload)
            
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

    @kivy.clock.mainthread
    def show_message_on_main_thread(self, message):
        show_popup("Aviso", message)

    @kivy.clock.mainthread
    def clear_inputs_and_show_message_on_main_thread(self, message):
        self.name_input.text = ''
        self.value_input.text = ''
        show_popup("Sucesso", message, is_success=True)

    def go_to_payments_screen(self, instance):
        self.manager.current = 'payments'

class PaymentsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        root_layout = BoxLayout(
            orientation='vertical',
            padding=dp(10),
            spacing=dp(10)
        )
        
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

        table_header = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            padding=(dp(20), 0),
            spacing=dp(10)
        )
        table_header.add_widget(Label(text='Nome', font_size='16sp', bold=True, color=TEXT_COLOR_DARK, halign='left', valign='middle', size_hint_x=0.4))
        table_header.add_widget(Label(text='Valor', font_size='16sp', bold=True, color=TEXT_COLOR_DARK, halign='center', valign='middle', size_hint_x=0.25))
        table_header.add_widget(Label(text='Data', font_size='16sp', bold=True, color=TEXT_COLOR_DARK, halign='center', valign='middle', size_hint_x=0.25))
        table_header.add_widget(Widget(size_hint_x=0.2)) 
        root_layout.add_widget(table_header)
        
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
        self.update_event = kivy.clock.Clock.schedule_interval(self.load_payments, 10)
        
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
            response = requests.get(f"http://127.0.0.1:5000/payments")
            if response.status_code == 200:
                pagamentos = response.json()
                self.populate_list_on_main_thread(pagamentos)
            else:
                self.add_message_on_main_thread("Erro ao carregar pagamentos.")
        except requests.exceptions.RequestException:
            self.add_message_on_main_thread("Erro de conexão com o servidor.")
            
    @kivy.clock.mainthread
    def populate_list_on_main_thread(self, pagamentos):
        self.payments_list_container.clear_widgets()
        if not pagamentos:
            self.payments_list_container.add_widget(Label(text="Nenhum pagamento registrado.", color=TEXT_COLOR_LIGHT))
        else:
            for p in pagamentos:
                data_formatada = p['data'].split('T')[0]
                valor_formatado = f"R$ {p['valor']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                
                list_item_container = BoxLayout(
                    orientation='horizontal',
                    size_hint_y=None,
                    height=dp(60),
                    padding=(dp(15), dp(10)),
                    spacing=dp(10)
                )

                with list_item_container.canvas.before:
                    Color(CARD_BG_COLOR[0], CARD_BG_COLOR[1], CARD_BG_COLOR[2], CARD_BG_COLOR[3])
                    self.rect = RoundedRectangle(size=list_item_container.size, pos=list_item_container.pos, radius=[dp(15)])
                
                list_item_container.bind(pos=self.update_rect, size=self.update_rect)
                
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

    def go_back(self, instance):
        self.manager.current = 'main'

    def show_edit_popup(self, payment_id, name, value):
        EditPaymentPopup(payment_id, name, value).open()

    def show_admin_password_popup(self, payment_id):
        AdminPasswordPopup(payment_id).open()

class ContractScreen(Screen):
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
        
        self.scroll_view = ScrollView()
        
        contract_content_layout = BoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(15),
            size_hint_y=None,
            height=self.scroll_view.height
        )
        contract_content_layout.bind(minimum_height=contract_content_layout.setter('height'))
        
        self.contract_images = []
        
        self.scroll_view.add_widget(contract_content_layout)
        root_layout.add_widget(self.scroll_view)
        
        self.add_widget(root_layout)

    def on_enter(self, *args):
        self.load_contract_images()

    def load_contract_images(self):
        self.scroll_view.children[0].clear_widgets()
        
        page_number = 1
        found_images = False
        while True:
            image_path = f'assets/contrato_pagina_{page_number}.jpg' # ALTERADO para .jpg
            if exists(image_path):
                found_images = True
                image_widget = Image(source=image_path, size_hint_y=None, allow_stretch=True)
                image_widget.bind(texture_size=image_widget.setter('size'))
                self.scroll_view.children[0].add_widget(image_widget)
                page_number += 1
            else:
                if not found_images:
                    self.scroll_view.children[0].add_widget(Label(text="Nenhuma página do contrato encontrada. Por favor, adicione as imagens na pasta 'assets' (ex: 'contrato_pagina_1.jpg').",
                                                                 halign='center', valign='middle', text_size=(Window.width - dp(40), None), color=TEXT_COLOR_LIGHT))
                break

    def go_back(self, instance):
        self.manager.current = 'main'

class CompraFirmeApp(App):
    def build(self):
        sm = ScreenManager()
        sm.app = self
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(PaymentsScreen(name='payments'))
        sm.add_widget(ContractScreen(name='contract'))
        return sm

if __name__ == '__main__':
    CompraFirmeApp().run()