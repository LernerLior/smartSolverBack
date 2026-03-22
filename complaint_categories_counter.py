import json

def categories_counter(lista):
	quantidade_categorias = {}
	def contar(lista):
		def apply(complaint):
			category = complaint["complaint_category"]
			return category
		return map(apply, lista)

	categorias = contar(lista)
	
	categorias = list(categorias)

	for categoria in categorias:
		quantidade_categorias[categoria] = 0
	
	for categoria in categorias:
		quantidade_categorias[categoria] += 1

	return json.dumps(quantidade_categorias)
	
