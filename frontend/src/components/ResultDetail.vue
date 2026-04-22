<template>
  <div class="result-detail">
    <!-- ═══ HEADER ═══════════════════════════════════════════════════════ -->
    <header class="rd-header">
      <div class="rd-header-main">
        <div class="rd-id">
          <span class="rd-id-label">Query</span>
          <h2 class="rd-id-value">{{ result.id || result.cdb_query_id || 'sequence' }}</h2>
        </div>
        <div class="rd-verdict" :class="verdictClass">
          <span class="rd-verdict-icon">{{ result.is_carboxylase ? '✓' : '✗' }}</span>
          <div class="rd-verdict-text">
            <strong>{{ result.is_carboxylase ? 'Carboxylase' : 'Not carboxylase' }}</strong>
            <span class="rd-verdict-sub">{{ formatConfidence }}</span>
          </div>
        </div>
      </div>

      <div class="rd-subtitle" v-if="result.ec_name">
        <span class="rd-ec-badge">EC {{ result.ec_predicted }}</span>
        <span class="rd-ec-name">{{ result.ec_name }}</span>
      </div>

      <button v-if="closable" @click="$emit('close')" class="rd-close" aria-label="Close">×</button>
    </header>

    <!-- ═══ WARNINGS ═════════════════════════════════════════════════════ -->
    <div v-if="result.warnings && result.warnings.length" class="rd-warnings">
      <div v-for="(w, i) in result.warnings" :key="i" class="rd-warning">
        <span class="rd-warning-icon">⚠</span>{{ w }}
      </div>
    </div>

    <!-- ═══ PREDICTION SUMMARY — 3 top-line scores ═══════════════════════ -->
    <section class="rd-section rd-summary">
      <div class="rd-metric">
        <div class="rd-metric-label">CO₂ probability</div>
        <div class="rd-metric-value" :class="probClass(result.carboxylase_probability)">
          {{ formatPct(result.carboxylase_probability) }}
        </div>
        <div class="rd-metric-bar">
          <div class="rd-metric-bar-fill" :class="probClass(result.carboxylase_probability)"
               :style="{ width: (result.carboxylase_probability * 100) + '%' }"></div>
        </div>
      </div>

      <div class="rd-metric">
        <div class="rd-metric-label">EC confidence</div>
        <div class="rd-metric-value" :class="probClass(result.ec_confidence)">
          {{ formatPct(result.ec_confidence) }}
        </div>
        <div class="rd-metric-bar">
          <div class="rd-metric-bar-fill" :class="probClass(result.ec_confidence)"
               :style="{ width: ((result.ec_confidence || 0) * 100) + '%' }"></div>
        </div>
      </div>

      <div class="rd-metric">
        <div class="rd-metric-label">Predicted Km (CO₂)</div>
        <div class="rd-metric-value rd-metric-km" v-if="result.km_predicted_uM != null">
          {{ result.km_predicted_uM.toFixed(1) }} <span class="rd-unit">µM</span>
        </div>
        <div class="rd-metric-value rd-metric-na" v-else>—</div>
        <div class="rd-metric-sub" v-if="result.km_predicted_log10 != null">
          log₁₀ = {{ result.km_predicted_log10.toFixed(2) }} mM
        </div>
      </div>
    </section>

    <!-- ═══ EC PROBABILITY DISTRIBUTION ══════════════════════════════════ -->
    <section v-if="sortedEcProbs.length > 0" class="rd-section">
      <h3 class="rd-section-title">EC classification — top candidates</h3>
      <div class="rd-ec-bars">
        <div v-for="(item, i) in sortedEcProbs" :key="item.ec"
             class="rd-ec-bar" :class="{ 'rd-ec-bar-top': i === 0 }">
          <span class="rd-ec-bar-label">EC {{ item.ec }}</span>
          <span class="rd-ec-bar-name">{{ item.name }}</span>
          <div class="rd-ec-bar-track">
            <div class="rd-ec-bar-fill" :style="{ width: (item.prob * 100) + '%' }"></div>
          </div>
          <span class="rd-ec-bar-value">{{ formatPct(item.prob) }}</span>
        </div>
      </div>
    </section>

    <!-- ═══ PFAM DOMAINS ═════════════════════════════════════════════════ -->
    <section v-if="pfamNormalized.length > 0" class="rd-section">
      <h3 class="rd-section-title">Pfam domains ({{ pfamNormalized.length }})</h3>
      <table class="rd-table">
        <thead>
          <tr><th>Accession</th><th>Name</th><th class="num">E-value</th><th class="num">Bitscore</th></tr>
        </thead>
        <tbody>
          <tr v-for="hit in pfamNormalized" :key="hit.accession">
            <td>
              <a :href="'https://www.ebi.ac.uk/interpro/entry/pfam/' + hit.accession"
                 target="_blank" rel="noopener" class="rd-link">
                {{ hit.accession }}
              </a>
            </td>
            <td class="rd-mono">{{ hit.name || '—' }}</td>
            <td class="num rd-mono">{{ hit.e_value != null ? hit.e_value.toExponential(1) : '—' }}</td>
            <td class="num rd-mono">{{ hit.bitscore != null ? hit.bitscore.toFixed(1) : '—' }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- ═══ SEQUENCE MOTIFS ══════════════════════════════════════════════ -->
    <section v-if="motifHits.length > 0" class="rd-section">
      <h3 class="rd-section-title">Sequence motifs</h3>
      <div class="rd-motif-grid">
        <div v-for="m in motifHits" :key="m.key"
             class="rd-motif" :class="{ 'rd-motif-hit': m.value > 0 }">
          <div class="rd-motif-label">{{ m.label }}</div>
          <div class="rd-motif-value">{{ m.value > 0 ? m.value.toFixed(3) : '—' }}</div>
          <div class="rd-motif-desc">{{ m.description }}</div>
        </div>
      </div>
    </section>

    <!-- ═══ PHYSICOCHEMICAL PROPERTIES ═══════════════════════════════════ -->
    <section v-if="physProps.length > 0" class="rd-section">
      <h3 class="rd-section-title">Physicochemical properties</h3>
      <div class="rd-phys-grid">
        <div v-for="p in physProps" :key="p.key" class="rd-phys-cell">
          <div class="rd-phys-label">{{ p.label }}</div>
          <div class="rd-phys-value">{{ p.display }}</div>
        </div>
      </div>
    </section>

    <!-- ═══ SHAP FEATURE IMPORTANCE ══════════════════════════════════════ -->
    <section v-if="hasShap" class="rd-section">
      <h3 class="rd-section-title">
        Feature importance
        <span class="rd-section-sub">from training-time SHAP analysis</span>
      </h3>

      <!-- Tabs -->
      <div class="rd-shap-tabs">
        <button v-for="tab in shapTabs" :key="tab.id"
                :class="{ active: shapTab === tab.id }"
                @click="shapTab = tab.id"
                class="rd-shap-tab">
          {{ tab.label }}
          <span v-if="tab.count" class="rd-shap-tab-count">{{ tab.count }}</span>
        </button>
      </div>

      <!-- Group importance pie -->
      <div v-if="currentGroupImportance" class="rd-shap-groups">
        <div class="rd-shap-groups-title">Feature group contribution</div>
        <div class="rd-shap-groups-bar">
          <div v-for="(pct, group) in currentGroupImportance" :key="group"
               class="rd-shap-group-seg"
               :style="{ width: pct + '%', background: groupColor(group) }"
               :title="`${group}: ${pct.toFixed(1)}%`"></div>
        </div>
        <div class="rd-shap-groups-legend">
          <span v-for="(pct, group) in currentGroupImportance" :key="group"
                class="rd-shap-group-item">
            <span class="rd-shap-group-swatch" :style="{ background: groupColor(group) }"></span>
            {{ group }} <strong>{{ pct.toFixed(1) }}%</strong>
          </span>
        </div>
      </div>

      <!-- Top features list -->
      <div v-if="currentShapFeatures.length > 0" class="rd-shap-features">
        <!-- Summary banner: how many of the top SHAP features are present in the query -->
        <div v-if="matchSummary" class="rd-match-summary" :class="'rd-match-verdict-' + matchSummary.verdict">
          <div class="rd-match-summary-main">
            Your sequence matches
            <strong>{{ matchSummary.hits }} / {{ matchSummary.interpretable }}</strong>
            of the most important features
            <span v-if="matchSummary.unknown > 0" class="rd-match-summary-unknown">
              ({{ matchSummary.unknown }} uninterpretable — e.g. ESM-2 embedding dims)
            </span>
          </div>
          <div class="rd-match-summary-verdict">
            <span v-if="matchSummary.verdict === 'strong'">Strong support</span>
            <span v-else-if="matchSummary.verdict === 'moderate'">Moderate support</span>
            <span v-else>Weak support — prediction likely extrapolated</span>
          </div>
        </div>

        <div v-for="feat in currentShapFeatures" :key="feat.rank + '-' + feat.feature"
             class="rd-shap-feat">
          <span class="rd-shap-rank">{{ feat.rank }}</span>
          <div class="rd-shap-feat-main">
            <span class="rd-shap-feat-name rd-mono">{{ featureDisplay(feat.feature) }}</span>
            <span class="rd-shap-feat-group" :style="{ color: groupColor(feat.group) }">
              {{ feat.group }}
            </span>
          </div>
          <div class="rd-shap-feat-bar">
            <div class="rd-shap-feat-bar-fill"
                 :style="{
                   width: shapBarWidth(feat, currentShapFeatures) + '%',
                   background: groupColor(feat.group)
                 }"></div>
          </div>
          <span class="rd-match-pill"
                :class="'rd-match-' + matchStatus(feat)"
                :title="matchTooltip(feat)">
            <template v-if="matchStatus(feat) === 'hit'">✓</template>
            <template v-else-if="matchStatus(feat) === 'absent'">✗</template>
            <template v-else-if="matchStatus(feat) === 'value'">{{ matchValue(feat) }}</template>
            <template v-else>—</template>
          </span>
          <span class="rd-shap-feat-value rd-mono">
            {{ feat.pct_importance != null ? feat.pct_importance.toFixed(2) + '%' : feat.mean_abs_shap?.toFixed(3) }}
          </span>
        </div>
      </div>
      <div v-else class="rd-shap-empty">
        No SHAP data available for this EC class.
        <span v-if="result.shap?.km_training_stats?.n_samples === 0">
          (No training samples in this class.)
        </span>
      </div>
    </section>

    <!-- NEAREST EXPERIMENTAL-Km NEIGHBORS (BLAST) -->
    <section class="rd-section">
      <h3 class="rd-section-title">
        Nearest neighbors with experimental Km
        <span class="rd-section-sub">BLAST against sequences with BRENDA/SwissProt measurements</span>
      </h3>

      <div v-if="!result.top_similar || result.top_similar.length === 0" class="rd-neighbor-empty">
        No experimental-Km reference available for EC <strong>{{ result.ec_predicted || '—' }}</strong>.
        Either this EC class has no measured Km values in CarboDB, or your sequence
        did not BLAST-match any of them above the significance threshold.
      </div>

      <div v-else class="rd-neighbor-list">
        <div v-for="sim in result.top_similar"
             :key="sim.uniprot_id"
             class="rd-neighbor-card"
             :class="'rd-tier-' + (sim.tier || 'unknown')">

          <div class="rd-neighbor-head">
            <span class="rd-neighbor-rank">#{{ sim.rank }}</span>
            <a :href="'https://www.uniprot.org/uniprotkb/' + sim.uniprot_id"
               target="_blank" rel="noopener" class="rd-link rd-neighbor-uid">
              {{ sim.uniprot_id }}
              <span class="rd-external">↗</span>
            </a>
            <span class="rd-neighbor-org">{{ sim.organism || 'unknown organism' }}</span>
            <span class="rd-neighbor-tier">{{ sim.tier_label || sim.tier }}</span>
          </div>

          <div class="rd-neighbor-identity">
            <div class="rd-identity-bar">
              <div class="rd-identity-fill"
                   :style="{ width: (sim.identity_pct || 0) + '%' }"></div>
            </div>
            <span class="rd-identity-label">
              {{ sim.identity_pct?.toFixed(1) ?? '?' }}% identity
              <span class="rd-identity-meta">
                (e={{ formatEvalue(sim.evalue) }},
                {{ sim.align_length }} aa aligned)
              </span>
            </span>
          </div>

          <div class="rd-km-compare">
            <div class="rd-km-box rd-km-experimental">
              <div class="rd-km-label">Measured K<sub>m</sub><span v-if="sim.km_exp_substrate">
                ({{ sim.km_exp_substrate }})</span></div>
              <div class="rd-km-value">
                {{ sim.km_experimental_uM?.toFixed(1) ?? '—' }}
                <span class="rd-km-unit">µM</span>
              </div>
            </div>
            <div class="rd-km-arrow">↔</div>
            <div class="rd-km-box rd-km-predicted">
              <div class="rd-km-label">Your predicted K<sub>m</sub></div>
              <div class="rd-km-value">
                {{ result.km_predicted_uM?.toFixed(1) ?? '—' }}
                <span class="rd-km-unit">µM</span>
              </div>
            </div>
            <div v-if="foldChange(sim) !== null"
                 class="rd-km-delta"
                 :class="deltaClass(foldChange(sim))">
              {{ foldChangeLabel(sim) }}
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══ FOOTER METADATA ══════════════════════════════════════════════ -->
    <footer class="rd-footer">
      <span>Mode: <strong>{{ result.mode }}</strong></span>
      <span>Kingdom: <strong>{{ result.kingdom }}</strong></span>
      <span>Features: <strong>{{ (result.features_used || []).join(', ') || '—' }}</strong></span>
      <span>Runtime: <strong>{{ result.runtime_seconds?.toFixed(1) }}s</strong></span>
      <span v-if="result.novelty_flag">
        Novelty: <strong :class="'rd-novelty-' + result.novelty_flag">{{ result.novelty_flag }}</strong>
      </span>
    </footer>
  </div>
