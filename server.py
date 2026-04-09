from fastapi import FastAPI
from fastapi.responses import JSONResponse
from crawler import collect_complaints
from dotenv import load_dotenv
import os
from azure.cosmos import CosmosClient
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from complaint_catgories import categorize_complaints

# Carregar variáveis do .env
load_dotenv()

# Variáveis do Cosmos DB
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DATABASE = os.getenv("COSMOS_DATABASE")
COSMOS_CONTAINER = os.getenv("COSMOS_CONTAINER")

# URL do frontend permitido
FRONTEND_URL = os.getenv("FRONTEND_URL")  

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
        data = collect_complaints("santander", complaint_number=6, wait_seconds=10)
        data = categorize_complaints(data, ["Cobrança Indevida", 
                                            "Problemas de Pagamento", 
                                            "Conta Bloqueada", 
                                            "Resgate de Investimento Não Realizado", 
                                            "Problemas de atendimento",
                                            "Problemas de conta",
                                            "Outros"])
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

@app.get("/complaint/{id}")
def get_complaint(id: str):
    try:
        item = container.read_item(item=id, partition_key="complaints")
        return item
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=404)
    
#For testing: uvicorn server:app --reload --host 0.0.0.0 --port 8000