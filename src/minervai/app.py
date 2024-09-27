import os

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from minervai.chain import conversational_rag_chain
from minervai.chemrxiv_utils import get_metadata_from_chemrxiv, get_relevant_papers_chemrxiv
from minervai.data import update_vector_db, vector_db

CHEMRXIV_DB_PATH = "./data/chemrxiv.jsonl"
CHEMRXIV_QUERY_PATH = "./data/chemrxiv_query.jsonl"
PDF_PATH = "./data/pdfs"
VECTOR_DB = "./data/chemrxiv_db"

if not os.path.exists(PDF_PATH):
    os.makedirs(PDF_PATH)
if not os.path.exists(VECTOR_DB):
    os.makedirs(VECTOR_DB)

GOOGLE_API_KEY = "AIzaSyCSfvhg0viV8eyQdLzr2yfI_I8qa5nGBWk"
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001", google_api_key=GOOGLE_API_KEY
)

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash", google_api_key=GOOGLE_API_KEY, temperature=0.9
)


vectorstore = vector_db(VECTOR_DB, embeddings)
retriever = vectorstore.as_retriever()


def add_documents_from_chmerxiv():
    container = st.container(border=True)
    container.markdown("""
                       ### Add papers from ChemRxiv: \n  
                       - Get the papers metadata from ChemRxiv based on the published date
                       - Filter the papers based on keywords and add them to the documents collection
                       """)
    cols = container.columns(3, vertical_alignment="bottom")
    start_date = cols[0].text_input("Start date", placeholder="YYYY-MM-DD")
    end_date = cols[1].text_input("End date", placeholder="YYYY-MM-DD")
    get_database = cols[2].button("Get metadata", key="get_database")
    if get_database:
        with st.spinner("Getting metadata"):
            _ = get_metadata_from_chemrxiv(CHEMRXIV_DB_PATH, start_date, end_date)

    cols = container.columns([0.667, 0.333], vertical_alignment="bottom")
    chemrxiv_keywords = cols[0].text_input(
        "Keywords",
        placeholder="keywords1, keywords2, ...",
    )
    chemrxiv_keywords = [chemrxiv_keywords.split(",")]
    add_chemrxiv = cols[1].button("Add papers", key="add_chemrxiv")

    if add_chemrxiv:
        with st.spinner("Adding papers"):
            _ = get_relevant_papers_chemrxiv(
                CHEMRXIV_DB_PATH, chemrxiv_keywords, CHEMRXIV_QUERY_PATH, PDF_PATH
            )
            document_list = os.listdir(PDF_PATH)
            document_list = [
                os.path.join(PDF_PATH, i) for i in document_list if i.endswith(".pdf")
            ]
            _ = update_vector_db(
                vector_db_path=VECTOR_DB,
                embeddings=embeddings,
                document_paths=document_list,
            )
            container.write("Database updated")


def add_documents_from_local():
    container = st.container(border=True)
    container.markdown("### Add documents from local folder")
    cols = container.columns([0.667, 0.333], vertical_alignment="bottom")
    documents_folder = cols[0].text_input("Folder path")
    add_documents_folder = cols[1].button("Add documents", key="add_documents_folder")
    if add_documents_folder:
        with st.spinner("Adding documents"):
            document_list = os.listdir(documents_folder)
            document_list = [
                os.path.join(documents_folder, i)
                for i in document_list
                if i.endswith(".pdf")
            ]
            _ = update_vector_db(
                vector_db_path=VECTOR_DB,
                embeddings=embeddings,
                document_paths=document_list,
            )
            container.write("Database updated")


def generate_response(question, chat_history=[]):
    model = conversational_rag_chain(retriever, llm)
    answer = model.invoke(
        {
            "input": question,
            "chat_history": chat_history,
        }
    )
    chat_history = [
        HumanMessage(content=question),
        AIMessage(content=answer["answer"]),
    ]

    return answer["answer"], chat_history


def chatbot():
    # Store LLM generated responses and chat history
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [
            {"role": "assistant", "content": "How may I help you?"}
        ]
    if "chat_history" not in st.session_state.keys():
        st.session_state.chat_history = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

    # Generate a new response if last message is not from assistant
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, chat_history = generate_response(
                    prompt, st.session_state.chat_history
                )
                st.write(response)
        message = {"role": "assistant", "content": response}
        st.session_state.messages.append(message)
        st.session_state.chat_history.extend(chat_history)


def main():
    st.title(" Chat with your documents")
    chatbot()

    with st.sidebar:
        st.title("Add Documents to Collection")
        add_documents_from_chmerxiv()
        add_documents_from_local()


if __name__ == "__main__":
    main()