</template>

<script setup>
import { computed, ref, watchEffect } from 'vue'

const props = defineProps({
  result:   { type: Object, required: true },
  closable: { type: Boolean, default: true },
})
defineEmits(['close'])

const shapTab = ref('ec_classification')

// ─── Formatting helpers ──────────────────────────────────────────────────
function formatPct(p) {
  if (p == null) return '—'
  return (p * 100).toFixed(p >= 0.999 ? 2 : 1) + '%'
}
function probClass(p) {
  if (p == null) return 'rd-prob-na'
  if (p >= 0.9) return 'rd-prob-high'
  if (p >= 0.5) return 'rd-prob-mid'
  return 'rd-prob-low'
}

const verdictClass = computed(() => {
  if (!props.result.is_carboxylase) return 'rd-verdict-neg'
  const p = props.result.carboxylase_probability || 0
  return p >= 0.9 ? 'rd-verdict-strong' : 'rd-verdict-weak'
})

const formatConfidence = computed(() => {
  const c = props.result.confidence
  const p = props.result.carboxylase_probability
  if (!c && p == null) return ''
  if (c) return `${c} confidence · ${formatPct(p)}`
  return formatPct(p)
})

// ─── EC probability distribution ─────────────────────────────────────────
// Backend returns ec_probabilities as { "4.1.1.39": 0.9998, ... }.
// Sort descending, keep top 5, look up names from EC_NAMES if available.
const EC_NAMES = {
  '4.1.1.39': 'RuBisCO',
  '4.1.1.31': 'PEP carboxylase',
  '4.1.1.32': 'PEPCK (GTP)',
  '4.1.1.49': 'PEPCK (ATP)',
  '4.1.1.1':  'Pyruvate decarboxylase',
  '4.2.1.1':  'Carbonic anhydrase',
  '6.3.4.14': 'Biotin carboxylase',
  '6.4.1.1':  'Pyruvate carboxylase',
  '6.4.1.2':  'Acetyl-CoA carboxylase',
  '6.4.1.3':  'Propionyl-CoA carboxylase',
  '6.4.1.4':  '3-MCC',
  '6.3.5.5':  'Carbamoyl-P synthase',
  '6.3.3.3':  'Dethiobiotin synthase',
  '1.2.7.7':  '2-OG:ferredoxin oxidoreductase',
  '2.7.2.2':  'Carbamate kinase',
}
const sortedEcProbs = computed(() => {
  const probs = props.result.ec_probabilities || {}
  return Object.entries(probs)
    .map(([ec, prob]) => ({ ec, prob, name: EC_NAMES[ec] || ec }))
    .sort((a, b) => b.prob - a.prob)
    .slice(0, 5)
    .filter(x => x.prob > 0.0001) // hide near-zero probabilities
})

