import os
from azure.cosmos import CosmosClient


def adjust_complaints(complaints: list[dict]) -> list[dict]:
    COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
    COSMOS_KEY = os.getenv("COSMOS_KEY")
    COSMOS_DATABASE = os.getenv("COSMOS_DATABASE")
    COSMOS_CONTAINER = os.getenv("COSMOS_CONTAINER")

    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = client.get_database_client(COSMOS_DATABASE)
    container = database.get_container_client(COSMOS_CONTAINER)

    # Buscar o maior id existente no banco
    query = "SELECT VALUE c.id FROM c WHERE c.pk = 'complaint'"
    existing_ids = list(container.query_items(query=query, enable_cross_partition_query=True))

    numeric_ids = []
    for id_val in existing_ids:
        try:
            numeric_ids.append(int(id_val))
        except (ValueError, TypeError):
            pass

    next_id = (max(numeric_ids) + 1) if numeric_ids else 1

    # Enriquecer cada reclamação e retornar
    enriched = []
    for i, complaint in enumerate(complaints):
        enriched.append({
            **complaint,
            "id": str(next_id + i),
            "pk": "complaint",
            "complaint_origin": "reclameaqui.com.br",
        })

    return enriched