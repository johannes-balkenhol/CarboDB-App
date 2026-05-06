<!--
  StructureViewer.vue
  -------------------
  3D structure viewer for a CarboDB sequence using NGL Viewer.

  Loads the PDB file from the CarboDB backend's /external/{uid}/structure proxy
  endpoint (same-origin, no CORS issues). Offers four coloring modes:
    - pLDDT       : default — shows AlphaFold confidence per residue
    - Pfam        : highlights Pfam domain spans (passed in via prop)
    - Motifs      : highlights residue ranges from CarboDB motifs (prop)
    - Plain       : rainbow N→C

  Props:
    uniprotId         (string, required) — CarboDB uniprot_id
    apiBase           (string, default '/api/v1') — backend mount point
    pfamHits          (array, optional)   — [{pfam_id, name, start, end}, ...]
    motifPositions    (array, optional)   — [{name, start, end}, ...]

  Emits:
    structure-loaded  — on successful render
    structure-error   — on failure (with error string)

  Dependencies:
    NGL Viewer, loaded via CDN. No bundler step required.
-->
<template>
  <div class="structure-viewer">
    <div v-if="loading" class="sv-loading">
      Loading structure for {{ uniprotId }}…
    </div>

    <div v-if="error" class="sv-error">
      <p>⚠ Could not load structure: {{ error }}</p>
      <p class="sv-hint">
        AlphaFold structures are not available for every UniProt entry,
        especially very recent or unreviewed (TrEMBL) sequences.
      </p>
    </div>

    <div v-show="!loading && !error" class="sv-canvas-wrap">
      <div ref="canvasEl" class="sv-canvas"></div>

      <div class="sv-controls">
        <label>Color by:</label>
        <select v-model="colorScheme" @change="applyColorScheme">
          <option value="plddt">pLDDT (confidence)</option>
          <option value="pfam" :disabled="!hasPfam">Pfam domains</option>
          <option value="motif" :disabled="!hasMotifs">CarboDB motifs</option>
          <option value="rainbow">Rainbow (N→C)</option>
        </select>

        <button class="sv-btn" @click="resetView" title="Reset orientation">
          ⟲ Reset view
        </button>

        <a
          :href="`${apiBase}/external/${uniprotId}/structure`"
          download
          class="sv-btn sv-btn-link"
          title="Download PDB file"
        >
          ↓ PDB
        </a>
      </div>

      <div v-if="meanPlddt !== null" class="sv-info">
        <span>
          <strong>Mean pLDDT:</strong> {{ meanPlddt.toFixed(1) }}
          <span class="sv-plddt-band" :title="plddtInterpretation">
            ({{ plddtInterpretation }})
          </span>
        </span>
        <span class="sv-source">
          Source: AlphaFold DB
          <a
            :href="`https://alphafold.ebi.ac.uk/entry/${uniprotId}`"
            target="_blank"
            rel="noopener"
          >↗</a>
        </span>
      </div>
    </div>
  </div>
</template>

<script>
// NGL is loaded globally via CDN (see usage instructions in INTEGRATION.md).
// We don't import it as a module to avoid bundler complications.

