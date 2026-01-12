"""
Comprehensive Batch Prediction Pipeline
- v3/v5 binary classification
- EC classification  
- Km prediction
- Database search for nearest neighbor
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import sqlite3
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

DB_PATH = Path('/app/database_files/carboxylase.db')
AA_LIST = 'ACDEFGHIKLMNPQRSTVWY'


def extract_features(seq):
    """Extract 447 features from sequence"""
    seq = ''.join(c for c in str(seq).upper() if c in AA_LIST)
    n = len(seq)
    if n < 50:
        return None
    
    f = {}
    
    # Invariant features
    start, end = n // 4, 3 * n // 4
    cat = seq[start:end]
    for aa in 'DEHKCST':
        f[f'inv_cat_{aa}'] = float(cat.count(aa) / len(cat)) if cat else 0.0
    
    cat_pos = [i for i, a in enumerate(seq) if a in 'DEHKC']
    if len(cat_pos) > 1:
        dists = [cat_pos[i+1] - cat_pos[i] for i in range(len(cat_pos) - 1)]
        f['inv_cat_mean_dist'] = float(np.mean(dists))
        f['inv_cat_std_dist'] = float(np.std(dists))
        f['inv_cat_min_dist'] = float(np.min(dists))
        f['inv_cat_max_dist'] = float(np.max(dists))
        f['inv_cat_clustering'] = float(1 / (np.mean(dists) + 1))
    else:
        for k in ['mean_dist', 'std_dist', 'min_dist', 'max_dist', 'clustering']:
            f[f'inv_cat_{k}'] = 0.0
    
    f['inv_hydrophobic'] = float(sum(seq.count(a) for a in 'AILMFVWY') / n)
    f['inv_charged'] = float(sum(seq.count(a) for a in 'DEKR') / n)
    f['inv_polar'] = float(sum(seq.count(a) for a in 'STNQ') / n)
    f['inv_aromatic'] = float(sum(seq.count(a) for a in 'FWY') / n)
    f['inv_small'] = float(sum(seq.count(a) for a in 'AGST') / n)
    f['inv_net_charge'] = float((seq.count('K') + seq.count('R') - seq.count('D') - seq.count('E')) / n)
    f['inv_length'] = float(n)
    f['inv_log_length'] = float(np.log10(n))
    
    # Amino acid composition
    for aa in AA_LIST:
        f[f'aa_{aa}'] = float(seq.count(aa) / n)
    
    # Dipeptides
    for a1 in AA_LIST:
        for a2 in AA_LIST:
            f[f'dp_{a1}{a2}'] = 0.0
    for i in range(n - 1):
        dp = f'dp_{seq[i]}{seq[i+1]}'
        if dp in f:
            f[dp] += 1
    if n > 1:
        for k in [k for k in f if k.startswith('dp_')]:
            f[k] = float(f[k] / (n - 1))
    
    # Motifs
    f['motif_rubisco_kk'] = float(seq.count('KK') / n * 100)
    f['motif_rubisco_gk'] = float(seq.count('GK') / n * 100)
    f['motif_ca_hh'] = float(seq.count('HH') / n * 100)
    f['motif_ca_his'] = float(sum(1 for i in range(n - 3) if seq[i:i+4].count('H') >= 2) / n * 100)
    f['motif_pepc_rr'] = float(seq.count('RR') / n * 100)
    f['motif_biotin_mk'] = float(seq.count('MK') / n * 100)
    f['motif_biotin_amk'] = float(seq.count('AMK') / n * 100)
    
    return f


def find_nearest_neighbor(sequence: str, ec_predicted: str = None, seq_len: int = 0) -> Optional[Dict]:
    """Find nearest neighbor in database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Find sequences with same EC and experimental Km
        if ec_predicted:
            cursor.execute("""
                SELECT s.uniprot_id, s.length, s.organism,
                       ec.ec_number, ec.ec_name,
                       km.km_value as km_experimental
                FROM sequences s
                JOIN ec_evidence ec ON s.id = ec.sequence_id AND ec.evidence_type IN ('experimental', 'curated')
                LEFT JOIN km_evidence km ON s.id = km.sequence_id AND km.evidence_type = 'experimental'
                WHERE ec.ec_number = ?
                ORDER BY km.km_value IS NOT NULL DESC, ABS(s.length - ?) ASC
                LIMIT 1
            """, (ec_predicted, seq_len))
            
            row = cursor.fetchone()
            if row:
                conn.close()
                return dict(row)
        
        # Fallback: any sequence with experimental Km
        cursor.execute("""
            SELECT s.uniprot_id, s.length, s.organism,
                   ec.ec_number, ec.ec_name,
                   km.km_value as km_experimental
            FROM sequences s
            JOIN ec_evidence ec ON s.id = ec.sequence_id
            JOIN km_evidence km ON s.id = km.sequence_id AND km.evidence_type = 'experimental'
            ORDER BY ABS(s.length - ?) ASC
            LIMIT 1
        """, (seq_len,))
        
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
            
    except Exception as e:
        logger.error(f"Nearest neighbor error: {e}")
        return None


