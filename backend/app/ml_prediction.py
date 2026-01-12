"""
ML Prediction Module for CarboxyPred
Handles binary classification (v3, v5), EC classification, and Km prediction
"""

import numpy as np
import joblib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Model paths - adjust for Docker container
MODEL_DIR = Path('/srv/app/backend/ml_models')

# Amino acid list
AA_LIST = 'ACDEFGHIKLMNPQRSTVWY'

class CarboxyPredPredictor:
    """Main prediction class for CarboxyPred"""
    
    def __init__(self, model_dir: str = None):
        self.model_dir = Path(model_dir) if model_dir else MODEL_DIR
        self.models = {}
        self.loaded = False
        self._load_models()
    
    def _load_models(self):
        """Load all ML models"""
        try:
            # Binary classifier v3
            v3_path = self.model_dir / 'binary_classifier_v3.pkl'
            if v3_path.exists():
                self.models['v3'] = joblib.load(v3_path)
                logger.info(f"Loaded v3 model from {v3_path}")
            
            # Binary classifier v5
            v5_path = self.model_dir / 'binary_classifier_v5.pkl'
            if v5_path.exists():
                self.models['v5'] = joblib.load(v5_path)
                logger.info(f"Loaded v5 model from {v5_path}")
            
            # EC classifier
            ec_path = self.model_dir / 'ec_classifier_v3.pkl'
            if ec_path.exists():
                self.models['ec'] = joblib.load(ec_path)
                logger.info(f"Loaded EC model from {ec_path}")
            
            # Km predictor
            km_path = self.model_dir / 'km_predictor_v3.pkl'
            if km_path.exists():
                self.models['km'] = joblib.load(km_path)
                logger.info(f"Loaded Km model from {km_path}")
            
            self.loaded = len(self.models) > 0
            logger.info(f"Loaded {len(self.models)} models")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            self.loaded = False
    
    def extract_features(self, sequence: str) -> Optional[Dict]:
        """Extract all 447 features from sequence"""
        # Clean sequence
        seq = ''.join(c for c in str(sequence).upper() if c in AA_LIST)
        n = len(seq)
        
        if n < 50:
            return None
        
        features = {}
        
        # Catalytic residue features (inverse distance from center)
        start, end = n // 4, 3 * n // 4
        cat_region = seq[start:end]
        
        for aa in 'DEHKCST':
            features[f'inv_cat_{aa}'] = cat_region.count(aa) / len(cat_region) if cat_region else 0
        
        # Catalytic clustering
        cat_positions = [i for i, a in enumerate(seq) if a in 'DEHKC']
        if len(cat_positions) > 1:
            dists = [cat_positions[i+1] - cat_positions[i] for i in range(len(cat_positions) - 1)]
            features['inv_cat_mean_dist'] = np.mean(dists) / n
            features['inv_cat_std_dist'] = np.std(dists) / n
            features['inv_cat_min_dist'] = np.min(dists) / n
            features['inv_cat_max_dist'] = np.max(dists) / n
            features['inv_cat_clustering'] = 1 / (np.mean(dists) / n + 0.01)
        else:
            for k in ['mean_dist', 'std_dist', 'min_dist', 'max_dist', 'clustering']:
                features[f'inv_cat_{k}'] = 0
        
        # Amino acid composition
        for aa in AA_LIST:
            features[f'aa_{aa}'] = seq.count(aa) / n
        
        # Physicochemical properties
        features['inv_hydrophobic'] = sum(seq.count(a) for a in 'AILMFVWY') / n
        features['inv_polar'] = sum(seq.count(a) for a in 'STNQ') / n
        features['inv_charged'] = sum(seq.count(a) for a in 'DEKR') / n
        features['inv_aromatic'] = sum(seq.count(a) for a in 'FWY') / n
        features['inv_small'] = sum(seq.count(a) for a in 'AGST') / n
        features['inv_tiny'] = sum(seq.count(a) for a in 'AGS') / n
        features['inv_aliphatic'] = sum(seq.count(a) for a in 'AILV') / n
        features['inv_positive'] = sum(seq.count(a) for a in 'KR') / n
        features['inv_negative'] = sum(seq.count(a) for a in 'DE') / n
        features['inv_net_charge'] = (seq.count('K') + seq.count('R') - seq.count('D') - seq.count('E')) / n
        features['inv_length'] = n / 1000  # Normalized
        features['inv_log_length'] = np.log10(n)
        
        # Dipeptide composition (400 features)
        for a1 in AA_LIST:
            for a2 in AA_LIST:
                features[f'dp_{a1}{a2}'] = 0
        
        for i in range(n - 1):
            dp = f'dp_{seq[i]}{seq[i+1]}'
            if dp in features:
                features[dp] += 1
        
        if n > 1:
            for k in [k for k in features if k.startswith('dp_')]:
                features[k] /= (n - 1)
        
        # Motif features (carboxylase-specific)
        features['motif_rubisco_kk'] = seq.count('KK') / n
        features['motif_rubisco_gk'] = seq.count('GK') / n
        features['motif_ca_hh'] = seq.count('HH') / n
        features['motif_ca_his'] = sum(1 for i in range(n - 3) if seq[i:i+4].count('H') >= 2) / n
        features['motif_pepc_rr'] = seq.count('RR') / n
        features['motif_biotin_mk'] = seq.count('MK') / n
        features['motif_biotin_amk'] = seq.count('AMK') / n
        
        return features
    
    def predict_v3(self, features: Dict) -> Tuple[float, bool]:
        """Binary classification with v3 model"""
        if 'v3' not in self.models:
            return 0.0, False
        
        model = self.models['v3']
        clf = model['classifier']
        scaler = model['scaler']
        feature_cols = model['feature_cols']
        
        X = np.array([[features.get(c, 0) for c in feature_cols]])
        X_scaled = scaler.transform(X)
        
        prob = clf.predict_proba(X_scaled)[0][1]
        pred = prob >= 0.5
        
        return float(prob), bool(pred)
    
    def predict_v5(self, features: Dict, ec_pred: str = None) -> Tuple[Optional[float], Optional[bool], bool]:
        """Binary classification with v5 model (14 EC only)"""
        if 'v5' not in self.models:
            return None, None, False
        
        model = self.models['v5']
        target_ecs = model.get('target_ecs', [])
        
        # Check if EC is applicable for v5
        if ec_pred and ec_pred not in target_ecs:
            return None, None, False
        
        clf = model['classifier']
        scaler = model['scaler']
        feature_cols = model['feature_cols']
        
        X = np.array([[features.get(c, 0) for c in feature_cols]])
        X_scaled = scaler.transform(X)
        
        prob = clf.predict_proba(X_scaled)[0][1]
        pred = prob >= 0.5
        
        return float(prob), bool(pred), True
    
    def predict_ec(self, features: Dict) -> Tuple[str, float]:
        """Predict EC class"""
        if 'ec' not in self.models:
            return None, 0.0
        
        model = self.models['ec']
        clf = model['model']
        scaler = model['scaler']
        feature_cols = model['feature_cols']
        classes = list(model['classes'])
        
        X = np.array([[features.get(c, 0) for c in feature_cols]])
        X_scaled = scaler.transform(X)
        
        pred_idx = clf.predict(X_scaled)[0]
        proba = clf.predict_proba(X_scaled)[0]
        
        ec_pred = classes[pred_idx]
        confidence = float(max(proba))
        
        return ec_pred, confidence
    
    def predict_km(self, features: Dict, ec_pred: str) -> Tuple[float, float]:
        """Predict Km value (returns µM)"""
        if 'km' not in self.models:
            return None, None
        
        model = self.models['km']
        reg = model['model']
        scaler = model['scaler']
        feature_cols = model['feature_cols']
        all_ecs = model['all_ecs']
        
        # Base features
        X_base = np.array([[features.get(c, 0) for c in feature_cols]])
        
        # EC one-hot encoding - MUST be added BEFORE scaling
        ec_onehot = np.array([[1.0 if ec == ec_pred else 0.0 for ec in all_ecs]])
        X = np.hstack([X_base, ec_onehot])
        
        # Scale
        X_scaled = scaler.transform(X)
        
        # Predict log10(Km_mM)
        km_log = reg.predict(X_scaled)[0]
        
        # CRITICAL: Convert to µM correctly
        # Model outputs log10(Km_mM), so:
        # km_mM = 10 ** km_log
        # km_uM = km_mM * 1000
        km_uM = (10 ** km_log) * 1000
        
        return float(km_uM), float(km_log)
    
    def predict_single(self, sequence: str) -> Dict:
        """Run full prediction pipeline on single sequence"""
        # Extract features
        features = self.extract_features(sequence)
        if features is None:
            return {
                'success': False,
                'error': 'Sequence too short (min 50 aa)'
            }
        
        result = {
            'success': True,
            'length': len(''.join(c for c in sequence.upper() if c in AA_LIST)),
            'features_count': len(features)
        }
        
        # V3 prediction
        v3_prob, v3_pred = self.predict_v3(features)
        result['v3_prob'] = v3_prob
        result['v3_pred'] = v3_pred
        
        # EC prediction
        ec_pred, ec_conf = self.predict_ec(features)
        result['ec_pred'] = ec_pred
        result['ec_conf'] = ec_conf
        
        # V5 prediction (if applicable)
        v5_prob, v5_pred, v5_applicable = self.predict_v5(features, ec_pred)
        result['v5_prob'] = v5_prob
        result['v5_pred'] = v5_pred
        result['v5_applicable'] = v5_applicable
        
        # Consensus
        if v5_applicable and v5_pred is not None:
            result['consensus'] = v3_pred and v5_pred
            result['high_confidence'] = v3_prob >= 0.9 and (v5_prob is None or v5_prob >= 0.9)
        else:
            result['consensus'] = v3_pred
            result['high_confidence'] = v3_prob >= 0.9
        
        # Km prediction (only if predicted as carboxylase)
        if result['consensus'] and ec_pred:
            km_uM, km_log = self.predict_km(features, ec_pred)
            result['km_uM'] = km_uM
            result['km_log'] = km_log
        else:
            result['km_uM'] = None
            result['km_log'] = None
        
        # Include features for storage
        result['features'] = features
        
        return result
    
    def predict_batch(self, sequences: List[Dict]) -> List[Dict]:
        """Predict batch of sequences (list of {id, sequence} dicts)"""
        results = []
        for seq_data in sequences:
            seq_id = seq_data.get('id', 'unknown')
            sequence = seq_data.get('sequence', '')
            
            result = self.predict_single(sequence)
            result['id'] = seq_id
            results.append(result)
        
        return results
    
    def get_model_info(self) -> Dict:
        """Get information about loaded models"""
        info = {
            'loaded': self.loaded,
            'models': {}
        }
        
        for name, model in self.models.items():
            info['models'][name] = {
                'loaded': True,
                'type': type(model.get('model', None)).__name__ if isinstance(model, dict) else type(model).__name__
            }
            if isinstance(model, dict):
                if 'classes' in model:
                    info['models'][name]['n_classes'] = len(model['classes'])
                if 'feature_cols' in model:
                    info['models'][name]['n_features'] = len(model['feature_cols'])
        
        return info


# Singleton instance
_predictor = None

def get_predictor() -> CarboxyPredPredictor:
    global _predictor
    if _predictor is None:
        _predictor = CarboxyPredPredictor()
    return _predictor
