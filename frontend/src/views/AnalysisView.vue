<script setup>
import { ref, computed, nextTick } from 'vue';
import CommonButton from '@/components/CommonButton.vue';
import Client from '../../utils/Client.js';

const sequence = ref('');
const selectedFile = ref(null);
const isLoading = ref(false);
const loadingStatus = ref('');
const error = ref(null);
const activeTab = ref('properties');
const chartsRendered = ref(false);

const fileId = ref(null);
const analysisResult = ref(null);
const chartsData = ref(null);
const domainResults = ref(null);

const hasInput = computed(() => sequence.value.trim().length > 0 || selectedFile.value !== null);

const cleanSequence = (seq) => seq.split('\n').filter(line => !line.startsWith('>')).join('').replace(/[^A-Za-z]/g, '').toUpperCase();

const getSequenceHeader = (seq) => {
  for (const line of seq.split('\n')) {
    if (line.startsWith('>')) return line.substring(1).split(' ')[0].trim();
  }
  return 'user_sequence';
};

const onFileSelect = (event) => {
  const file = event.target.files[0];
  if (file) {
    selectedFile.value = file;
    const reader = new FileReader();
    reader.onload = (e) => { sequence.value = e.target.result; };
    reader.readAsText(file);
  }
};

const runFullAnalysis = async () => {
  error.value = null;
  isLoading.value = true;
  chartsRendered.value = false;
  domainResults.value = null;
  
  try {
    const cleanedSeq = cleanSequence(sequence.value);
    const seqHeader = getSequenceHeader(sequence.value);
    if (cleanedSeq.length < 10) throw new Error('Sequence too short (min 10 aa)');

    loadingStatus.value = 'Running BioPython analysis...';
    const analysisResponse = await fetch('/api/analyze-sequence', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sequence: cleanedSeq })
    });
    const analysisData = await analysisResponse.json();
    if (!analysisData.success) throw new Error(analysisData.error);
    analysisResult.value = analysisData.analysis;

    loadingStatus.value = 'Generating visualizations...';
    const chartsResponse = await fetch('/api/visualize-sequence', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sequence: cleanedSeq })
    });
    const chartsJson = await chartsResponse.json();
    if (chartsJson.success) chartsData.value = chartsJson.charts;

    loadingStatus.value = 'Running HMMER & Prosite...';
    const fastaBlob = new Blob([`>${seqHeader}\n${cleanedSeq}`], { type: 'text/plain' });
    const fastaFile = new File([fastaBlob], 'sequence.fasta', { type: 'text/plain' });
    const formData = new FormData();
    formData.append('file', fastaFile);
    
    try {
      const validateResponse = await Client.post('/validate-fasta', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      if (validateResponse.data.is_valid) {
        fileId.value = validateResponse.data.file_id;
        const searchResponse = await Client.post('/all-searches', { fileId: fileId.value });
        if (searchResponse.data) domainResults.value = searchResponse.data;
      }
    } catch (e) { console.warn('Domain search:', e); }

    loadingStatus.value = 'Complete!';
  } catch (err) {
    error.value = err.message;
  } finally {
    isLoading.value = false;
    loadingStatus.value = '';
  }
};

const resetAnalysis = () => {
  sequence.value = '';
  selectedFile.value = null;
  fileId.value = null;
  analysisResult.value = null;
  chartsData.value = null;
  domainResults.value = null;
  error.value = null;
  activeTab.value = 'properties';
  chartsRendered.value = false;
};

const loadExampleSequence = () => {
  sequence.value = `>sp|P38435|VKGC_HUMAN Vitamin K-dependent gamma-carboxylase
MAVSAGSARTSPSSDKVQKDKAELISGPRQDSRIGKLLGFEWTDLSSWRRLVTLLNRPTD
PASLAVFRFLFGFLMVLDIPQERGLSSLDRKYLDGLDVCRFPLLDALRPLPLDWMYLVYT
IMFLGALGMMLGLCYRISCVLFLLPYWYVFLLDKTSWNNHSYLYGLLAFQLTFMDANHYW
SVDGLLNAHRRNAHVPLWNYAVLRGQIFIVYFIAGVKKLDADWVEGYSMEYLSRHWLFSP
FKLLLSEELTSLLVVHWGGLLLDLSAGFLLFFDVSRSIGLFFVSYFHCMNSQLFSIGMFS
YVMLASSPLFCSPEWPRKLVSYCPRRLQQLLPLKAAPQPSVSCVYKRSRGKSGQKPGLRH
QLGAAFTLLYLLEQLFLPYSHFLTQGYNNWTNGLYGYSWDMMVHSRSHQHVKITYRDGRT
GELGYLNPGVFTQSRRWKDHADMLKQYATCLSRLLPKYNVTEPQIYFDIWVSINDRFQQR
IFDPRVDIVQAAWSPFQRTSWVQPLLMDLSPWRAKLQEIKSSLDNHTEVVFIADFPGLHL
ENFVSEDLGNTSIQLLQGEVTVELVAEQKNQTLREGEKMQLPAGEYHKVYTTSPSPSCYM
YVYVNTTELALEQDLAYLQELKEKVENGSETGPLPPELQPLLEGEVKGGPEPTPLVQTFL
RRQQRLQEIERRRNTPFHERFFRFLLRKLYVFRRSFLMTCISLRNLILGRPSLEQLAQEV
TYANLRPFEAVGELNPSNTDSSHSNPPESNPDPVHSEF`;
};