// ─── Pfam normalization (handles both old list[str] and new list[dict]) ──
const pfamNormalized = computed(() => {
  const hits = props.result.pfam_hits || []
  return hits.map(h => {
    if (typeof h === 'string') return { accession: h, name: null, e_value: null, bitscore: null }
    return { accession: h.accession, name: h.name, e_value: h.e_value, bitscore: h.bitscore }
  })
})

// ─── Motif interpretation ────────────────────────────────────────────────
// The pipeline computes 7 EC-specific regex motifs. Surface them with labels.
// Motif keys map to EC numbers with digits concatenated (motif_4111 = EC 4.1.1.1).
// The 'inv_*' keys are the human-readable catalytic-core signatures.
const MOTIF_META = {
  // Catalytic core signatures (inv_*)
  inv_rubisco_sig: { label: 'RuBisCO signature',  description: 'RuBisCO large-subunit catalytic core' },
  inv_pepc_sig:    { label: 'PEPC signature',     description: 'PEP carboxylase catalytic region' },
  inv_ca_zinc:     { label: 'CA zinc site',       description: 'Carbonic anhydrase zinc coordination' },
  inv_atp_grasp:   { label: 'ATP-grasp fold',     description: 'Biotin carboxylase ATP-binding fold' },
  inv_amkm:        { label: 'AMKM motif',         description: 'Biotin attachment Ala-Met-Lys-Met context' },
  // EC-specific regex motifs (motif_* — keyed by EC number digits)
  motif_4111:  { label: 'Pyruvate decarboxylase (4.1.1.1)',  description: 'PDC regex motif' },
  motif_4113:  { label: 'Oxaloacetate decarboxylase (4.1.1.3)', description: 'OAA decarboxylase motif' },
  motif_4113b: { label: 'OAA decarb. alt (4.1.1.3)',         description: 'OAA decarboxylase alt form' },
  motif_4113c: { label: 'OAA decarb. alt2 (4.1.1.3)',        description: 'OAA decarboxylase alt form 2' },
  motif_4114:  { label: 'Acetolactate decarb. (4.1.1.4)',    description: 'Acetolactate decarboxylase motif' },
  motif_41112: { label: 'β-Carbonic anhydrase (4.1.1.112)',  description: 'β-CA motif' },
  motif_41149: { label: 'PEPCK ATP (4.1.1.49)',              description: 'PEP carboxykinase ATP form' },
  motif_4211:  { label: 'Carbonic anhydrase (4.2.1.1)',      description: 'CA superfamily motif' },
  motif_6316:  { label: 'Acetyl-CoA synth. (6.3.1.6)',       description: 'Acetate-CoA ligase motif' },
  motif_6333:  { label: 'Dethiobiotin synth. (6.3.3.3)',     description: 'Dethiobiotin synthase motif' },
  motif_6341:  { label: 'Carbamoyl-P synth. (6.3.4.1)',      description: 'Carbamoyl-phosphate motif' },
  motif_6341b: { label: 'Carbamoyl-P alt (6.3.4.1)',         description: 'Carbamoyl-phosphate alt form' },
  motif_6355:  { label: 'Carbamoyl-P synth. (6.3.5.5)',      description: 'Carbamoyl-P synthase large' },
  motif_6411:  { label: 'Pyruvate carboxylase (6.4.1.1)',    description: 'Pyruvate carboxylase motif' },
  motif_6412:  { label: 'Acetyl-CoA carb. (6.4.1.2)',        description: 'ACC motif' },
  motif_6413:  { label: 'Propionyl-CoA carb. (6.4.1.3)',     description: 'PCC motif' },
  motif_6414:  { label: '3-MCC (6.4.1.4)',                   description: '3-methylcrotonyl-CoA carb.' },
}
const motifHits = computed(() => {
  const f = props.result.features_computed || {}
  return Object.keys(MOTIF_META)
    .filter(k => k in f)
    .map(k => ({ key: k, label: MOTIF_META[k].label, description: MOTIF_META[k].description, value: Number(f[k]) || 0 }))
})

