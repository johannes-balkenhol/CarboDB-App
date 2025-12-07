<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue';
import CommonButton from '@/components/CommonButton.vue';

const sequence = ref('');
const isLoading = ref(false);
const analysisResult = ref(null);
const chartsData = ref(null);
const error = ref(null);
const activeTab = ref('properties');
const plotlyLoaded = ref(false);

const hasSequence = computed(() => sequence.value.trim().length > 0);

const cleanSequence = (seq) => {
  return seq
    .split('\n')
    .filter(line => !line.startsWith('>'))
    .join('')
    .replace(/[^A-Za-z]/g, '')
    .toUpperCase();
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
    
    if (!analysisData.success) {
      throw new Error(analysisData.error || 'Analysis failed');
    }
    
    analysisResult.value = analysisData.analysis;
    
    const chartsResponse = await fetch('/api/visualize-sequence', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sequence: cleanedSeq })
    });
    
    const chartsJson = await chartsResponse.json();
    
    if (chartsJson.success) {
      chartsData.value = chartsJson.charts;
    }
    
  } catch (err) {
    error.value = err.message;
    console.error('Analysis error:', err);
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
  sequence.value = `>sp|P00875|RUBP_SPIOL RuBisCO large chain (Spinach)
MSPQTETKASVGFKAGVKDYKLTYYTPEYETKDTDILAAFRVTPQPGVPPEEAGAAVAAE
SSTGTWTTVWTDGLTSLDRYKGRCYHIEPVAGEENQYICYVAYPLDLFEEGSVTNMFTSI
VGNVFGFKALRALRLEDLRIPPAYTKTFQGPPHGIQVERDKLNKYGRPLLGCTIKPKLGL
SAKNYGRAVYECLRGGLDFTKDDENVNSQPFMRWRDRFLFCAEAIYKAQAETGEIKGHYL
NATAGTCEEMIKRAIFARELGVPIVR`;
};

const tabs = [
  { id: 'properties', label: 'Properties' },
  { id: 'composition', label: 'Composition' },
  { id: 'structure', label: 'Structure' },
  { id: 'motifs', label: 'Motifs' },
  { id: 'charts', label: 'Charts' }
];