const doRenderCharts = async () => {
  if (!chartsData.value || chartsRendered.value || !window.Plotly) return;
  await nextTick();
  for (const { id, key } of [
    { id: 'chart-composition', key: 'amino_acid_composition' },
    { id: 'chart-structure', key: 'secondary_structure' },
    { id: 'chart-charge', key: 'charge_distribution' },
    { id: 'chart-hydrophobicity', key: 'hydrophobicity' }
  ]) {
    const el = document.getElementById(id);
    if (el && chartsData.value[key]) {
      try {
        const data = JSON.parse(chartsData.value[key]);
        await window.Plotly.newPlot(id, data.data, { ...data.layout, height: 350 }, { responsive: true });
      } catch (e) { console.error(e); }
    }
  }
  chartsRendered.value = true;
};

const selectTab = async (tabId) => {
  activeTab.value = tabId;
  if (tabId === 'charts' && chartsData.value && !chartsRendered.value) {
    await nextTick();
    setTimeout(doRenderCharts, 300);
  }
};

const downloadResults = async () => {
  if (!fileId.value) return;
  try {
    const response = await Client.get('/download-results', { params: { fileId: fileId.value }, responseType: 'blob' });
    const link = document.createElement('a');
    link.href = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
    link.download = `analysis_${fileId.value}.pdf`;
    link.click();
  } catch (e) { console.error(e); }
};

// FIXED: Key is "Pfam hits" not "pfam_hits"
const getPfamHits = computed(() => {
  if (!domainResults.value) return [];
  const hits = [];
  for (const [seqId, searches] of Object.entries(domainResults.value)) {
    const pfamArray = searches['Pfam hits'] || searches['pfam_hits'] || [];
    hits.push(...pfamArray.map(h => ({ ...h, sequence_id: seqId })));
  }
  return hits;
});

const getPrositeHits = computed(() => {
  if (!domainResults.value) return [];
  const hits = [];
  for (const [seqId, searches] of Object.entries(domainResults.value)) {
    const prositeArray = searches['Prosite hits'] || searches['prosite_hits'] || [];
    hits.push(...prositeArray.map(h => ({ ...h, sequence_id: seqId })));
  }
  return hits;
});

const tabs = [
  { id: 'properties', label: 'Properties' },
  { id: 'composition', label: 'Composition' },
  { id: 'structure', label: 'Structure' },
  { id: 'domains', label: 'Domains' },
  { id: 'motifs', label: 'Motifs' },
  { id: 'charts', label: 'Charts' }
];
</script>

