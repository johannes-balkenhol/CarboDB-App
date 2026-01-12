"""
Main API Routes for CarboxyPred
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os

from .ml_prediction import get_predictor
from .batch_prediction import run_batch_prediction, format_results_table

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
