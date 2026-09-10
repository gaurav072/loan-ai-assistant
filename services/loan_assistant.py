import json

from services.llm_service import get_llm
from services.rag_service import (
    retrieve_documents,
    get_sources
)


def build_prompt(customer_context, question, rag_context):

    return f"""
You are a Loan Officer AI Assistant.

Analyze the customer against the retrieved loan policy
and answer the loan officer's question.

CUSTOMER:
{json.dumps(customer_context)}

QUESTION:
{question}

RETRIEVED POLICY:
{rag_context}

Return ONLY the following format:

Customer: <name>

Answer:
<short answer to the question>

Eligibility:
- Credit Score: <PASS/FAIL/MISSING> - <short reason>
- Income: <PASS/FAIL/MISSING> - <short reason>
- Tenure: <PASS/FAIL/MISSING> - <short reason>
- Employment: <PASS/FAIL/MISSING> - <short reason>
- LTV: <PASS/FAIL/MISSING> - <short reason>

Action: <one short sentence>

RULES:
- Maximum 500 words.
- Be concise.
- Answer the QUESTION directly.
- Do not provide a Customer Summary.
- Do not repeat the policy.
- Do not give long explanations.
- Do not invent missing information.
- Mark unavailable customer information as MISSING.
- Do not make a final loan approval or rejection decision.
"""

def analyze_customer(customer_context, question):

    # ---------------------------------------------
    # 1. Retrieve relevant loan policies
    # ---------------------------------------------

    query = f"""
    Home loan eligibility requirements relevant to:

    {question}

    Include applicable rules for:
    minimum income, credit score, FOIR,
    loan tenure, loan-to-value and employment.
    """

    documents = retrieve_documents(query, k=2)

    # ---------------------------------------------
    # 2. Build RAG context
    # ---------------------------------------------

    rag_context = "\n\n".join(
        document.page_content
        for document in documents
    )

    # ---------------------------------------------
    # 3. Build prompt
    # ---------------------------------------------

    prompt = build_prompt(
        customer_context,
        question,
        rag_context
    )

    # ---------------------------------------------
    # 4. Call Gemini
    # ---------------------------------------------

    llm = get_llm()

    response = llm.invoke(prompt)

    # ---------------------------------------------
    # 5. Get sources
    # ---------------------------------------------

    sources = get_sources(documents)

    return response.content, sources