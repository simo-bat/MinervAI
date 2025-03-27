import os

import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from minervai.chain import conversational_rag_chain
from minervai.data import update_vector_db, vector_db
from minervai.xrxiv_utils import (
    download_papers_from_archive,
    filter_metadata_from_archive,
    get_metadata_from_archive,
)

DUMP_PATH = "./data/dump"
QUERY_PATH = "./data/query"
PDF_PATH = "./data/pdfs"
VECTOR_DB = "./data/vector_db"


os.makedirs(PDF_PATH, exist_ok=True)
os.makedirs(VECTOR_DB, exist_ok=True)


def get_info():
    container = st.container(border=True)
    container.markdown("### LLM API ")
    cols = container.columns(2, vertical_alignment="bottom")
    llm_option = cols[0].selectbox("Select Models", ["Gemini", "OpenAI"])
    api_key = container.text_input("### LLM API Key")

    return llm_option, api_key


def add_documents_from_archive(embeddings):
    container = st.container(border=True)
    container.markdown(
        """
                       ### Add papers from X-rxiv: \n
                       - Select an archive and get the papers based on the
                       publishing date. Note that this can take more than
                       1 hour.
                       - Filter the papers based on keywords and add them to
                       the documents collection
        """
    )
    cols = container.columns(2, vertical_alignment="bottom")
    archive = cols[0].selectbox(
        "Select Archive", ["medrxiv", "chemrxiv", "biorxiv", "arxiv"]
    )
    dump_path = f"{DUMP_PATH}_{archive}.jsonl"
    query_path = f"{QUERY_PATH}_{archive}.jsonl"
    cols = container.columns(3, vertical_alignment="bottom")
    start_date = cols[0].text_input("Start date", placeholder="YYYY-MM-DD")
    end_date = cols[1].text_input("End date", placeholder="YYYY-MM-DD")
    get_database = cols[2].button("Get metadata", key="get_database")
    if get_database:
        with st.spinner("Getting metadata"):
            num_papers, failed_dates = get_metadata_from_archive(
                dump_path, start_date, end_date, archive
            )
            st.write(f"Number of papers retrieved: {num_papers}")

    cols = container.columns([0.667, 0.333], vertical_alignment="bottom")
    keywords = cols[0].text_input(
        "Keywords",
        placeholder="keywords1, keywords2, ...",
    )
    keywords = [keywords.split(",")]
    add_archive = cols[1].button("Add papers", key="add_archive")

    if add_archive:
        with st.spinner("Adding papers"):
            querier_df = filter_metadata_from_archive(dump_path, keywords, query_path)
            if querier_df.shape[0] > 0:
                n_downloaded_papers, _ = download_papers_from_archive(
                    query_path, PDF_PATH
                )
                cols[0].write(f"Number of papers dowloaded: {n_downloaded_papers}")
            else:
                cols[0].write("No papers found")

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


def add_documents_from_local(embeddings):
    container = st.container(border=True)
    container.markdown("### Add documents from local folder")
    cols = container.columns([0.667, 0.333], vertical_alignment="bottom")
    documents_folder = cols[0].text_input("Folder path")
    add_documents_folder = cols[1].button("Add documents", key="add_documents_folder")
    if add_documents_folder and documents_folder:
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


def generate_response(retriever, llm, question, chat_history=[]):
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


def chatbot(retriever, llm):
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
                    retriever, llm, prompt, st.session_state.chat_history
                )
                st.write(response)
        message = {"role": "assistant", "content": response}
        st.session_state.messages.append(message)
        st.session_state.chat_history.extend(chat_history)


def main():
    with st.sidebar:
        st.title("Add Documents to Collection")
        llm_model, api_key = get_info()
        if api_key:
            if llm_model == "OpenAI":
                embeddings = OpenAIEmbeddings(
                    model="gpt-3.5-turbo", openai_api_key=api_key
                )
                llm = ChatOpenAI(
                    model="gpt-3.5-turbo", openai_api_key=api_key, temperature=0.9
                )
            else:
                embeddings = GoogleGenerativeAIEmbeddings(
                    model="models/embedding-001", google_api_key=api_key
                )
                llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash", google_api_key=api_key, temperature=0.9
                )
            # if not os.path.exists(vector_db_path):
            #     os.makedirs(vector_db_path)
            vectorstore = vector_db(VECTOR_DB, embeddings)
            retriever = vectorstore.as_retriever()
            add_documents_from_archive(embeddings)
            add_documents_from_local(embeddings)

    st.title(" Chat with your documents")
    if api_key:
        chatbot(retriever, llm)


if __name__ == "__main__":
    main()
