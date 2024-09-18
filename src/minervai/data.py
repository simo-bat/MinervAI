import faiss
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore

from langchain_community.document_loaders import PDFMinerLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_core.documents import Document
from langchain_core.embeddings.embeddings import Embeddings

# TODO: add additional metadata to documents
# TODO: consider to use PyMuPDFLoader, more efficient and more complete metadata
# TODO: check if the document is already in the database before adding it


def vector_db(database_name: str, embeddings: "Embeddings") -> FAISS:
    """
    load a FAISS vector database if it exists, otherwise create a new one

    Parameters
    ----------
    database_name : str
        The name of the vector database
    embeddings : Embeddings
        The embeddings object to use for the vector database

    Returns
    -------
    vector_store : FAISS
        A FAISS vector database

    """
    database_path = f"./data/{database_name}"
    try:
        vector_store = FAISS.load_local(
            database_path, embeddings, allow_dangerous_deserialization=True
        )
    except Exception as e:
        print(e)
        index = faiss.IndexFlatL2(len(embeddings.embed_query("hello world")))
        vector_store = FAISS(
            embedding_function=embeddings,
            index=index,
            docstore=InMemoryDocstore(),
            index_to_docstore_id={},
        )
    return vector_store


def load_document(document_path: str) -> "list[Document]":
    """
    Load a document from a bucket, split it and return a list of Document objects

    Parameters
    ----------
    document_path : str
        The path to the document in the bucket

    Returns
    -------
    list[Document]
        A list of Document objects

    """

    def len_func(text: str) -> int:
        return len(text)

    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", " "],
        chunk_size=20480,
        chunk_overlap=2048,
        length_function=len_func,
        is_separator_regex=False,
    )

    return PDFMinerLoader(document_path).load_and_split(text_splitter)


def load_list_documents(document_paths: list) -> list["Document"]:
    """
    Load a list of documents from a bucket, split them and return a list of Document objects

    Parameters
    ----------
    document_paths : list
        A list of paths to the documents in the bucket

    Returns
    -------
    list[Document]
        A list of Document objects

    """

    documents = []
    for document_path in document_paths:
        documents.extend(load_document(document_path))
    return documents


def add_documents_to_db(
    documents: list["Document"], vector_store: "FAISS", database_name: str
) -> None:
    """
    Add a list of documents to a vector database

    Parameters
    ----------

    """
    vector_store.add_documents(documents)
    vector_store.save_local(f"./data/{database_name}")


def update_vector_db(
    database_name: str, embeddings: "Embeddings", document_paths: list
) -> FAISS:
    vector_store = vector_db(database_name, embeddings)
    documents = load_list_documents(document_paths)
    add_documents_to_db(documents, vector_store, database_name)
    return vector_store
