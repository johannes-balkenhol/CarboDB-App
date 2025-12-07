from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors


def export_hits_to_pdf(results_by_sequence, output_filename):
    """
    Args:
        results_by_sequence: the dictionary containing all hits found by the search
        output_filename: the name of the pdf to generate

    Returns:
        Saves a PDF file with the search results
    """
    search_strategies = set()

    # Extract unique search result types
    for search_results in results_by_sequence.values():
        for search_result_type in search_results.keys():
            search_strategies.add(search_result_type)

    search_strategies = sorted(search_strategies)

    # Prepare table headers
    headers = ["Sequence ID"] + search_strategies
    data = [headers]

    # Populate the table
    for seq_id, search_results in results_by_sequence.items():
        row = [seq_id]
        for strategy in search_strategies:
            if strategy in search_results:
                # Collect all accession numbers for the search strategies
                if strategy == "Pfam hits":
                    accession_numbers = [item.pfam_accession for item in search_results[strategy]]
                    row.append("\n".join(accession_numbers))
                elif strategy == "Prosite hits":
                    accession_numbers = [item.prosite_accession for item in search_results[strategy]]
                    row.append("\n".join(accession_numbers))
            else:
                row.append("")
        data.append(row)

    # Create a PDF document with styling
    doc = SimpleDocTemplate(output_filename, pagesize=letter)
    table = Table(data)

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    table.setStyle(style)

    doc.build([table])
