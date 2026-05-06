<!--
  ExtendedDetails.vue
  -------------------
  Lazy-loaded "extended details" section for a CarboDB sequence detail panel.

  Hidden behind a button until the user clicks "Show extended annotation".
  On click, fetches /api/v1/external/{uniprot_id} from the CarboDB backend
  (which proxies+caches UniProt + AlphaFold). Renders:
    - Function description
    - Subcellular location
    - GO terms (3 columns)
    - Active sites + binding sites (with positions)
    - Cross-references (PDB, KEGG, Reactome, BRENDA, etc.)
    - Taxonomic lineage
    - 3D structure viewer (StructureViewer.vue)

  Props:
    uniprotId      (string, required) — CarboDB uniprot_id
    apiBase        (string, default '/api/v1')
    pfamHits       (array, optional)  — passed through to StructureViewer
                                         for Pfam-based coloring; expected
                                         shape: [{pfam_id, name, start?, end?}]

  Note on Pfam coordinates: CarboDB's pfam_hits don't always carry residue
  positions (depends on whether 04b_hmmer.sh stored them). If positions are
  missing, the StructureViewer falls back to the pLDDT or rainbow scheme;
  the "Pfam" coloring option is disabled.
-->
<template>
  <div class="extended-details">
    <!-- Trigger button -->
    <button
      v-if="!loaded && !loading"
      class="ed-trigger"
      @click="loadExternalData"
    >
      🔬 Show extended annotation (UniProt + AlphaFold)
      <span class="ed-trigger-hint">
        — fetches GO terms, function description, active sites, 3D structure
      </span>
    </button>

    <div v-if="loading" class="ed-loading">
      Fetching extended annotation from UniProt and AlphaFold…
    </div>

    <div v-if="loadError" class="ed-error">
      <p>⚠ Could not load extended annotation: {{ loadError }}</p>
      <button class="ed-retry" @click="loadExternalData">Retry</button>
    </div>

    <div v-if="loaded && data" class="ed-content">
      <!-- Header with metadata + cache status -->
      <div class="ed-header">
        <h3 class="ed-h">Extended annotation</h3>
        <div class="ed-meta">
          <span v-if="data.stale" class="ed-badge ed-badge-warn">
            Cached ({{ formatRelative(data.cached_at) }}) — upstream unavailable
          </span>
          <span v-else-if="data.from_cache" class="ed-badge">
            Cached {{ formatRelative(data.cached_at) }}
          </span>
          <span v-else class="ed-badge ed-badge-fresh">Just fetched</span>
          <button class="ed-refresh" @click="loadExternalData(true)" title="Force refresh">
            ⟲ Refresh
          </button>
        </div>
      </div>

      <!-- 3D structure -->
      <section v-if="data.alphafold && data.alphafold.available" class="ed-section">
        <h4 class="ed-h4">3D structure (AlphaFold)</h4>
        <StructureViewer
          :uniprot-id="uniprotId"
          :api-base="apiBase"
          :pfam-hits="annotatedPfamHits"
          :motif-positions="motifPositionsFromUniprot"
          :mean-plddt="data.alphafold.mean_plddt"
        />
      </section>
      <section v-else class="ed-section ed-no-structure">
        <h4 class="ed-h4">3D structure</h4>
        <p>No AlphaFold structure available for this UniProt entry.</p>
      </section>

      <!-- Function -->
      <section v-if="data.uniprot.function_text" class="ed-section">
        <h4 class="ed-h4">Function (UniProt)</h4>
        <p class="ed-fn">{{ data.uniprot.function_text }}</p>
      </section>

      <!-- Subcellular location -->
      <section v-if="data.uniprot.subcellular_location && data.uniprot.subcellular_location.length" class="ed-section">
        <h4 class="ed-h4">Subcellular location</h4>
        <p>
          <span
            v-for="(loc, i) in data.uniprot.subcellular_location"
            :key="i"
            class="ed-pill"
          >{{ loc }}</span>
        </p>
      </section>

      <!-- GO terms in 3 columns -->
      <section v-if="hasAnyGoTerms" class="ed-section">
        <h4 class="ed-h4">Gene Ontology</h4>
        <div class="ed-go-cols">
          <div class="ed-go-col">
            <h5>Molecular function</h5>
            <ul>
              <li v-for="g in data.uniprot.go_terms.molecular_function" :key="g.id">
                <a :href="`https://www.ebi.ac.uk/QuickGO/term/${g.id}`" target="_blank" rel="noopener">{{ g.name }}</a>
                <span class="ed-evidence" :title="evidenceTooltip(g.evidence)">[{{ g.evidence }}]</span>
              </li>
              <li v-if="!data.uniprot.go_terms.molecular_function.length" class="ed-empty">—</li>
            </ul>
          </div>
          <div class="ed-go-col">
            <h5>Biological process</h5>
            <ul>
              <li v-for="g in data.uniprot.go_terms.biological_process" :key="g.id">
                <a :href="`https://www.ebi.ac.uk/QuickGO/term/${g.id}`" target="_blank" rel="noopener">{{ g.name }}</a>
                <span class="ed-evidence" :title="evidenceTooltip(g.evidence)">[{{ g.evidence }}]</span>
              </li>
              <li v-if="!data.uniprot.go_terms.biological_process.length" class="ed-empty">—</li>
            </ul>
          </div>
          <div class="ed-go-col">
            <h5>Cellular component</h5>
            <ul>
              <li v-for="g in data.uniprot.go_terms.cellular_component" :key="g.id">
                <a :href="`https://www.ebi.ac.uk/QuickGO/term/${g.id}`" target="_blank" rel="noopener">{{ g.name }}</a>
                <span class="ed-evidence" :title="evidenceTooltip(g.evidence)">[{{ g.evidence }}]</span>
              </li>
              <li v-if="!data.uniprot.go_terms.cellular_component.length" class="ed-empty">—</li>
            </ul>
          </div>
        </div>
      </section>

      <!-- Active and binding sites -->
      <section v-if="(data.uniprot.active_sites || []).length || (data.uniprot.binding_sites || []).length" class="ed-section">
        <h4 class="ed-h4">Functional sites</h4>
        <div class="ed-sites">
          <div v-if="data.uniprot.active_sites && data.uniprot.active_sites.length">
            <strong>Active sites:</strong>
            <ul class="ed-site-list">
              <li v-for="s in data.uniprot.active_sites" :key="`a${s.position}`">
                Position {{ s.position }} — {{ s.description || "active site" }}
              </li>
            </ul>
          </div>
          <div v-if="data.uniprot.binding_sites && data.uniprot.binding_sites.length">
            <strong>Binding sites:</strong>
            <ul class="ed-site-list">
              <li v-for="(s, i) in data.uniprot.binding_sites" :key="`b${i}`">
                Pos {{ s.position_start }}{{ s.position_end !== s.position_start ? `-${s.position_end}` : '' }}
                — {{ s.ligand || s.description || "binding site" }}
              </li>
            </ul>
          </div>
        </div>
      </section>

      <!-- Taxonomy -->
      <section v-if="data.uniprot.lineage && data.uniprot.lineage.length" class="ed-section">
        <h4 class="ed-h4">Taxonomy</h4>
        <p class="ed-lineage">
          <span v-for="(l, i) in data.uniprot.lineage" :key="i">
            {{ l }}<span v-if="i < data.uniprot.lineage.length - 1" class="ed-arrow"> › </span>
          </span>
        </p>
      </section>

      <!-- Cross-references -->
      <section v-if="hasCrossRefs" class="ed-section">
        <h4 class="ed-h4">Cross-references</h4>
        <div class="ed-xrefs">
          <div v-for="(ids, db) in data.uniprot.cross_refs" :key="db" class="ed-xref-group">
            <strong>{{ db }}:</strong>
            <a
              v-for="id in ids.slice(0, 5)"
              :key="id"
              :href="crossRefUrl(db, id)"
              target="_blank"
              rel="noopener"
              class="ed-xref-link"
            >{{ id }}</a>
            <span v-if="ids.length > 5" class="ed-xref-more">+{{ ids.length - 5 }} more</span>
          </div>
        </div>
      </section>

      <!-- Footer -->
      <p class="ed-footer">
        Data: <a :href="`https://www.uniprot.org/uniprotkb/${uniprotId}`" target="_blank" rel="noopener">UniProt {{ uniprotId }}</a>
        ·
        <a :href="`https://alphafold.ebi.ac.uk/entry/${uniprotId}`" target="_blank" rel="noopener">AlphaFold</a>
      </p>
    </div>
  </div>
