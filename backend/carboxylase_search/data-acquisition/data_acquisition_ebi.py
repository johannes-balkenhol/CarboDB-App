#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 29 10:31:33 2024

@author: eva
"""

import requests

#Find all entry Ids with predicted CDS
link_to_ressource_basic = "https://www.ebi.ac.uk/metagenomics/api/v1/analyses"
link_to_ressource_page = "https://www.ebi.ac.uk/metagenomics/api/v1/analyses?page="
number_of_last_page = 25046

def get_ids_with_predicted_CDS(link_to_ressource):
     ids_with_prediceted_CDs = []
     for num in range(1, 2):
         try:
             r = fetch_page_of_db(link_to_ressource, num)
             if r is None or r.status_code != 200:
                print(f"Skipping page {num} due to fetch error.")
                continue
            
             r_json = r.json()
             test_if_entry_has_predicted_CDS(r_json, ids_with_prediceted_CDs)
         except Exception as e:
             print(f"Error processing page {num}: {e}")
     return ids_with_prediceted_CDs
            

def fetch_page_of_db(link_to_ressource, variable, append=""):
    try:
        r = requests.get(link_to_ressource+f"{variable}"+append)
        r.raise_for_status()
        print(f"Fetched page {variable}")
        return r
    except: 
        print(f"An error occured with requesting page {variable}")
        return None

def test_if_entry_has_predicted_CDS(r_json, ids_with_prediceted_CDs):
    if r_json is None or "data" not in r_json:
        print("Invalid JSON response or missing 'data' key.")
        return
    
    for entry in r_json["data"]:
        analysis_summary = entry["attributes"]["analysis-summary"]
        for item in analysis_summary:
            if item["key"] == "Predicted CDS" and int(item["value"]) > 0:
               ids_with_prediceted_CDs.append(entry['id']) 
               #print(f"Entry ID {entry['id']} has 'Predicted CDS' with value > 0: {item['value']}")
               
def save_ids_to_file(ids, filename="out/ids_with_predicted_CDS.txt"):
    try:
        with open(filename, "w") as file:
            for id in ids:
                file.write(id + "\n")
        print(f"IDs successfully saved to {filename}")
    except Exception as e:
        print(f"An error occurred while saving IDs to file: {e}")
 
    
#ids_with_predicted_CDS = get_ids_with_predicted_CDS(link_to_ressource_page)
#save_ids_to_file(ids_with_predicted_CDS)
#print(ids_with_predicted_CDS)

#Use collected entry Ids to collect the file Ids with the CDS data
    
def collect_data_for_given_ids(link_to_ressource, filename="out/ids_with_predicted_CDS.txt"):
    ids = read_ids_from_txt(filename)
    id_list = []
    for id in ids: 
        try: 
            r = fetch_page_of_db(link_to_ressource+"/", id, "/downloads")
            if r is None or r.status_code != 200:
               print(f"Skipping page {id} due to fetch error.")
               continue
           
            
            r_json = r.json()
            get_download_file_ids(r_json, id_list)
            
        except Exception as e:
            print(f"An error occurred while collecting data for IDs: {e}")
    return id_list
    
    
    
def read_ids_from_txt(filename):
    try:
        with open(filename, "r") as file:
            ids = [line.strip() for line in file]  # Read each line and strip newline characters
        print(f"IDs successfully read from {filename}")
        return ids
    except Exception as e:
        print(f"An error occurred while reading IDs from file: {e}")
        return []
    
def get_download_file_ids(r_json, id_list):
    if r_json is None or "data" not in r_json:
        print("Invalid JSON response or missing 'data' key.")
        return
    
    for entry in r_json["data"]:
        analysis_description = entry["attributes"].get("description")
        if (analysis_description.get("label") == "Predicted CDS (aa)" and 
            analysis_description.get("description") == "All predicted CDS"):
            id_list.append(entry.get('id'))
    

ids = collect_data_for_given_ids(link_to_ressource_basic)
save_ids_to_file(ids, "out/file_ids_for_download.txt")

