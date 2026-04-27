import os
import json
import numpy as np
from google import genai
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import normalize
from typing import List
import httpx
from dotenv import load_dotenv
load_dotenv()

def categorize_complaints(data_list: List[dict], category_list: List[str]) -> List[dict]:
    """
    Classifica uma lista de reclamações adicionando 'complaint_category' a cada item.

    Args:
        data_list: Lista de dicts com 'complaint_title' e 'complaint_description'
        category_list: Lista de categorias disponíveis

    Returns:
        Lista de dicts com 'complaint_category' e 'complaint_importance' adicionado
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    model_name = os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    openrouter_model = os.environ.get("OPENROUTER_MODEL")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set.")

    descriptions = [item["complaint_description"] for item in data_list]
    categories_formatted = "\n".join(f"- {cat}" for cat in category_list)
    numbered_descriptions = "\n".join(
        f"{i+1}. {desc}" for i, desc in enumerate(descriptions)
    )

    classification_prompt = f"""Você é um assistente de classificação de reclamações.

Para cada reclamação numerada abaixo, escolha a categoria mais apropriada da lista e defina a importância de 1 a 5 (5 sendo o mais importante).

Reclamações:
{numbered_descriptions}

Categorias Disponíveis:
{categories_formatted}

Instruções:
- Retorne a categoria e a importância separadas por pipe (|), uma por linha, na mesma ordem das reclamações.
- Formato: Nome da Categoria | Número
- ESCOLHA APENAS UMA CATEGORIA POR RECLAMAÇÃO.
- Sem numeração, sem explicações, sem texto extra.
"""

    response_text = ""

    # Tenta Gemini primeiro
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=classification_prompt
        )
        response_text = response.text
    except Exception as e:
        print(f"Gemini falhou, tentando OpenRouter... Erro: {e}")
        # Fallback para OpenRouter
        try:
            headers = {
                "Authorization": f"Bearer {openrouter_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": openrouter_model,
                "messages": [{"role": "user", "content": classification_prompt}]
            }
            with httpx.Client() as http_client:
                res = http_client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                data = res.json()
                response_text = data["choices"][0]["message"]["content"]
        except Exception as e2:
            print(f"OpenRouter também falhou: {e2}")
            response_text = ""

    raw_lines = [line.strip() for line in response_text.strip().splitlines() if line.strip()]
    lower_map = {cat.lower(): cat for cat in category_list}

    categories_assigned = []
    importances_assigned = []

    for line in raw_lines:
        if "|" in line:
            parts = line.split("|")
            cat_part = parts[0].strip()
            imp_part = "".join(filter(str.isdigit, parts[1].strip()))
            
            categories_assigned.append(lower_map.get(cat_part.lower(), category_list[0]))
            importances_assigned.append(int(imp_part) if imp_part else 1)
        else:
            categories_assigned.append(lower_map.get(line.lower(), category_list[0]))
            importances_assigned.append(1)

    while len(categories_assigned) < len(data_list):
        categories_assigned.append(category_list[0])
        importances_assigned.append(1)
        
    categories_assigned = categories_assigned[: len(data_list)]
    importances_assigned = importances_assigned[: len(data_list)]

    results = []
    for i, item in enumerate(data_list):
        result = item.copy()
        result["complaint_category"] = categories_assigned[i]
        result["complaint_importance"] = importances_assigned[i]
        results.append(result)

    return results