import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from minervai.chain import conversational_rag_chain

# openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
GOOGLE_API_KEY = "AIzaSyCSfvhg0viV8eyQdLzr2yfI_I8qa5nGBWk"
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001", google_api_key=GOOGLE_API_KEY
)

vectorstore = FAISS.load_local(
    "./data/db_test",
    embeddings,
    allow_dangerous_deserialization=True,
)
retriever = vectorstore.as_retriever()


llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash", google_api_key=GOOGLE_API_KEY, temperature=0.9
)


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

# sidebar: data source
with st.sidebar:
    st.title("Data source")
    container = st.container(border=True)
    container.write("Add papers from ChemRxiv")
    chemrxiv_tags=container.text_input(
        "Tags",
        # label_visibility=st.session_state.visibility,
        # disabled=st.session_state.disabled,
        # placeholder=st.session_state.placeholder,
    )
    cols=container.columns(2)
    start_date=cols[0].text_input("Start date")
    end_date=cols[1].text_input("End date")
    add_chemrxiv=container.button("Add papers", key="add_chemrxiv")
    # if add_chemrxiv:
        # add_papers_from_chemrxiv(chemrxiv_tags, start_date, end_date)
        # add progress bar


    container = st.container(border=True)
    container.write("Add papers from local folder")
    papers_folder=container.text_input(
        "Folder path",
        # label_visibility=st.session_state.visibility,
        # disabled=st.session_state.disabled,
        # placeholder=st.session_state.placeholder,
    )
    add_papers_folder=container.button("Add papers", key="add_papers_folder")
    # if add_papers_folder:
        # add_papers_from_folder(papers_folder)
        # add progress bar
    




st.title(" MinervAI Chatbot")

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
