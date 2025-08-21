import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.metrics import dp

# Importa as funções de lógica que criamos
from app_logic import add_payment, get_remaining_amount, get_total_paid

class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(10)
        self.padding = dp(20)

        # Labels de exibição do valor total
        self.total_imovel_label = Label(text='Valor Total do Imóvel: R$ 280.000,00', font_size='20sp')
        self.add_widget(self.total_imovel_label)

        self.remaining_amount_label = Label(text='Valor Restante: R$ 0.00', font_size='24sp', bold=True)
        self.add_widget(self.remaining_amount_label)

        self.total_paid_label = Label(text='Total Pago: R$ 0.00', font_size='18sp')
        self.add_widget(self.total_paid_label)

        self.update_values()

        # Campos para adicionar um novo pagamento
        self.add_widget(Label(text='Adicionar Novo Pagamento', font_size='18sp'))

        self.name_input = TextInput(hint_text='Nome do Pagador', multiline=False)
        self.add_widget(self.name_input)

        self.value_input = TextInput(hint_text='Valor (ex: 10000.00)', multiline=False, input_type='number')
        self.add_widget(self.value_input)

        # Botão para registrar o pagamento
        self.add_button = Button(text='Registrar Pagamento', size_hint_y=None, height=dp(44))
        self.add_button.bind(on_press=self.register_payment)
        self.add_widget(self.add_button)

    def update_values(self):
        """Atualiza os valores exibidos na tela."""
        total_pago = get_total_paid()
        valor_restante = get_remaining_amount()
        self.total_paid_label.text = f'Total Pago: R$ {total_pago:.2f}'
        self.remaining_amount_label.text = f'Valor Restante: R$ {valor_restante:.2f}'

    def register_payment(self, instance):
        """Função chamada ao clicar no botão de registrar."""
        nome = self.name_input.text
        try:
            valor = float(self.value_input.text)
            if nome and valor > 0:
                add_payment(nome, valor)
                self.update_values()
                self.name_input.text = ''
                self.value_input.text = ''
            else:
                print("Por favor, preencha nome e valor corretamente.")
        except ValueError:
            print("Valor inválido. Use um número (ex: 10000.00).")

class CompraFirmeApp(App):
    def build(self):
        return MainScreen()

if __name__ == '__main__':
    CompraFirmeApp().run()