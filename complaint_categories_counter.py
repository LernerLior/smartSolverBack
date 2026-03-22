import json

def categories_counter(lista):
	quantidade_categorias = {}
	def contar(lista):
		def apply(complaint):
			category = complaint[complaint_category]
			return category
		return map(apply, lista)

	categorias = contar(lista)
	
	categorias = list(categorias)
	print(categorias)

	for categoria in categorias:
		quantidade_categorias[categoria] = 0
	
	for categoria in categorias:
		quantidade_categorias[categoria] += 1

	return json.dumps(quantidade_categorias)
	


lista = [
    {
        "id": "1",
        "pk": "complaints",
        "complaint_title": "Erro no valor do cheque compensado",
        "complaint_description": "Emiti um cheque de 300 Reais e o banco Santander debitou 3000 Reais.\n\nAguardo o estorno.",
        "complaint_creation_date": "20/11/2025 às 12:00",
        "complaint_solution": "",
        "complaint_num": 1,
        "complaint_per": 0.167,
	"complaint_category" : "Cobrança Indevida",
        "_rid": "MpICALms7d8HAAAAAAAAAA==",
        "_self": "dbs/MpICAA==/colls/MpICALms7d8=/docs/MpICALms7d8HAAAAAAAAAA==/",
        "_etag": "\"440168b8-0000-0b00-0000-691f8e3e0000\"",
        "_attachments": "attachments/",
        "_ts": 1763675710
    },
    {
        "id": "2",
        "pk": "complaints",
        "complaint_title": "Mau atendimento",
        "complaint_description": "Um dos piores atendimentos ao público em relação a banco! Não recomendo",
        "complaint_creation_date": "20/11/2025 às 12:00",
        "complaint_solution": "",
        "complaint_num": 2,
        "complaint_per": 0.167,
	"complaint_category" :"Problemas de Pagamento",
        "_rid": "MpICALms7d8IAAAAAAAAAA==",
        "_self": "dbs/MpICAA==/colls/MpICALms7d8=/docs/MpICALms7d8IAAAAAAAAAA==/",
        "_etag": "\"440169b8-0000-0b00-0000-691f8e3e0000\"",
        "_attachments": "attachments/",
        "_ts": 1763675710
    },
    {
        "id": "3",
        "pk": "complaints",
        "complaint_title": "Contrato desconhecido e sem informações claras no Cadastro Positivo",
        "complaint_description": "Boa Tarde, está no Cadastro Positivo esse contrato, número do contrato\n*****\n\nE número de operação *****\n\nGostaria de saber do que este contrato se trata? Porque nem nas dívidas para negociar no Serasa e nem em lugar nenhum consta este contrato ou número de operação. Além disso, não tem data de término previsto, só conta as parcelas no total e as que estão pagas. Já pedi a revisão no cadastro positivo. Se este contrato não existe mais peço que seja retirado do meu nome. Aguardo a resposta",
        "complaint_creation_date": "20/11/2025 às 12:00",
        "complaint_num": 3,
        "complaint_per": 0.167,
	"complaint_category" : "Conta Bloqueada",
        "_rid": "MpICALms7d8JAAAAAAAAAA==",
        "_self": "dbs/MpICAA==/colls/MpICALms7d8=/docs/MpICALms7d8JAAAAAAAAAA==/",
        "_etag": "\"44016ab8-0000-0b00-0000-691f8e3e0000\"",
        "_attachments": "attachments/",
        "_ts": 1763675710
    },
    {
        "id": "4",
        "pk": "complaints",
        "complaint_title": "Cobrança indevida de juros e parcelamento automático não autorizado no cartão de crédito Santander",
        "complaint_description": "A dois meses, atrás fiz o pagamento da Fatura parcial da Fatura do cartão de crédito do Santander, só Que quando realizei o pagamento, eles cobraram um Juros que nas minhas contas deu um total de R$ 180,00, só que mesmo assim eles fizeram um parcelamento automático no valor de mais de R$ 500,00 e agora todo mês eles descontam do limite do cartão! Eu ligo no banco e nada é resolvido! Ou eles resolvem meu problema, ou terei que ir atrás dos meus direitos!",
        "complaint_creation_date": "20/11/2025 às 12:00",
        "complaint_solution": "",
        "complaint_num": 4,
        "complaint_per": 0.167,
	"complaint_category" :"Resgate de Investimento Não Realizado",
        "_rid": "MpICALms7d8KAAAAAAAAAA==",
        "_self": "dbs/MpICAA==/colls/MpICALms7d8=/docs/MpICALms7d8KAAAAAAAAAA==/",
        "_etag": "\"44016bb8-0000-0b00-0000-691f8e3e0000\"",
        "_attachments": "attachments/",
        "_ts": 1763675710
    },
    {
        "id": "5",
        "pk": "complaints",
        "complaint_title": "Aplicativo fora do ar há 17 dias sem solução",
        "complaint_description": "o meu aplicativo está fora do ar faz 17 dias, já liguei para resolverem e até agora nada de resolver, sempre aparece a mesma mensagem que encontraram um problema técnico e já estão resolvendo. O plicativo da minha irmã voltou rápido a funcionar, já o meu até hoje está fora.",
        "complaint_creation_date": "20/11/2025 às 12:00",
        "complaint_solution": "",
        "complaint_num": 5,
        "complaint_per": 0.167,
	"complaint_category" : "Outros",
        "_rid": "MpICALms7d8LAAAAAAAAAA==",
        "_self": "dbs/MpICAA==/colls/MpICALms7d8=/docs/MpICALms7d8LAAAAAAAAAA==/",
        "_etag": "\"44016cb8-0000-0b00-0000-691f8e3e0000\"",
        "_attachments": "attachments/",
        "_ts": 1763675710
    },
    {
        "id": "6",
        "pk": "complaints",
        "complaint_title": "Cobrança indevida de valor alto na conta corrente para aluguel e falta de opções de acordo",
        "complaint_description": "Mais o mês o Santander retira quase R$ 400 reais do valor destinado pra pagar meu aluguel.\nTentei acordo ligando na central e só me deram a opção de R$ 169 que não cabe no meu orçamento, por isso não foi feito.\nAnos de conta, cartão com limite baixo acabei cancelando e agora isso.\nSegundo mês seguido que retiram quase R$ 400 e eu não tenho dessa vez onde repor.\nEsse é o tratamento do banco, desumano.\nPreciso que devolvam o valor e tenham o mínimo de empatia na hora de fazer o acordo para que chegamos a um meio termo.",
        "complaint_creation_date": "20/11/2025 às 12:00",
        "complaint_solution": "",
        "complaint_num": 6,
        "complaint_per": 0.1667,
	"complaint_category" : "Outros",
        "_rid": "MpICALms7d8MAAAAAAAAAA==",
        "_self": "dbs/MpICAA==/colls/MpICALms7d8=/docs/MpICALms7d8MAAAAAAAAAA==/",
        "_etag": "\"44016db8-0000-0b00-0000-691f8e3e0000\"",
        "_attachments": "attachments/",
        "_ts": 1763675710
    }
]

teste = categories_counter(lista)
print(teste)
