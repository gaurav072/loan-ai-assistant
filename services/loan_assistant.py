import json

from services.llm_service import get_llm
from services.rag_service import (
    retrieve_documents,
    get_sources
)

from services.guardrail_service import (
    validate_question,
    mask_pii,
    validate_customer_context,
    calculate_eligibility,
    validate_llm_output,
    safe_fallback
)


# ============================================================
# PROMPT
# ============================================================

def build_prompt(
    customer_context,
    question,
    rag_context,
    eligibility
):

    return f"""
You are a Loan Officer AI Assistant.

Analyze the customer using the deterministic
eligibility results and retrieved loan policy.

CUSTOMER:
{json.dumps(customer_context)}

QUESTION:
{question}

DETERMINISTIC ELIGIBILITY:
{json.dumps(eligibility, indent=2)}

RETRIEVED POLICY:
{rag_context}

Return ONLY:

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
- Do not invent missing information.
- Use the deterministic eligibility results.
- Do not change PASS, FAIL or MISSING status.
- Do not make a final loan approval or rejection decision.
"""


# ============================================================
# ANALYZE CUSTOMER
# ============================================================

def analyze_customer(
    customer_context,
    question
):

    # ========================================================
    # 1. INPUT GUARDRAIL
    # ========================================================

    safe, error = validate_question(
        question
    )

    if not safe:

        return (
            f"Request blocked: {error}",
            []
        )

    # ========================================================
    # 2. CUSTOMER DATA VALIDATION
    # ========================================================

    valid, errors = validate_customer_context(
        customer_context
    )

    if not valid:

        return (
            "Invalid customer data: "
            + ", ".join(errors),
            []
        )

    # ========================================================
    # 3. REMOVE UNNECESSARY PII
    # ========================================================

    llm_customer_context = {
        "name": customer_context.get("name"),
        "monthly_income": customer_context.get(
            "monthly_income"
        ),
        "requested_loan_amount": customer_context.get(
            "requested_loan_amount"
        ),
        "requested_tenure_years": customer_context.get(
            "requested_tenure_years"
        ),
        "credit_score": customer_context.get(
            "credit_score"
        ),
        "employment_type": customer_context.get(
            "employment_type"
        ),
        "property_value": customer_context.get(
            "property_value"
        )
    }

    # ========================================================
    # 4. DETERMINISTIC ELIGIBILITY
    # ========================================================

    eligibility = calculate_eligibility(
        customer_context
    )

    # ========================================================
    # 5. RAG
    # ========================================================

    safe_question = mask_pii(
        question
    )

    documents = retrieve_documents(
        safe_question,
        k=2
    )

    if not documents:

        return (
            "No relevant loan policy was found.",
            []
        )

    rag_context = "\n\n".join(
        document.page_content
        for document in documents
    )

    # ========================================================
    # 6. BUILD PROMPT
    # ========================================================

    prompt = build_prompt(
        llm_customer_context,
        safe_question,
        rag_context,
        eligibility
    )

    # ========================================================
    # 7. GEMINI
    # ========================================================

    llm = get_llm()

    response = llm.invoke(
        prompt
    )

    answer = response.content

    # ========================================================
    # 8. OUTPUT GUARDRAIL
    # ========================================================

    valid, error = validate_llm_output(
        answer
    )

    if not valid:

        return (
            safe_fallback(),
            []
        )

    # ========================================================
    # 9. SOURCES
    # ========================================================

    sources = get_sources(
        documents
    )

    return answer, sources