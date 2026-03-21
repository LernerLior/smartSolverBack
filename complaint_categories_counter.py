import json

def categories_counter(latest_items):
	t = latest_items.read()
	quantidade_categorias = {}
	categorias = []
	lista = t.split('"')
	for i in range(len(lista)):
		if lista[i] == 'complaint_category':
			categorias.append(lista[i+2])
			
	
	for categoria in categorias:
		quantidade_categorias[categoria] = 0
	
	for categoria in categorias:
		quantidade_categorias[categoria] += 1

	return json.dumps(quantidade_categorias)
	
		





with open('latest_items.txt', 'r') as f:
	j = categories_counter(f)
	print(j)
	
