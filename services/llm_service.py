from langchain_google_genai import ChatGoogleGenerativeAI


def get_llm():

    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        max_output_tokens=1000
    )