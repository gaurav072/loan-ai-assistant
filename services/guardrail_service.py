# services/guardrail_service.py

import re
import logging


# ============================================================
# PII PATTERNS
# ============================================================

PII_PATTERNS = {

    "EMAIL": (
        r"\b[A-Za-z0-9._%+-]+@"
        r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    ),

    "PHONE": (
        r"(?:\+91[-\s]?)?[6-9]\d{9}"
    ),

    "PAN": (
        r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"
    ),

    "AADHAAR": (
        r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"
    ),
}


# ============================================================
# PROMPT INJECTION PATTERNS
# ============================================================

PROMPT_INJECTION_PATTERNS = [

    r"ignore previous instructions",
    r"ignore all previous instructions",
    r"disregard previous instructions",
    r"forget your instructions",

    r"reveal your system prompt",
    r"show me your system prompt",
    r"print your system prompt",

    r"bypass your rules",
    r"override your rules",

    r"jailbreak",
]


# ============================================================
# FORBIDDEN LENDING DECISION PATTERNS
# ============================================================

FORBIDDEN_DECISION_PATTERNS = [

    r"\bloan\s+approved\b",
    r"\bloan\s+rejected\b",

    r"\bapplication\s+approved\b",
    r"\bapplication\s+rejected\b",

    r"\bguaranteed\s+approval\b",
    r"\bguaranteed\s+loan\b",

    r"\bdefinitely\s+eligible\b",
    r"\bdefinitely\s+approved\b",
]
logger = logging.getLogger(__name__)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

logger.setLevel(logging.INFO)


# ============================================================
# INPUT GUARDRAIL
# ============================================================

def validate_question(question: str):

    if not question:
        return False, "Question cannot be empty."

    question = question.strip()

    if not question:
        return False, "Question cannot be empty."

    if len(question) > 1000:
        return False, "Question is too long."

    question_lower = question.lower()

    for pattern in PROMPT_INJECTION_PATTERNS:

        if re.search(
            pattern,
            question_lower
        ):
            logger.warning(
            "GUARDRAIL_BLOCKED | type=prompt_injection"
)
            return (
                False,
                "Prompt injection detected."
            )

    return True, None


# ============================================================
# PII DETECTION
# ============================================================

def detect_pii(text: str):

    detected = []

    for pii_type, pattern in PII_PATTERNS.items():

        if re.search(
            pattern,
            text
        ):
            detected.append(pii_type)

    return detected


# ============================================================
# PII MASKING
# ============================================================

def mask_pii(text: str):

    masked_text = text

    # Email
    masked_text = re.sub(
        PII_PATTERNS["EMAIL"],
        "[EMAIL_REDACTED]",
        masked_text
    )

    # Phone
    masked_text = re.sub(
        PII_PATTERNS["PHONE"],
        "[PHONE_REDACTED]",
        masked_text
    )

    # PAN
    masked_text = re.sub(
        PII_PATTERNS["PAN"],
        "[PAN_REDACTED]",
        masked_text
    )

    # Aadhaar
    masked_text = re.sub(
        PII_PATTERNS["AADHAAR"],
        "[AADHAAR_REDACTED]",
        masked_text
    )

    return masked_text


# ============================================================
# CUSTOMER DATA VALIDATION
# ============================================================

def validate_customer_context(customer):

    errors = []

    # ----------------------------------------
    # Income
    # ----------------------------------------

    income = customer.get(
        "monthly_income"
    )

    if income is not None:

        if income < 0:
            errors.append(
                "Monthly income cannot be negative."
            )

    # ----------------------------------------
    # Loan amount
    # ----------------------------------------

    loan_amount = customer.get(
        "requested_loan_amount"
    )

    if loan_amount is not None:

        if loan_amount < 0:
            errors.append(
                "Loan amount cannot be negative."
            )

    # ----------------------------------------
    # Credit score
    # ----------------------------------------

    credit_score = customer.get(
        "credit_score"
    )

    if credit_score is not None:

        if credit_score < 0 or credit_score > 900:
            errors.append(
                "Credit score must be between 0 and 900."
            )

    # ----------------------------------------
    # Tenure
    # ----------------------------------------

    tenure = customer.get(
        "requested_tenure_years"
    )

    if tenure is not None:

        if tenure < 0:
            errors.append(
                "Loan tenure cannot be negative."
            )

    # ----------------------------------------
    # Property value
    # ----------------------------------------

    property_value = customer.get(
        "property_value"
    )

    if property_value is not None:

        if property_value < 0:
            errors.append(
                "Property value cannot be negative."
            )

    # ----------------------------------------
    # Result
    # ----------------------------------------

    if errors:
        return False, errors

    return True, []