export default {
  name: "StructureViewer",
  props: {
    uniprotId:      { type: String, required: true },
    apiBase:        { type: String, default: "/api/v1" },
    pfamHits:       { type: Array,  default: () => [] },
    motifPositions: { type: Array,  default: () => [] },
    meanPlddt:      { type: Number, default: null },
  },
  data() {
    return {
      loading: true,
      error: null,
      colorScheme: "plddt",
      stage: null,
      structureComponent: null,
    };
  },
  computed: {
    hasPfam() {
      return this.pfamHits.some(h => h.start != null && h.end != null);
    },
    hasMotifs() {
      return this.motifPositions.some(m => m.start != null && m.end != null);
    },
    plddtInterpretation() {
      const v = this.meanPlddt;
      if (v == null) return "";
      if (v >= 90) return "very high";
      if (v >= 70) return "confident";
      if (v >= 50) return "low";
      return "very low";
    },
  },
  mounted() {
    this.initStage();
  },
  beforeUnmount() {
    if (this.stage) {
      this.stage.dispose();
      this.stage = null;
    }
  },
  methods: {
    async initStage() {
      if (typeof NGL === "undefined") {
        this.error = "NGL Viewer library not loaded. See integration docs.";
        this.loading = false;
        return;
      }

      try {
        this.stage = new NGL.Stage(this.$refs.canvasEl, {
          backgroundColor: "white",
          quality: "medium",
        });
        // Resize handler so the canvas adjusts when its container resizes
        window.addEventListener("resize", this.handleResize);

        const url = `${this.apiBase}/external/${this.uniprotId}/structure`;
        this.structureComponent = await this.stage.loadFile(url, { ext: "pdb" });

        this.applyColorScheme();
        this.structureComponent.autoView();

        this.loading = false;
        this.$emit("structure-loaded");
      } catch (e) {
        this.error = e.message || "Unknown error";
        this.loading = false;
        this.$emit("structure-error", this.error);
      }
    },
    handleResize() {
      if (this.stage) this.stage.handleResize();
    },
    applyColorScheme() {
      if (!this.structureComponent) return;
      this.structureComponent.removeAllRepresentations();

      let colorScheme;
      let representation = "cartoon";

      switch (this.colorScheme) {
        case "plddt":
          // AlphaFold stores pLDDT in the B-factor column
          colorScheme = "bfactor";
          this.structureComponent.addRepresentation(representation, {
            colorScheme,
            colorScale: ["red", "orange", "yellow", "lightblue", "blue"],
            colorDomain: [50, 70, 90, 100],
          });
          break;

        case "pfam":
          // Default: light grey, then color each Pfam domain span
          this.structureComponent.addRepresentation(representation, {
            color: "lightgrey",
          });
          this.pfamHits.forEach((hit, i) => {
            if (hit.start == null || hit.end == null) return;
            const color = this.pfamColor(i);
            this.structureComponent.addRepresentation(representation, {
              sele: `${hit.start}-${hit.end}`,
              color,
            });
          });
          break;

        case "motif":
          this.structureComponent.addRepresentation(representation, {
            color: "lightgrey",
          });
          this.motifPositions.forEach((m, i) => {
            if (m.start == null || m.end == null) return;
            this.structureComponent.addRepresentation(representation, {
              sele: `${m.start}-${m.end}`,
              color: this.motifColor(i),
            });
          });
          // Show motif residues as sticks for emphasis
          this.motifPositions.forEach(m => {
            if (m.start == null || m.end == null) return;
            this.structureComponent.addRepresentation("ball+stick", {
              sele: `${m.start}-${m.end} and not (water or ion)`,
              color: this.motifColor(0),
            });
          });
          break;

        case "rainbow":
        default:
          this.structureComponent.addRepresentation(representation, {
            colorScheme: "residueindex",
          });
          break;
      }
    },
    resetView() {
      if (this.structureComponent) this.structureComponent.autoView(500);
    },
    pfamColor(i) {
      const palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
                       "#8c564b", "#e377c2", "#17becf"];
      return palette[i % palette.length];
    },
    motifColor(i) {
      const palette = ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00"];
      return palette[i % palette.length];
    },
  },
};
</script>

<style scoped>
.structure-viewer {
  width: 100%;
  background: #fafafa;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  overflow: hidden;
}
.sv-loading, .sv-error {
  padding: 2em;
  text-align: center;
  color: #666;
}
.sv-error { color: #b22; }
.sv-hint { font-size: 0.85em; color: #888; margin-top: 0.5em; }
.sv-canvas-wrap {
  display: flex;
  flex-direction: column;
}
.sv-canvas {
  width: 100%;
  height: 420px;
  background: white;
}
.sv-controls {
  display: flex;
  align-items: center;
  gap: 0.75em;
  padding: 0.5em 0.75em;
  border-top: 1px solid #e0e0e0;
  background: #f5f5f5;
  font-size: 0.9em;
  flex-wrap: wrap;
}
.sv-controls label { font-weight: 600; color: #444; }
.sv-controls select {
  padding: 0.25em 0.5em;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: white;
}
.sv-btn {
  padding: 0.25em 0.6em;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 0.9em;
  text-decoration: none;
  color: inherit;
}
.sv-btn:hover { background: #eef; }
.sv-btn-link { display: inline-block; }
.sv-info {
  display: flex;
  justify-content: space-between;
  padding: 0.4em 0.75em;
  font-size: 0.8em;
  color: #555;
  border-top: 1px solid #e0e0e0;
  background: #fff;
}
.sv-plddt-band { color: #888; }
.sv-source a { color: #36c; text-decoration: none; }
</style>
