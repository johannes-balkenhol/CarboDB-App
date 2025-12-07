<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue';
import CommonButton from '@/components/CommonButton.vue';

const sequence = ref('');
const isLoading = ref(false);
const analysisResult = ref(null);
const chartsData = ref(null);
const error = ref(null);
const activeTab = ref('properties');

const hasSequence = computed(() => sequence.value.trim().length > 0);

const cleanSequence = (seq) => {
  return seq.split('\n').filter(line => !line.startsWith('>')).join('').replace(/[^A-Za-z]/g, '').toUpperCase();
};

const runAnalysis = async () => {
  error.value = null;
  isLoading.value = true;
  
  try {
    const cleanedSeq = cleanSequence(sequence.value);
    
    const analysisResponse = await fetch('/api/analyze-sequence', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sequence: cleanedSeq })
    });
    const analysisData = await analysisResponse.json();
    if (!analysisData.success) throw new Error(analysisData.error || 'Analysis failed');
    analysisResult.value = analysisData.analysis;
    
    const chartsResponse = await fetch('/api/visualize-sequence', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sequence: cleanedSeq })
    });
    const chartsJson = await chartsResponse.json();
    if (chartsJson.success) chartsData.value = chartsJson.charts;
    
  } catch (err) {
    error.value = err.message;
  } finally {
    isLoading.value = false;
  }
};

const resetAnalysis = () => {
  sequence.value = '';
  analysisResult.value = null;
  chartsData.value = null;
  error.value = null;
  activeTab.value = 'properties';
};

const loadExampleSequence = () => {
  sequence.value = '>RuBisCO\nMSPQTETKASVGFKAGVKDYKLTYYTPEYETKDTDILAAFRVTPQPGVPPEEAGAAVAAESSTGTWTTVWTDGLTSLDRYKGRCYHIEPVAGEENQYICYVAYPLDLFEEGSVTNMFTSIVGNVFGFKALRALRLEDLRIPPAYTKTFQGPPHGIQVERDKLNKYGRPLLGCTIKPKLGLSAKNYGRAVYECLRGGLDFTKDDENVNSQPFMRWRDRFLFCAEAIYKAQAETGEIKGHYLNATAGTCEEMIKRAIFARELGVPIVR';
};

const renderCharts = () => {
  if (!chartsData.value || !window.Plotly) return;
  
  setTimeout(() => {
    const charts = [
      { id: 'chart-composition', key: 'amino_acid_composition' },
      { id: 'chart-structure', key: 'secondary_structure' },
      { id: 'chart-charge', key: 'charge_distribution' },
      { id: 'chart-hydrophobicity', key: 'hydrophobicity' }
    ];
    
    charts.forEach(({ id, key }) => {
      const el = document.getElementById(id);
      if (el && chartsData.value[key]) {
        try {
          const data = JSON.parse(chartsData.value[key]);
          window.Plotly.newPlot(id, data.data, { ...data.layout, height: 350 }, { responsive: true });
        } catch (e) {
          console.error('Chart error:', id, e);
        }
      }
    });
  }, 200);
};

watch(activeTab, (tab) => { if (tab === 'charts') renderCharts(); });
watch(chartsData, () => { if (activeTab.value === 'charts') renderCharts(); });

onMounted(() => {
  if (!window.Plotly) {
    const s = document.createElement('script');
    s.src = 'https://cdn.plot.ly/plotly-2.27.0.min.js';
    document.head.appendChild(s);
  }
});

const tabs = [
  { id: 'properties', label: 'Properties' },
  { id: 'composition', label: 'Composition' },
  { id: 'structure', label: 'Structure' },
  { id: 'motifs', label: 'Motifs' },
  { id: 'charts', label: 'Charts' }
];
</script>

