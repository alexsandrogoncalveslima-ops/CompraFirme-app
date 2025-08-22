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

class EditPaymentPopup(Popup):
    def __init__(self, payment_id, nome, valor, callback, **kwargs):
        super().__init__(**kwargs)
        self.payment_id = payment_id
        self.callback = callback
        self.title = 'Editar Pagamento'
        self.size_hint = (0.8, 0.6)
        
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Campo para o nome
        layout.add_widget(Label(text='Nome do Pagador', halign='left', text_size=(self.width, None), color=TEXT_COLOR_DARK))
        self.name_input = TextInput(
            text=nome,
            multiline=False,
            size_hint_y=None,
            height=dp(40)
        )
        layout.add_widget(self.name_input)
        
        # Campo para o valor
        layout.add_widget(Label(text='Valor', halign='left', text_size=(self.width, None), color=TEXT_COLOR_DARK))
        self.value_input = TextInput(
            text=str(valor),
            multiline=False,
            input_type='number',
            size_hint_y=None,
            height=dp(40)
        )
        layout.add_widget(self.value_input)
        
        # Campo para a senha do admin
        layout.add_widget(Label(text='Senha de Administrador', halign='left', text_size=(self.width, None), color=TEXT_COLOR_DARK))
        self.password_input = TextInput(
            password=True,
            multiline=False,
            size_hint_y=None,
            height=dp(40)
        )
        layout.add_widget(self.password_input)
        
        # Botões
        buttons_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(40))
        cancel_button = RoundedButton(text='Cancelar', background_color=SECONDARY_COLOR, color=TEXT_COLOR_DARK)
        save_button = RoundedButton(text='Salvar', background_color=SUCCESS_COLOR)
        
        buttons_layout.add_widget(cancel_button)
        buttons_layout.add_widget(save_button)
        
        layout.add_widget(buttons_layout)
        
        cancel_button.bind(on_press=self.dismiss)
        save_button.bind(on_press=self.save_and_dismiss)
        
        self.content = layout

    def save_and_dismiss(self, instance):
        new_nome = self.name_input.text.strip()
        new_valor = self.value_input.text.strip()
        password = self.password_input.text.strip()
        
        if not new_nome or not new_valor or not password:
            show_popup("Erro", "Preencha todos os campos.")
            return

        try:
            float(new_valor)
        except ValueError:
            show_popup("Erro", "Valor inválido.")
            return

        self.callback(self.payment_id, new_nome, new_valor, password)
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