// ─── Physicochemical properties ──────────────────────────────────────────
const PHYS_META = [
  { key: 'phys_mw',          label: 'MW (kDa)',     fmt: v => (v / 1000).toFixed(1) },
  { key: 'phys_length_raw',  label: 'Length (aa)',  fmt: v => Math.round(v).toString() },
  { key: 'phys_length',      label: 'log₁₀ length', fmt: v => v.toFixed(2) },
  { key: 'phys_pi',          label: 'pI',           fmt: v => v.toFixed(2) },
  { key: 'phys_gravy',       label: 'GRAVY',        fmt: v => v.toFixed(3) },
  { key: 'phys_hydrophob',   label: 'Hydrophob.',   fmt: v => v.toFixed(2) },
  { key: 'phys_aromaticity', label: 'Aromaticity',  fmt: v => (v * 100).toFixed(1) + '%' },
  { key: 'phys_aromatic',    label: 'Aromatic f',   fmt: v => (v * 100).toFixed(1) + '%' },
  { key: 'phys_instability', label: 'Instability',  fmt: v => v.toFixed(2) },
  { key: 'phys_net_charge',  label: 'Net charge',   fmt: v => v.toFixed(3) },
  { key: 'phys_charge_pos',  label: 'Positive f',   fmt: v => (v * 100).toFixed(1) + '%' },
  { key: 'phys_charge_neg',  label: 'Negative f',   fmt: v => (v * 100).toFixed(1) + '%' },
  { key: 'phys_polar',       label: 'Polar f',      fmt: v => (v * 100).toFixed(1) + '%' },
  { key: 'phys_aliphatic',   label: 'Aliphatic f',  fmt: v => (v * 100).toFixed(1) + '%' },
  { key: 'phys_acidic',      label: 'Acidic f',     fmt: v => (v * 100).toFixed(1) + '%' },
  { key: 'phys_basic',       label: 'Basic f',      fmt: v => (v * 100).toFixed(1) + '%' },
  { key: 'phys_cys_ratio',   label: 'Cys %',        fmt: v => (v * 100).toFixed(2) + '%' },
  { key: 'phys_pro_ratio',   label: 'Pro %',        fmt: v => (v * 100).toFixed(2) + '%' },
  { key: 'phys_gly_ratio',   label: 'Gly %',        fmt: v => (v * 100).toFixed(2) + '%' },
  { key: 'phys_his_ratio',   label: 'His %',        fmt: v => (v * 100).toFixed(2) + '%' },
]
const physProps = computed(() => {
  const f = props.result.features_computed || {}
  return PHYS_META
    .filter(meta => meta.key in f && f[meta.key] != null)
    .map(meta => ({ key: meta.key, label: meta.label, display: meta.fmt(Number(f[meta.key])) }))
})

// ─── SHAP tabs ───────────────────────────────────────────────────────────
const hasShap = computed(() => !!props.result.shap)

const shapTabs = computed(() => {
  const s = props.result.shap || {}
  return [
    { id: 'ec_classification', label: 'EC class',     count: (s.ec_classification || []).length },
    { id: 'km_regression',     label: 'Km',           count: (s.km_regression || []).length },
    { id: 'binary_global',     label: 'Carboxylase',  count: (s.binary_global || []).length },
  ].filter(t => t.count > 0)
})

const currentShapFeatures = computed(() => {
  return (props.result.shap || {})[shapTab.value] || []
})

const currentGroupImportance = computed(() => {
  const s = props.result.shap || {}
  const map = {
    ec_classification: 'ec_group_importance',
    km_regression:     'km_group_importance',
    binary_global:     'binary_group_importance',
  }
  return s[map[shapTab.value]] || null
})

