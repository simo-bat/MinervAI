import json
import os
import time
from datetime import datetime, timedelta
from typing import List

import pandas as pd
from paperscraper.get_dumps import arxiv, biorxiv, chemrxiv, medrxiv
from paperscraper.pdf import save_pdf_from_dump
from paperscraper.xrxiv.xrxiv_query import XRXivQuery


def get_metadata_from_archive(
    dump_path: str, start_date: str, end_date: str, archive_str: str
) -> tuple[int, list[str]]:
    """
    Retrieves metadata from the X-rxiv database.

    Parameters
    ----------
    dump_path: str
        The file path where the retrieved metadata is saved.
    start_date : str
        The beginning date of the time range to retrieve metadata from.
    end_date : str
        The end date of the time range to retrieve metadata from.

    Returns
    -------
    papers_number: int
        The number of papers retrieved.
    failed_dates: list
        A list of dates where the function failed to retrieve metadata.
    """
    archives = {
        "medrxiv": medrxiv,
        "chemrxiv": chemrxiv,
        "biorxiv": biorxiv,
        "arxiv": arxiv,
    }
    archive = archives[archive_str]

    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    final_date = datetime.strptime(end_date, "%Y-%m-%d")
    generated_files = []  # Keep track of generated files
    failed_dates = []  # List to track dates where fun failed after retrying

    # Retrieve metadata for each day with a unique filename.
    while current_date <= final_date:
        date_str = current_date.strftime("%Y-%m-%d")
        daily_filename = f"{dump_path}_{date_str}.jsonl"
        try:
            archive(start_date=date_str, end_date=date_str, save_path=daily_filename)
            success = True
        except Exception:
            time.sleep(5)  # Wait 5 seconds before retrying
            try:
                archive(
                    start_date=date_str, end_date=date_str, save_path=daily_filename
                )
                success = True
            except Exception:
                success = False
                failed_dates.append(date_str)
        if success:
            generated_files.append(daily_filename)
        current_date += timedelta(days=1)

    # Combine all the generated files into one.
    papers_number = 0
    with open(dump_path, "w", encoding="utf-8") as outfile:
        for fname in generated_files:
            if os.path.exists(fname):
                file_lines = 0
                with open(fname, "r", encoding="utf-8") as infile:
                    for line in infile:
                        outfile.write(line)
                        papers_number += 1
                        file_lines += 1
                # Add a newline after each file to ensure proper separation
                if file_lines > 0:
                    outfile.write("\n")
                os.remove(fname)

    print(f"Combined file created: {dump_path}")
    print(f"Total number of lines: {papers_number}")
    return papers_number, failed_dates


def filter_metadata_from_archive(
    dump_path: str, query: List[str], query_result_path: str
) -> pd.DataFrame:
    """
    Filters metadata based on a given query.

    Parameters
    ----------
    dump_path : str
        The file path of the JSONL file containing the metadata.
    query : List[str]
        The list of keywords to search for in the metadata.
    query_result_path : str
        The file path where the query results will be saved.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the query results.
    """

    querier = XRXivQuery(dump_path)
    querier_df = querier.search_keywords(query, output_filepath=query_result_path)
    return querier_df


def check_downloaded_papers(query_result_path: str, pdf_path: str) -> tuple:
    """
    Checks how many of the files in the query result are saved in the PDF path
    and returns info about missing papers.

    Parameters
    ----------
    query_result_path : str
        The file path where the query results are saved.
    pdf_path : str
        The directory path where the PDFs of the relevant papers are saved.

    Returns
    -------
    tuple[int, pd.DataFrame]
        The number of papers successfully downloaded as PDFs and a DataFrame
        containing info about missing papers.
    """

    with open(query_result_path, "r") as file:
        query_results = [json.loads(line) for line in file]

    n_downloaded_papers = 0
    missing_papers = []

    for result in query_results:
        doi = result.get("doi", "").replace("/", "_")
        pdf_file_path = f"{pdf_path}/{doi}.pdf"
        if os.path.exists(pdf_file_path):
            n_downloaded_papers += 1
        else:
            missing_papers.append(result)

    missing_papers_df = pd.DataFrame(missing_papers)
    return n_downloaded_papers, missing_papers_df


def download_papers_from_archive(query_result_path: str, pdf_path: str) -> tuple:
    """
    Downloads papers from the ChemRxiv database based on a given query.

    Parameters
    ----------
    query_result_path : str
        The file path where the query results are saved.
    pdf_path : str
        The directory path where the PDFs of the relevant papers will be saved.

    Returns
    -------
    None
    """

    save_pdf_from_dump(query_result_path, pdf_path=pdf_path, key_to_save="doi")
    n_downloaded_papers, missing_papers_df = check_downloaded_papers(
        query_result_path, pdf_path
    )
    return n_downloaded_papers, missing_papers_df
