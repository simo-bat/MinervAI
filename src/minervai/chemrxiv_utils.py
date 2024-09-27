import json
from typing import List

import pandas as pd
from paperscraper.get_dumps import chemrxiv
from paperscraper.pdf import save_pdf_from_dump
from paperscraper.xrxiv.xrxiv_query import XRXivQuery

TODO = """generalize for other sources"""


def get_metadata_from_chemrxiv(
    chemrxiv_db_path: str, begin_date: str | None = None, end_date: str | None = None
):
    """
    Retrieves metadata from the ChemRxiv database.

    Parameters
    ----------
    chemrxiv_db_path: str
        The file path where the retrieved metadata is saved.
    begin_date : str | None, optional
        The beginning date of the time range to retrieve metadata from. If not provided, the default is None.
    end_date : str | None, optional
        The end date of the time range to retrieve metadata from. If not provided, the default is None.

    Returns
    -------
    str
        The file path where the retrieved metadata is saved.
    """

    try:
        chemrxiv(begin_date=begin_date, end_date=end_date, save_path=chemrxiv_db_path)
    except Exception as e:
        print(f"Error: {e}")


# def get_metadata_from_chemrxiv(
#     begin_date: str | None = None, end_date: str | None = None
# ) -> str:
#     """
#     Retrieves metadata from the ChemRxiv database.

#     Parameters
#     ----------
#     begin_date : str | None, optional
#         The beginning date of the time range to retrieve metadata from. If not provided, the default is None.
#     end_date : str | None, optional
#         The end date of the time range to retrieve metadata from. If not provided, the default is None.

#     Returns
#     -------
#     str
#         The file path where the retrieved metadata is saved.
#     """

#     if begin_date is None:
#         chemrxiv_jsonl_path = "./data/chemarxiv.jsonl"
#     else:
#         chemrxiv_jsonl_path = f"./data/jsonls/chemarxiv_{begin_date.replace('-', '')}_{end_date.replace('-', '')}.jsonl"  # type: ignore

#     try:
#         chemrxiv(
#             begin_date=begin_date, end_date=end_date, save_path=chemrxiv_jsonl_path
#         )
#     except Exception as e:
#         print(f"Error: {e}")
#     return chemrxiv_jsonl_path


def concat_metadata_from_chemrxiv(
    jsonl_files: List[str], output_file_path: str
) -> None:
    """
    Concatenates metadata from multiple JSONL files into a single output file.

    Parameters
    ----------
    jsonl_files : List[str]
        The list of JSONL files containing metadata.
    output_file_path : str
        The file path where the concatenated metadata will be saved.

    Returns
    -------
    None
    """

    output_file = []
    for jsonl_file in jsonl_files:
        with open(jsonl_file, "r") as f:
            for line in f:
                output_file.append(json.loads(line))

    with open(output_file_path, "w") as f:
        for item in output_file:
            f.write(json.dumps(item) + "\n")


def get_relevant_papers_chemrxiv(
    chemrxiv_jsonl_path: str, query: List[str], query_result_path: str, pdf_path: str
) -> pd.DataFrame:
    """
    Retrieves relevant papers from the ChemRxiv database based on a given query.

    Parameters
    ----------
    chemrxiv_jsonl_path : str
        The file path of the JSONL file containing the metadata.
    query : List[str]
        The list of keywords to search for in the metadata.
    query_result_path : str
        The file path where the query results will be saved.
    pdf_path : str
        The directory path where the PDFs of the relevant papers will be saved.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the relevant papers.
    """

    querier = XRXivQuery(chemrxiv_jsonl_path)
    querier_df = querier.search_keywords(query, output_filepath=query_result_path)
    save_pdf_from_dump(query_result_path, pdf_path=pdf_path, key_to_save="doi")
    print(f"Saved {querier_df.shape[0]} papers to {pdf_path}")
    return querier_df


# get_metadata_from_chemrxiv("2024-01-01", "2024-01-02")
# list_files=os.listdir('./data/jsonls')
# list_files=[f'./data/jsonls/{f}' for f in list_files]
# concat_metadata_from_chemrxiv(list_files, 'test.jsonl')
# query=[['Li-metal']]
# get_relevant_papers_chemrxiv(chemrxiv_jsonl_path='test.jsonl', query=query,query_result_path='./data/query_tmp.jsonl' ,pdf_path='./data/' )
