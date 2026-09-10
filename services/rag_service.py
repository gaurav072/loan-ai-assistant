import os

from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader
)
from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings
)
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from config import LOAN_DATA_DIR


def get_embeddings():

    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001"
    )


def load_documents():

    loader = DirectoryLoader(
        str(LOAN_DATA_DIR),
        glob="*.txt",
        loader_cls=TextLoader
    )

    return loader.load()


def split_documents(documents):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    return splitter.split_documents(documents)


def create_vectorstore():

    documents = load_documents()

    chunks = split_documents(documents)

    embeddings = get_embeddings()

    return Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name="loan_knowledge"
    )


def retrieve_documents(question, k=3):

    vectorstore = create_vectorstore()

    return vectorstore.similarity_search(
        question,
        k=k
    )


def get_sources(documents):

    return list(
        set(
            os.path.basename(
                document.metadata.get(
                    "source",
                    "Unknown"
                )
            )
            for document in documents
        )
    )