#!/usr/bin/env python3
"""
Import 695k HPC predictions into CarboxyPred webapp database

Usage:
    python import_695k_predictions.py /path/to/full_predictions.csv /path/to/carboxylase.db

The CSV should have columns:
    uid, ec_uniprot, organism, length, sequence, v3_prob, v3_pred, v5_prob, 
    v5_applicable, high_confidence, consensus, ec_pred, ec_conf, ec_match, 
    km_log, km_uM, brenda_km_mM, brenda_ec, features_json
"""

import sqlite3
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import shutil
import argparse
import sys


def backup_database(db_path: Path) -> Path:
    """Create a backup of the database"""
    backup_path = db_path.parent / f"{db_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{db_path.suffix}"
    shutil.copy(db_path, backup_path)
    print(f"✓ Database backed up to {backup_path}")
    return backup_path


def get_existing_uids(conn: sqlite3.Connection) -> set:
    """Get set of existing UniProt IDs"""
    cursor = conn.cursor()
    cursor.execute("SELECT uniprot_id FROM sequences")
    return set(row[0] for row in cursor.fetchall())


def import_predictions(csv_path: Path, db_path: Path, batch_size: int = 10000):
    """Import predictions from CSV to database"""
    
    print(f"Loading predictions from {csv_path}...")
    
    # Check file exists
    if not csv_path.exists():
        print(f"ERROR: CSV file not found: {csv_path}")
        sys.exit(1)
    
    if not db_path.exists():
        print(f"ERROR: Database not found: {db_path}")
        sys.exit(1)
    
    # Backup database
    backup_database(db_path)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get existing UIDs
    print("Checking existing sequences...")
    existing = get_existing_uids(conn)
    print(f"Found {len(existing)} existing sequences")
    
    # Process in chunks
    total_inserted = 0
    total_skipped = 0
    chunk_num = 0
    
    for chunk in pd.read_csv(csv_path, chunksize=batch_size, low_memory=False):
        chunk_num += 1
        print(f"\nProcessing chunk {chunk_num}...")
        
        new_rows = chunk[~chunk['uid'].isin(existing)]
        skipped = len(chunk) - len(new_rows)
        total_skipped += skipped
        
        if len(new_rows) == 0:
            print(f"  All {len(chunk)} sequences already exist, skipping")
            continue
        
        print(f"  {len(new_rows)} new sequences ({skipped} skipped)")
        
        for _, row in new_rows.iterrows():
            try:
                # Insert sequence
                cursor.execute("""
                    INSERT INTO sequences (uniprot_id, sequence, length, organism, is_consensus_positive)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    row['uid'], 
                    row.get('sequence', ''), 
                    row['length'], 
                    row.get('organism', ''),
                    row.get('consensus', False) == True or row.get('v3_pred', False) == True
                ))
                
                seq_id = cursor.lastrowid
                
                # Insert binary predictions
                cursor.execute("""
                    INSERT INTO binary_predictions (sequence_id, v3_prob, v3_pred, v5_prob, v5_pred, consensus)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    seq_id,
                    row.get('v3_prob'),
                    row.get('v3_pred', False) == True,
                    row.get('v5_prob') if pd.notna(row.get('v5_prob')) else None,
                    None,
                    row.get('consensus', False) == True
                ))
                
                # Insert EC evidence - UniProt annotation
                if pd.notna(row.get('ec_uniprot')) and row.get('ec_uniprot'):
                    cursor.execute("""
                        INSERT INTO ec_evidence (sequence_id, ec_number, source, evidence_type, priority)
                        VALUES (?, ?, 'uniprot', 'curated', 2)
                    """, (seq_id, row['ec_uniprot']))
                
                # Insert EC evidence - Model prediction
                if pd.notna(row.get('ec_pred')) and row.get('ec_pred'):
                    cursor.execute("""
                        INSERT INTO ec_evidence (sequence_id, ec_number, source, evidence_type, confidence, priority)
                        VALUES (?, ?, 'model_predicted', 'predicted', ?, 5)
                    """, (seq_id, row['ec_pred'], row.get('ec_conf')))
                
                # Insert Km evidence - Model prediction (ALREADY CORRECTED in CSV!)
                if pd.notna(row.get('km_uM')):
                    cursor.execute("""
                        INSERT INTO km_evidence (sequence_id, km_value, km_unit, km_log, source, evidence_type, priority)
                        VALUES (?, ?, 'uM', ?, 'model_predicted', 'predicted', 5)
                    """, (seq_id, row['km_uM'], row.get('km_log')))
                
                # Insert Km evidence - BRENDA experimental
                if pd.notna(row.get('brenda_km_mM')):
                    brenda_km_uM = row['brenda_km_mM'] * 1000
                    cursor.execute("""
                        INSERT INTO km_evidence (sequence_id, km_value, km_unit, source, evidence_type, priority)
                        VALUES (?, ?, 'uM', 'brenda', 'experimental', 1)
                    """, (seq_id, brenda_km_uM))
                
                # Insert features
                if pd.notna(row.get('features_json')):
                    cursor.execute("""
                        INSERT INTO sequence_features (sequence_id, features_json, n_features)
                        VALUES (?, ?, 447)
                    """, (seq_id, row['features_json']))
                
                total_inserted += 1
                existing.add(row['uid'])
                
            except Exception as e:
                print(f"  Error inserting {row['uid']}: {e}")
                continue
        
        # Commit after each chunk
        conn.commit()
        print(f"  Committed. Total inserted: {total_inserted}")
    
    # Final summary
    print("\n" + "="*60)
    print("IMPORT COMPLETE")
    print("="*60)
    print(f"Total inserted: {total_inserted}")
    print(f"Total skipped (already existed): {total_skipped}")
    
    # Verify counts
    cursor.execute("SELECT COUNT(*) FROM sequences")
    print(f"Total sequences in database: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM sequences WHERE is_consensus_positive = 1")
    print(f"CO2 enzymes (consensus positive): {cursor.fetchone()[0]}")
    
    conn.close()


def main():
    parser = argparse.ArgumentParser(description='Import 695k predictions to CarboxyPred database')
    parser.add_argument('csv_path', type=Path, help='Path to full_predictions CSV file')
    parser.add_argument('db_path', type=Path, help='Path to carboxylase.db database')
    parser.add_argument('--batch-size', type=int, default=10000, help='Batch size for processing')
    
    args = parser.parse_args()
    
    import_predictions(args.csv_path, args.db_path, args.batch_size)


if __name__ == '__main__':
    main()
