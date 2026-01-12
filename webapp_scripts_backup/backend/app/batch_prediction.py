"""
Batch Prediction Pipeline for CarboxyPred
Includes v3, v5, EC, Km predictions with database matching
"""

import re
from typing import List, Dict, Optional
from .ml_prediction import get_predictor
from .database_service import get_database
import logging

logger = logging.getLogger(__name__)


def parse_fasta(fasta_text: str) -> List[Dict]:
    """Parse FASTA format text into list of sequences"""
    sequences = []
    current_id = None
    current_seq = []
    
    for line in fasta_text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        
        if line.startswith('>'):
            # Save previous sequence
            if current_id and current_seq:
                sequences.append({
                    'id': current_id,
                    'sequence': ''.join(current_seq)
                })
            
            # Start new sequence
            # Parse header: >sp|P00875|RBL_SPIOL or >P00875 or >seq_1
            header = line[1:].strip()
            
            # Try to extract UniProt ID
            if '|' in header:
                parts = header.split('|')
                if len(parts) >= 2:
                    current_id = parts[1]
                else:
                    current_id = parts[0]
            else:
                current_id = header.split()[0] if header else f'seq_{len(sequences) + 1}'
            
            current_seq = []
        else:
            current_seq.append(line)
    
    # Don't forget last sequence
    if current_id and current_seq:
        sequences.append({
            'id': current_id,
            'sequence': ''.join(current_seq)
        })
    
    return sequences


def find_database_match(uniprot_id: str) -> Optional[Dict]:
    """Find exact match in database by UniProt ID"""
    try:
        db = get_database()
        return db.get_sequence_by_uniprot(uniprot_id)
    except Exception as e:
        logger.warning(f"Database lookup failed for {uniprot_id}: {e}")
        return None


def find_similar_by_ec(ec_number: str, limit: int = 5) -> List[Dict]:
    """Find similar sequences in database by EC number"""
    try:
        db = get_database()
        return db.search_sequences(ec_class=ec_number, has_km=True, limit=limit)
    except Exception as e:
        logger.warning(f"Similar search failed for EC {ec_number}: {e}")
        return []


def run_batch_prediction(fasta_text: str, include_features: bool = False) -> Dict:
    """
    Run complete prediction pipeline on batch of sequences
    
    Returns:
        {
            'success': True/False,
            'total': int,
            'results': [
                {
                    'id': str,
                    'length': int,
                    'v3_prob': float,
                    'v3_pred': bool,
                    'v5_prob': float or None,
                    'v5_pred': bool or None,
                    'v5_applicable': bool,
                    'consensus': bool,
                    'high_confidence': bool,
                    'ec_pred': str,
                    'ec_conf': float,
                    'km_uM': float or None,
                    'km_log': float or None,
                    'db_match': {dict} or None,
                    'similar_with_km': [{dict}] or [],
                    'features': {dict} if include_features else None
                }
            ],
            'summary': {
                'total': int,
                'co2_positive': int,
                'high_confidence': int,
                'with_db_match': int,
                'ec_distribution': {ec: count}
            }
        }
    """
    try:
        # Parse FASTA
        sequences = parse_fasta(fasta_text)
        
        if not sequences:
            return {
                'success': False,
                'error': 'No valid sequences found in input'
            }
        
        # Get predictor
        predictor = get_predictor()
        
        if not predictor.loaded:
            return {
                'success': False,
                'error': 'ML models not loaded'
            }
        
        results = []
        summary = {
            'total': len(sequences),
            'co2_positive': 0,
            'high_confidence': 0,
            'with_db_match': 0,
            'ec_distribution': {}
        }
        
        for seq_data in sequences:
            seq_id = seq_data['id']
            sequence = seq_data['sequence']
            
            # Run prediction
            pred = predictor.predict_single(sequence)
            
            if not pred.get('success', False):
                results.append({
                    'id': seq_id,
                    'error': pred.get('error', 'Prediction failed')
                })
                continue
            
            result = {
                'id': seq_id,
                'length': pred['length'],
                'v3_prob': pred['v3_prob'],
                'v3_pred': pred['v3_pred'],
                'v5_prob': pred.get('v5_prob'),
                'v5_pred': pred.get('v5_pred'),
                'v5_applicable': pred.get('v5_applicable', False),
                'consensus': pred.get('consensus', False),
                'high_confidence': pred.get('high_confidence', False),
                'ec_pred': pred.get('ec_pred'),
                'ec_conf': pred.get('ec_conf'),
                'km_uM': pred.get('km_uM'),
                'km_log': pred.get('km_log'),
            }
            
            # Database lookup
            db_match = find_database_match(seq_id)
            if db_match:
                result['db_match'] = {
                    'uniprot_id': db_match.get('uniprot_id'),
                    'ec_verified': db_match.get('ec_verified'),
                    'km_experimental': db_match.get('km_experimental'),
                    'km_best': db_match.get('km_best'),
                    'organism': db_match.get('organism')
                }
                summary['with_db_match'] += 1
            else:
                result['db_match'] = None
            
            # Find similar sequences with experimental Km
            if pred.get('ec_pred'):
                similar = find_similar_by_ec(pred['ec_pred'], limit=3)
                result['similar_with_km'] = [
                    {
                        'uniprot_id': s.get('uniprot_id'),
                        'ec_verified': s.get('ec_verified'),
                        'km_best': s.get('km_best'),
                        'km_experimental': s.get('km_experimental'),
                        'organism': s.get('organism')
                    }
                    for s in similar if s.get('km_best') or s.get('km_experimental')
                ]
            else:
                result['similar_with_km'] = []
            
            # Include features if requested
            if include_features:
                result['features'] = pred.get('features')
            
            # Update summary
            if pred.get('consensus'):
                summary['co2_positive'] += 1
            if pred.get('high_confidence'):
                summary['high_confidence'] += 1
            if pred.get('ec_pred'):
                ec = pred['ec_pred']
                summary['ec_distribution'][ec] = summary['ec_distribution'].get(ec, 0) + 1
            
            results.append(result)
        
        return {
            'success': True,
            'total': len(sequences),
            'results': results,
            'summary': summary
        }
        
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def format_results_table(results: List[Dict]) -> str:
    """Format results as TSV table"""
    headers = [
        'ID', 'Length', 'V3_Prob', 'V5_Prob', 'Consensus',
        'EC_Pred', 'EC_Conf', 'Km_uM', 'Km_log',
        'DB_Match', 'EC_Verified', 'Km_Experimental'
    ]
    
    lines = ['\t'.join(headers)]
    
    for r in results:
        if 'error' in r:
            lines.append(f"{r['id']}\tERROR: {r['error']}")
            continue
        
        db = r.get('db_match', {}) or {}
        row = [
            r.get('id', ''),
            str(r.get('length', '')),
            f"{r.get('v3_prob', 0):.4f}" if r.get('v3_prob') is not None else '',
            f"{r.get('v5_prob', 0):.4f}" if r.get('v5_prob') is not None else '',
            'Yes' if r.get('consensus') else 'No',
            r.get('ec_pred', ''),
            f"{r.get('ec_conf', 0):.4f}" if r.get('ec_conf') is not None else '',
            f"{r.get('km_uM', 0):.2f}" if r.get('km_uM') is not None else '',
            f"{r.get('km_log', 0):.4f}" if r.get('km_log') is not None else '',
            'Yes' if db else 'No',
            db.get('ec_verified', ''),
            f"{db.get('km_experimental', 0):.2f}" if db.get('km_experimental') else ''
        ]
        lines.append('\t'.join(row))
    
    return '\n'.join(lines)
