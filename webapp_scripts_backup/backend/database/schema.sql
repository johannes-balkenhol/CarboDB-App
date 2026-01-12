-- CarboxyPred Database Schema
-- Version 2.0 - January 2026

-- Main sequences table
CREATE TABLE IF NOT EXISTS sequences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uniprot_id VARCHAR(20) UNIQUE NOT NULL,
    sequence TEXT,
    length INTEGER NOT NULL,
    description TEXT,
    gene_name VARCHAR(100),
    organism VARCHAR(255),
    is_consensus_positive BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_seq_uniprot ON sequences(uniprot_id);
CREATE INDEX IF NOT EXISTS idx_seq_organism ON sequences(organism);

-- EC evidence from multiple sources
CREATE TABLE IF NOT EXISTS ec_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sequence_id INTEGER NOT NULL,
    ec_number VARCHAR(20) NOT NULL,
    ec_name VARCHAR(255),
    source VARCHAR(50) NOT NULL,  -- 'uniprot', 'brenda', 'model_predicted', 'pfam'
    evidence_type VARCHAR(50) NOT NULL,  -- 'experimental', 'curated', 'predicted'
    confidence REAL,
    priority INTEGER DEFAULT 5,  -- 1=highest priority
    details_json TEXT,
    reference TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sequence_id) REFERENCES sequences(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ec_seq ON ec_evidence(sequence_id);
CREATE INDEX IF NOT EXISTS idx_ec_source ON ec_evidence(source);
CREATE INDEX IF NOT EXISTS idx_ec_number ON ec_evidence(ec_number);

-- Km evidence from multiple sources
CREATE TABLE IF NOT EXISTS km_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sequence_id INTEGER NOT NULL,
    km_value REAL NOT NULL,  -- in µM
    km_unit VARCHAR(20) DEFAULT 'uM',
    km_log REAL,  -- log10(Km_mM)
    source VARCHAR(50) NOT NULL,  -- 'brenda', 'model_predicted', 'literature'
    evidence_type VARCHAR(50) NOT NULL,  -- 'experimental', 'predicted'
    confidence REAL,
    priority INTEGER DEFAULT 5,
    substrate VARCHAR(100),
    ph REAL,
    temperature REAL,
    details_json TEXT,
    reference TEXT,
    pubmed_id VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sequence_id) REFERENCES sequences(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_km_seq ON km_evidence(sequence_id);
CREATE INDEX IF NOT EXISTS idx_km_source ON km_evidence(source);

-- Binary predictions (v3, v5)
CREATE TABLE IF NOT EXISTS binary_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sequence_id INTEGER NOT NULL,
    v3_prob REAL,
    v3_pred BOOLEAN,
    v5_prob REAL,
    v5_pred BOOLEAN,
    consensus BOOLEAN,
    consensus_confidence VARCHAR(20),  -- 'high', 'medium', 'low'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sequence_id) REFERENCES sequences(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_binary_seq ON binary_predictions(sequence_id);
CREATE INDEX IF NOT EXISTS idx_binary_consensus ON binary_predictions(consensus);

-- Sequence features (447 features)
CREATE TABLE IF NOT EXISTS sequence_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sequence_id INTEGER NOT NULL,
    features_json TEXT NOT NULL,  -- JSON blob of all 447 features
    n_features INTEGER DEFAULT 447,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sequence_id) REFERENCES sequences(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_feat_seq ON sequence_features(sequence_id);

-- Pfam domains
CREATE TABLE IF NOT EXISTS pfam_domains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sequence_id INTEGER NOT NULL,
    pfam_id VARCHAR(20) NOT NULL,
    pfam_name VARCHAR(100),
    start_pos INTEGER,
    end_pos INTEGER,
    evalue REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sequence_id) REFERENCES sequences(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_pfam_seq ON pfam_domains(sequence_id);
CREATE INDEX IF NOT EXISTS idx_pfam_id ON pfam_domains(pfam_id);

-- EC classes reference table
CREATE TABLE IF NOT EXISTS ec_classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ec_number VARCHAR(20) UNIQUE NOT NULL,
    ec_name VARCHAR(255),
    enzyme_type VARCHAR(50),  -- 'carboxylase', 'decarboxylase', 'carbonic_anhydrase', etc.
    co2_role VARCHAR(50),  -- 'fixation', 'release', 'hydration'
    is_co2_fixing BOOLEAN DEFAULT FALSE,
    sequence_count INTEGER DEFAULT 0
);

