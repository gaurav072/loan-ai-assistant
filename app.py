import streamlit as st

from services.loan_assistant import analyze_customer
from services.memory_service import (
    get_customer_context,
    update_customer_context,
    clear_customer_context
)


# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="Loan Officer AI Assistant",
    page_icon="🏦",
    layout="wide"
)


# ==================================================
# HEADER
# ==================================================

st.title("🏦 Loan Officer AI Assistant")

st.caption(
    "Customer Context + RAG + Gemini"
)


# ==================================================
# SIDEBAR - CUSTOMER INPUT
# ==================================================

with st.sidebar:

    st.header("👤 Customer Information")

    current_customer = get_customer_context()

    name = st.text_input(
        "Customer Name",
        value=current_customer.get("name", "")
    )

    monthly_income = st.number_input(
        "Monthly Income (₹)",
        min_value=0,
        value=int(
            current_customer.get(
                "monthly_income",
                0
            )
        ),
        step=1000
    )

    requested_loan_amount = st.number_input(
        "Requested Loan Amount (₹)",
        min_value=0,
        value=int(
            current_customer.get(
                "requested_loan_amount",
                0
            )
        ),
        step=10000
    )

    requested_tenure_years = st.number_input(
        "Requested Tenure (Years)",
        min_value=0,
        max_value=100,
        value=int(
            current_customer.get(
                "requested_tenure_years",
                0
            )
        )
    )

    credit_score = st.number_input(
        "Credit Score",
        min_value=0,
        max_value=900,
        value=int(
            current_customer.get(
                "credit_score",
                0
            )
        )
    )

    employment_options = [
        "",
        "Salaried",
        "Self-employed"
    ]

    current_employment = current_customer.get(
        "employment_type",
        ""
    )

    employment_index = (
        employment_options.index(current_employment)
        if current_employment in employment_options
        else 0
    )

    employment_type = st.selectbox(
        "Employment Type",
        employment_options,
        index=employment_index
    )

    property_value = st.number_input(
        "Property Value (₹)",
        min_value=0,
        value=int(
            current_customer.get(
                "property_value",
                0
            )
        ),
        step=10000
    )

    st.divider()

    # ==================================================
    # LOAN OFFICER QUESTION
    # ==================================================

    st.subheader("💬 Loan Officer Question")

    question = st.text_area(
        "Ask the AI Assistant",
        placeholder=(
            "Example: Is this customer eligible "
            "for the requested home loan?"
        ),
        height=100
    )

    st.divider()

    check_eligibility = st.button(
        "🔍 Check Eligibility",
        use_container_width=True
    )

    clear_customer = st.button(
        "Clear Customer",
        use_container_width=True
    )


# ==================================================
# CLEAR CUSTOMER
# ==================================================

if clear_customer:

    clear_customer_context()

    st.session_state.pop(
        "analysis_result",
        None
    )

    st.session_state.pop(
        "analysis_sources",
        None
    )

    st.rerun()


# ==================================================
# CUSTOMER CONTEXT
# ==================================================

customer_context = get_customer_context()


# ==================================================
# CHECK ELIGIBILITY
# ==================================================

if check_eligibility:

    if not name.strip():

        st.warning(
            "Please enter the customer name."
        )

    elif not question.strip():

        st.warning(
            "Please enter a question for the AI assistant."
        )

    else:

        # ------------------------------------------
        # Save customer context
        # ------------------------------------------

        update_customer_context(
            name=name,
            monthly_income=monthly_income,
            requested_loan_amount=requested_loan_amount,
            requested_tenure_years=requested_tenure_years,
            credit_score=credit_score,
            employment_type=employment_type,
            property_value=property_value
        )

        customer_context = get_customer_context()

        # ------------------------------------------
        # Run AI analysis
        # ------------------------------------------

        with st.spinner(
            "Retrieving policies and analyzing application..."
        ):

            answer, sources = analyze_customer(
                customer_context,
                question
            )

        st.session_state.analysis_result = answer

        st.session_state.analysis_sources = sources

        st.session_state.last_question = question


# ==================================================
# DISPLAY CUSTOMER CONTEXT
# ==================================================

if customer_context.get("name"):

    st.subheader(
        f"👤 Customer: {customer_context['name']}"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Monthly Income",
            f"₹{customer_context['monthly_income']:,.0f}"
        )

        st.metric(
            "Credit Score",
            customer_context["credit_score"]
        )

    with col2:

        st.metric(
            "Loan Amount",
            f"₹{customer_context['requested_loan_amount']:,.0f}"
        )

        st.metric(
            "Tenure",
            f"{customer_context['requested_tenure_years']} years"
        )

    with col3:

        employment = (
            customer_context["employment_type"]
            or "Missing"
        )

        st.metric(
            "Employment",
            employment
        )

        property_value_display = (
            f"₹{customer_context['property_value']:,.0f}"
            if customer_context["property_value"] > 0
            else "Missing"
        )

        st.metric(
            "Property Value",
            property_value_display
        )


# ==================================================
# DISPLAY LAST QUESTION
# ==================================================

if st.session_state.get("last_question"):

    st.divider()

    st.markdown(
        f"**💬 Loan Officer Question:** "
        f"{st.session_state.last_question}"
    )


# ==================================================
# DISPLAY AI ANALYSIS
# ==================================================

if "analysis_result" in st.session_state:

    st.divider()

    st.subheader(
        "🤖 AI Eligibility Analysis"
    )

    st.markdown(
        st.session_state.analysis_result
    )

    # ----------------------------------------------
    # SOURCES
    # ----------------------------------------------

    if st.session_state.get(
        "analysis_sources"
    ):

        with st.expander(
            "📚 Retrieved Loan Policy Sources"
        ):

            for source in (
                st.session_state.analysis_sources
            ):

                st.write("•", source)


# ==================================================
# MEMORY / CUSTOMER CONTEXT
# ==================================================

with st.expander(
    "🧠 View Customer Context / Memory"
):

    st.json(
        get_customer_context()
    )