from operator import itemgetter
from typing import List, Tuple

from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    format_document,
)
from langchain_core.prompts.prompt import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import (
    RunnableBranch,
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
    RunnableSerializable,
)


def conversational_rag_chain(
    vector_store: "FAISS", llm: "ChatGoogleGenerativeAI"
) -> "RunnableSerializable":
    """
    Conversational RAG Chain

    Parameters
    ----------
    vector_store : FAISS
        The vector store used for retrieval.
    llm : ChatGoogleGenerativeAI
        The ChatGoogleGenerativeAI model used for answer synthesis.

    Returns
    -------
    RunnableSequence
        The runnable sequence representing the conversational RAG chain.
    """
    retriever = vector_store.as_retriever()
    # Condense a chat history and follow-up question into a standalone question
    _template = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, in its original language.
    Chat History:
    {chat_history}
    Follow Up Input: {question}
    Standalone question:"""  # noqa: E501
    CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(_template)

    # RAG answer synthesis prompt
    template = """Answer the question based only on the following context:
    <context>
    {context}
    </context>"""
    ANSWER_PROMPT = ChatPromptTemplate.from_messages(
        [
            ("system", template),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{question}"),
        ]
    )

    # Conversational Retrieval Chain
    DEFAULT_DOCUMENT_PROMPT = PromptTemplate.from_template(template="{page_content}")

    def _combine_documents(
        docs, document_prompt=DEFAULT_DOCUMENT_PROMPT, document_separator="\n\n"
    ):
        doc_strings = [format_document(doc, document_prompt) for doc in docs]
        return document_separator.join(doc_strings)

    def _format_chat_history(
        chat_history: List[Tuple],
    ) -> List:
        # AIMessage | HumanMessage, AIMessage | HumanMessage | ...
        buffer = []
        for human, ai in chat_history:
            buffer.append(HumanMessage(content=human))  # type: ignore
            buffer.append(AIMessage(content=ai))  # type: ignore
        return buffer

    # User input
    class ChatHistory(BaseModel):
        chat_history: List[Tuple] = Field(..., extra={"widget": {"type": "chat"}})
        question: str

    _search_query = RunnableBranch(  # type: ignore
        # If input includes chat_history, we condense it with the follow-up question
        (
            RunnableLambda(lambda x: bool(x.get("chat_history"))).with_config(
                run_name="HasChatHistoryCheck"
            ),  # Condense follow-up question and chat into a standalone_question
            RunnablePassthrough.assign(
                chat_history=lambda x: _format_chat_history(x["chat_history"])
            )
            | CONDENSE_QUESTION_PROMPT
            | llm
            | StrOutputParser(),
        ),
        # Else, we have no chat history, so just pass through the question
        RunnableLambda(itemgetter("question")),
    )

    _inputs = RunnableParallel(
        {  # type: ignore
            "question": lambda x: x["question"],
            "chat_history": lambda x: _format_chat_history(x["chat_history"]),
            "context": _search_query | retriever | _combine_documents,
        }
    ).with_types(input_type=ChatHistory)  # type: ignore

    return _inputs | ANSWER_PROMPT | llm | StrOutputParser()