-- Feature importance for interpretability
CREATE TABLE IF NOT EXISTS feature_importance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_type VARCHAR(50) NOT NULL,  -- 'v3', 'ec', 'km'
    rank INTEGER,
    feature_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),  -- 'catalytic', 'composition', 'dipeptide', 'physicochemical', 'motif'
    importance REAL,
    importance_pct REAL,
    description TEXT,
    biological_interpretation TEXT
);

-- View for best annotations (combines evidence sources)
CREATE VIEW IF NOT EXISTS v_best_annotations AS
SELECT 
    s.id, s.uniprot_id, s.length, s.organism, s.is_consensus_positive,
    bp.v3_prob, bp.v5_prob, bp.consensus,
    
    -- Best EC (by priority)
    (SELECT ec_number FROM ec_evidence WHERE sequence_id = s.id ORDER BY priority, confidence DESC LIMIT 1) as ec_best,
    (SELECT source FROM ec_evidence WHERE sequence_id = s.id ORDER BY priority, confidence DESC LIMIT 1) as ec_best_source,
    (SELECT ec_number FROM ec_evidence WHERE sequence_id = s.id AND evidence_type IN ('experimental', 'curated') LIMIT 1) as ec_verified,
    (SELECT ec_number FROM ec_evidence WHERE sequence_id = s.id AND source = 'model_predicted' LIMIT 1) as ec_predicted,
    
    -- Best Km (by priority)
    (SELECT km_value FROM km_evidence WHERE sequence_id = s.id ORDER BY priority, confidence DESC LIMIT 1) as km_best,
    (SELECT source FROM km_evidence WHERE sequence_id = s.id ORDER BY priority, confidence DESC LIMIT 1) as km_best_source,
    (SELECT km_value FROM km_evidence WHERE sequence_id = s.id AND evidence_type = 'experimental' LIMIT 1) as km_experimental,
    (SELECT km_value FROM km_evidence WHERE sequence_id = s.id AND source = 'model_predicted' LIMIT 1) as km_predicted,
    
    -- Source counts
    (SELECT COUNT(*) FROM ec_evidence WHERE sequence_id = s.id) as ec_evidence_count,
    (SELECT COUNT(*) FROM km_evidence WHERE sequence_id = s.id) as km_evidence_count

FROM sequences s
LEFT JOIN binary_predictions bp ON s.id = bp.sequence_id;

-- View for CO2 enzymes only
CREATE VIEW IF NOT EXISTS v_co2_enzymes AS
SELECT * FROM v_best_annotations WHERE is_consensus_positive = 1;

-- View for comparing experimental vs predicted values
CREATE VIEW IF NOT EXISTS v_evidence_comparison AS
SELECT 
    s.uniprot_id,
    ec_exp.ec_number as ec_experimental,
    ec_pred.ec_number as ec_predicted,
    ec_exp.ec_number = ec_pred.ec_number as ec_match,
    km_exp.km_value as km_experimental,
    km_pred.km_value as km_predicted,
    CASE WHEN km_exp.km_value IS NOT NULL AND km_pred.km_value IS NOT NULL
         THEN ABS(LOG10(km_exp.km_value) - LOG10(km_pred.km_value)) END as km_log_diff
FROM sequences s
LEFT JOIN ec_evidence ec_exp ON s.id = ec_exp.sequence_id AND ec_exp.evidence_type IN ('experimental', 'curated')
LEFT JOIN ec_evidence ec_pred ON s.id = ec_pred.sequence_id AND ec_pred.source = 'model_predicted'
LEFT JOIN km_evidence km_exp ON s.id = km_exp.sequence_id AND km_exp.evidence_type = 'experimental'
LEFT JOIN km_evidence km_pred ON s.id = km_pred.sequence_id AND km_pred.source = 'model_predicted'
WHERE ec_exp.ec_number IS NOT NULL OR km_exp.km_value IS NOT NULL;
