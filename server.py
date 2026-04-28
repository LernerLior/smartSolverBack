from fastapi import FastAPI
from fastapi.responses import JSONResponse
from crawler import collect_complaints
from dotenv import load_dotenv
import os
from azure.cosmos import CosmosClient
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from google import genai
from complaint_catgories import categorize_complaints
from adjust_complaints import adjust_complaints
# Carregar variáveis do .env
load_dotenv()

# Variáveis do Cosmos DB
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DATABASE = os.getenv("COSMOS_DATABASE")
COSMOS_CONTAINER = os.getenv("COSMOS_CONTAINER")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview") 
# URL do frontend permitido
FRONTEND_URL = os.getenv("FRONTEND_URL")  
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemma-3-27b-it:free")

# Inicializar cliente do Cosmos
client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
database = client.get_database_client(COSMOS_DATABASE)
container = database.get_container_client(COSMOS_CONTAINER)

# Inicializar FastAPI
app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/run-main")
def run_main():
    try:
        data = collect_complaints("santander", complaint_number=10, wait_seconds=10)
        data = categorize_complaints(data, ["Cobrança Indevida", 
        "Problemas de Pagamento", 
        "Conta Bloqueada", 
        "Resgate de Investimento Não Realizado", 
        "Problemas de Atendimento",
        "Vítima de golpe",
        "Outros"])
        data = adjust_complaints(data)
        if isinstance(data, list):
            for item in data:
                container.upsert_item(item)
        else:
            container.upsert_item(data)

        return JSONResponse({"status": "success", "data": data})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.get("/latest")
def get_latest(n: int = 6, page: int = 1):
    try:
        offset = (page - 1) * n

        # Conta o total sem trazer os dados
        count_query = "SELECT VALUE COUNT(1) FROM c"
        total = list(container.query_items(
            query=count_query,
            enable_cross_partition_query=True
        ))[0]

        # Busca só a página necessária
        query = f"SELECT * FROM c ORDER BY c.complaint_creation_date DESC OFFSET {offset} LIMIT {n}"
        items = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))

        return {
            "items": items,
            "total": total,
            "page": page,
            "pages": -(-total // n)
        }

    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.get("/categories")
def get_categories():
    query = """
    SELECT c.complaint_category AS category
    FROM c
    """

    items = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    
    counts = {}
    for item in items:
        cat = item.get("category")
        counts[cat] = counts.get(cat, 0) + 1

    return [{"category": k, "total": v} for k, v in counts.items()]

@app.get("/complaint/{id}")
def get_complaint(id: str):
    try:
        item = container.read_item(item=id, partition_key="complaint")
        return item
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=404)
    
@app.get("/categories-by-date")
def get_categories_by_date():
    query = """
    SELECT c.complaint_category AS category, c.complaint_creation_date  AS date
    FROM c
    """

    items = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))

    grouped = {}
    for item in items:
        print(items)
        raw_date = item.get("date")
        cat = item.get("category")

        # Extrai só a data do formato "05/04/2026 às 14:28"
        try:
            date = datetime.strptime(raw_date.split(" às ")[0], "%d/%m/%Y").strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            date = "unknown"

        if date not in grouped:
            grouped[date] = {}

        grouped[date][cat] = grouped[date].get(cat, 0) + 1

    return [
        {
            "date": date,
            "categories": [
                {"category": str(cat), "total": str(total)}
                for cat, total in cats.items()
            ]
        }
        for date, cats in sorted(grouped.items())
    ]

@app.post("/ai-analysis")
async def ai_analysis(body: dict):
    instruction = "Você é um assistente que ajuda a analisar dados de reclamações de clientes. Forneça insights úteis e sugestões de fácil entendimento com base nos dados fornecidos. Seja breve e preciso, mas apresente detalhes suficientes para que as recomendações possam ser implementadas, principalmente nas de maior importância"
    prompt = f"{instruction}\nReclamação: {body['title']}\nTexto: {body['text']}"

    # Tenta Gemini primeiro
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        return {"solution": response.text}
    except Exception as e:
        print(f"Gemini falhou, tentando DeepSeek... Erro: {e}")

    # Fallback para OpenRouter (Gemma gratuito)
    try:
        import httpx
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}]
        }
        async with httpx.AsyncClient() as http_client:
            res = await http_client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            data = res.json()
            return {"solution": data["choices"][0]["message"]["content"]}
    except Exception as e:
        print(f"OpenRouter também falhou: {e}")
        return JSONResponse({"status": "error", "message": "Ambos os modelos falharam."}, status_code=500)

#For testing: uvicorn server:app --reload --host 0.0.0.0 --port 8000