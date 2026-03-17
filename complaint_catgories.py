import os
import json
import numpy as np
from google import genai
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import normalize
from typing import List
from dotenv import load_dotenv
load_dotenv()


def categorize_complaints(data_list: List[dict], category_list: List[str]) -> List[dict]:
    """
    Classifica uma lista de reclamações adicionando 'complaint_category' a cada item.

    Args:
        data_list: Lista de dicts com 'complaint_title' e 'complaint_description'
        category_list: Lista de categorias disponíveis

    Returns:
        Lista de dicts com 'complaint_category' adicionado
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set.")

    client = genai.Client(api_key=api_key)

    descriptions = [item["complaint_description"] for item in data_list]
    categories_formatted = "\n".join(f"- {cat}" for cat in category_list)
    numbered_descriptions = "\n".join(
        f"{i+1}. {desc}" for i, desc in enumerate(descriptions)
    )

    classification_prompt = f"""Você é um assistente de classificação de reclamações.

Para cada reclamação numerada abaixo, escolha a categoria mais apropriada da lista.

Reclamações:
{numbered_descriptions}

Categorias Disponíveis:
{categories_formatted}

Instruções:
- Retorne APENAS as categorias, uma por linha, na mesma ordem das reclamações.
- Formato: somente o nome da categoria, exatamente como aparece na lista.
- ESCOLHA APENAS UMA CATEGORIA POR RECLAMAÇÃO, mesmo que haja sobreposição. Escolha a mais relevante.
- Sem numeração, sem explicações, sem texto extra.
"""

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=classification_prompt
    )

    raw_lines = [line.strip() for line in response.text.strip().splitlines() if line.strip()]
    lower_map = {cat.lower(): cat for cat in category_list}

    categories_assigned = []
    for line in raw_lines:
        matched = lower_map.get(line.lower(), category_list[0])
        categories_assigned.append(matched)

    while len(categories_assigned) < len(data_list):
        categories_assigned.append(category_list[0])
    categories_assigned = categories_assigned[: len(data_list)]

    results = []
    for i, item in enumerate(data_list):
        result = item.copy()
        result["complaint_category"] = categories_assigned[i]
        results.append(result)

    return results