// Fallback: if the active tab becomes empty after a data swap, pick the first available
watchEffect(() => {
  if (shapTabs.value.length > 0 && !shapTabs.value.find(t => t.id === shapTab.value)) {
    shapTab.value = shapTabs.value[0].id
  }
})

// ─── SHAP rendering helpers ──────────────────────────────────────────────
const GROUP_COLORS = {
  'ESM-2 embedding':          '#667eea',
  'Pfam domains':             '#48bb78',
  'Catalytic core motifs':    '#ed8936',
  'Dipeptide composition':    '#9f7aea',
  'Amino acid composition':   '#38b2ac',
  'Physicochemical':          '#f56565',
  'EC-specific motifs':       '#d69e2e',
  'InterPro':                 '#4299e1',
  'Other':                    '#a0aec0',
}
function groupColor(g) { return GROUP_COLORS[g] || '#a0aec0' }

function shapBarWidth(feat, list) {
  const max = Math.max(...list.map(f => f.pct_importance ?? f.mean_abs_shap ?? 0))
  const v = feat.pct_importance ?? feat.mean_abs_shap ?? 0
  return max > 0 ? (v / max) * 100 : 0
}

// Make raw feature names more human-readable where possible.
function featureDisplay(name) {
  if (!name) return ''
  if (name.startsWith('pfam_'))  return name.replace('pfam_', 'Pfam ')
  if (name.startsWith('dp_'))    return 'dipeptide ' + name.slice(3)
  if (name.startsWith('aac_'))   return 'AAC ' + name.slice(4)
  if (name.startsWith('phys_'))  return name.replace('phys_', '').replace(/_/g, ' ')
  if (name.startsWith('motif_')) return name.replace('motif_', '').replace(/_/g, ' ')
  if (name.startsWith('inv_'))   return 'catalytic ' + name.slice(4).replace(/_/g, ' ')
  if (name.startsWith('esm2_'))  return 'ESM-2 dim ' + name.slice(5)
  return name
}


// Nearest-neighbor helper functions (BLAST hits)
function formatEvalue(e) {
  if (e === null || e === undefined) return '?'
  if (e === 0) return '0'
  if (e < 1e-100) return '<1e-100'
  if (e < 0.01) return e.toExponential(1)
  return e.toFixed(3)
}

function foldChange(sim) {
  const pred = props.result?.km_predicted_uM
  const exp = sim?.km_experimental_uM
  if (!pred || !exp || pred <= 0 || exp <= 0) return null
  return pred >= exp ? pred / exp : exp / pred
}

function foldChangeLabel(sim) {
  const fc = foldChange(sim)
  if (fc === null) return ''
  const pred = props.result?.km_predicted_uM
  const exp = sim?.km_experimental_uM
  const dir = pred >= exp ? 'higher' : 'lower'
  return `Δ = ${fc.toFixed(1)}× ${dir}`
}

function deltaClass(fc) {
  if (fc === null) return ''
  if (fc < 2) return 'rd-km-delta-good'
  if (fc < 5) return 'rd-km-delta-ok'
  return 'rd-km-delta-warn'
}


// ─── SHAP "Your sequence" column helpers ─────────────────────────────────
function matchStatus(feat) {
  const name = feat.feature || ''
  const computed = props.result.features_computed || {}
  const pfamHits = (props.result.pfam_hits || []).map(h => h.accession || h)

  let m = name.match(/^pfam_(PF\d+)$/i)
  if (m) return pfamHits.includes(m[1]) ? 'hit' : 'absent'
  if (name === 'Pfam n_hits' || name === 'pfam_n_hits') {
    return pfamHits.length > 0 ? 'hit' : 'absent'
  }
  if (/^(motif_|inv_)/.test(name)) {
    const v = computed[name]
    if (v == null) return 'unknown'
    return v > 0 ? 'hit' : 'absent'
  }
  if (name.startsWith('phys_')) {
    return computed[name] != null ? 'value' : 'unknown'
  }
  return 'unknown'
}

function matchValue(feat) {
  const computed = props.result.features_computed || {}
  const v = computed[feat.feature]
  if (v == null || typeof v !== 'number') return '?'
  return Math.abs(v) < 0.01 ? v.toExponential(1) : v.toFixed(3)
}

function matchTooltip(feat) {
  const status = matchStatus(feat)
  const name = feat.feature
  if (status === 'hit')     return `${name}: present in your sequence`
  if (status === 'absent')  return `${name}: not found in your sequence`
  if (status === 'value')   return `${name}: ${matchValue(feat)}`
  return `${name}: not directly interpretable (embedding/composition dim)`
}

const matchSummary = computed(() => {
  const feats = currentShapFeatures.value || []
  if (!feats.length) return null
  let hits = 0, absent = 0, unknown = 0
  for (const f of feats) {
    const s = matchStatus(f)
    if (s === 'hit') hits++
    else if (s === 'absent') absent++
    else unknown++
  }
  const interpretable = hits + absent
  if (interpretable === 0) return null
  const ratio = hits / interpretable
  let verdict = 'weak'
  if (ratio >= 0.6) verdict = 'strong'
  else if (ratio >= 0.3) verdict = 'moderate'
  return { hits, absent, unknown, total: feats.length, interpretable, verdict }
})

</script>

<style scoped>
/* ═══ Root ═══════════════════════════════════════════════════════════════ */
.result-detail {
  background: white;
  border-radius: 12px;
  padding: 0;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  position: relative;
}