<template>
  <main class="analysis-container">
    <div v-if="!analysisResult" class="input-section">
      <h1 class="heading">Sequence Analysis</h1>
      <div class="input-area">
        <div class="sequence-input">
          <label>Enter protein sequence (FASTA or plain):</label>
          <textarea v-model="sequence" placeholder="Paste sequence here..." rows="10"></textarea>
          <div class="button-row">
            <CommonButton label="Analyze Sequence" :function="runAnalysis" :disabled="!hasSequence || isLoading" />
            <CommonButton label="Load Example (RuBisCO)" :function="loadExampleSequence" />
          </div>
          <p v-if="isLoading" class="loading">Analyzing...</p>
          <p v-if="error" class="error">{{ error }}</p>
        </div>
        <div class="info-panel">
          <h2>Features</h2>
          <ul><li>✓ MW, pI, Stability</li><li>✓ Amino Acid Composition</li><li>✓ Secondary Structure</li><li>✓ Motif Detection</li><li>✓ Interactive Charts</li></ul>
        </div>
      </div>
    </div>
    
    <div v-else class="results-section">
      <div class="results-header">
        <h1 class="heading">Analysis Results</h1>
        <CommonButton label="New Analysis" :function="resetAnalysis" />
      </div>
      
      <div class="tabs">
        <button v-for="tab in tabs" :key="tab.id" :class="['tab', { active: activeTab === tab.id }]" @click="activeTab = tab.id">{{ tab.label }}</button>
      </div>
      
      <div class="tab-content">
        <div v-show="activeTab === 'properties'" class="properties-grid">
          <div class="property-card"><h3>Molecular Weight</h3><p class="value">{{ analysisResult.basic_properties.molecular_weight.toFixed(2) }} Da</p></div>
          <div class="property-card"><h3>Isoelectric Point</h3><p class="value">{{ analysisResult.basic_properties.isoelectric_point.toFixed(2) }}</p></div>
          <div class="property-card"><h3>Instability Index</h3><p class="value" :class="{ stable: analysisResult.basic_properties.instability_index < 40 }">{{ analysisResult.basic_properties.instability_index.toFixed(2) }} <span>{{ analysisResult.basic_properties.instability_index < 40 ? '(Stable)' : '(Unstable)' }}</span></p></div>
          <div class="property-card"><h3>GRAVY</h3><p class="value">{{ analysisResult.basic_properties.gravy.toFixed(3) }}</p></div>
          <div class="property-card"><h3>Aromaticity</h3><p class="value">{{ (analysisResult.basic_properties.aromaticity * 100).toFixed(1) }}%</p></div>
          <div class="property-card"><h3>Charge (pH 7)</h3><p class="value">{{ analysisResult.basic_properties.charge_at_pH7.toFixed(2) }}</p></div>
          <div class="property-card"><h3>Length</h3><p class="value">{{ analysisResult.basic_properties.length }} aa</p></div>
        </div>
        
        <div v-show="activeTab === 'composition'">
          <h2>Top 5 Amino Acids</h2>
          <div class="composition-bars">
            <div v-for="(pct, aa) in analysisResult.amino_acid_composition.top_5" :key="aa" class="aa-bar">
              <span class="aa-label">{{ aa }}</span>
              <div class="bar-container"><div class="bar" :style="{ width: pct + '%' }"></div></div>
              <span>{{ pct.toFixed(1) }}%</span>
            </div>
          </div>
          <h2>Charge Distribution</h2>
          <div class="charge-grid">
            <div class="charge-card positive"><h4>Positive (R,K)</h4><p>{{ analysisResult.charge_distribution.positive_residues }} ({{ analysisResult.charge_distribution.positive_percent.toFixed(1) }}%)</p></div>
            <div class="charge-card negative"><h4>Negative (D,E)</h4><p>{{ analysisResult.charge_distribution.negative_residues }} ({{ analysisResult.charge_distribution.negative_percent.toFixed(1) }}%)</p></div>
            <div class="charge-card neutral"><h4>Neutral</h4><p>{{ analysisResult.charge_distribution.neutral_residues }}</p></div>
          </div>
        </div>
        
        <div v-show="activeTab === 'structure'">
          <h2>Secondary Structure</h2>
          <div class="structure-grid">
            <div class="structure-card helix"><h4>α-Helix</h4><p class="percent">{{ analysisResult.secondary_structure.helix_percent.toFixed(1) }}%</p></div>
            <div class="structure-card sheet"><h4>β-Sheet</h4><p class="percent">{{ analysisResult.secondary_structure.sheet_percent.toFixed(1) }}%</p></div>
            <div class="structure-card turn"><h4>Turn</h4><p class="percent">{{ analysisResult.secondary_structure.turn_percent.toFixed(1) }}%</p></div>
          </div>
          <h2>Hydrophobic Regions</h2>
          <div v-if="analysisResult.hydrophobic_regions.length" class="regions-list">
            <div v-for="(r, i) in analysisResult.hydrophobic_regions.slice(0,10)" :key="i" class="region-item">
              <span>{{ r.start }}-{{ r.end }}</span><span class="seq">{{ r.sequence }}</span><span class="score">{{ r.hydrophobicity_score.toFixed(2) }}</span>
            </div>
          </div>
          <p v-else>No hydrophobic regions found.</p>
        </div>
        
        <div v-show="activeTab === 'motifs'">
          <h2>RuBisCO Motif Detection</h2>
          <div class="motif-card">
            <h3>PS00157</h3>
            <span v-if="analysisResult.rubisco_motifs.PS00157.found" class="badge success">Found</span>
            <span v-else class="badge">Not Found</span>
            <div v-for="(m, i) in analysisResult.rubisco_motifs.PS00157.matches" :key="i" class="match">{{ m.start }}-{{ m.end }}: <code>{{ m.sequence }}</code></div>
          </div>
          <div class="motif-card">
            <h3>Catalytic Lysine</h3>
            <span v-if="analysisResult.rubisco_motifs.catalytic_lysine.found" class="badge success">Found ({{ analysisResult.rubisco_motifs.catalytic_lysine.count }})</span>
            <span v-else class="badge">Not Found</span>
            <div v-for="(m, i) in analysisResult.rubisco_motifs.catalytic_lysine.matches.slice(0,5)" :key="i" class="match">{{ m.start }}-{{ m.end }}: <code>{{ m.sequence }}</code></div>
          </div>
          <div class="motif-card">
            <h3>Loop 6</h3>
            <span v-if="analysisResult.rubisco_motifs.loop6.found" class="badge success">Found</span>
            <span v-else class="badge">Not Found</span>
          </div>
        </div>
        
        <div v-show="activeTab === 'charts'" class="charts-section">
          <h2>Interactive Visualizations</h2>
          <p v-if="!chartsData">Loading charts...</p>
          <div v-else class="charts-grid">
            <div class="chart-box" id="chart-composition"></div>
            <div class="chart-box" id="chart-structure"></div>
            <div class="chart-box" id="chart-charge"></div>
            <div class="chart-box" id="chart-hydrophobicity"></div>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
