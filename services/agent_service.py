from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware

from services.llm_service import get_llm
from services.rag_tool import search_loan_policy


def create_loan_agent():

    llm = get_llm()

    return create_agent(

        model=llm,

        tools=[
            search_loan_policy
        ],

        system_prompt="""
You are a Loan Officer AI Assistant.

Your responsibility is to assist loan officers
with customer analysis.

Use the search_loan_policy tool for policy-related
questions.

Rules:

1. Use retrieved loan policy as the authoritative
   source for policy questions.

2. Do not invent missing customer information.

3. Do not make final loan approval or rejection
   decisions.

4. Clearly identify PASS, FAIL and MISSING criteria.

5. Final lending decisions must remain with
   deterministic underwriting rules and human review.

6. Keep responses concise.

Return:

Customer:
Answer:
Eligibility:
Action:
""",

        middleware=[

            # Email
            PIIMiddleware(
                "email",
                strategy="redact",
                apply_to_input=True,
                apply_to_output=True,
            ),

            # Phone
            PIIMiddleware(
                "phone_number",
                detector=r"(?:\+91[-\s]?)?[6-9]\d{9}",
                strategy="mask",
                apply_to_input=True,
                apply_to_output=True,
            ),

            # PAN
            PIIMiddleware(
                "pan",
                detector=r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
                strategy="redact",
                apply_to_input=True,
                apply_to_output=True,
            ),

            # Aadhaar
            PIIMiddleware(
                "aadhaar",
                detector=r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
                strategy="redact",
                apply_to_input=True,
                apply_to_output=True,
            ),
        ],
    )