</template>

<script>
import StructureViewer from "./StructureViewer.vue";

const GO_EVIDENCE_TOOLTIPS = {
  IDA: "Inferred from Direct Assay (experimental)",
  IMP: "Inferred from Mutant Phenotype",
  IGI: "Inferred from Genetic Interaction",
  IPI: "Inferred from Physical Interaction",
  IEP: "Inferred from Expression Pattern",
  ISS: "Inferred from Sequence/Structural Similarity",
  ISO: "Inferred from Sequence Orthology",
  ISA: "Inferred from Sequence Alignment",
  ISM: "Inferred from Sequence Model",
  IBA: "Inferred from Biological aspect of Ancestor",
  IEA: "Inferred from Electronic Annotation (automatic)",
  TAS: "Traceable Author Statement",
  NAS: "Non-traceable Author Statement",
  IC:  "Inferred by Curator",
};

const CROSS_REF_URL_PATTERNS = {
  PDB:        "https://www.rcsb.org/structure/{id}",
  KEGG:       "https://www.kegg.jp/entry/{id}",
  Reactome:   "https://reactome.org/content/detail/{id}",
  BRENDA:     "https://www.brenda-enzymes.org/enzyme.php?ecno={id}",
  InterPro:   "https://www.ebi.ac.uk/interpro/entry/InterPro/{id}",
  Pfam:       "https://www.ebi.ac.uk/interpro/entry/pfam/{id}",
  PANTHER:    "http://www.pantherdb.org/panther/family.do?clsAccession={id}",
  AlphaFoldDB:"https://alphafold.ebi.ac.uk/entry/{id}",
};

