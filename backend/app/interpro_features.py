"""
InterPro API Integration for domain annotations.
"""
import requests
import re
from typing import Optional, Dict, Any

INTERPRO_API_BASE = "https://www.ebi.ac.uk/interpro/api"

def extract_uniprot_id(fasta_header: str) -> Optional[str]:
    if not fasta_header:
        return None
    header = fasta_header.lstrip('>')
    match = re.match(r'^(?:sp|tr)\|([A-Z0-9]+)\|', header)
    if match:
        return match.group(1)
    match = re.match(r'^([A-Z][A-Z0-9]{5})\b', header)
    if match:
        return match.group(1)
    return None

def get_interpro_annotations(uniprot_id: str) -> Dict[str, Any]:
    result = {"uniprot_id": uniprot_id, "success": False, "entries": []}
    try:
        url = f"{INTERPRO_API_BASE}/entry/all/protein/uniprot/{uniprot_id}"
        response = requests.get(url, headers={"Accept": "application/json"}, timeout=30)
        if response.status_code == 200:
            result["success"] = True
            result["data"] = response.json()
    except Exception as e:
        result["error"] = str(e)
    return result

def get_alphafold_url(uniprot_id: str) -> Dict[str, Any]:
    result = {"uniprot_id": uniprot_id, "has_structure": False}
    try:
        url = f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                result["has_structure"] = True
                result["pdb_url"] = data[0].get("pdbUrl")
                result["cif_url"] = data[0].get("cifUrl")
    except Exception as e:
        result["error"] = str(e)
    return result
