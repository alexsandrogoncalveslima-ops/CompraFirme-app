import os

# Altere a URL do servidor aqui
SERVER_URL = "https://comprafirme-app.onrender.com"

# --- Modelo de Contrato completo ---
# Este é o modelo de contrato com os campos para preenchimento
CONTRATO_TEMPLATE = """
MODELO DE CONTRATO DE COMPRA E VENDA DE IMÓVEL
IDENTIFICAÇÃO DAS PARTES

VENDEDOR (ES): {vendedor_nome}, {vendedor_nacionalidade}, {vendedor_profissao}, {vendedor_estado_civil}, portador da Cédula de Identidade, RG nº {vendedor_rg}, inscrito no CPF sob o nº {vendedor_cpf}, residente e domiciliado à Rua {vendedor_rua}, nº {vendedor_numero}, Bairro {vendedor_bairro}, Estado de {vendedor_estado}, adiante denominado simplesmente VENDEDOR.

COMPRADOR (ES): {comprador_nome}, {comprador_nacionalidade}, {comprador_profissao}, {comprador_estado_civil}, portador da Cédula de Identidade, RG nº {comprador_rg}, inscrito no CPF sob o nº {comprador_cpf}, residente e domiciliado à Rua {comprador_rua}, nº {comprador_numero}, Bairro {comprador_bairro}, Estado de {comprador_estado}, adiante denominado simplesmente COMPRADOR.

Pelo presente instrumento particular e na melhor forma de direito, têm entre si justo e contratado o que segue, que se obrigam a cumprir por si, seus herdeiros e sucessores:

CLÁUSULA PRIMEIRA - O VENDEDOR, na qualidade de legítimo proprietário do imóvel situado à Rua {imovel_rua}, nº {imovel_numero}, Bairro {imovel_bairro}, Estado de {imovel_estado}, constituído de {imovel_descricao}, adquirido através de {imovel_aquisicao} averbada no {imovel_registro} Registro de Imóveis desta Capital sob o nº de matrícula {imovel_matricula}, resolve vendê-lo ao COMPRADOR, pelo valor de R$ {valor_total} ({valor_total_extenso}), que deverá ser pago da seguinte forma:

CLÁUSULA SEGUNDA - {forma_pagamento_clausula_2} O valor de R$ {sinal} ({sinal_extenso}), a título de sinal e princípio de pagamento, pago neste ato, através do cheque nº {cheque_sinal} do Banco {banco_sinal}, do qual o VENDEDOR dará plena quitação após a compensação ou cobrança respectiva.

PARÁGRAFO PRIMEIRO - O valor de R$ {valor_parcela_1} ({valor_parcela_1_extenso}), no dia {data_parcela_1}, contra a apresentação dos documentos e certidões pessoais e do imóvel, adiante relacionados;

PARÁGRAFO SEGUNDO - E o saldo restante no valor de R$ {saldo_restante} ({saldo_restante_extenso}), no dia {data_lavratura_escritura}, quando será lavrada a Escritura definitiva.

CLÁUSULA TERCEIRA – Na data do pagamento da segunda parcela, o VENDEDOR apresentará ao COMPRADOR os documentos abaixo relacionados, em perfeita ordem:

(Especifique os documentos necessários.....)

CLÁUSULA QUARTA – Na hipótese de pagamento em cheques, a quitação das parcelas e do negócio estará condicionada a compensação ou cobrança bancária correspondente.

PARÁGRAFO PRIMEIRO – Se o COMPRADOR não efetuar o pagamento das parcelas devidas, ou se os cheques não forem liquidados ou pagos, o presente instrumento considerar-se-á rescindido de pleno direito, ficando o COMPRADOR constituído em mora.

PARÁGRAFO SEGUNDO – Na hipótese de ocorrência de mora, o VENDEDOR restituirá ao COMPRADOR o valor equivalente a {porcentagem_multa}% ({porcentagem_multa_extenso}) da quantia efetivamente paga, corrigido pelo {indice_reajuste} até a data da devolução.

CLÁUSULA QUINTA – O presente Contrato é feito em caráter irrevogável e irretratável, obrigando os contratantes por si, seus herdeiros ou sucessores.

CLÁUSULA SEXTA – A posse do imóvel será transferida ao COMPRADOR no dia {data_transferencia_posse}, passando a responder por todos os impostos e taxas que recaírem sobre o imóvel, a partir desta data, ainda que lançados em nome do VENDEDOR. Até o momento da tradição (transmissão da posse), os riscos do bem correm por conta do vendedor, e os do preço por conta do comprador. O Comprador está ciente do atual estado em que se encontra o imóvel, objeto do presente contrato, recebendo-o nestas condições, nada mais tendo a reclamar, eis que vistoriou o mesmo.

PARÁGRAFO PRIMEIRO – Na hipótese do VENDEDOR não desocupar o imóvel na data especificada, ficará sujeito a um aluguel diário de R$ {aluguel_diario} ({aluguel_diario_extenso}), até a desocupação e entrega definitiva das chaves.

PARÁGRAFO SEGUNDO – Ao VENDEDOR caberá zelar pela conservação do imóvel até a data da desocupação e entrega definitiva das chaves, inclusive arcando com as despesas que para isso forem necessárias, defendendo-o da turbação ou esbulho de terceiros.

PARÁGRAFO TERCEIRO – O VENDEDOR declara, sob responsabilidade civil e penal, que o imóvel objeto deste Contrato está completamente livre e desembaraçado de quaisquer dívidas e ônus reais, inclusive hipotecas, impostos e taxas em atraso.

PARÁGRAFO QUARTO – Declara ainda o VENDEDOR que não está vinculado ao INSS (Instituto Nacional do Seguro Social), como empregador ou produtor rural.

CLÁUSULA SÉTIMA – As partes elegem o foro da Comarca de {foro}, com renúncia de qualquer outro, por mais privilegiado que seja, para dirimir quaisquer dúvidas ou questões decorrentes deste Contrato, correndo por conta da parte vencida, a multa ou pena convencional de 10% (dez por cento) sobre o valor do presente Contrato, além de despesas judiciais, extrajudiciais e honorários advocatícios da parte vencedora.

Isto posto, e, por estarem justas, contratadas, cientes e de acordo com todas as cláusulas e condições do presente Contrato, assinam este instrumento em 02 (duas) vias para um só efeito, na presença das testemunhas abaixo.

{local_assinatura}, {dia_assinatura} de {mes_assinatura} de {ano_assinatura}.

VENDEDOR

COMPRADOR

Testemunhas:

(Nome da Testemunha e Documento de Identificação)

(Nome da Testemunha e Documento de Identificação)
"""