/* ═══ Header ═════════════════════════════════════════════════════════════ */
.rd-header {
  padding: 24px 28px 18px;
  background: linear-gradient(135deg, #f7fafc 0%, #ffffff 100%);
  border-bottom: 1px solid #e2e8f0;
  position: relative;
}
.rd-header-main {
  display: flex; justify-content: space-between; align-items: flex-start;
  gap: 24px; flex-wrap: wrap;
}
.rd-id-label {
  display: block; font-size: 11px; text-transform: uppercase;
  letter-spacing: 0.08em; color: #a0aec0; font-weight: 600;
}
.rd-id-value {
  margin: 2px 0 0; font-size: 22px; color: #2d3748; font-weight: 700;
  font-family: 'Monaco', 'SF Mono', monospace;
}
.rd-subtitle {
  margin-top: 12px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
}
.rd-ec-badge {
  padding: 4px 10px; background: #2d3748; color: white;
  border-radius: 6px; font-size: 12px; font-weight: 600;
  font-family: 'Monaco', monospace;
}
.rd-ec-name { color: #4a5568; font-size: 15px; font-style: italic; }

.rd-verdict {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 16px; border-radius: 10px; background: #f7fafc;
  border: 1px solid #e2e8f0;
}
.rd-verdict-strong { background: #f0fff4; border-color: #9ae6b4; }
.rd-verdict-weak   { background: #fffaf0; border-color: #fbd38d; }
.rd-verdict-neg    { background: #fff5f5; border-color: #feb2b2; }
.rd-verdict-icon {
  font-size: 20px; width: 32px; height: 32px; display: flex;
  align-items: center; justify-content: center; border-radius: 50%;
}
.rd-verdict-strong .rd-verdict-icon { background: #48bb78; color: white; }
.rd-verdict-weak   .rd-verdict-icon { background: #ed8936; color: white; }
.rd-verdict-neg    .rd-verdict-icon { background: #e53e3e; color: white; }
.rd-verdict-text strong { display: block; font-size: 14px; color: #2d3748; }
.rd-verdict-sub { font-size: 12px; color: #718096; text-transform: capitalize; }

.rd-close {
  position: absolute; top: 16px; right: 16px;
  width: 28px; height: 28px; border: none; border-radius: 50%;
  background: #edf2f7; color: #4a5568; font-size: 20px; line-height: 1;
  cursor: pointer; transition: background 0.15s;
}
.rd-close:hover { background: #e2e8f0; }

/* ═══ Warnings ═══════════════════════════════════════════════════════════ */
.rd-warnings { padding: 0 28px; margin-top: 14px; }
.rd-warning {
  background: #fffaf0; border: 1px solid #fbd38d; color: #7b341e;
  padding: 8px 12px; border-radius: 6px; margin-bottom: 6px;
  font-size: 13px; display: flex; align-items: center; gap: 8px;
}
.rd-warning-icon { flex-shrink: 0; color: #d69e2e; }

/* ═══ Sections ═══════════════════════════════════════════════════════════ */
.rd-section { padding: 22px 28px; border-bottom: 1px solid #edf2f7; }
.rd-section:last-of-type { border-bottom: none; }
.rd-section-title {
  margin: 0 0 16px; font-size: 14px; color: #4a5568;
  text-transform: uppercase; letter-spacing: 0.06em; font-weight: 700;
  display: flex; align-items: baseline; gap: 10px;
}
.rd-section-sub {
  font-size: 12px; color: #a0aec0; text-transform: none;
  letter-spacing: 0; font-weight: 400; font-style: italic;
}

/* ═══ Summary metrics ════════════════════════════════════════════════════ */
.rd-summary {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;
}
.rd-metric-label {
  font-size: 11px; color: #a0aec0; text-transform: uppercase;
  letter-spacing: 0.06em; font-weight: 600;
}
.rd-metric-value {
  font-size: 28px; font-weight: 700; color: #2d3748; margin: 4px 0 8px;
  font-variant-numeric: tabular-nums;
}
.rd-metric-value.rd-prob-high { color: #38a169; }
.rd-metric-value.rd-prob-mid  { color: #d69e2e; }
.rd-metric-value.rd-prob-low  { color: #e53e3e; }
.rd-metric-value.rd-metric-na { color: #cbd5e0; font-weight: 500; }
.rd-metric-km   { color: #2d3748; font-family: 'Monaco', monospace; font-size: 24px; }
.rd-unit { font-size: 14px; color: #718096; font-weight: 500; margin-left: 2px; }
.rd-metric-sub { font-size: 11px; color: #a0aec0; font-family: 'Monaco', monospace; }
.rd-metric-bar { height: 4px; background: #edf2f7; border-radius: 2px; overflow: hidden; }
.rd-metric-bar-fill { height: 100%; transition: width 0.4s ease; }
.rd-metric-bar-fill.rd-prob-high { background: #48bb78; }
.rd-metric-bar-fill.rd-prob-mid  { background: #ed8936; }
.rd-metric-bar-fill.rd-prob-low  { background: #e53e3e; }
.rd-metric-bar-fill.rd-prob-na   { background: #cbd5e0; }

/* ═══ EC probability bars ════════════════════════════════════════════════ */
.rd-ec-bars { display: flex; flex-direction: column; gap: 8px; }
.rd-ec-bar {
  display: grid; grid-template-columns: 80px 1fr 2fr 60px; gap: 12px;
  align-items: center; padding: 6px 0; font-size: 13px;
}
.rd-ec-bar-top { font-weight: 600; }
.rd-ec-bar-label { font-family: 'Monaco', monospace; color: #2d3748; }
.rd-ec-bar-name { color: #718096; font-style: italic; }
.rd-ec-bar-top .rd-ec-bar-name { color: #2d3748; font-style: normal; }
.rd-ec-bar-track { height: 8px; background: #edf2f7; border-radius: 4px; overflow: hidden; }
.rd-ec-bar-fill  { height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); transition: width 0.5s ease; }
.rd-ec-bar-top .rd-ec-bar-fill { background: linear-gradient(90deg, #48bb78, #38a169); }
.rd-ec-bar-value {
  font-family: 'Monaco', monospace; text-align: right; color: #4a5568;
  font-variant-numeric: tabular-nums;
}

/* ═══ Tables (Pfam, similar) ═════════════════════════════════════════════ */
.rd-table {
  width: 100%; border-collapse: collapse; font-size: 13px;
}
.rd-table th {
  text-align: left; padding: 8px 12px; background: #f7fafc;
  color: #718096; font-weight: 600; font-size: 11px;
  text-transform: uppercase; letter-spacing: 0.05em;
  border-bottom: 1px solid #e2e8f0;
}
.rd-table th.num, .rd-table td.num { text-align: right; }
.rd-table td { padding: 10px 12px; border-bottom: 1px solid #edf2f7; color: #2d3748; }
.rd-table tr:last-child td { border-bottom: none; }
.rd-table tr:hover td { background: #fafbfc; }

.rd-link { color: #667eea; text-decoration: none; font-weight: 500; }
.rd-link:hover { text-decoration: underline; }
.rd-mono { font-family: 'Monaco', 'SF Mono', 'Menlo', monospace; font-size: 12px; }

/* ═══ Motif grid ═════════════════════════════════════════════════════════ */
.rd-motif-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 10px;
}
.rd-motif {
  padding: 12px 14px; background: #f7fafc; border-radius: 8px;
  border: 1px solid #edf2f7; opacity: 0.5; transition: all 0.2s;
}
.rd-motif-hit {
  opacity: 1; background: #f0fff4; border-color: #9ae6b4;
  box-shadow: 0 1px 3px rgba(72, 187, 120, 0.15);
}
.rd-motif-label {
  font-size: 12px; font-weight: 700; color: #4a5568;
  text-transform: uppercase; letter-spacing: 0.04em;
}
.rd-motif-hit .rd-motif-label { color: #22543d; }
.rd-motif-value {
  font-family: 'Monaco', monospace; font-size: 18px;
  font-weight: 700; color: #2d3748; margin: 2px 0;
  font-variant-numeric: tabular-nums;
}
.rd-motif:not(.rd-motif-hit) .rd-motif-value { color: #cbd5e0; }
.rd-motif-desc { font-size: 11px; color: #718096; line-height: 1.3; }

/* ═══ Phys grid ══════════════════════════════════════════════════════════ */
.rd-phys-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 2px; background: #edf2f7; border-radius: 8px; overflow: hidden;
  border: 1px solid #edf2f7;
}
.rd-phys-cell { padding: 10px 12px; background: white; }
.rd-phys-label {
  font-size: 10px; color: #a0aec0; text-transform: uppercase;
  letter-spacing: 0.05em; font-weight: 600;
}
.rd-phys-value {
  font-family: 'Monaco', monospace; font-size: 14px;
  color: #2d3748; font-weight: 600; margin-top: 2px;
  font-variant-numeric: tabular-nums;
}

/* ═══ SHAP ═══════════════════════════════════════════════════════════════ */
.rd-shap-tabs { display: flex; gap: 4px; margin-bottom: 16px; border-bottom: 1px solid #e2e8f0; }
.rd-shap-tab {
  padding: 8px 14px; border: none; background: transparent;
  color: #718096; font-size: 13px; font-weight: 500; cursor: pointer;
  border-bottom: 2px solid transparent; margin-bottom: -1px;
  display: flex; align-items: center; gap: 6px;
}
.rd-shap-tab:hover { color: #4a5568; }
.rd-shap-tab.active {
  color: #2d3748; border-bottom-color: #667eea; font-weight: 600;
}
.rd-shap-tab-count {
  background: #edf2f7; color: #718096; padding: 1px 6px;
  border-radius: 10px; font-size: 11px;
}
.rd-shap-tab.active .rd-shap-tab-count { background: #667eea; color: white; }

.rd-shap-groups { margin-bottom: 18px; }
.rd-shap-groups-title {
  font-size: 11px; color: #a0aec0; text-transform: uppercase;
  letter-spacing: 0.05em; margin-bottom: 6px; font-weight: 600;
}
.rd-shap-groups-bar {
  height: 12px; border-radius: 6px; overflow: hidden;
  display: flex; background: #edf2f7;
}
.rd-shap-group-seg { transition: opacity 0.2s; }
.rd-shap-group-seg:hover { opacity: 0.8; }
.rd-shap-groups-legend {
  display: flex; flex-wrap: wrap; gap: 12px; margin-top: 8px;
  font-size: 12px; color: #4a5568;
}
.rd-shap-group-item { display: flex; align-items: center; gap: 5px; }
.rd-shap-group-swatch {
  width: 10px; height: 10px; border-radius: 2px; display: inline-block;
}

.rd-shap-features { display: flex; flex-direction: column; gap: 6px; }
.rd-shap-feat {
  display: grid; grid-template-columns: 24px 1fr 1.5fr 60px; gap: 10px;
  align-items: center; padding: 6px 0; font-size: 13px;
}
.rd-shap-rank {
  font-family: 'Monaco', monospace; color: #a0aec0;
  font-size: 11px; text-align: right;
}
.rd-shap-feat-main { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.rd-shap-feat-name {
  color: #2d3748; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.rd-shap-feat-group { font-size: 10px; font-weight: 600; }
.rd-shap-feat-bar {
  height: 6px; background: #edf2f7; border-radius: 3px; overflow: hidden;
}
.rd-shap-feat-bar-fill { height: 100%; transition: width 0.4s ease; }
.rd-shap-feat-value {
  text-align: right; color: #4a5568; font-variant-numeric: tabular-nums;
}
.rd-shap-empty {
  padding: 20px; text-align: center; color: #a0aec0; font-style: italic;
  background: #f7fafc; border-radius: 8px; font-size: 13px;
}

/* ═══ Footer ═════════════════════════════════════════════════════════════ */
.rd-footer {
  padding: 14px 28px; background: #f7fafc; font-size: 12px;
  color: #718096; display: flex; flex-wrap: wrap; gap: 20px;
}
.rd-footer strong { color: #2d3748; font-weight: 600; }
.rd-novelty-known      { color: #38a169; }
.rd-novelty-borderline { color: #d69e2e; }
.rd-novelty-novel      { color: #3182ce; }

/* ═══ Tags ═══════════════════════════════════════════════════════════════ */
.rd-tag {
  display: inline-block; padding: 2px 8px; border-radius: 10px;
  font-size: 11px; background: #edf2f7; color: #718096; font-weight: 500;
}
.rd-tag-reviewed { background: #bee3f8; color: #2c5282; }

/* ═══ Responsive ═════════════════════════════════════════════════════════ */
@media (max-width: 640px) {
  .rd-header, .rd-section, .rd-footer, .rd-warnings { padding-left: 16px; padding-right: 16px; }
  .rd-ec-bar { grid-template-columns: 70px 1fr; gap: 6px; }
  .rd-ec-bar-name, .rd-ec-bar-value { display: none; }
  .rd-shap-feat { grid-template-columns: 20px 1fr 40px; }
  .rd-shap-feat-bar { display: none; }
}

/* Nearest-neighbor cards (BLAST hits) */
.rd-neighbor-empty {
  padding: 20px 24px; background: #f7fafc;
  border: 1px dashed #cbd5e0; border-radius: 8px;
  color: #718096; font-size: 13px; text-align: center; line-height: 1.6;
}
.rd-neighbor-list {
  display: flex; flex-direction: column; gap: 12px;
}
.rd-neighbor-card {
  padding: 14px 18px; background: #fff;
  border: 1px solid #e2e8f0; border-left: 4px solid #a0aec0;
  border-radius: 8px; transition: box-shadow 0.15s;
}
.rd-neighbor-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.04); }

.rd-neighbor-card.rd-tier-swissprot_experimental { border-left-color: #38a169; }
.rd-neighbor-card.rd-tier-brenda_experimental    { border-left-color: #3182ce; }
.rd-neighbor-card.rd-tier-trembl_experimental    { border-left-color: #319795; }
.rd-neighbor-card.rd-tier-swissprot_predicted    { border-left-color: #a0aec0; }
.rd-neighbor-card.rd-tier-brenda_predicted       { border-left-color: #a0aec0; }
.rd-neighbor-card.rd-tier-trembl_predicted       { border-left-color: #cbd5e0; }

.rd-neighbor-head {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 10px; flex-wrap: wrap;
}
.rd-neighbor-rank {
  font-family: 'Monaco', monospace; font-size: 13px; font-weight: 700;
  color: #718096; min-width: 24px;
}
.rd-neighbor-uid {
  font-family: 'Monaco', monospace; font-weight: 600;
}
.rd-external { font-size: 10px; opacity: 0.6; margin-left: 2px; }
.rd-neighbor-org {
  font-style: italic; color: #4a5568; font-size: 13px; flex: 1;
}
.rd-neighbor-tier {
  font-size: 11px; font-weight: 600; padding: 3px 10px;
  border-radius: 10px; background: #edf2f7; color: #4a5568;
  white-space: nowrap;
}
.rd-tier-swissprot_experimental .rd-neighbor-tier { background: #c6f6d5; color: #22543d; }
.rd-tier-brenda_experimental    .rd-neighbor-tier { background: #bee3f8; color: #2a4365; }
.rd-tier-trembl_experimental    .rd-neighbor-tier { background: #b2f5ea; color: #234e52; }

.rd-neighbor-identity {
  display: flex; align-items: center; gap: 12px; margin-bottom: 12px;
}
.rd-identity-bar {
  flex: 1; height: 8px; background: #edf2f7;
  border-radius: 4px; overflow: hidden;
}
.rd-identity-fill {
  height: 100%; border-radius: 4px;
  background: linear-gradient(90deg, #667eea, #5568d3);
}
.rd-identity-label {
  font-size: 13px; color: #2d3748; font-weight: 500;
  font-variant-numeric: tabular-nums; white-space: nowrap;
}
.rd-identity-meta {
  font-size: 11px; color: #a0aec0; font-weight: 400;
  margin-left: 6px; font-family: 'Monaco', monospace;
}

.rd-km-compare {
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
  padding: 10px 14px; background: #fafbfc;
  border-radius: 6px; border: 1px solid #edf2f7;
}
.rd-km-box { flex: 1; min-width: 120px; }
.rd-km-label {
  font-size: 10px; font-weight: 600; color: #718096;
  text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 2px;
}
.rd-km-value {
  font-family: 'Monaco', monospace; font-size: 18px; font-weight: 600;
  color: #2d3748; font-variant-numeric: tabular-nums;
}
.rd-km-unit { font-size: 12px; color: #a0aec0; font-weight: 400; margin-left: 2px; }
.rd-km-arrow { color: #cbd5e0; font-size: 18px; font-weight: 300; }
.rd-km-experimental .rd-km-value { color: #2c5282; }
.rd-km-predicted    .rd-km-value { color: #4a5568; }
.rd-km-delta {
  padding: 4px 10px; border-radius: 12px; font-size: 11px;
  font-weight: 600; font-variant-numeric: tabular-nums; white-space: nowrap;
}
.rd-km-delta-good { background: #c6f6d5; color: #22543d; }
.rd-km-delta-ok   { background: #faf089; color: #744210; }
.rd-km-delta-warn { background: #fed7d7; color: #742a2a; }


/* ═══ SHAP match summary + status pills ═══════════════════════════════════ */
.rd-match-summary {
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px; flex-wrap: wrap;
  padding: 10px 14px; margin-bottom: 14px;
  border-radius: 8px; font-size: 13px;
  border-left: 4px solid #a0aec0;
  background: #f7fafc; color: #2d3748;
}
.rd-match-summary-main { flex: 1; }
.rd-match-summary-unknown {
  color: #a0aec0; font-size: 11px; margin-left: 6px; font-style: italic;
}
.rd-match-summary-verdict {
  font-weight: 600; font-size: 12px; white-space: nowrap;
  padding: 3px 10px; border-radius: 10px;
  background: #edf2f7; color: #4a5568;
}
.rd-match-verdict-strong   { border-left-color: #38a169; background: #f0fff4; }
.rd-match-verdict-strong   .rd-match-summary-verdict { background: #c6f6d5; color: #22543d; }
.rd-match-verdict-moderate { border-left-color: #ecc94b; background: #fffff0; }
.rd-match-verdict-moderate .rd-match-summary-verdict { background: #faf089; color: #744210; }
.rd-match-verdict-weak     { border-left-color: #e53e3e; background: #fff5f5; }
.rd-match-verdict-weak     .rd-match-summary-verdict { background: #fed7d7; color: #742a2a; }

.rd-match-pill {
  min-width: 40px; padding: 2px 8px;
  font-size: 11px; font-weight: 600;
  border-radius: 10px; text-align: center;
  font-variant-numeric: tabular-nums;
  font-family: 'Monaco', monospace;
  cursor: default;
}
.rd-match-hit     { background: #c6f6d5; color: #22543d; }
.rd-match-absent  { background: #fed7d7; color: #742a2a; }
.rd-match-value   { background: #e2e8f0; color: #4a5568; }
.rd-match-unknown { background: #f7fafc; color: #a0aec0; }

</style>
