#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 29 10:31:33 2024

@author: eva
"""
import urllib.request

import requests

#Find all analysis Ids with predicted CDS
link_to_resource_basic = "https://www.ebi.ac.uk/metagenomics/api/v1/analyses"
link_to_resource_page = "https://www.ebi.ac.uk/metagenomics/api/v1/analyses?page="
number_of_last_page = 25046


def get_ids_with_predicted_CDS(link_to_resource, page_num):
    """
        Collects MGnify analysis ids from EMBL_EBI which include predicted protein sequences.
        Currently uses link_to_resource_page to find the desired page by their numbers.

        Args:
            link_to_resource: link to the page
            page_num: Specifies till which page number to screen for (starting with page one)

        Returns:
            Array of analyses IDs with predicted protein sequences
    """
    ids_with_predicted_CDs = []
    for num in range(1, page_num):
        try:
            page = fetch_page_of_db(link_to_resource, num)
            if page is None or page.status_code != 200:
                print(f"Skipping page {num} due to fetch error.")
                continue

            page_json = page.json()
            test_if_entry_has_predicted_CDS(page_json, ids_with_predicted_CDs)
        except Exception as e:
            print(f"Error processing page {num}: {e}")
    return ids_with_predicted_CDs


def fetch_page_of_db(link_to_resource, variable, append=""):
    """
        Tries to fetch a page

        Args:
            link_to_resource: basic link to the page
            variable: can be used to add variable parts to the link like the page number
            append: optional appendix to the link

        Returns:
            page or None
    """
    try:
        page = requests.get(link_to_resource+f"{variable}"+append)
        page.raise_for_status()
        print(f"Fetched page {variable}")
        return page
    except: 
        print(f"An error occured with requesting page {variable}")
        return None

def test_if_entry_has_predicted_CDS(page_json, ids_with_predicted_CDs):
    """
    Checks if a MGnify analysis entry from EMBL_EBI includes predicted protein sequences.

    Args:
        page_json: page content as json
        ids_with_predicted_CDs: array to add the IDs to

    """
    if page_json is None or "data" not in page_json:
        print("Invalid JSON response or missing 'data' key.")
        return
    
    for entry in page_json["data"]:
        analysis_summary = entry["attributes"]["analysis-summary"]
        for item in analysis_summary:
            if item["key"] == "Predicted CDS" and int(item["value"]) > 0:
               ids_with_predicted_CDs.append(entry['id'])
               
def save_ids_to_file(ids, filename):
    """
    Saves ids to .txt file
    Args:
        ids: array of ids
        filename: name of the file to save
    """
    try:
        with open(filename, "w") as file:
            for id in ids:
                file.write(id + "\n")
        print(f"IDs successfully saved to {filename}")
    except Exception as e:
        print(f"An error occurred while saving IDs to file: {e}")


#Use collected analysis Ids to collect the file Ids with the CDS data
    
def collect_data_ids_for_analyses(link_to_resource, filename):
    """
    Collects the Ids that correspond to the predicted protein data of the analyses.
    Currently uses link_to_resource_basic to find the pages.

    Args:
        link_to_resource: link to the page
        filename: path of the file from which the Ids should be taken

    Returns:
        array of ids referencing the predicted protein data of the analyses

    """
    ids = read_ids_from_txt(filename)
    id_list = []
    for id in ids: 
        try: 
            page = fetch_page_of_db(link_to_resource+"/", id, "/downloads")
            if page is None or page.status_code != 200:
               print(f"Skipping page {id} due to fetch error.")
               continue

            page_json = page.json()
            get_download_file_id(page_json, id_list)
            
        except Exception as e:
            print(f"An error occurred while collecting data for IDs: {e}")
    return id_list
    
    
    
def read_ids_from_txt(filename):
    """
    Reads ids from a file
    Args:
        filename: path to file to read

    Returns:
        array of ids or empty array
    """
    try:
        with open(filename, "r") as file:
            ids = [line.strip() for line in file]  # Read each line and strip newline characters
        print(f"IDs successfully read from {filename}")
        return ids
    except Exception as e:
        print(f"An error occurred while reading IDs from file: {e}")
        return []
    
def get_download_file_id(page_json, id_list):
    """
    Finds the id that corresponds to the predicted protein data of one analyses
    Args:
        page_json: page content as json

    Returns:
        found id or None

    """
    if page_json is None or "data" not in page_json:
        print("Invalid JSON response or missing 'data' key.")
        return
    
    for entry in page_json["data"]:
        analysis_description = entry["attributes"].get("description")
        if (analysis_description.get("label") == "Predicted CDS (aa)" and 
            analysis_description.get("description") == "All predicted CDS"):
            id_list.append(entry.get('id'))
    


# Actually download the data

def download_data(link_to_resource, analysis_id_file, data_ids_file, save_file_location):
    """
    Downloads the predicted protein sequence data.

    Args:
        link_to_resource: link to the page
        analysis_id_file: file containing the collected analysis ids
        data_ids_file: file containing the collected data ids
        save_file_location: location to save the downloaded files

    Returns:
        Saves the fetched download to a given path

    """

    analysis_ids = read_ids_from_txt(analysis_id_file)
    data_ids = read_ids_from_txt(data_ids_file)
    if len(analysis_ids) != len(data_ids):
        print("Your id files don't have equal length")
        return

    dictionary = dict(zip(analysis_ids, data_ids))

    for key, value in dictionary.items():
        try:
            link = f"{link_to_resource}/{key}/file/{value}"
            urllib.request.urlretrieve(link, f"{save_file_location}/{value}")

        except Exception as e:
            print(f"An error occurred while downloading data for IDs: {e}")
    return


ids_with_predicted_protein_seqs = "out/ids_with_predicted_CDS.txt"
ids_for_data_download = "out/file_ids_for_download.txt"
save_location = "/home/eva/PycharmProjects/Carboxylase_Server/backend/carboxylase_search/data_acquisition"

#Find all analysis Ids with predicted CDS
ids_with_predicted_CDS = get_ids_with_predicted_CDS(link_to_resource_page, 10)
save_ids_to_file(ids_with_predicted_CDS, ids_with_predicted_protein_seqs)

#Use collected analysis Ids to collect the file Ids with the CDS data
ids = collect_data_ids_for_analyses(link_to_resource_basic, ids_with_predicted_protein_seqs)
save_ids_to_file(ids, ids_for_data_download)

#Actually download the data
download_data(link_to_resource_basic, ids_with_predicted_protein_seqs, ids_for_data_download, save_location)


