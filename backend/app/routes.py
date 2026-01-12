"""
Main API Routes for CarboxyPred
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os

from .ml_prediction import get_predictor
from .batch_prediction import run_batch_prediction
from .biopython_features import QuickSequenceAnalyzer, format_results_table

main = Blueprint('main', __name__)


@main.route('/')
def index():
    """API root endpoint"""
    return jsonify({
        'name': 'CarboxyPred API',
        'version': '2.0',
        'endpoints': {
            'prediction': ['/predict', '/predict-batch', '/model-info'],
            'database': ['/db/stats', '/db/search', '/db/sequence/<id>', '/db/ec-classes']
        }
    })


@main.route('/health')
def health():
    """Health check endpoint"""
    predictor = get_predictor()
    return jsonify({
        'status': 'healthy',
        'models_loaded': predictor.loaded
    })


@main.route('/model-info', methods=['GET'])
def model_info():
    """Get information about loaded models"""
    predictor = get_predictor()
    return jsonify({
        'success': True,
        'info': predictor.get_model_info()
    })


@main.route('/predict', methods=['POST'])
def predict_single():
    """
    Predict single sequence
    
    Request body:
    {
        "sequence": "MSPQTET...",
        "include_features": false
    }
    
    Returns prediction results
    """
    try:
        data = request.get_json()
        
        if not data or 'sequence' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing sequence in request body'
            }), 400
        
        sequence = data['sequence']
        include_features = data.get('include_features', False)
        
        predictor = get_predictor()
        
        if not predictor.loaded:
            return jsonify({
                'success': False,
                'error': 'ML models not loaded'
            }), 503
        
        result = predictor.predict_single(sequence)
        
        if not include_features and 'features' in result:
            del result['features']
        
        return jsonify({
            'success': True,
            'prediction': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main.route('/predict-batch', methods=['POST'])
def predict_batch():
    """
    Predict batch of sequences (FASTA format)
    
    Request body:
    {
        "fasta": ">seq1\nMSPQTET...\n>seq2\nMKTAYIA...",
        "include_features": false
    }
    
    Or multipart form with file upload
    """
    try:
        # Check for JSON body
        if request.is_json:
            data = request.get_json()
            fasta_text = data.get('fasta', '')
            include_features = data.get('include_features', False)
        
        # Check for file upload
        elif 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'error': 'No file selected'
                }), 400
            
            fasta_text = file.read().decode('utf-8')
            include_features = request.form.get('include_features', 'false').lower() == 'true'
        
        # Check for form data
        elif 'fasta' in request.form:
            fasta_text = request.form.get('fasta', '')
            include_features = request.form.get('include_features', 'false').lower() == 'true'
        
        else:
            return jsonify({
                'success': False,
                'error': 'No FASTA data provided. Send JSON with "fasta" key or upload file.'
            }), 400
        
        if not fasta_text.strip():
            return jsonify({
                'success': False,
                'error': 'Empty FASTA data'
            }), 400
        
        # Run batch prediction
        result = run_batch_prediction(fasta_text, include_features=include_features)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main.route('/predict-batch/download', methods=['POST'])
def predict_batch_download():
    """
    Predict batch and return as downloadable TSV
    """
    try:
        if request.is_json:
            data = request.get_json()
            fasta_text = data.get('fasta', '')
        elif 'file' in request.files:
            file = request.files['file']
            fasta_text = file.read().decode('utf-8')
        elif 'fasta' in request.form:
            fasta_text = request.form.get('fasta', '')
        else:
            return jsonify({
                'success': False,
                'error': 'No FASTA data provided'
            }), 400
        
        result = run_batch_prediction(fasta_text, include_features=False)
        
        if not result.get('success'):
            return jsonify(result), 400
        
        # Format as TSV
        tsv_content = format_results_table(result['results'])
        
        from flask import Response
        return Response(
            tsv_content,
            mimetype='text/tab-separated-values',
            headers={'Content-Disposition': 'attachment; filename=carboxypred_results.tsv'}
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Error handlers
@main.app_errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@main.app_errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500
from flask import Blueprint, request, jsonify
from .batch_prediction import run_batch_prediction
from .biopython_features import QuickSequenceAnalyzer

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/predict-comprehensive', methods=['POST'])
@analysis_bp.route('/analyze-sequence', methods=['POST'])
def analyze_comprehensive():
    """Comprehensive analysis - BioPython + ML predictions"""
    data = request.get_json() or {}
    sequence = data.get('sequence', '')
    
    if not sequence:
        return jsonify({'success': False, 'error': 'No sequence provided'})
    
    try:
        # BioPython analysis
        analyzer = QuickSequenceAnalyzer(sequence)
        bio_analysis = {
            'basic_properties': analyzer.get_basic_properties(),
            'amino_acid_composition': analyzer.get_amino_acid_composition(),
            'secondary_structure': analyzer.predict_secondary_structure(),
            'charge_distribution': analyzer.analyze_charge_distribution(),
        }
        
        # ML predictions
        fasta = f">query\n{sequence}"
        ml_result = run_batch_prediction(fasta)
        
        # Combine results
        if ml_result.get('success') and ml_result.get('results'):
            ml_pred = ml_result['results'][0]
            bio_analysis['ml_predictions'] = ml_pred
            bio_analysis['ec_predicted'] = ml_pred.get('ec_predicted')
            bio_analysis['ec_confidence'] = ml_pred.get('ec_confidence')
            bio_analysis['km_predicted_uM'] = ml_pred.get('km_predicted_uM')
            bio_analysis['consensus'] = ml_pred.get('consensus')
            bio_analysis['v3_prob'] = ml_pred.get('v3_prob')
            bio_analysis['v5_prob'] = ml_pred.get('v5_prob')
        
        return jsonify({
            'success': True,
            'analysis': bio_analysis
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@analysis_bp.route('/visualize-sequence', methods=['POST'])
def visualize_sequence():
    """Generate visualization data for sequence"""
    data = request.get_json() or {}
    sequence = data.get('sequence', '')
    
    # Return placeholder charts data
    return jsonify({
        'success': True,
        'charts': {
            'amino_acid_composition': {},
            'hydrophobicity': [],
            'secondary_structure': {}
        }
    })

@analysis_bp.route('/validate-fasta', methods=['POST'])
def validate_fasta():
    """Validate FASTA input - handles both JSON and form-data"""
    if request.is_json:
        data = request.get_json()
        fasta = data.get('fasta', '')
    elif 'file' in request.files:
        fasta = request.files['file'].read().decode('utf-8')
    else:
        fasta = request.form.get('fasta', request.form.get('sequence', ''))
    
    sequences = []
    current_id = None
    current_seq = []
    
    for line in fasta.strip().split('\n'):
        if line.startswith('>'):
            if current_id:
                sequences.append({'id': current_id, 'length': len(''.join(current_seq))})
            current_id = line[1:].split()[0]
            current_seq = []
        else:
            current_seq.append(line.strip())
    
    if current_id:
        sequences.append({'id': current_id, 'length': len(''.join(current_seq))})
    
    import uuid
    file_id = str(uuid.uuid4()) if len(sequences) > 0 else None
    return jsonify({
        'is_valid': len(sequences) > 0,
        'valid': len(sequences) > 0,
        'file_id': file_id,
        'sequence_count': len(sequences),
        'sequences': sequences
    })