# Global models cache
_models = None

def get_models():
    global _models
    if _models is None:
        import joblib
        model_dir = Path('/srv/app/backend/ml_models')
        
        # Try alternative paths
        if not model_dir.exists():
            model_dir = Path('/app/ml_models')
        
        _models = {}
        
        # Load v3 model
        v3_path = model_dir / 'binary_classifier_v3.pkl'
        if v3_path.exists():
            _models['v3'] = joblib.load(v3_path)
        
        # Load v5 model
        v5_path = model_dir / 'binary_classifier_v5.pkl'
        if v5_path.exists():
            _models['v5'] = joblib.load(v5_path)
        
        # Load EC model
        ec_path = model_dir / 'ec_classifier_v3.pkl'
        if ec_path.exists():
            _models['ec'] = joblib.load(ec_path)
        
        # Load Km model
        km_path = model_dir / 'km_predictor_v3.pkl'
        if km_path.exists():
            _models['km'] = joblib.load(km_path)
        
        logger.info(f"Loaded models: {list(_models.keys())}")
    
    return _models


def predict_single(sequence: str, seq_id: str = "query") -> Dict:
    """Run complete prediction on single sequence"""
    models = get_models()
    
    # Clean and extract features
    seq_clean = ''.join(c for c in sequence.upper() if c in AA_LIST)
    features = extract_features(seq_clean)
    
    if features is None:
        return {'id': seq_id, 'error': 'Sequence too short', 'length': len(seq_clean)}
    
    result = {
        'id': seq_id,
        'length': len(seq_clean),
    }
    
    # v3 prediction
    if 'v3' in models:
        v3_model = models['v3']
        v3_features = v3_model['feature_cols']
        X_v3 = np.array([[features.get(c, 0) for c in v3_features]])
        X_v3_scaled = v3_model['scaler'].transform(X_v3)
        result['v3_prob'] = float(v3_model['model'].predict_proba(X_v3_scaled)[0][1])
    else:
        result['v3_prob'] = 0.0
    
    # v5 prediction
    if 'v5' in models:
        v5_model = models['v5']
        v5_features = v5_model['feature_cols']
        X_v5 = np.array([[features.get(c, 0) for c in v5_features]])
        X_v5_scaled = v5_model['scaler'].transform(X_v5)
        result['v5_prob'] = float(v5_model['model'].predict_proba(X_v5_scaled)[0][1])
    else:
        result['v5_prob'] = 0.0
    
    # EC prediction
    if 'ec' in models:
        ec_model = models['ec']
        ec_features = ec_model['feature_cols']
        ec_classes = list(ec_model['classes'])
        X_ec = np.array([[features.get(c, 0) for c in ec_features]])
        X_ec_scaled = ec_model['scaler'].transform(X_ec)
        ec_pred_idx = ec_model['model'].predict(X_ec_scaled)[0]
        ec_proba = ec_model['model'].predict_proba(X_ec_scaled)[0]
        result['ec_predicted'] = ec_classes[ec_pred_idx]
        result['ec_confidence'] = float(max(ec_proba))
    else:
        result['ec_predicted'] = None
        result['ec_confidence'] = 0.0
    
    # Km prediction - CORRECTED CONVERSION
    if 'km' in models and result.get('ec_predicted'):
        km_model = models['km']
        km_features = km_model['feature_cols']
        km_ecs = km_model['all_ecs']
        X_km_base = np.array([[features.get(c, 0) for c in km_features]])
        ec_onehot = np.array([[1.0 if ec == result['ec_predicted'] else 0.0 for ec in km_ecs]])
        X_km = np.hstack([X_km_base, ec_onehot])
        X_km_scaled = km_model['scaler'].transform(X_km)
        km_log = float(km_model['model'].predict(X_km_scaled)[0])
        # CRITICAL: Correct conversion - model outputs log10(Km_mM)
        result['km_predicted_uM'] = float((10 ** km_log) * 1000)
    else:
        result['km_predicted_uM'] = None
    
    # Consensus
    result['consensus'] = result['v3_prob'] > 0.5 and result['v5_prob'] > 0.3
    
    # Find nearest neighbor
    result['nearest_neighbor'] = find_nearest_neighbor(
        seq_clean, 
        result.get('ec_predicted'), 
        len(seq_clean)
    )
    
    return result


def predict_batch(sequences: List[Tuple[str, str]]) -> List[Dict]:
    """Predict on multiple sequences"""
    return [predict_single(seq, sid) for sid, seq in sequences]


def parse_fasta(fasta_text: str) -> List[Tuple[str, str]]:
    """Parse FASTA into (id, sequence) tuples"""
    sequences = []
    current_id = None
    current_seq = []
    
    for line in fasta_text.strip().split('\n'):
        line = line.strip()
        if line.startswith('>'):
            if current_id and current_seq:
                sequences.append((current_id, ''.join(current_seq)))
            current_id = line[1:].split()[0]
            current_seq = []
        elif line and current_id:
            current_seq.append(line)
    
    if current_id and current_seq:
        sequences.append((current_id, ''.join(current_seq)))
    
    return sequences