class WizardScreen(Screen):
    """Classe base para as telas do wizard de contrato."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(20)
        )
        self.add_widget(self.layout)
    
    def build_header(self, title_text, step_text):
        header_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50)
        )
        
        # O botão Voltar só aparece nas telas intermediárias
        if self.name in ['comprador_form', 'vendedor_form', 'contrato_resumo']:
            back_button = RoundedButton(
                text='Voltar',
                size_hint_x=0.2,
                background_color=SECONDARY_COLOR,
                color=TEXT_COLOR_DARK
            )
            back_button.bind(on_press=self.go_back)
            header_layout.add_widget(back_button)
        
        header_layout.add_widget(Label(
            text=f'Etapa {step_text}',
            font_size='18sp',
            color=TEXT_COLOR_LIGHT,
            halign='right',
            valign='middle',
            size_hint_x=0.2
        ))
        
        header_layout.add_widget(Label(
            text=title_text,
            font_size='22sp',
            bold=True,
            color=TEXT_COLOR_DARK,
            halign='left',
            valign='middle',
            size_hint_x=0.6
        ))
        
        self.layout.add_widget(header_layout, index=len(self.layout.children))
        
    def add_input_field(self, label_text, hint_text='', **kwargs):
        box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(70), spacing=dp(5))
        box.add_widget(Label(
            text=label_text,
            halign='left',
            valign='bottom',
            size_hint_y=None,
            height=dp(20),
            text_size=(Window.width - dp(40), None),
            color=TEXT_COLOR_DARK
        ))
        text_input = TextInput(
            multiline=kwargs.get('multiline', False),
            size_hint_y=None,
            height=dp(40),
            background_color=CARD_BG_COLOR,
            foreground_color=TEXT_COLOR_DARK,
            hint_text=hint_text
        )
        box.add_widget(text_input)
        return box, text_input

    def validate_fields(self):
        # Validação simples
        for field in self.fields:
            if not field.text.strip():
                show_popup("Erro de Validação", "Por favor, preencha todos os campos.", is_success=False)
                return False
        return True

    def go_back(self, instance):
        self.manager.current = 'contrato_resumo' if self.name == 'new_contract' else self.manager.previous()

class ImovelFormScreen(WizardScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_header('Dados do Imóvel', '1/4')
        
        content_layout = BoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(15),
            size_hint_y=None
        )
        with content_layout.canvas.before:
            Color(CARD_BG_COLOR[0], CARD_BG_COLOR[1], CARD_BG_COLOR[2], CARD_BG_COLOR[3])
            self.rect = RoundedRectangle(size=content_layout.size, pos=content_layout.pos, radius=[dp(15)])
            content_layout.bind(pos=self.update_rect, size=self.update_rect)
        
        self.imovel_rua = TextInput(hint_text='Rua do Imóvel', multiline=False, size_hint_y=None, height=dp(45))
        self.imovel_numero = TextInput(hint_text='Número do Imóvel', multiline=False, size_hint_y=None, height=dp(45))
        self.imovel_bairro = TextInput(hint_text='Bairro do Imóvel', multiline=False, size_hint_y=None, height=dp(45))
        self.imovel_cidade = TextInput(hint_text='Cidade do Imóvel', multiline=False, size_hint_y=None, height=dp(45))
        self.imovel_estado = TextInput(hint_text='Estado do Imóvel (Ex: MG)', multiline=False, size_hint_y=None, height=dp(45))
        self.imovel_cep = TextInput(hint_text='CEP do Imóvel', multiline=False, size_hint_y=None, height=dp(45))
        
        content_layout.add_widget(Label(text='Endereço do Imóvel', font_size='16sp', color=TEXT_COLOR_DARK, size_hint_y=None, height=dp(30)))
        content_layout.add_widget(self.imovel_rua)
        content_layout.add_widget(self.imovel_numero)
        content_layout.add_widget(self.imovel_bairro)
        content_layout.add_widget(self.imovel_cidade)
        content_layout.add_widget(self.imovel_estado)
        content_layout.add_widget(self.imovel_cep)
        
        self.layout.add_widget(content_layout)

        next_button = RoundedButton(
            text='Próximo',
            size_hint_y=None,
            height=dp(50),
            background_color=PRIMARY_COLOR,
            color=(1, 1, 1, 1)
        )
        next_button.bind(on_press=self.go_next)
        self.layout.add_widget(next_button)

    def update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
    
    def on_enter(self, *args):
        data = self.manager.app.contract_data.get('imovel', {})
        self.imovel_rua.text = data.get('imovel_rua', '')
        self.imovel_numero.text = data.get('imovel_numero', '')
        self.imovel_bairro.text = data.get('imovel_bairro', '')
        self.imovel_cidade.text = data.get('imovel_cidade', '')
        self.imovel_estado.text = data.get('imovel_estado', '')
        self.imovel_cep.text = data.get('imovel_cep', '')
        
    def go_next(self, instance):
        if self.imovel_rua.text and self.imovel_numero.text and self.imovel_bairro.text and self.imovel_cidade.text and self.imovel_estado.text and self.imovel_cep.text:
            self.manager.app.contract_data['imovel'] = {
                'imovel_rua': self.imovel_rua.text,
                'imovel_numero': self.imovel_numero.text,
                'imovel_bairro': self.imovel_bairro.text,
                'imovel_cidade': self.imovel_cidade.text,
                'imovel_estado': self.imovel_estado.text,
                'imovel_cep': self.imovel_cep.text,
            }
            self.manager.current = 'comprador_form'
        else:
            show_popup("Erro", "Por favor, preencha todos os campos do imóvel.")

class CompradorFormScreen(WizardScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_header('Dados do Comprador', '2/4')
        
        content_layout = BoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(15),
            size_hint_y=None
        )
        with content_layout.canvas.before:
            Color(CARD_BG_COLOR[0], CARD_BG_COLOR[1], CARD_BG_COLOR[2], CARD_BG_COLOR[3])
            self.rect = RoundedRectangle(size=content_layout.size, pos=content_layout.pos, radius=[dp(15)])
            content_layout.bind(pos=self.update_rect, size=self.update_rect)
        
        self.comprador_nome = TextInput(hint_text='Nome Completo', multiline=False, size_hint_y=None, height=dp(45))
        self.comprador_nacionalidade = TextInput(hint_text='Nacionalidade', multiline=False, size_hint_y=None, height=dp(45))
        self.comprador_estado_civil = TextInput(hint_text='Estado Civil', multiline=False, size_hint_y=None, height=dp(45))
        self.comprador_cpf = TextInput(hint_text='CPF / RG (somente números)', multiline=False, size_hint_y=None, height=dp(45))
        self.comprador_telefone = TextInput(hint_text='Telefone', multiline=False, size_hint_y=None, height=dp(45))
        self.comprador_email = TextInput(hint_text='E-mail', multiline=False, size_hint_y=None, height=dp(45))
        
        content_layout.add_widget(Label(text='Informações Pessoais', font_size='16sp', color=TEXT_COLOR_DARK, size_hint_y=None, height=dp(30)))
        content_layout.add_widget(self.comprador_nome)
        content_layout.add_widget(self.comprador_nacionalidade)
        content_layout.add_widget(self.comprador_estado_civil)
        content_layout.add_widget(self.comprador_cpf)
        content_layout.add_widget(self.comprador_telefone)
        content_layout.add_widget(self.comprador_email)
        
        self.layout.add_widget(content_layout)

        next_button = RoundedButton(
            text='Próximo',
            size_hint_y=None,
            height=dp(50),
            background_color=PRIMARY_COLOR,
            color=(1, 1, 1, 1)
        )
        next_button.bind(on_press=self.go_next)
        self.layout.add_widget(next_button)

    def update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        
    def on_enter(self, *args):
        data = self.manager.app.contract_data.get('comprador', {})
        self.comprador_nome.text = data.get('comprador_nome', '')
        self.comprador_nacionalidade.text = data.get('comprador_nacionalidade', '')
        self.comprador_estado_civil.text = data.get('comprador_estado_civil', '')
        self.comprador_cpf.text = data.get('comprador_cpf', '')
        self.comprador_telefone.text = data.get('comprador_telefone', '')
        self.comprador_email.text = data.get('comprador_email', '')

    def go_next(self, instance):
        if self.comprador_nome.text and self.comprador_cpf.text:
            self.manager.app.contract_data['comprador'] = {
                'comprador_nome': self.comprador_nome.text,
                'comprador_nacionalidade': self.comprador_nacionalidade.text,
                'comprador_estado_civil': self.comprador_estado_civil.text,
                'comprador_cpf': self.comprador_cpf.text,
                'comprador_telefone': self.comprador_telefone.text,
                'comprador_email': self.comprador_email.text,
            }
            self.manager.current = 'vendedor_form'
        else:
            show_popup("Erro", "Por favor, preencha os campos obrigatórios.")

class VendedorFormScreen(WizardScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_header('Dados do Vendedor', '3/4')
        
        content_layout = BoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(15),
            size_hint_y=None
        )
        with content_layout.canvas.before:
            Color(CARD_BG_COLOR[0], CARD_BG_COLOR[1], CARD_BG_COLOR[2], CARD_BG_COLOR[3])
            self.rect = RoundedRectangle(size=content_layout.size, pos=content_layout.pos, radius=[dp(15)])
            content_layout.bind(pos=self.update_rect, size=self.update_rect)

        self.vendedor_nome = TextInput(hint_text='Nome Completo', multiline=False, size_hint_y=None, height=dp(45))
        self.vendedor_nacionalidade = TextInput(hint_text='Nacionalidade', multiline=False, size_hint_y=None, height=dp(45))
        self.vendedor_estado_civil = TextInput(hint_text='Estado Civil', multiline=False, size_hint_y=None, height=dp(45))
        self.vendedor_cpf = TextInput(hint_text='CPF / RG (somente números)', multiline=False, size_hint_y=None, height=dp(45))
        self.vendedor_telefone = TextInput(hint_text='Telefone', multiline=False, size_hint_y=None, height=dp(45))
        self.vendedor_email = TextInput(hint_text='E-mail', multiline=False, size_hint_y=None, height=dp(45))

        content_layout.add_widget(Label(text='Informações Pessoais', font_size='16sp', color=TEXT_COLOR_DARK, size_hint_y=None, height=dp(30)))
        content_layout.add_widget(self.vendedor_nome)
        content_layout.add_widget(self.vendedor_nacionalidade)
        content_layout.add_widget(self.vendedor_estado_civil)
        content_layout.add_widget(self.vendedor_cpf)
        content_layout.add_widget(self.vendedor_telefone)
        content_layout.add_widget(self.vendedor_email)

        self.layout.add_widget(content_layout)

        next_button = RoundedButton(
            text='Próximo',
            size_hint_y=None,
            height=dp(50),
            background_color=PRIMARY_COLOR,
            color=(1, 1, 1, 1)
        )
        next_button.bind(on_press=self.go_next)
        self.layout.add_widget(next_button)

    def update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        
    def on_enter(self, *args):
        data = self.manager.app.contract_data.get('vendedor', {})
        self.vendedor_nome.text = data.get('vendedor_nome', '')
        self.vendedor_nacionalidade.text = data.get('vendedor_nacionalidade', '')
        self.vendedor_estado_civil.text = data.get('vendedor_estado_civil', '')
        self.vendedor_cpf.text = data.get('vendedor_cpf', '')
        self.vendedor_telefone.text = data.get('vendedor_telefone', '')
        self.vendedor_email.text = data.get('vendedor_email', '')

    def go_next(self, instance):
        if self.vendedor_nome.text and self.vendedor_cpf.text:
            self.manager.app.contract_data['vendedor'] = {
                'vendedor_nome': self.vendedor_nome.text,
                'vendedor_nacionalidade': self.vendedor_nacionalidade.text,
                'vendedor_estado_civil': self.vendedor_estado_civil.text,
                'vendedor_cpf': self.vendedor_cpf.text,
                'vendedor_telefone': self.vendedor_telefone.text,
                'vendedor_email': self.vendedor_email.text,
            }
            self.manager.current = 'contrato_resumo'
        else:
            show_popup("Erro", "Por favor, preencha os campos obrigatórios.")

class ContratoResumoScreen(WizardScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_header('Resumo do Contrato', '4/4')
        
        self.scroll_view = ScrollView()
        self.resumo_container = BoxLayout(
            orientation='vertical',
            padding=dp(10),
            spacing=dp(15),
            size_hint_y=None
        )
        self.resumo_container.bind(minimum_height=self.resumo_container.setter('height'))
        self.scroll_view.add_widget(self.resumo_container)
        self.layout.add_widget(self.scroll_view)

        generate_button = RoundedButton(
            text='Gerar Contrato',
            size_hint_y=None,
            height=dp(50),
            background_color=SUCCESS_COLOR,
            color=(1, 1, 1, 1)
        )
        generate_button.bind(on_press=self.generate_contract)
        self.layout.add_widget(generate_button)

    def on_enter(self, *args):
        self.update_resumo()

    def update_resumo(self):
        self.resumo_container.clear_widgets()
        data = self.manager.app.contract_data

        # Resumo do Imóvel
        imovel_card = self.create_resumo_card("Dados do Imóvel", 'imovel_form')
        if 'imovel' in data:
            imovel_data = data['imovel']
            imovel_card.add_widget(Label(text=f"Rua: {imovel_data.get('imovel_rua')}", color=TEXT_COLOR_DARK))
            imovel_card.add_widget(Label(text=f"Número: {imovel_data.get('imovel_numero')}", color=TEXT_COLOR_DARK))
            imovel_card.add_widget(Label(text=f"Bairro: {imovel_data.get('imovel_bairro')}", color=TEXT_COLOR_DARK))
            imovel_card.add_widget(Label(text=f"Cidade: {imovel_data.get('imovel_cidade')}", color=TEXT_COLOR_DARK))
            imovel_card.add_widget(Label(text=f"Estado: {imovel_data.get('imovel_estado')}", color=TEXT_COLOR_DARK))
            imovel_card.add_widget(Label(text=f"CEP: {imovel_data.get('imovel_cep')}", color=TEXT_COLOR_DARK))
        self.resumo_container.add_widget(imovel_card)
        
        # Resumo do Comprador
        comprador_card = self.create_resumo_card("Dados do Comprador", 'comprador_form')
        if 'comprador' in data:
            comprador_data = data['comprador']
            comprador_card.add_widget(Label(text=f"Nome: {comprador_data.get('comprador_nome')}", color=TEXT_COLOR_DARK))
            comprador_card.add_widget(Label(text=f"CPF: {comprador_data.get('comprador_cpf')}", color=TEXT_COLOR_DARK))
            comprador_card.add_widget(Label(text=f"E-mail: {comprador_data.get('comprador_email')}", color=TEXT_COLOR_DARK))
        self.resumo_container.add_widget(comprador_card)

        # Resumo do Vendedor
        vendedor_card = self.create_resumo_card("Dados do Vendedor", 'vendedor_form')
        if 'vendedor' in data:
            vendedor_data = data['vendedor']
            vendedor_card.add_widget(Label(text=f"Nome: {vendedor_data.get('vendedor_nome')}", color=TEXT_COLOR_DARK))
            vendedor_card.add_widget(Label(text=f"CPF: {vendedor_data.get('vendedor_cpf')}", color=TEXT_COLOR_DARK))
            vendedor_card.add_widget(Label(text=f"E-mail: {vendedor_data.get('vendedor_email')}", color=TEXT_COLOR_DARK))
        self.resumo_container.add_widget(vendedor_card)
    
    def create_resumo_card(self, title, screen_name):
        card = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(5), size_hint_y=None)
        with card.canvas.before:
            Color(CARD_BG_COLOR[0], CARD_BG_COLOR[1], CARD_BG_COLOR[2], CARD_BG_COLOR[3])
            self.rect = RoundedRectangle(size=card.size, pos=card.pos, radius=[dp(15)])
            card.bind(pos=self.update_rect, size=self.update_rect)
        
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30))
        header_layout.add_widget(Label(text=title, font_size='16sp', bold=True, color=PRIMARY_COLOR, size_hint_x=0.8))
        edit_button = RoundedButton(text='Editar', size_hint_x=0.2, background_color=SECONDARY_COLOR, color=TEXT_COLOR_DARK)
        edit_button.bind(on_press=lambda instance: setattr(self.manager, 'current', screen_name))
        header_layout.add_widget(edit_button)
        
        card.add_widget(header_layout)
        return card

    def update_rect(self, instance, value):
        instance.canvas.before.children[-1].pos = instance.pos
        instance.canvas.before.children[-1].size = instance.size

    def generate_contract(self, instance):
        # A lógica de geração do contrato com o template vai aqui
        # As informações estão em self.manager.app.contract_data
        
        # Exemplo de como usar os dados
        dados = self.manager.app.contract_data
        
        # A lógica para preencher o CONTRATO_TEMPLATE com os dados preenchidos
        # e gerar o contrato final está faltando, mas os dados necessários estão aqui.
        # Exemplo: contrato_final = CONTRATO_TEMPLATE.format(**dados['imovel'], **dados['comprador'], etc.)
        
        show_popup("Contrato Gerado", "O contrato foi gerado com sucesso!")
        self.manager.current = 'contract'

class MainScreen(Screen):
    # (Código da MainScreen, PaymentsScreen, etc. não foi alterado para manter o foco)
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
        self.manager.current = 'new_contract_start'

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

class ContractScreen(Screen):
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

        self.scroll_view = ScrollView()
        
        contract_content_layout = BoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(15),
            size_hint_y=None
        )
        contract_content_layout.bind(minimum_height=contract_content_layout.setter('height'))

        self.contract_label = Label(
            font_size='14sp',
            halign='left',
            valign='top',
            color=TEXT_COLOR_DARK,
            text_size=(Window.width - dp(40), None),
            size_hint_y=None
        )

        self.bind(contract_text=self.contract_label.setter('text'))
        self.contract_label.bind(texture_size=self.contract_label.setter('size'))

        contract_content_layout.add_widget(self.contract_label)
        self.scroll_view.add_widget(contract_content_layout)
        root_layout.add_widget(self.scroll_view)

        button_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10)
        )
        
        create_new_button = RoundedButton(text='Criar Novo Contrato', background_color=PRIMARY_COLOR)
        create_new_button.bind(on_press=self.go_to_new_contract_screen)
        
        generate_pdf_button = RoundedButton(text='Gerar PDF', background_color=SUCCESS_COLOR)

        button_layout.add_widget(create_new_button)
        button_layout.add_widget(generate_pdf_button)
        root_layout.add_widget(button_layout)
        self.add_widget(root_layout)
        
    def update_contract_text(self, new_text):
        self.contract_text = new_text

    def go_to_new_contract_screen(self, instance):
        self.manager.current = 'new_contract_start'

    def go_back(self, instance):
        self.manager.current = 'main'

class CompraFirmeApp(App):
    def build(self):
        self.contract_data = {}
        sm = ScreenManager()
        sm.app = self  # Linha adicionada para corrigir o erro
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(PaymentsScreen(name='payments'))
        sm.add_widget(ContractScreen(name='contract'))
        
        # Telas do novo fluxo de contrato
        sm.add_widget(ImovelFormScreen(name='imovel_form'))
        sm.add_widget(CompradorFormScreen(name='comprador_form'))
        sm.add_widget(VendedorFormScreen(name='vendedor_form'))
        sm.add_widget(ContratoResumoScreen(name='contrato_resumo'))
        
        # Adiciona a tela inicial do fluxo de contrato
        sm.add_widget(Screen(name='new_contract_start'))
        self.setup_new_contract_start_screen(sm.get_screen('new_contract_start'))

        return sm
    
    def setup_new_contract_start_screen(self, screen):
        layout = BoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(20)
        )
        layout.add_widget(Label(text='Novo Contrato', font_size='22sp', bold=True, color=TEXT_COLOR_DARK))
        layout.add_widget(Label(text='Vamos preencher as informações para gerar o contrato.', font_size='16sp', color=TEXT_COLOR_LIGHT))

        start_button = RoundedButton(
            text='Começar',
            size_hint_y=None,
            height=dp(50),
            background_color=PRIMARY_COLOR,
            color=(1,1,1,1)
        )
        start_button.bind(on_press=self.start_new_contract)

        layout.add_widget(Widget()) # Espaçador
        layout.add_widget(start_button)
        layout.add_widget(Widget()) # Espaçador

        screen.add_widget(layout)
    
    def start_new_contract(self, instance):
        self.contract_data = {} # Limpa os dados do contrato anterior
        self.root.current = 'imovel_form'

if __name__ == '__main__':
    CompraFirmeApp().run()