# ============================================================
# DETERMINISTIC LOAN ELIGIBILITY
# ============================================================

def calculate_eligibility(customer):

    result = {}

    # ----------------------------------------
    # Credit Score
    # ----------------------------------------

    credit_score = customer.get(
        "credit_score"
    )

    if credit_score is None or credit_score == 0:

        result["credit_score"] = {
            "status": "MISSING",
            "reason": "Credit score is required."
        }

    elif credit_score >= 700:

        result["credit_score"] = {
            "status": "PASS",
            "reason": f"{credit_score} meets minimum 700."
        }

    else:

        result["credit_score"] = {
            "status": "FAIL",
            "reason": f"{credit_score} is below minimum 700."
        }

    # ----------------------------------------
    # Income
    # ----------------------------------------

    income = customer.get(
        "monthly_income"
    )

    if income is None or income == 0:

        result["income"] = {
            "status": "MISSING",
            "reason": "Monthly income is required."
        }

    elif income >= 50000:

        result["income"] = {
            "status": "PASS",
            "reason": f"₹{income:,.0f} meets minimum ₹50,000."
        }

    else:

        result["income"] = {
            "status": "FAIL",
            "reason": f"₹{income:,.0f} is below ₹50,000."
        }

    # ----------------------------------------
    # Tenure
    # ----------------------------------------

    tenure = customer.get(
        "requested_tenure_years"
    )

    if tenure is None or tenure == 0:

        result["tenure"] = {
            "status": "MISSING",
            "reason": "Loan tenure is required."
        }

    elif tenure <= 30:

        result["tenure"] = {
            "status": "PASS",
            "reason": "Tenure is within 30-year limit."
        }

    else:

        result["tenure"] = {
            "status": "FAIL",
            "reason": (
                f"{tenure} years exceeds maximum 30 years."
            )
        }

    # ----------------------------------------
    # Employment
    # ----------------------------------------

    employment = customer.get(
        "employment_type"
    )

    if not employment:

        result["employment"] = {
            "status": "MISSING",
            "reason": "Employment type is required."
        }

    else:

        result["employment"] = {
            "status": "PASS",
            "reason": f"Employment type: {employment}."
        }

    # ----------------------------------------
    # LTV
    # ----------------------------------------

    property_value = customer.get(
        "property_value"
    )

    loan_amount = customer.get(
        "requested_loan_amount"
    )

    if not property_value or not loan_amount:

        result["ltv"] = {
            "status": "MISSING",
            "reason": (
                "Property value and loan amount are required."
            )
        }

    else:

        ltv = (
            loan_amount /
            property_value
        ) * 100

        # Policy
        if property_value < 5000000:
            maximum_ltv = 90
        else:
            maximum_ltv = 80

        if ltv <= maximum_ltv:

            result["ltv"] = {
                "status": "PASS",
                "reason": (
                    f"LTV {ltv:.1f}% is within "
                    f"maximum {maximum_ltv}%."
                )
            }

        else:

            result["ltv"] = {
                "status": "FAIL",
                "reason": (
                    f"LTV {ltv:.1f}% exceeds "
                    f"maximum {maximum_ltv}%."
                )
            }

    return result


# ============================================================
# OUTPUT GUARDRAIL
# ============================================================

def validate_llm_output(response: str):

    if not response:

        return False, "Empty AI response."

    # ----------------------------------------
    # Maximum length
    # ----------------------------------------

    if len(response.split()) > 500:

        return (
            False,
            "AI response exceeded 500 words."
        )

    response_lower = response.lower()

    # ----------------------------------------
    # Final lending decision
    # ----------------------------------------

    for pattern in FORBIDDEN_DECISION_PATTERNS:

        if re.search(
            pattern,
            response_lower
        ):

            return (
                False,
                "AI attempted to make a final lending decision."
            )

    # ----------------------------------------
    # PII leakage
    # ----------------------------------------

    pii_found = detect_pii(
        response
    )

    if pii_found:

        return (
            False,
            "PII detected in AI response: "
            + ", ".join(pii_found)
        )

    # ----------------------------------------
    # Required sections
    # ----------------------------------------

    required_sections = [
        "Customer:",
        "Answer:",
        "Eligibility:",
        "Credit Score:",
        "Income:",
        "Tenure:",
        "Employment:",
        "LTV:",
        "Action:"
    ]

    for section in required_sections:

        if section not in response:

            return (
                False,
                f"Missing required section: {section}"
            )

    return True, None


# ============================================================
# FALLBACK
# ============================================================

def safe_fallback():

    return """
The AI response could not be safely generated.

Please review the customer information
and loan policy manually.
""".strip()