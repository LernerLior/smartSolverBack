from urllib import response
from google import genai
from google.genai import types
import json

def solution_generation(json_data):
   client = genai.Client(api_key =)

   response = client.models.generate_content(
      model="gemini-2.5-flash",

   config=types.GenerateContentConfig(
      system_instruction="Você é um assistente que ajuda a analisar dados de reclamações de clientes. Forneça insights úteis e sugestões de fácil entendimento com base nos dados fornecidos." \
      "" \
      r"Você deve colocar ** para indicar negrito e \n para indicar quebra de linha" \
      "Sua resposta deve ser concatenada com os dados de entrada, e estar no formato JSON, seguindo o formato:" \
      "compaint-solution: {sua solução}, para cada reclamação.",
      max_output_tokens=1024,
      temperature=0.2),
      contents=json.dumps(json_data)
   )
   
   return response



j = open('complaintss.json', 'r')
g = j.read()
response = solution_generation(g)
j.close()
print(response)

