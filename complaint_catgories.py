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


complaints_list = [
  {
    "complaint_title":"Cobrança Indevida",
    "complaint_description":"Fui cobrado(a) em meu extrato por uma \"Tarifa de Manutenção de Conta Premium\" no valor de R$ 45,00. Nunca solicitei ou autorizei a migração para um pacote de serviços Premium, meu contrato prevê apenas o pacote de serviços essenciais, sem custos. Solicito o estorno imediato do valor e o cancelamento desta cobrança recorrente.",
    "complaint_creation_date":"18/10/2025 às 20:31",
    "complaint_solution":"1. **Estorno e Correção Imediata:** Realizar o estorno imediato de R$ 45,00 para a conta do cliente, com a devida justificativa no extrato (Ex: \"Estorno Tarifa Indevida\").\n2. **Bloqueio da Cobrança:** Revisar o cadastro do cliente e a configuração do pacote de serviços, garantindo que a Tarifa Premium seja cancelada permanentemente, mantendo-o no pacote Essencial.\n3. **Análise de Causa_Raiz:** Auditar o processo de migração de pacotes para identificar a falha que gerou a cobrança (erro de sistema, erro humano ou contratação não solicitada) e aplicar correção sistêmica para evitar reincidência.",
    "complaint_num":1,
    "complaint_per":0.167
  },
  {
    "complaint_title":"Problemas de Pagamento",
    "complaint_description":"Realizei o pagamento de um boleto no valor de R$ 850,00 no dia 15/10/2025, às 14:30h, através do aplicativo do banco. O comprovante foi gerado, mas o beneficiário informou que o pagamento não foi compensado. O débito ocorreu em minha conta, mas o banco alega falha sistêmica e o boleto está em atraso. Exijo a confirmação urgente do repasse ou o estorno imediato para que eu possa pagar novamente sem multas.",
    "complaint_creation_date":"18/10/2025 às 09:54",
    "complaint_solution":"1. **Resolução Prioritária:** Abrir uma investigação urgente na área de TI/Compensação.\n2. **Comunicação e Estorno/Repasse:** Em até 4 horas úteis, confirmar o status:\na) Se o repasse puder ser forçado (compensação imediata), fazê-lo e enviar o comprovante ao cliente.\nb) Caso contrário, realizar o estorno imediato de R$ 850,00 para a conta do cliente.\n3. **Mitigação de Danos:** Emitir uma declaração oficial (carta ou e-mail com timbre do banco) ao cliente, assumindo a falha sistêmica e se responsabilizando por quaisquer multas e juros de atraso que o cliente venha a ter com o beneficiário do boleto.",
    "complaint_num":2,
    "complaint_per":0.167
  },
  {
    "complaint_title":"Conta Bloqueada",
    "complaint_description":"Meu cartão de débito e crédito foi bloqueado repentinamente sem aviso prévio. Ao entrar em contato, fui informado(a) que houve uma \"análise de segurança\", o que causou grande transtorno, pois estava tentando realizar uma compra essencial. A conta continua bloqueada há mais de 24 horas, impedindo qualquer movimentação, mesmo após confirmação de identidade. Solicito o desbloqueio imediato e explicação formal.",
    "complaint_creation_date":"19/10/2025 às 10:25",
    "complaint_solution":"1. **Desbloqueio Imediato:** Priorizar o atendimento e, após a confirmação de identidade do cliente (seja por senha, biometria ou token), realizar o desbloqueio do cartão/conta em até 1 hora.\n2. **Aviso Prévio:** Revisar a política de segurança para que, em casos de bloqueio administrativo, o cliente receba uma notificação (SMS/e-mail/Push Notification) antes do bloqueio, solicitando a validação da transação suspeita, se possível.\n3. **Comunicação:** Enviar um comunicado formal ao cliente explicando o motivo exato do bloqueio (Ex: Compra em país de risco, valor incomum), pedindo desculpas pelo transtorno e garantindo que o sistema de monitoramento será calibrado para evitar falsos positivos.",
    "complaint_num":3,
    "complaint_per":0.167
  },
  {
    "complaint_title":"Resgate de Investimento Não Realizado",
    "complaint_description":"Solicitei o resgate total do meu investimento em CDB (Rendimento Automático) com liquidez D+1 no dia 17/10/2025, respeitando o prazo de corte. No entanto, o valor não foi creditado na minha conta corrente no prazo estipulado (18/10/2025). O aplicativo exibe status de \"em processamento\" e o gerente não oferece uma data concreta. Preciso do valor com urgência para cobrir despesas.",
    "complaint_creation_date":"19/10/2025 às 10:23",
    "complaint_solution":"1. **Resgate de Urgência:** Realizar a liquidação manual do valor do investimento pendente (R$ X.XXX,XX + rendimentos D+1) na conta corrente do cliente em até 2 horas após o registro da reclamação.\n2. **Compensação por Perdas:** Caso o cliente comprove ter sofrido perda (Ex: Pagamento de conta em atraso por falta de saldo), o banco deve se prontificar a compensar os juros e multas decorrentes.\n3. **Atualização de Status:** Implementar uma melhoria no aplicativo e no sistema de retaguarda para que o status de resgate seja claro (Ex: \"Resgate Solicitado\", \"Em Liquidação\", \"Creditado\") e que os prazos contratuais sejam rigorosamente cumpridos.",
    "complaint_num":4,
    "complaint_per":0.167
  },
  {
    "complaint_title":"Cobrança Indevida",
    "complaint_description":"Fui cobrado(a) indevidamente por juros e IOF de cheque especial referentes ao dia 05/10/2025. O saldo negativo que gerou a cobrança ocorreu devido a um estorno não processado de uma TED que falhou no dia anterior, mas que foi debitada da minha conta. O erro é do sistema do banco e a cobrança dos juros é injusta. Exijo o cancelamento dos juros e o estorno do valor cobrado.",
    "complaint_creation_date":"19/10/2025 às 10:14",
    "complaint_solution":"1. **Estorno dos Encargos:** Realizar o estorno imediato de todos os juros e IOF cobrados no cheque especial (repetição do indébito), pois o saldo negativo foi provocado por erro interno do banco na compensação da TED.\n2. **Correção do Lançamento:** Assegurar que o valor total da TED seja creditado corretamente na conta.\n3. **Monitoramento e Alerta:** Implementar um alerta sistêmico que identifique débitos de cheque especial originados de falhas de processamento de TED/PIX e suspenda automaticamente a cobrança de juros até a resolução do problema.",
    "complaint_num":5,
    "complaint_per":0.167
  },
  {
    "complaint_title":"Atendimento/Suporte Deficiente",
    "complaint_description":"Tentei contato com a central de atendimento (SAC) por 4 vezes nas últimas 48 horas para tratar de uma divergência em minha fatura de cartão. O tempo de espera em todas as ligações ultrapassou 30 minutos, e em duas ocasiões a ligação \"caiu\" após ser transferida para o setor responsável, sem que meu problema fosse solucionado. O número de protocolo fornecido não gera acompanhamento. A falta de resolutividade do atendimento é inaceitável.",
    "complaint_creation_date":"19/10/2025 às 10:14",
    "complaint_solution":"1. **Contato Proativo e Resolução:** Um supervisor deve entrar em contato imediato com o cliente para resolver a divergência na fatura.\n2. **Melhoria do SAC:** Reduzir o tempo médio de espera do SAC para um padrão aceitável (máximo de 5 minutos, por exemplo) e aumentar o número de agentes em horários de pico.\n3. **Sistema de Protocolo Efetivo:** Garantir que o protocolo gerado seja rastreável e que o agente da próxima ligação possa retomar o atendimento do ponto exato onde parou, evitando que o cliente precise repetir toda a história.\n4. **Treinamento:** Treinar a equipe para evitar a queda de ligação em transferências e garantir que o primeiro contato tente resolver o problema (First Call Resolution _ FCR).",
    "complaint_num":6,
    "complaint_per":0.1667
  }
]

teste = categorize_complaints(
    complaints_list,
    [
        "Cobrança Indevida",
        "Problemas de Pagamento",
        "Conta Bloqueada",
        "Resgate de Investimento Não Realizado",
        "Atendimento/Suporte Deficiente"
    ]
)

print(teste)