.analysis-container { padding: 20px; max-width: 1400px; margin: 0 auto; }
.heading { color: #2c3e50; margin-bottom: 20px; }
.input-area { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
.sequence-input { background: white; padding: 20px; border-radius: 8px; }
.sequence-input textarea { width: 100%; padding: 10px; font-family: monospace; border: 1px solid #ddd; border-radius: 4px; }
.button-row { display: flex; gap: 10px; margin-top: 15px; }
.info-panel { background: white; padding: 20px; border-radius: 8px; }
.info-panel ul { list-style: none; padding: 0; }
.info-panel li { padding: 5px 0; }
.loading { color: #3498db; }
.error { color: #e74c3c; }
.results-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.tabs { display: flex; gap: 5px; margin-bottom: 20px; }
.tab { padding: 10px 20px; border: none; background: #f0f0f0; cursor: pointer; border-radius: 4px 4px 0 0; }
.tab.active { background: #2c3e50; color: white; }
.tab-content { background: white; padding: 20px; border-radius: 0 8px 8px 8px; min-height: 400px; }
.properties-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; }
.property-card { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
.property-card h3 { font-size: 12px; color: #666; margin-bottom: 5px; }
.property-card .value { font-size: 22px; font-weight: bold; color: #2c3e50; }
.property-card .value.stable { color: #27ae60; }
.composition-bars { margin-bottom: 20px; }
.aa-bar { display: flex; align-items: center; margin-bottom: 8px; }
.aa-label { width: 25px; font-weight: bold; }
.bar-container { flex: 1; height: 20px; background: #eee; border-radius: 4px; margin: 0 10px; }
.bar { height: 100%; background: linear-gradient(90deg, #3498db, #2ecc71); border-radius: 4px; }
.charge-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }
.charge-card { padding: 15px; border-radius: 8px; text-align: center; }
.charge-card.positive { background: #e3f2fd; }
.charge-card.negative { background: #ffebee; }
.charge-card.neutral { background: #f5f5f5; }
.structure-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px; }
.structure-card { padding: 25px; border-radius: 8px; text-align: center; }
.structure-card.helix { background: #ffebee; }
.structure-card.sheet { background: #e3f2fd; }
.structure-card.turn { background: #fff3e0; }
.structure-card .percent { font-size: 32px; font-weight: bold; color: #2c3e50; }
.regions-list { background: #f8f9fa; padding: 10px; border-radius: 8px; }
.region-item { display: flex; gap: 15px; padding: 8px; border-bottom: 1px solid #eee; font-family: monospace; font-size: 13px; }
.region-item .seq { font-weight: bold; }
.region-item .score { color: #3498db; }
.motif-card { background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px; }
.motif-card h3 { margin-bottom: 10px; }
.badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 11px; background: #ddd; }
.badge.success { background: #27ae60; color: white; }
.match { margin-top: 8px; padding: 8px; background: white; border-radius: 4px; font-size: 13px; }
.match code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; }
.charts-section h2 { margin-bottom: 15px; }
.charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.chart-box { background: #fafafa; border: 1px solid #eee; border-radius: 8px; min-height: 380px; }
@media (max-width: 900px) { .input-area, .charts-grid { grid-template-columns: 1fr; } }
</style>
