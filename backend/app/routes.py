from flask import Blueprint, request, current_app, jsonify
from backend.app.tasks import *
from backend.carboxylase_search.run_all_searches_task import combined_search_task
from backend.app.biopython_features import QuickSequenceAnalyzer
from backend.app.plotly_visualizations import SequenceVisualizer

main = Blueprint('main', __name__)

# ===== EXISTING ENDPOINTS =====

@main.route("/validate-fasta", methods=['POST'])
def validate_fasta():
    file = request.files['file']
    return validate_fasta_task(file, current_app.config['ALLOWED_FILE_EXTENSIONS'], current_app.config['UPLOADED_USER_DATA_FOLDER'])

@main.errorhandler(413)
def request_entity_too_large(error):
    return jsonify(error=f"The file exceeds the maximum file size of {current_app.config['MAX_CONTENT_LENGTH_STRING']}"), 413

@main.route("/hmmer-search", methods=['POST'])
def hmmer_search():
    data = request.get_json()
    file_id = data.get('fileId')
    return hmmer_search_task(file_id)

@main.route("/prosite-scan", methods=['POST'])
def prosite_scan():
    data = request.get_json()
    file_id = data.get('fileId')
    return prosite_scan_task(file_id)

@main.route("/all-searches", methods=['POST'])
def all_searches():
    data = request.get_json()
    file_id = data.get('fileId')
    return combined_search_task(file_id)

@main.route("/download-results", methods=['GET'])
def download_results():
    file_id = request.args.get('fileId')
    return download_results_task(file_id)


# ===== NEW ENDPOINTS - BioPython Analysis =====

@main.route('/analyze-sequence', methods=['POST'])
def analyze_sequence():
    """
    Analyze a protein sequence using BioPython
    
    Request JSON: {"sequence": "MKALVLGFGKGQQQQK"}
    """
    try:
        data = request.get_json()
        
        if not data or 'sequence' not in data:
            return jsonify({
                'success': False,
                'error': 'No sequence provided'
            }), 400
        
        sequence = data.get('sequence', '').strip()
        
        if not sequence:
            return jsonify({
                'success': False,
                'error': 'Empty sequence'
            }), 400
        
        # Analyze sequence
        analyzer = QuickSequenceAnalyzer(sequence)
        analysis = analyzer.complete_analysis()
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main.route('/visualize-sequence', methods=['POST'])
def visualize_sequence():
    """
    Create Plotly visualizations for a protein sequence
    
    Request JSON: {"sequence": "MKALVLGFGKGQQQQK"}
    """
    try:
        data = request.get_json()
        
        if not data or 'sequence' not in data:
            return jsonify({
                'success': False,
                'error': 'No sequence provided'
            }), 400
        
        sequence = data.get('sequence', '').strip()
        
        if not sequence:
            return jsonify({
                'success': False,
                'error': 'Empty sequence'
            }), 400
        
        # Analyze sequence first
        analyzer = QuickSequenceAnalyzer(sequence)
        analysis = analyzer.complete_analysis()
        
        # Create visualizations
        visualizer = SequenceVisualizer(sequence, analysis)
        charts = visualizer.create_all_charts()
        
        return jsonify({
            'success': True,
            'charts': charts
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