export default {
  name: "ExtendedDetails",
  components: { StructureViewer },
  props: {
    uniprotId:  { type: String, required: true },
    apiBase:    { type: String, default: "/api/v1" },
    pfamHits:   { type: Array,  default: () => [] },
  },
  data() {
    return {
      loaded: false,
      loading: false,
      loadError: null,
      data: null,
    };
  },
  computed: {
    hasAnyGoTerms() {
      const g = this.data?.uniprot?.go_terms || {};
      return ["molecular_function", "biological_process", "cellular_component"]
        .some(k => (g[k] || []).length);
    },
    hasCrossRefs() {
      const xr = this.data?.uniprot?.cross_refs || {};
      return Object.keys(xr).length > 0;
    },
    annotatedPfamHits() {
      // StructureViewer needs {pfam_id, name, start, end}. CarboDB may
      // pass hits without start/end; merge in any positions we found in
      // UniProt's domain features as a fallback.
      const upd = this.data?.uniprot?.domains_uniprot || [];
      return this.pfamHits.map(h => {
        if (h.start != null && h.end != null) return h;
        const match = upd.find(d => d.name && h.name && d.name.includes(h.name));
        return match ? { ...h, start: match.start, end: match.end } : h;
      });
    },
    motifPositionsFromUniprot() {
      // Pull active and binding sites as "motifs" for the Motif coloring scheme.
      const sites = [];
      (this.data?.uniprot?.active_sites || []).forEach(s => sites.push({
        name: `Active site (${s.description})`,
        start: s.position, end: s.position
      }));
      (this.data?.uniprot?.binding_sites || []).forEach(s => sites.push({
        name: `Binding site (${s.ligand || 'ligand'})`,
        start: s.position_start, end: s.position_end
      }));
      return sites;
    },
  },
  methods: {
    async loadExternalData(refresh = false) {
      this.loading = true;
      this.loadError = null;
      try {
        const url = `${this.apiBase}/external/${this.uniprotId}` +
                    (refresh ? "?refresh=true" : "");
        const r = await fetch(url);
        if (!r.ok) {
          const txt = await r.text();
          throw new Error(`${r.status}: ${txt}`);
        }
        this.data = await r.json();
        this.loaded = true;
      } catch (e) {
        this.loadError = e.message;
      } finally {
        this.loading = false;
      }
    },
    formatRelative(ts) {
      if (!ts) return "";
      const ago = Math.floor((Date.now() / 1000) - ts);
      if (ago < 3600)        return `${Math.floor(ago / 60)}m ago`;
      if (ago < 86400)       return `${Math.floor(ago / 3600)}h ago`;
      if (ago < 30 * 86400)  return `${Math.floor(ago / 86400)}d ago`;
      return `${Math.floor(ago / (30 * 86400))}mo ago`;
    },
    evidenceTooltip(code) {
      return GO_EVIDENCE_TOOLTIPS[code] || `Evidence code: ${code}`;
    },
    crossRefUrl(db, id) {
      const pat = CROSS_REF_URL_PATTERNS[db];
      return pat ? pat.replace("{id}", id) : "#";
    },
  },
};
</script>

