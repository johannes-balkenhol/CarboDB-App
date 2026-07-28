## Open Questions to discuss / implement 

1) new model for pfam / --no-esm mode
2) No predicted or experimental km for some entries in Database. Should they be there then?
3) I have added local shap contribution per sequence (as asked) but if not fully accurate can be removed. The model-level Shap is also present under collapsable header.
4) The database does not contain pfam annotation details (description, e-value, bitscore) for entries. If that is by choice, then ignore.
5) 894 entries are missing both features_composition and features_esm2. to check which ones 
    ```
    sqlite3 -header -tabs data/primary/carbodb.sqlite "
        SELECT
        s.id AS sequence_id,
        s.cdb_id,
        s.uniprot_id,
        s.ec_number,
        s.organism,
        s.source,
        s.length,
        p.co2_prob AS carboxylase_probability,
        p.ec_pred,
        p.ec_conf,
        p.km_predicted_mM,
        p.km_predicted_log10
        FROM sequences s
        JOIN predictions p
        ON p.sequence_id = s.id
        LEFT JOIN features_composition fc
        ON fc.sequence_id = s.id
        LEFT JOIN features_esm2 fe
        ON fe.sequence_id = s.id
        WHERE fc.sequence_id IS NULL
        AND fe.sequence_id IS NULL
        ORDER BY s.id;
        "
    ```
