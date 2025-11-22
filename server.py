from fastapi import FastAPI
from fastapi.responses import JSONResponse
from crawler import collect_complaints
from dotenv import load_dotenv
import os
from azure.cosmos import CosmosClient
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

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
        
        if isinstance(data, list):
            for item in data:
                container.upsert_item(item)
        else:
            container.upsert_item(data)

        return JSONResponse({"status": "success", "data": data})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.get("/latest")
def get_latest(n: int = 6):
    """
    Retorna os últimos n documentos gravados no Cosmos DB, ordenados por complaint_creation_date.
    Retorna diretamente um array para o frontend consumir com .map()
    """
    try:
        items = list(container.query_items(
            query="SELECT * FROM c",
            enable_cross_partition_query=True
        ))

        for item in items:
            item['parsed_date'] = datetime.strptime(item['complaint_creation_date'], "%d/%m/%Y às %H:%M")

        items_sorted = sorted(items, key=lambda x: x['parsed_date'], reverse=True)

        latest_items = items_sorted[:n]

        for item in latest_items:
            item.pop('parsed_date', None)

        return latest_items

    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


    
#For testing: uvicorn server:app --reload --host 0.0.0.0 --port 8000