const loadPlotly = () => {
  return new Promise((resolve) => {
    if (window.Plotly) {
      resolve();
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://cdn.plot.ly/plotly-2.27.0.min.js';
    script.onload = () => {
      plotlyLoaded.value = true;
      resolve();
    };
    document.head.appendChild(script);
  });
};

const renderCharts = async () => {
  if (!chartsData.value) return;
  
  await loadPlotly();
  await nextTick();
  
  const chartMappings = [
    { id: 'chart-composition', data: 'amino_acid_composition' },
    { id: 'chart-structure', data: 'secondary_structure' },
    { id: 'chart-charge', data: 'charge_distribution' },
    { id: 'chart-hydrophobicity', data: 'hydrophobicity' }
  ];
  
  chartMappings.forEach(({ id, data }) => {
    const el = document.getElementById(id);
    if (el && chartsData.value[data]) {
      try {
        const chartData = JSON.parse(chartsData.value[data]);
        window.Plotly.newPlot(id, chartData.data, chartData.layout, { responsive: true });
      } catch (e) {
        console.error(`Error rendering ${id}:`, e);
      }
    }
  });
};

watch(activeTab, async (newTab) => {
  if (newTab === 'charts' && chartsData.value) {
    await nextTick();
    setTimeout(renderCharts, 100);
  }
});

watch(chartsData, async (newVal) => {
  if (newVal && activeTab.value === 'charts') {
    await nextTick();
    setTimeout(renderCharts, 100);
  }
});

onMounted(() => {
  loadPlotly();
});
</script>

<template>
  <main class="analysis-container">
    <!-- Input Section -->
    <div v-if="!analysisResult" class="input-section">
      <h1 class="heading">Sequence Analysis</h1>
      
      <div class="input-area">
        <div class="sequence-input">
          <label for="sequence">Enter protein sequence (FASTA or plain):</label>
          <textarea 
            id="sequence"
            v-model="sequence"
            placeholder="Paste your protein sequence here..."
            rows="10"
          ></textarea>
          
          <div class="button-row">
            <CommonButton 
              label="Analyze Sequence" 
              :function="runAnalysis"
              :disabled="!hasSequence || isLoading"
            />
            <CommonButton 
              label="Load Example (RuBisCO)" 
              :function="loadExampleSequence"
            />
          </div>
          
          <p v-if="isLoading" class="loading">Analyzing sequence...</p>
          <p v-if="error" class="error">{{ error }}</p>
        </div>
        
        <div class="info-panel">
          <h2>BioPython Analysis Features</h2>
          <ul>
            <li>✓ Molecular Weight & pI</li>
            <li>✓ Stability Index</li>
            <li>✓ Amino Acid Composition</li>
            <li>✓ Secondary Structure Prediction</li>
            <li>✓ Hydrophobic Regions</li>
            <li>✓ RuBisCO Motif Detection</li>
            <li>✓ Interactive Plotly Charts</li>
          </ul>
        </div>
      </div>
    </div>
    
    <!-- Results Section -->
    <div v-else class="results-section">
      <div class="results-header">
        <h1 class="heading">Analysis Results</h1>
        <CommonButton label="New Analysis" :function="resetAnalysis" />
      </div>
      
      <div class="tabs">
        <button 
          v-for="tab in tabs" 
          :key="tab.id"
          :class="['tab', { active: activeTab === tab.id }]"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>
      
      <div class="tab-content">
        
        <!-- Properties Tab -->
        <div v-if="activeTab === 'properties'" class="properties-grid">
          <div class="property-card">
            <h3>Molecular Weight</h3>
            <p class="value">{{ analysisResult.basic_properties.molecular_weight.toFixed(2) }} Da</p>
          </div>
          <div class="property-card">
            <h3>Isoelectric Point (pI)</h3>
            <p class="value">{{ analysisResult.basic_properties.isoelectric_point.toFixed(2) }}</p>
          </div>
          <div class="property-card">
            <h3>Instability Index</h3>
            <p class="value" :class="{ stable: analysisResult.basic_properties.instability_index < 40 }">
              {{ analysisResult.basic_properties.instability_index.toFixed(2) }}
              <span class="label">{{ analysisResult.basic_properties.instability_index < 40 ? '(Stable)' : '(Unstable)' }}</span>
            </p>
          </div>
          <div class="property-card">
            <h3>GRAVY Score</h3>
            <p class="value">{{ analysisResult.basic_properties.gravy.toFixed(3) }}</p>
            <span class="label">{{ analysisResult.basic_properties.gravy > 0 ? 'Hydrophobic' : 'Hydrophilic' }}</span>
          </div>
          <div class="property-card">
            <h3>Aromaticity</h3>
            <p class="value">{{ (analysisResult.basic_properties.aromaticity * 100).toFixed(1) }}%</p>
          </div>
          <div class="property-card">
            <h3>Charge at pH 7</h3>
            <p class="value">{{ analysisResult.basic_properties.charge_at_pH7.toFixed(2) }}</p>
          </div>
          <div class="property-card">
            <h3>Sequence Length</h3>
            <p class="value">{{ analysisResult.basic_properties.length }} aa</p>
          </div>
        </div>
        
        <!-- Composition Tab -->
        <div v-if="activeTab === 'composition'" class="composition-section">
          <h2>Top 5 Amino Acids</h2>
          <div class="composition-bars">
            <div v-for="(percent, aa) in analysisResult.amino_acid_composition.top_5" :key="aa" class="aa-bar">
              <span class="aa-label">{{ aa }}</span>
              <div class="bar-container">
                <div class="bar" :style="{ width: percent + '%' }"></div>
              </div>
              <span class="aa-percent">{{ percent.toFixed(1) }}%</span>
            </div>
          </div>
          
          <h2>Charge Distribution</h2>
          <div class="charge-grid">
            <div class="charge-card positive">
              <h4>Positive (R, K)</h4>
              <p>{{ analysisResult.charge_distribution.positive_residues }} ({{ analysisResult.charge_distribution.positive_percent.toFixed(1) }}%)</p>
            </div>
            <div class="charge-card negative">
              <h4>Negative (D, E)</h4>
              <p>{{ analysisResult.charge_distribution.negative_residues }} ({{ analysisResult.charge_distribution.negative_percent.toFixed(1) }}%)</p>
            </div>
            <div class="charge-card neutral">
              <h4>Neutral</h4>
              <p>{{ analysisResult.charge_distribution.neutral_residues }}</p>
            </div>
          </div>
        </div>
        
        <!-- Structure Tab -->
        <div v-if="activeTab === 'structure'" class="structure-section">
          <h2>Secondary Structure Prediction</h2>
          <div class="structure-grid">
            <div class="structure-card helix"><h4>α-Helix</h4><p class="percent">{{ analysisResult.secondary_structure.helix_percent.toFixed(1) }}%</p></div>
            <div class="structure-card sheet"><h4>β-Sheet</h4><p class="percent">{{ analysisResult.secondary_structure.sheet_percent.toFixed(1) }}%</p></div>
            <div class="structure-card turn"><h4>Turn</h4><p class="percent">{{ analysisResult.secondary_structure.turn_percent.toFixed(1) }}%</p></div>
          </div>
          
          <h2>Hydrophobic Regions</h2>
          <div v-if="analysisResult.hydrophobic_regions.length > 0" class="regions-list">
            <div v-for="(region, idx) in analysisResult.hydrophobic_regions.slice(0, 10)" :key="idx" class="region-item">
              <span class="position">{{ region.start }}-{{ region.end }}</span>
              <span class="sequence">{{ region.sequence }}</span>
              <span class="score">Score: {{ region.hydrophobicity_score.toFixed(2) }}</span>
            </div>
          </div>
          <p v-else class="no-data">No significant hydrophobic regions found.</p>
        </div>
        
        <!-- Motifs Tab -->
        <div v-if="activeTab === 'motifs'" class="motifs-section">
          <h2>RuBisCO Motif Detection</h2>
          
          <div class="motif-card">
            <h3>PS00157 (RuBisCO Signature)</h3>
            <div v-if="analysisResult.rubisco_motifs.PS00157.found" class="found">
              <span class="badge success">Found</span>
              <div v-for="(match, idx) in analysisResult.rubisco_motifs.PS00157.matches" :key="idx" class="match">
                Position {{ match.start }}-{{ match.end }}: <code>{{ match.sequence }}</code>
              </div>
            </div>
            <div v-else class="not-found"><span class="badge">Not Found</span></div>
          </div>
          
          <div class="motif-card">
            <h3>Catalytic Lysine (K-X-X-K)</h3>
            <div v-if="analysisResult.rubisco_motifs.catalytic_lysine.found" class="found">
              <span class="badge success">Found ({{ analysisResult.rubisco_motifs.catalytic_lysine.count }})</span>
              <div v-for="(match, idx) in analysisResult.rubisco_motifs.catalytic_lysine.matches.slice(0, 5)" :key="idx" class="match">
                Position {{ match.start }}-{{ match.end }}: <code>{{ match.sequence }}</code>
              </div>
            </div>
            <div v-else class="not-found"><span class="badge">Not Found</span></div>
          </div>
          
          <div class="motif-card">
            <h3>Loop 6 Consensus</h3>
            <div v-if="analysisResult.rubisco_motifs.loop6.found" class="found">
              <span class="badge success">Found ({{ analysisResult.rubisco_motifs.loop6.count }})</span>
              <div v-for="(match, idx) in analysisResult.rubisco_motifs.loop6.matches.slice(0, 5)" :key="idx" class="match">
                Position {{ match.start }}-{{ match.end }}: <code>{{ match.sequence }}</code>
              </div>
            </div>
            <div v-else class="not-found"><span class="badge">Not Found</span></div>
          </div>
        </div>
        
        <!-- Charts Tab -->
        <div v-if="activeTab === 'charts'" class="charts-section">
          <h2>Interactive Visualizations</h2>
          <div v-if="chartsData" class="charts-grid">
            <div class="chart-container" id="chart-composition"></div>
            <div class="chart-container" id="chart-structure"></div>
            <div class="chart-container" id="chart-charge"></div>
            <div class="chart-container" id="chart-hydrophobicity"></div>
          </div>
          <p v-else class="loading">Loading charts...</p>
        </div>
        
      </div>
    </div>
  </main>
</template>

<style scoped>
.analysis-container { padding: 20px; max-width: 1400px; margin: 0 auto; }
.heading { color: var(--color-navigation); margin-bottom: 20px; }
.input-area { display: grid; grid-template-columns: 2fr 1fr; gap: 30px; }
.sequence-input { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.sequence-input label { display: block; margin-bottom: 10px; font-weight: bold; color: var(--color-navigation); }
.sequence-input textarea { width: 100%; padding: 15px; border: 1px solid #ddd; border-radius: 4px; font-family: monospace; font-size: 14px; resize: vertical; }
.button-row { display: flex; gap: 10px; margin-top: 15px; }
.info-panel { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.info-panel h2 { color: var(--color-navigation); margin-bottom: 15px; }
.info-panel ul { list-style: none; padding: 0; }
.info-panel li { padding: 8px 0; border-bottom: 1px solid #eee; }
.loading { color: #3498db; font-style: italic; margin-top: 10px; }
.error { color: #e74c3c; margin-top: 10px; }
.results-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.tabs { display: flex; gap: 5px; margin-bottom: 20px; border-bottom: 2px solid #ddd; }
.tab { padding: 10px 20px; border: none; background: #f5f5f5; cursor: pointer; border-radius: 4px 4px 0 0; font-size: 14px; transition: all 0.2s; }
.tab:hover { background: #e0e0e0; }
.tab.active { background: var(--color-navigation); color: white; }
.tab-content { background: white; padding: 20px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); min-height: 400px; }
.properties-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
.property-card { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }
.property-card h3 { color: #666; font-size: 14px; margin-bottom: 10px; }
.property-card .value { font-size: 24px; font-weight: bold; color: var(--color-navigation); }
.property-card .value.stable { color: #27ae60; }
.property-card .label { display: block; font-size: 12px; color: #888; margin-top: 5px; }
.composition-bars { margin-bottom: 30px; }
.aa-bar { display: flex; align-items: center; margin-bottom: 10px; }
.aa-label { width: 30px; font-weight: bold; font-family: monospace; }
.bar-container { flex: 1; height: 25px; background: #eee; border-radius: 4px; margin: 0 10px; overflow: hidden; }
.bar { height: 100%; background: linear-gradient(90deg, #3498db, #2ecc71); border-radius: 4px; transition: width 0.5s ease; }
.aa-percent { width: 60px; text-align: right; }
.charge-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.charge-card { padding: 20px; border-radius: 8px; text-align: center; }
.charge-card.positive { background: #e3f2fd; }
.charge-card.negative { background: #ffebee; }
.charge-card.neutral { background: #f5f5f5; }
.structure-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }
.structure-card { padding: 30px; border-radius: 8px; text-align: center; }
.structure-card.helix { background: #ffebee; }
.structure-card.sheet { background: #e3f2fd; }
.structure-card.turn { background: #fff3e0; }
.structure-card .percent { font-size: 36px; font-weight: bold; color: var(--color-navigation); }
.regions-list { background: #f8f9fa; border-radius: 8px; padding: 15px; }
.region-item { display: flex; gap: 20px; padding: 10px; border-bottom: 1px solid #eee; font-family: monospace; }
.region-item .position { color: #666; }
.region-item .sequence { font-weight: bold; }
.region-item .score { color: #3498db; }
.motif-card { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
.motif-card h3 { margin-bottom: 15px; color: var(--color-navigation); }
.badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; background: #e0e0e0; margin-right: 10px; }
.badge.success { background: #27ae60; color: white; }
.match { margin-top: 10px; padding: 10px; background: white; border-radius: 4px; }
.match code { background: #f0f0f0; padding: 2px 8px; border-radius: 3px; font-weight: bold; }
.no-data, .not-found { color: #888; font-style: italic; }
.charts-section h2 { margin-bottom: 20px; }
.charts-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
.chart-container { background: white; border-radius: 8px; padding: 10px; min-height: 400px; border: 1px solid #eee; }
@media (max-width: 768px) {
  .input-area { grid-template-columns: 1fr; }
  .charts-grid { grid-template-columns: 1fr; }
  .properties-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