<template>
  <main class="analysis-container">
    <div v-if="!analysisResult" class="input-section">
      <h1 class="heading">🧬 Unified Sequence Analysis</h1>
      <p class="subtitle">BioPython + HMMER + Prosite + Visualizations</p>
      <div class="input-area">
        <div class="sequence-input">
          <label>Protein sequence (FASTA or plain):</label>
          <textarea v-model="sequence" placeholder="Paste sequence here..." rows="12"></textarea>
          <div class="file-upload">
            <input type="file" accept=".fasta,.fa,.txt" @change="onFileSelect" />
            <span v-if="selectedFile">📄 {{ selectedFile.name }}</span>
          </div>
          <div class="button-row">
            <CommonButton label="🔬 Run Full Analysis" :function="runFullAnalysis" :disabled="!hasInput || isLoading" />
            <CommonButton label="📋 Load Example" :function="loadExampleSequence" />
          </div>
          <div v-if="isLoading" class="loading-box"><div class="spinner"></div><p>{{ loadingStatus }}</p></div>
          <p v-if="error" class="error">❌ {{ error }}</p>
        </div>
        <div class="info-panel">
          <h2>Features</h2>
          <ul><li>✓ MW, pI, Stability</li><li>✓ Amino Acid Composition</li><li>✓ Secondary Structure</li><li>✓ HMMER Domain Search</li><li>✓ Prosite Patterns</li><li>✓ Interactive Charts</li></ul>
        </div>
      </div>
    </div>
    
    <div v-else class="results-section">
      <div class="results-header">
        <h1 class="heading">Analysis Results</h1>
        <div class="header-buttons">
          <CommonButton label="📥 PDF" :function="downloadResults" v-if="fileId" />
          <CommonButton label="🔄 New" :function="resetAnalysis" />
        </div>
      </div>
      
      <div class="summary-cards">
        <div class="summary-card"><span class="icon">⚖️</span><span class="val">{{ analysisResult.basic_properties.molecular_weight.toFixed(0) }} Da</span></div>
        <div class="summary-card"><span class="icon">⚡</span><span class="val">pI {{ analysisResult.basic_properties.isoelectric_point.toFixed(1) }}</span></div>
        <div class="summary-card"><span class="icon">📏</span><span class="val">{{ analysisResult.basic_properties.length }} aa</span></div>
        <div class="summary-card" v-if="getPfamHits.length"><span class="icon">🎯</span><span class="val">{{ getPfamHits.length }} Pfam</span></div>
        <div class="summary-card" v-if="getPrositeHits.length"><span class="icon">🔍</span><span class="val">{{ getPrositeHits.length }} Prosite</span></div>
      </div>
      
      <div class="tabs">
        <button v-for="tab in tabs" :key="tab.id" :class="['tab', { active: activeTab === tab.id }]" @click="selectTab(tab.id)">{{ tab.label }}</button>
      </div>
      
      <div class="tab-content">
        <div v-if="activeTab === 'properties'" class="properties-grid">
          <div class="property-card"><h3>Molecular Weight</h3><p class="value">{{ analysisResult.basic_properties.molecular_weight.toFixed(2) }} Da</p></div>
          <div class="property-card"><h3>pI</h3><p class="value">{{ analysisResult.basic_properties.isoelectric_point.toFixed(2) }}</p></div>
          <div class="property-card"><h3>Instability</h3><p class="value">{{ analysisResult.basic_properties.instability_index.toFixed(1) }}</p></div>
          <div class="property-card"><h3>GRAVY</h3><p class="value">{{ analysisResult.basic_properties.gravy.toFixed(3) }}</p></div>
          <div class="property-card"><h3>Aromaticity</h3><p class="value">{{ (analysisResult.basic_properties.aromaticity * 100).toFixed(1) }}%</p></div>
          <div class="property-card"><h3>Charge pH7</h3><p class="value">{{ analysisResult.basic_properties.charge_at_pH7.toFixed(1) }}</p></div>
          <div class="property-card"><h3>Length</h3><p class="value">{{ analysisResult.basic_properties.length }} aa</p></div>
        </div>
        
        <div v-if="activeTab === 'composition'">
          <h2>Top 5 Amino Acids</h2>
          <div v-for="(pct, aa) in analysisResult.amino_acid_composition.top_5" :key="aa" class="aa-bar">
            <span class="aa-label">{{ aa }}</span>
            <div class="bar-container"><div class="bar" :style="{ width: pct*2 + '%' }"></div></div>
            <span>{{ pct.toFixed(1) }}%</span>
          </div>
        </div>
        
        <div v-if="activeTab === 'structure'">
          <div class="structure-grid">
            <div class="structure-card helix"><h4>α-Helix</h4><p>{{ analysisResult.secondary_structure.helix_percent.toFixed(1) }}%</p></div>
            <div class="structure-card sheet"><h4>β-Sheet</h4><p>{{ analysisResult.secondary_structure.sheet_percent.toFixed(1) }}%</p></div>
            <div class="structure-card turn"><h4>Turn</h4><p>{{ analysisResult.secondary_structure.turn_percent.toFixed(1) }}%</p></div>
          </div>
          <h2>Hydrophobic Regions</h2>
          <div v-for="(r, i) in analysisResult.hydrophobic_regions.slice(0,8)" :key="i" class="region-item">
            {{ r.start }}-{{ r.end }}: <strong>{{ r.sequence }}</strong> ({{ r.hydrophobicity_score.toFixed(2) }})
          </div>
        </div>
        
        <div v-if="activeTab === 'domains'">
          <h2>HMMER Pfam Domain Hits</h2>
          <div v-if="getPfamHits.length" class="domain-list">
            <div v-for="(hit, i) in getPfamHits" :key="i" class="domain-item">
              <span class="pfam-id">{{ hit.pfam_accession || hit.pfam_id || 'Unknown' }}</span>
              <span class="evalue">E-value: {{ hit.e_value ? hit.e_value.toExponential(2) : 'N/A' }}</span>
              <span class="seq-id">{{ hit.sequence_id }}</span>
            </div>
          </div>
          <p v-else class="no-data">No Pfam domains found.</p>
        </div>
        
        <div v-if="activeTab === 'motifs'">
          <h2>Prosite Patterns</h2>
          <div v-if="getPrositeHits.length" class="motif-list">
            <div v-for="(hit, i) in getPrositeHits" :key="i" class="badge success">
              {{ hit.prosite_id || hit.prosite_accession || hit }}
            </div>
          </div>
          <p v-else class="no-data">No Prosite patterns found.</p>
          
          <h2 style="margin-top:20px">RuBisCO Motifs (BioPython)</h2>
          <div class="motif-card">
            <h4>Catalytic Lysine</h4>
            <span v-if="analysisResult.rubisco_motifs.catalytic_lysine.found" class="badge success">Found ({{ analysisResult.rubisco_motifs.catalytic_lysine.count }})</span>
            <span v-else class="badge">Not Found</span>
          </div>
        </div>
        
        <div v-if="activeTab === 'charts'">
          <button v-if="!chartsRendered" @click="doRenderCharts" class="render-btn">📊 Load Charts</button>
          <div class="charts-grid">
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
.heading { color: #1a365d; margin-bottom: 8px; }
.subtitle { color: #666; margin-bottom: 20px; }
.input-area { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
.sequence-input { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
.sequence-input textarea { width: 100%; padding: 12px; font-family: monospace; border: 2px solid #e2e8f0; border-radius: 6px; }
.file-upload { margin: 15px 0; }
.button-row { display: flex; gap: 10px; margin-top: 15px; }
.loading-box { display: flex; align-items: center; gap: 10px; margin-top: 15px; padding: 12px; background: #ebf8ff; border-radius: 6px; }
.spinner { width: 20px; height: 20px; border: 3px solid #bee3f8; border-top-color: #3182ce; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.error { color: #c53030; margin-top: 10px; }
.info-panel { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
.info-panel ul { list-style: none; padding: 0; }
.info-panel li { padding: 5px 0; }
.results-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
.header-buttons { display: flex; gap: 8px; }
.summary-cards { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.summary-card { display: flex; align-items: center; gap: 8px; background: white; padding: 12px 16px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }
.summary-card .icon { font-size: 20px; }
.summary-card .val { font-weight: 600; color: #1a365d; }
.tabs { display: flex; gap: 4px; background: #edf2f7; padding: 4px; border-radius: 10px 10px 0 0; flex-wrap: wrap; }
.tab { padding: 10px 16px; border: none; background: transparent; cursor: pointer; border-radius: 6px; font-size: 13px; }
.tab.active { background: white; color: #1a365d; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.tab-content { background: white; padding: 20px; border-radius: 0 0 10px 10px; min-height: 350px; }
.properties-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
.property-card { background: #f7fafc; padding: 15px; border-radius: 8px; text-align: center; }
.property-card h3 { font-size: 11px; color: #718096; margin-bottom: 5px; text-transform: uppercase; }
.property-card .value { font-size: 20px; font-weight: bold; color: #1a365d; }
.aa-bar { display: flex; align-items: center; margin-bottom: 8px; }
.aa-label { width: 25px; font-weight: bold; }
.bar-container { flex: 1; height: 20px; background: #eee; border-radius: 4px; margin: 0 10px; }
.bar { height: 100%; background: linear-gradient(90deg, #4299e1, #38b2ac); border-radius: 4px; }
.structure-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px; }
.structure-card { padding: 20px; border-radius: 8px; text-align: center; }
.structure-card.helix { background: #fed7d7; }
.structure-card.sheet { background: #bee3f8; }
.structure-card.turn { background: #fefcbf; }
.structure-card p { font-size: 28px; font-weight: bold; color: #1a365d; }
.region-item { padding: 8px; background: #f7fafc; margin-bottom: 6px; border-radius: 4px; font-family: monospace; font-size: 13px; }
.domain-list { display: flex; flex-direction: column; gap: 10px; }
.domain-item { background: linear-gradient(135deg, #ebf8ff, #e6fffa); padding: 15px 20px; border-radius: 10px; display: flex; gap: 20px; align-items: center; border-left: 4px solid #3182ce; }
.pfam-id { font-weight: bold; color: #2b6cb0; font-size: 18px; }
.evalue { font-size: 13px; color: #38a169; background: #c6f6d5; padding: 4px 10px; border-radius: 12px; }
.seq-id { font-size: 12px; color: #718096; margin-left: auto; }
.motif-list { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }
.badge { display: inline-block; padding: 8px 16px; border-radius: 20px; font-size: 14px; background: #edf2f7; }
.badge.success { background: #c6f6d5; color: #276749; }
.motif-card { background: #f7fafc; padding: 15px; border-radius: 8px; margin-bottom: 12px; }
.no-data { color: #a0aec0; font-style: italic; }
.render-btn { background: #4299e1; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; margin-bottom: 15px; }
.charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
.chart-box { background: #fafafa; border: 1px solid #e2e8f0; border-radius: 8px; min-height: 350px; }
@media (max-width: 900px) { .input-area, .charts-grid { grid-template-columns: 1fr; } }
</style>
