"""
Database API Routes for CarboxyPred
"""

from flask import Blueprint, request, jsonify
from .database_service import get_database

db_bp = Blueprint('database', __name__)


@db_bp.route('/db/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        db = get_database()
        stats = db.get_stats()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@db_bp.route('/db/search', methods=['GET'])
def search_sequences():
    """Search sequences with filters"""
    try:
        db = get_database()
        
        results = db.search_sequences(
            query=request.args.get('query'),
            ec_class=request.args.get('ec_class'),
            is_co2_enzyme=request.args.get('is_co2') == 'true' if request.args.get('is_co2') else None,
            min_length=int(request.args.get('min_length')) if request.args.get('min_length') else None,
            max_length=int(request.args.get('max_length')) if request.args.get('max_length') else None,
            organism=request.args.get('organism'),
            has_km=request.args.get('has_km') == 'true' if request.args.get('has_km') else None,
            verified_only=request.args.get('verified_only') == 'true' if request.args.get('verified_only') else None,
            limit=int(request.args.get('limit', 100)),
            offset=int(request.args.get('offset', 0)),
        )
        
        return jsonify({'success': True, 'results': results, 'count': len(results)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@db_bp.route('/db/sequence/<int:seq_id>', methods=['GET'])
def get_sequence_by_id(seq_id):
    """Get complete sequence record by ID"""
    try:
        db = get_database()
        record = db.get_sequence_by_id(seq_id)
        if record:
            return jsonify({'success': True, 'sequence': record})
        return jsonify({'success': False, 'error': 'Sequence not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@db_bp.route('/db/sequence/uniprot/<uniprot_id>', methods=['GET'])
def get_sequence_by_uniprot(uniprot_id):
    """Get complete sequence record by UniProt ID"""
    try:
        db = get_database()
        record = db.get_sequence_by_uniprot(uniprot_id)
        if record:
            return jsonify({'success': True, 'sequence': record})
        return jsonify({'success': False, 'error': 'Sequence not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@db_bp.route('/db/sequence/<int:seq_id>/features', methods=['GET'])
def get_features(seq_id):
    """Get all 447 features for a sequence"""
    try:
        db = get_database()
        features = db.get_sequence_features(seq_id)
        if features:
            return jsonify({'success': True, 'features': features, 'count': len(features)})
        return jsonify({'success': False, 'error': 'Features not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@db_bp.route('/db/ec-classes', methods=['GET'])
def get_ec_classes():
    """Get all EC classes"""
    try:
        db = get_database()
        ec_classes = db.get_ec_classes()
        return jsonify({'success': True, 'ec_classes': ec_classes})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@db_bp.route('/db/ec/<ec_number>/sequences', methods=['GET'])
def get_ec_sequences(ec_number):
    """Get sequences by EC class"""
    try:
        db = get_database()
        limit = int(request.args.get('limit', 50))
        sequences = db.search_sequences(ec_class=ec_number, limit=limit)
        return jsonify({'success': True, 'sequences': sequences, 'count': len(sequences)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@db_bp.route('/db/evidence-comparison', methods=['GET'])
def get_evidence_comparison():
    """Get sequences with experimental vs predicted comparison"""
    try:
        db = get_database()
        limit = int(request.args.get('limit', 100))
        results = db.get_evidence_comparison(limit=limit)
        return jsonify({'success': True, 'results': results, 'count': len(results)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@db_bp.route('/db/feature-importance', methods=['GET'])
def get_feature_importance():
    """Get feature importance rankings"""
    try:
        db = get_database()
        importance = db.get_feature_importance()
        return jsonify({'success': True, 'features': importance})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