<style scoped>
.extended-details { margin-top: 1.5em; }

.ed-trigger {
  width: 100%;
  padding: 0.85em 1em;
  background: linear-gradient(180deg, #f0f6ff, #e0ecff);
  border: 1px solid #b8d0ee;
  border-radius: 6px;
  font-size: 1em;
  font-weight: 600;
  color: #234;
  cursor: pointer;
  text-align: left;
}
.ed-trigger:hover { background: linear-gradient(180deg, #e8f0fc, #cee0fc); }
.ed-trigger-hint { font-weight: normal; color: #678; font-size: 0.88em; }

.ed-loading, .ed-error {
  padding: 1.5em;
  text-align: center;
  color: #666;
  border: 1px dashed #ccc;
  border-radius: 6px;
}
.ed-error { color: #b22; border-color: #ebb; }
.ed-retry {
  margin-top: 0.5em;
  padding: 0.3em 1em;
  background: white;
  border: 1px solid #b22;
  color: #b22;
  border-radius: 4px;
  cursor: pointer;
}

.ed-content {
  border: 1px solid #d8d8d8;
  border-radius: 6px;
  padding: 1em 1.25em;
  background: #fff;
}
.ed-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75em;
  padding-bottom: 0.5em;
  border-bottom: 1px solid #eee;
}
.ed-h { margin: 0; font-size: 1.05em; }
.ed-h4 {
  font-size: 0.95em;
  margin: 0.25em 0 0.5em;
  color: #345;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.ed-meta { display: flex; gap: 0.5em; align-items: center; }
.ed-badge {
  font-size: 0.75em;
  padding: 0.15em 0.6em;
  border-radius: 99px;
  background: #eef;
  color: #557;
}
.ed-badge-fresh { background: #dfe; color: #261; }
.ed-badge-warn  { background: #fea; color: #841; }
.ed-refresh {
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 0.15em 0.6em;
  cursor: pointer;
  font-size: 0.8em;
}

.ed-section { margin: 1.25em 0; }
.ed-section.ed-no-structure { color: #888; font-style: italic; }
.ed-fn { line-height: 1.5; color: #234; }
.ed-pill {
  display: inline-block;
  margin: 0.15em 0.3em 0.15em 0;
  padding: 0.2em 0.7em;
  background: #eef;
  border-radius: 99px;
  font-size: 0.9em;
}

.ed-go-cols {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1em;
}
.ed-go-col h5 {
  font-size: 0.85em;
  font-weight: 600;
  color: #56a;
  text-transform: uppercase;
  margin: 0 0 0.4em;
}
.ed-go-col ul { margin: 0; padding-left: 1.1em; }
.ed-go-col li { font-size: 0.9em; margin: 0.15em 0; }
.ed-go-col li a { color: #234; text-decoration: none; }
.ed-go-col li a:hover { text-decoration: underline; }
.ed-evidence {
  font-size: 0.8em;
  color: #888;
  margin-left: 0.3em;
  font-family: monospace;
}
.ed-empty { color: #aaa; }

.ed-sites { display: flex; gap: 2em; flex-wrap: wrap; }
.ed-site-list { margin: 0.25em 0; padding-left: 1.1em; font-size: 0.9em; }

.ed-lineage { font-size: 0.92em; color: #456; }
.ed-arrow   { color: #aaa; margin: 0 0.2em; }

.ed-xrefs { display: flex; flex-direction: column; gap: 0.4em; }
.ed-xref-group { font-size: 0.9em; }
.ed-xref-link {
  display: inline-block;
  margin: 0 0.3em;
  padding: 0.1em 0.5em;
  background: #f0f4f8;
  border-radius: 3px;
  color: #234;
  text-decoration: none;
  font-family: monospace;
  font-size: 0.88em;
}
.ed-xref-link:hover { background: #dde6f2; }
.ed-xref-more { color: #888; font-size: 0.85em; }

.ed-footer {
  margin-top: 1.25em;
  padding-top: 0.5em;
  border-top: 1px solid #eee;
  font-size: 0.85em;
  color: #888;
  text-align: right;
}
.ed-footer a { color: #36c; text-decoration: none; }

@media (max-width: 800px) {
  .ed-go-cols { grid-template-columns: 1fr; }
}
</style>
