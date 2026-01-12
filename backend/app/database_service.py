"""
CarboxyPred Database Service
Provides access to the comprehensive carboxylase database
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager

DB_PATH = Path('/app/database_files/carboxylase.db')

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


@dataclass
class SequenceRecord:
    """Complete sequence record with all annotations"""
    id: int
    uniprot_id: str
    length: int
    description: Optional[str] = None
    gene_name: Optional[str] = None
    organism: Optional[str] = None
    sequence: Optional[str] = None
    
    # ML predictions
    is_co2_enzyme: Optional[bool] = None
    co2_prob_v3: Optional[float] = None
    co2_prob_v5: Optional[float] = None
    consensus_confidence: Optional[str] = None
    ec_predicted: Optional[str] = None
    km_predicted_uM: Optional[float] = None
    
    # Verified annotations
    ec_verified: Optional[str] = None
    ec_name: Optional[str] = None
    
    # Experimental data
    km_experimental: Optional[float] = None
    
    # Domains
    pfam_domains: Optional[str] = None
    
    # Features (JSON)
    features: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


class CarboxyPredDB:
    """Database access class for CarboxyPred"""
    
    def __init__(self, db_path: str = None):
        self.db_path = Path(db_path) if db_path else DB_PATH
    
    def get_sequence_by_id(self, seq_id: int) -> Optional[Dict]:
        """Get complete sequence record by ID"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM v_best_annotations WHERE id = ?
            """, (seq_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None
    
    def get_sequence_by_uniprot(self, uniprot_id: str) -> Optional[Dict]:
        """Get complete sequence record by UniProt ID"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM v_best_annotations WHERE uniprot_id = ?
            """, (uniprot_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None
    
    def search_sequences(self, 
                        query: str = None,
                        ec_class: str = None,
                        is_co2_enzyme: bool = None,
                        min_length: int = None,
                        max_length: int = None,
                        organism: str = None,
                        has_km: bool = None,
                        verified_only: bool = None,
                        limit: int = 100,
                        offset: int = 0) -> List[Dict]:
        """Search sequences with filters"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            conditions = []
            params = []
            
            if query:
                conditions.append("(uniprot_id LIKE ? OR organism LIKE ?)")
                params.extend([f'%{query}%', f'%{query}%'])
            
            if ec_class:
                conditions.append("(ec_best = ? OR ec_predicted = ?)")
                params.extend([ec_class, ec_class])
            
            if is_co2_enzyme is not None:
                conditions.append("consensus_prediction = ?")
                params.append(1 if is_co2_enzyme else 0)
            
            if min_length:
                conditions.append("length >= ?")
                params.append(min_length)
            
            if max_length:
                conditions.append("length <= ?")
                params.append(max_length)
            
            if organism:
                conditions.append("organism LIKE ?")
                params.append(f'%{organism}%')
            
            if has_km:
                conditions.append("(km_best IS NOT NULL OR km_predicted IS NOT NULL)")
            
            if verified_only:
                conditions.append("ec_verified IS NOT NULL")
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            sql = f"""
                SELECT * FROM v_best_annotations
                WHERE {where_clause}
                ORDER BY v3_prob DESC NULLS LAST
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])
            
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_sequence_features(self, seq_id: int) -> Optional[Dict]:
        """Get all 447 features for a sequence"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT features_json
                FROM sequence_features
                WHERE sequence_id = ?
            """, (seq_id,))
            row = cursor.fetchone()
            if row and row['features_json']:
                return json.loads(row['features_json'])
        return None
    
    def get_ec_classes(self) -> List[Dict]:
        """Get all EC classes with counts"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ec_number, ec_name, is_co2_fixing, sequence_count
                FROM ec_classes
                ORDER BY sequence_count DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total sequences
            cursor.execute("SELECT COUNT(*) FROM sequences")
            stats['total_sequences'] = cursor.fetchone()[0]
            
            # CO2 enzymes (consensus positive)
            cursor.execute("SELECT COUNT(*) FROM ml_predictions WHERE consensus_prediction = 1")
            stats['co2_enzymes'] = cursor.fetchone()[0]
            
            # With verified EC
            cursor.execute("SELECT COUNT(DISTINCT sequence_id) FROM ec_annotations WHERE source IN ('uniprot', 'brenda')")
            stats['with_verified_ec'] = cursor.fetchone()[0]
            
            # With experimental Km
            cursor.execute("SELECT COUNT(DISTINCT sequence_id) FROM brenda_kinetics ")
            stats['with_experimental_km'] = cursor.fetchone()[0]
            
            # With features
            cursor.execute("SELECT COUNT(*) FROM sequence_features")
            stats['with_features'] = cursor.fetchone()[0]
            
            # EC distribution (top 10)
            cursor.execute("""
                SELECT ec_number, COUNT(*) as count
                FROM ec_annotations
                GROUP BY ec_number
                ORDER BY count DESC
                LIMIT 10
            """)
            stats['ec_distribution'] = [dict(row) for row in cursor.fetchall()]
            
            return stats
    
    def get_evidence_comparison(self, limit: int = 100) -> List[Dict]:
        """Get sequences with both experimental and predicted values"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM v_evidence_comparison
                WHERE ec_experimental IS NOT NULL OR km_experimental IS NOT NULL
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_feature_importance(self) -> List[Dict]:
        """Get feature importance rankings"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM feature_importance
                ORDER BY rank
            """)
            return [dict(row) for row in cursor.fetchall()]


# Singleton instance
_db = None

def get_database() -> CarboxyPredDB:
    global _db
    if _db is None:
        _db = CarboxyPredDB()
    return _db
