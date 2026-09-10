import streamlit as st


def initialize_customer_context():

    if "customer_context" not in st.session_state:

        st.session_state.customer_context = {
            "name": "",
            "monthly_income": 0,
            "requested_loan_amount": 0,
            "requested_tenure_years": 0,
            "credit_score": 0,
            "employment_type": "",
            "property_value": 0
        }

    return st.session_state.customer_context


def update_customer_context(
    name,
    monthly_income,
    requested_loan_amount,
    requested_tenure_years,
    credit_score,
    employment_type,
    property_value
):

    st.session_state.customer_context = {
        "name": name,
        "monthly_income": monthly_income,
        "requested_loan_amount": requested_loan_amount,
        "requested_tenure_years": requested_tenure_years,
        "credit_score": credit_score,
        "employment_type": employment_type,
        "property_value": property_value
    }


def get_customer_context():

    return initialize_customer_context()


def clear_customer_context():

    st.session_state.customer_context = {
        "name": "",
        "monthly_income": 0,
        "requested_loan_amount": 0,
        "requested_tenure_years": 0,
        "credit_score": 0,
        "employment_type": "",
        "property_value": 0
    }