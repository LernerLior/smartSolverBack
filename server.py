from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from crawler import collect_complaints
from dotenv import load_dotenv
import os
import traceback
from azure.cosmos import CosmosClient
from datetime import datetime, timedelta
from google import genai
from complaint_catgories import categorize_complaints
from pydantic import BaseModel, EmailStr
import bcrypt
from jose import JWTError, jwt
import uuid
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
LANDING_URL = os.getenv("LANDING_URL")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemma-3-27b-it:free")
LOGIN_KEY = os.getenv("LOGIN_KEY", "chave")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
 
LANDING_URL = os.getenv("LANDING_URL")

# Inicializar cliente do Cosmos
client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
database = client.get_database_client(COSMOS_DATABASE)
container = database.get_container_client(COSMOS_CONTAINER)

# Inicializar FastAPI
app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL,LANDING_URL],  
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
                                            "Problemas de Atendimento",
                                            "Vítima de golpe",
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

@app.get("/origin")
def get_origin():
    query = """
    SELECT c.complaint_origin AS origin
    FROM c
    """

    items = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    
    counts = {}
    for item in items:
        origin = item.get("origin")
        counts[origin] = counts.get(origin, 0) + 1

    return [{"origin": k, "total": v} for k, v in counts.items()]


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


# Endpoints de login

COSMOS_USERS_DATABASE = os.getenv("COSMOS_USERS_DATABASE")
COSMOS_USERS_CONTAINER = os.getenv("COSMOS_USERS_CONTAINER", "users")

users_database = client.get_database_client(COSMOS_USERS_DATABASE)
users_container = users_database.get_container_client(COSMOS_USERS_CONTAINER)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
 
class Token(BaseModel):
    access_token: str
    token_type: str
 
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain[:72].encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain[:72].encode(), hashed.encode())

def validate_password_strength(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(status_code=422, detail="A senha deve ter pelo menos 8 caracteres.")
    if not any(c.isupper() for c in password):
        raise HTTPException(status_code=422, detail="A senha deve conter pelo menos uma letra maiúscula.")
    if not any(c.isdigit() for c in password):
        raise HTTPException(status_code=422, detail="A senha deve conter pelo menos um número.")
 
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, LOGIN_KEY, algorithm=ALGORITHM)
 
def get_user_by_email(email: str):
    query = f"SELECT * FROM c WHERE c.email = '{email}' AND c.type = 'user'"
    items = list(users_container.query_items(query=query, enable_cross_partition_query=True))
    return items[0] if items else None
 
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, LOGIN_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado.")
    return user
 

@app.post("/create_user", status_code=201, tags=["Auth"])
def create_user(payload: CreateUserRequest):
    """Cadastra um novo administrador."""
    validate_password_strength(payload.password)

    if get_user_by_email(payload.email):
        raise HTTPException(status_code=409, detail="Este e-mail já está cadastrado.")

    new_user = {
        "id": payload.email,
        "type": "user",
        "email": payload.email,
        "hashed_password": hash_password(payload.password),
        "created_at": datetime.utcnow().isoformat(),
    }
    users_container.upsert_item(new_user)

    return {"message": "Conta criada com sucesso.", "email": payload.email}

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@app.post("/login_user", tags=["Auth"])
def login_user(payload: LoginRequest):
    """Autentica o usuário e retorna um JWT."""
    user = get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")

    token = create_access_token({"sub": user["email"]})
    return {"access_token": token, "token_type": "bearer"}

# Comentários:
COSMOS_COMMENTS_CONTAINER = os.getenv("COSMOS_COMMENTS_CONTAINER", "comments")
comments_container = users_database.get_container_client(COSMOS_COMMENTS_CONTAINER)

class CommentPostRequest(BaseModel):
    complaint_id: str
    text: str

class CommentDeleteRequest(BaseModel):
    comment_id: str

@app.post("/comments_post", status_code=201, tags=["Comments"])
def post_comment(
    payload: CommentPostRequest,
    current_user: dict = Depends(get_current_user)
):
    """Cria um comentário vinculado a uma reclamação. Requer autenticação."""
    import uuid

    comment = {
        "id": str(uuid.uuid4()),
        "complaint_id": payload.complaint_id,
        "text": payload.text,
        "author_email": current_user["email"],
        "created_at": datetime.utcnow().isoformat(),
    }
    comments_container.upsert_item(comment)
    return comment


@app.delete("/comments_delete", tags=["Comments"])
def delete_comment(
    payload: CommentDeleteRequest,
    current_user: dict = Depends(get_current_user)
):
    """Deleta um comentário. Só o autor pode deletar o próprio comentário."""
    query = f"SELECT * FROM c WHERE c.id = '{payload.comment_id}'"
    items = list(comments_container.query_items(query=query, enable_cross_partition_query=True))

    if not items:
        raise HTTPException(status_code=404, detail="Comentário não encontrado.")

    comment = items[0]

    if comment["author_email"] != current_user["email"]:
        raise HTTPException(status_code=403, detail="Você não tem permissão para excluir este comentário.")

    comments_container.delete_item(item=comment["id"], partition_key=comment["complaint_id"])
    return {"message": "Comentário excluído com sucesso."}

@app.get("/comments_get", tags=["Comments"])
def get_comments(
    complaint_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Retorna todos os comentários vinculados a uma reclamação."""
    query = f"SELECT * FROM c WHERE c.complaint_id = '{complaint_id}' ORDER BY c.created_at ASC"
    items = list(comments_container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))

    for item in items:
        item["text"] = item.get("text", "")

    return items

#Status (Concluído ou Pendente)
COSMOS_COMPLETED_CONTAINER = os.getenv("COSMOS_COMPLETED_CONTAINER", "completed")
completed_container = database.get_container_client(COSMOS_COMPLETED_CONTAINER)

@app.patch("/complaint_status")
def toggle_status(body: dict, current_user: dict = Depends(get_current_user)):
    try:
        item = container.read_item(item=body["complaint_id"], partition_key="complaint")
        item["complaint_status"] = body.get("status", False)

        if item["complaint_status"]:
            completed_container.upsert_item(item)
            container.delete_item(item=item["id"], partition_key="complaint")
        else:
            container.upsert_item(item)

        return {"complaint_status": item["complaint_status"]}
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.get("/solved")
def get_solved(current_user: dict = Depends(get_current_user)):
    try:
        items = list(completed_container.query_items(
            query="SELECT * FROM c",
            enable_cross_partition_query=True
        ))
        return {"items": items}
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

COSMOS_CONTACTS_CONTAINER = os.getenv("COSMOS_CONTACTS_CONTAINER", "contacts")
contacts_container = users_database.get_container_client(COSMOS_CONTACTS_CONTAINER)

class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    company: str = ""
    message: str


#For testing: python -m uvicorn server:app --reload --host 0.0.0.0 --port 8000