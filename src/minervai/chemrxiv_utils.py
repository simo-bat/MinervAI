from typing import List
import pandas as pd
import json
from paperscraper.get_dumps import chemrxiv
from paperscraper.xrxiv.xrxiv_query import XRXivQuery
from paperscraper.pdf import save_pdf_from_dump

TODO = """generalize for other sources"""


def get_metadata_from_chemrxiv(
    begin_date: str | None = None, end_date: str | None = None
) -> str:
    if begin_date is None:
        chemrxiv_jsonl_path = "./data/chemarxiv.jsonl"
    else:
        chemrxiv_jsonl_path = f"./data/jsonls/chemarxiv_{begin_date.replace('-', '')}_{end_date.replace('-', '')}.jsonl"  # type: ignore

    try:
        chemrxiv(
            begin_date=begin_date, end_date=end_date, save_path=chemrxiv_jsonl_path
        )
    except Exception as e:
        print(f"Error: {e}")
    return chemrxiv_jsonl_path


def concat_metadata_from_chemrxiv(
    jsonl_files: List[str], output_file_path: str
) -> None:
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
