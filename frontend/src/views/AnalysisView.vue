<script setup>
import { ref, computed, nextTick, onMounted, watch } from 'vue';
import CommonButton from '@/components/CommonButton.vue';
import Client from '../../utils/Client.js';

const sequence = ref('');
const selectedFile = ref(null);
const isLoading = ref(false);
const loadingStatus = ref('');
const error = ref(null);
const activeTab = ref('properties');
const chartsRendered = ref(false);
const molstarLoaded = ref(false);

const fileId = ref(null);
const analysisResult = ref(null);
const chartsData = ref(null);
const domainResults = ref(null);
const interproData = ref(null);
const alphafoldData = ref(null);
const uniprotId = ref(null);

const hasInput = computed(() => sequence.value.trim().length > 0 || selectedFile.value !== null);

const cleanSequence = (seq) => seq.split('\n').filter(line => !line.startsWith('>')).join('').replace(/[^A-Za-z]/g, '').toUpperCase();

const getSequenceHeader = (seq) => {
  for (const line of seq.split('\n')) {
    if (line.startsWith('>')) return line.substring(1).trim();
  }
  return 'user_sequence';
};

const extractUniprotFromHeader = (header) => {
  const match = header.match(/(?:sp|tr)\|([A-Z0-9]+)\|/);
  return match ? match[1] : null;
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
  molstarLoaded.value = false;
  domainResults.value = null;
  interproData.value = null;
  alphafoldData.value = null;
  
  try {
    const cleanedSeq = cleanSequence(sequence.value);
    const seqHeader = getSequenceHeader(sequence.value);
    uniprotId.value = extractUniprotFromHeader(seqHeader);
    
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
    const fastaBlob = new Blob([`>${seqHeader.split(' ')[0]}\n${cleanedSeq}`], { type: 'text/plain' });
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
    } catch (e) { console.warn('HMMER search:', e); }

    if (uniprotId.value) {
      loadingStatus.value = 'Fetching InterPro annotations...';
      try {
        const interproResponse = await fetch(`/api/interpro/${uniprotId.value}`);
        const interproJson = await interproResponse.json();
        if (interproJson.success) interproData.value = interproJson.data;
      } catch (e) { console.warn('InterPro:', e); }

      loadingStatus.value = 'Checking AlphaFold structure...';
      try {
        const afResponse = await fetch(`/api/alphafold/${uniprotId.value}`);
        alphafoldData.value = await afResponse.json();
      } catch (e) { console.warn('AlphaFold:', e); }
    }

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
  interproData.value = null;
  alphafoldData.value = null;
  uniprotId.value = null;
  error.value = null;
  activeTab.value = 'properties';
  chartsRendered.value = false;
  molstarLoaded.value = false;
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

// Load Mol* viewer
const loadMolstar = async () => {
  if (molstarLoaded.value || !alphafoldData.value?.has_structure) return;
  
  await nextTick();
  const container = document.getElementById("molstar-viewer");
  if (!container) return;
  
  container.innerHTML = "<div style=\"display:flex;align-items:center;justify-content:center;height:500px;\">Loading 3D structure...</div>";
  
  try {
    const pdbUrl = alphafoldData.value.pdb_url;
    const response = await fetch(pdbUrl);
    const pdbData = await response.text();
    
    container.innerHTML = "";
    container.style.height = "500px";
    container.style.position = "relative";
    
    const viewer = window.$3Dmol.createViewer(container, {
      backgroundColor: "white"
    });
    
    viewer.addModel(pdbData, "pdb");
    viewer.setStyle({}, { cartoon: { color: "spectrum" } });
    viewer.zoomTo();
    viewer.render();
    
    molstarLoaded.value = true;
  } catch (e) {
    console.error("3Dmol error:", e);
    container.innerHTML = `<div style="text-align:center;padding:40px;"><p>Could not load structure</p><a href="https://alphafold.ebi.ac.uk/entry/${uniprotId.value}" target="_blank" style="color:#667eea;">View on AlphaFold DB</a></div>`;
  }
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
  if (tabId === 'structure' && alphafoldData.value?.has_structure && !molstarLoaded.value) {
    await nextTick();
    setTimeout(loadMolstar, 300);
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

const interproEntries = computed(() => {
  if (!interproData.value?.results) return [];
  return interproData.value.results.map(entry => ({
    accession: entry.metadata?.accession || '',
    name: entry.metadata?.name || '',
    type: entry.metadata?.type || '',
    database: entry.metadata?.source_database || '',
    integrated: entry.metadata?.integrated || '',
    start: entry.proteins?.[0]?.entry_protein_locations?.[0]?.fragments?.[0]?.start || 0,
    end: entry.proteins?.[0]?.entry_protein_locations?.[0]?.fragments?.[0]?.end || 0,
    go_terms: entry.metadata?.go_terms || []
  }));
});

// SCOP/Superfamily entries from InterPro
const scopEntries = computed(() => {
  return interproEntries.value.filter(e => 
    e.database === 'ssf' || 
    e.database === 'superfamily' ||
    e.accession.startsWith('SSF')
  );
});

// CATH entries
const cathEntries = computed(() => {
  return interproEntries.value.filter(e => 
    e.database === 'cathgene3d' || 
    e.database === 'cath' ||
    e.accession.startsWith('G3DSA')
  );
});

// Other domain databases
const otherDomains = computed(() => {
  return interproEntries.value.filter(e => 
    !['pfam', 'ssf', 'superfamily', 'cathgene3d', 'cath'].includes(e.database) &&
    !e.accession.startsWith('SSF') &&
    !e.accession.startsWith('G3DSA')
  );
});

const allGoTerms = computed(() => {
  const terms = [];
  for (const entry of interproEntries.value) {
    if (entry.go_terms) terms.push(...entry.go_terms);
  }
  const unique = [];
  const seen = new Set();
  for (const t of terms) {
    if (!seen.has(t.identifier)) {
      seen.add(t.identifier);
      unique.push(t);
    }
  }
  return unique;
});

const tabs = [
  { id: 'properties', label: 'Properties', icon: '📊' },
  { id: 'composition', label: 'Composition', icon: '🧪' },
  { id: 'structure', label: '3D Structure', icon: '🔮' },
  { id: 'domains', label: 'Domains', icon: '🎯' },
  { id: 'motifs', label: 'Motifs', icon: '🔍' },
  { id: 'charts', label: 'Charts', icon: '📈' }
];

// Load Molstar script on mount
onMounted(() => {
  if (!document.getElementById('molstar-script')) {
    const script = document.createElement('script');
    script.id = 'molstar-script';
    script.src = 'https://www.ebi.ac.uk/pdbe/pdb-component-library/js/pdbe-molstar-component-3.1.0.js';
    script.type = 'module';
    document.head.appendChild(script);
  }
});
</script>

<template>
  <main class="analysis-container">
    <!-- Input Section -->
    <div v-if="!analysisResult" class="input-section">
      <div class="page-header">
        <h1>🧬 Unified Sequence Analysis</h1>
        <p>Complete protein characterization: BioPython • HMMER • InterPro • AlphaFold</p>
      </div>
      
      <div class="input-area">
        <div class="sequence-input">
          <label>Protein sequence (FASTA or plain):</label>
          <textarea v-model="sequence" placeholder="Paste your protein sequence here...&#10;&#10;Example:&#10;>sp|P38435|VKGC_HUMAN&#10;MAVSAGSARTS..." rows="14"></textarea>
          <div class="file-upload">
            <label class="file-btn">
              📁 Upload FASTA
              <input type="file" accept=".fasta,.fa,.txt" @change="onFileSelect" hidden />
            </label>
            <span v-if="selectedFile" class="file-name">{{ selectedFile.name }}</span>
          </div>
          <div class="button-row">
            <button class="btn-primary" @click="runFullAnalysis" :disabled="!hasInput || isLoading">
              🔬 Run Full Analysis
            </button>
            <button class="btn-secondary" @click="loadExampleSequence">
              📋 Load Example
            </button>
          </div>
          <div v-if="isLoading" class="loading-box">
            <div class="spinner"></div>
            <p>{{ loadingStatus }}</p>
          </div>
          <p v-if="error" class="error">❌ {{ error }}</p>
        </div>
        
        <div class="info-panel">
          <h3>Analysis Pipeline</h3>
          <div class="pipeline-steps">
            <div class="pipeline-step completed"><span class="step-icon">🤖</span><span>ML Predictions (EC, Km)</span></div>
            <div class="pipeline-step completed"><span class="step-icon">🔗</span><span>Database Nearest Neighbor</span></div>
            <div class="pipeline-step"><span class="step-icon">🧬</span><span>BioPython Analysis</span></div>
            <div class="pipeline-step"><span class="step-icon">🎯</span><span>HMMER/Pfam Search</span></div>
            <div class="pipeline-step"><span class="step-icon">🌐</span><span>InterPro Lookup</span></div>
            <div class="pipeline-step"><span class="step-icon">🏛️</span><span>SCOP/CATH Classification</span></div>
            <div class="pipeline-step"><span class="step-icon">🔮</span><span>AlphaFold Structure</span></div>
            <div class="pipeline-step"><span class="step-icon">📊</span><span>Interactive Charts</span></div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Results Section -->
    <div v-else class="results-section">
      <div class="results-header">
        <div>
          <h1>Analysis Results</h1>
          <p class="uniprot-badge" v-if="uniprotId">UniProt: {{ uniprotId }}</p>
        </div>
        <div class="header-buttons">
          <button class="btn-icon" @click="downloadResults" v-if="fileId" title="Download PDF">📥</button>
          <button class="btn-secondary" @click="resetAnalysis">🔄 New Analysis</button>
        </div>
      </div>
      
      <!-- Summary Cards -->
      <div class="summary-cards">
        <div class="summary-card"><span class="card-icon">⚖️</span><div><span class="card-value">{{ analysisResult.basic_properties.molecular_weight.toFixed(0) }}</span><span class="card-label">Da</span></div></div>
        <div class="summary-card"><span class="card-icon">⚡</span><div><span class="card-value">{{ analysisResult.basic_properties.isoelectric_point.toFixed(1) }}</span><span class="card-label">pI</span></div></div>
        <div class="summary-card"><span class="card-icon">📏</span><div><span class="card-value">{{ analysisResult.basic_properties.length }}</span><span class="card-label">aa</span></div></div>
        <div class="summary-card" v-if="getPfamHits.length"><span class="card-icon">🎯</span><div><span class="card-value">{{ getPfamHits.length }}</span><span class="card-label">Pfam</span></div></div>
        <div class="summary-card" v-if="interproEntries.length"><span class="card-icon">🌐</span><div><span class="card-value">{{ interproEntries.length }}</span><span class="card-label">InterPro</span></div></div>
        <div class="summary-card success" v-if="alphafoldData?.has_structure"><span class="card-icon">🔮</span><div><span class="card-value">3D</span><span class="card-label">Ready</span></div></div>
      </div>
      
      <!-- Tabs -->
      <div class="tabs">
        <button v-for="tab in tabs" :key="tab.id" :class="['tab', { active: activeTab === tab.id }]" @click="selectTab(tab.id)">
          <span class="tab-icon">{{ tab.icon }}</span>
          <span class="tab-label">{{ tab.label }}</span>
        </button>
      </div>
      
      <div class="tab-content">
        <!-- Properties Tab -->
        <div v-if="activeTab === 'properties'">
          <div class="properties-grid">
            <div class="property-card"><h3>Molecular Weight</h3><p class="value">{{ analysisResult.basic_properties.molecular_weight.toFixed(2) }} Da</p></div>
            <div class="property-card"><h3>Isoelectric Point</h3><p class="value">{{ analysisResult.basic_properties.isoelectric_point.toFixed(2) }}</p></div>
            <div class="property-card"><h3>Instability Index</h3><p class="value" :class="{ stable: analysisResult.basic_properties.instability_index < 40 }">{{ analysisResult.basic_properties.instability_index.toFixed(1) }}<span class="stability-label">{{ analysisResult.basic_properties.instability_index < 40 ? 'Stable' : 'Unstable' }}</span></p></div>
            <div class="property-card"><h3>GRAVY Score</h3><p class="value">{{ analysisResult.basic_properties.gravy.toFixed(3) }}<span class="stability-label">{{ analysisResult.basic_properties.gravy > 0 ? 'Hydrophobic' : 'Hydrophilic' }}</span></p></div>
            <div class="property-card"><h3>Aromaticity</h3><p class="value">{{ (analysisResult.basic_properties.aromaticity * 100).toFixed(1) }}%</p></div>
            <div class="property-card"><h3>Charge at pH 7</h3><p class="value">{{ analysisResult.basic_properties.charge_at_pH7.toFixed(1) }}</p></div>
            <div class="property-card"><h3>Sequence Length</h3><p class="value">{{ analysisResult.basic_properties.length }} aa</p></div>
          </div>
        </div>
        
        <!-- Composition Tab -->
        <div v-if="activeTab === 'composition'">
          <h2>Top Amino Acids</h2>
          <div class="composition-chart">
            <div v-for="(pct, aa) in analysisResult.amino_acid_composition.top_5" :key="aa" class="aa-bar">
              <span class="aa-code">{{ aa }}</span>
              <div class="bar-track"><div class="bar-fill" :style="{ width: pct*2.5 + '%' }"></div></div>
              <span class="aa-pct">{{ pct.toFixed(1) }}%</span>
            </div>
          </div>
          
          <h2>Charge Distribution</h2>
          <div class="charge-cards">
            <div class="charge-card positive">
              <h4>Positive (R, K, H)</h4>
              <p>{{ analysisResult.charge_distribution.positive_residues }} residues</p>
              <span>{{ analysisResult.charge_distribution.positive_percent.toFixed(1) }}%</span>
            </div>
            <div class="charge-card negative">
              <h4>Negative (D, E)</h4>
              <p>{{ analysisResult.charge_distribution.negative_residues }} residues</p>
              <span>{{ analysisResult.charge_distribution.negative_percent.toFixed(1) }}%</span>
            </div>
            <div class="charge-card neutral">
              <h4>Neutral</h4>
              <p>{{ analysisResult.charge_distribution.neutral_residues }} residues</p>
            </div>
          </div>
        </div>
        
        <!-- 3D Structure Tab -->
        <div v-if="activeTab === 'structure'">
          <!-- Secondary Structure -->
          <h2>Secondary Structure Prediction</h2>
          <div class="structure-grid">
            <div class="structure-card helix"><div class="struct-icon">🌀</div><h4>α-Helix</h4><p>{{ analysisResult.secondary_structure.helix_percent.toFixed(1) }}%</p></div>
            <div class="structure-card sheet"><div class="struct-icon">📄</div><h4>β-Sheet</h4><p>{{ analysisResult.secondary_structure.sheet_percent.toFixed(1) }}%</p></div>
            <div class="structure-card turn"><div class="struct-icon">↩️</div><h4>Turn</h4><p>{{ analysisResult.secondary_structure.turn_percent.toFixed(1) }}%</p></div>
          </div>
          
          <!-- AlphaFold 3D Viewer -->
          <div v-if="alphafoldData?.has_structure" class="alphafold-section">
            <h2>🔮 AlphaFold Predicted Structure</h2>
            <div class="viewer-container">
              <div id="molstar-viewer" class="molstar-viewer"></div>
            </div>
            <div class="structure-actions">
              <a :href="alphafoldData.pdb_url" target="_blank" class="action-btn">📥 Download PDB</a>
              <a :href="alphafoldData.cif_url" target="_blank" class="action-btn">📥 Download mmCIF</a>
              <a :href="`https://alphafold.ebi.ac.uk/entry/${uniprotId}`" target="_blank" class="action-btn primary">🔗 AlphaFold DB</a>
            </div>
          </div>
          <div v-else class="no-structure-box">
            <p v-if="uniprotId">⚠️ No AlphaFold structure available for {{ uniprotId }}</p>
            <p v-else>💡 Enter a UniProt sequence to view AlphaFold structure</p>
          </div>
          
          <!-- Hydrophobic Regions -->
          <h2>Hydrophobic Regions</h2>
          <div class="regions-list">
            <div v-for="(r, i) in analysisResult.hydrophobic_regions.slice(0,6)" :key="i" class="region-item">
              <span class="region-pos">{{ r.start }}-{{ r.end }}</span>
              <span class="region-seq">{{ r.sequence }}</span>
              <span class="region-score">{{ r.hydrophobicity_score.toFixed(2) }}</span>
            </div>
          </div>
        </div>
        
        <!-- Domains Tab -->
        <div v-if="activeTab === 'domains'">
          <!-- HMMER Pfam -->
          <h2>🎯 Pfam Domains (HMMER)</h2>
          <div v-if="getPfamHits.length" class="domain-list">
            <div v-for="(hit, i) in getPfamHits" :key="'pfam-'+i" class="domain-card pfam">
              <div class="domain-header">
                <span class="domain-id">{{ hit.pfam_accession }}</span>
                <span class="domain-badge">Pfam</span>
              </div>
              <div class="domain-info">
                <span class="evalue">E-value: {{ hit.e_value?.toExponential(2) || 'N/A' }}</span>
              </div>
            </div>
          </div>
          <p v-else class="empty-state">No Pfam domains found</p>
          
          <!-- SCOP/Superfamily -->
          <h2>🏛️ SCOP Classification (Superfamily)</h2>
          <div v-if="scopEntries.length" class="domain-list">
            <div v-for="(entry, i) in scopEntries" :key="'scop-'+i" class="domain-card scop">
              <div class="domain-header">
                <span class="domain-id">{{ entry.accession }}</span>
                <span class="domain-badge scop">SCOP</span>
              </div>
              <div class="domain-name">{{ entry.name }}</div>
              <div class="domain-location" v-if="entry.start">Position: {{ entry.start }}-{{ entry.end }}</div>
            </div>
          </div>
          <p v-else class="empty-state">No SCOP classifications found</p>
          
          <!-- CATH -->
          <h2>🏗️ CATH Classification</h2>
          <div v-if="cathEntries.length" class="domain-list">
            <div v-for="(entry, i) in cathEntries" :key="'cath-'+i" class="domain-card cath">
              <div class="domain-header">
                <span class="domain-id">{{ entry.accession }}</span>
                <span class="domain-badge cath">CATH</span>
              </div>
              <div class="domain-name">{{ entry.name }}</div>
              <div class="domain-location" v-if="entry.start">Position: {{ entry.start }}-{{ entry.end }}</div>
            </div>
          </div>
          <p v-else class="empty-state">No CATH classifications found</p>
          
          <!-- Other InterPro -->
          <h2>🌐 Other Annotations</h2>
          <div v-if="otherDomains.length" class="interpro-grid">
            <div v-for="(entry, i) in otherDomains" :key="'other-'+i" class="domain-card other">
              <div class="domain-header">
                <span class="domain-id">{{ entry.accession }}</span>
                <span class="domain-badge">{{ entry.database }}</span>
              </div>
              <div class="domain-name">{{ entry.name }}</div>
              <div class="domain-type">{{ entry.type }}</div>
            </div>
          </div>
          <p v-else class="empty-state">No additional annotations</p>
        </div>
        
        <!-- Motifs Tab -->
        <div v-if="activeTab === 'motifs'">
          <h2>🔍 Prosite Patterns</h2>
          <div v-if="getPrositeHits.length" class="motif-list">
            <span v-for="(hit, i) in getPrositeHits" :key="'ps-'+i" class="motif-badge">
              {{ hit.prosite_id || hit.prosite_accession }}
            </span>
          </div>
          <p v-else class="empty-state">No Prosite patterns found</p>
          
          <h2>🏷️ Gene Ontology Terms</h2>
          <div v-if="allGoTerms.length" class="go-grid">
            <div v-for="(go, i) in allGoTerms" :key="'go-'+i" class="go-card" :class="go.category?.code?.toLowerCase()">
              <span class="go-id">{{ go.identifier }}</span>
              <span class="go-name">{{ go.name }}</span>
              <span class="go-category">{{ go.category?.name }}</span>
            </div>
          </div>
          <p v-else class="empty-state">No GO terms available</p>
          
          <h2>🧬 Sequence Motifs</h2>
          <div class="motif-cards">
            <div class="motif-card">
              <h4>Catalytic Lysine (K-X-X-K)</h4>
              <span v-if="analysisResult.rubisco_motifs.catalytic_lysine.found" class="found-badge">Found ({{ analysisResult.rubisco_motifs.catalytic_lysine.count }})</span>
              <span v-else class="not-found-badge">Not Found</span>
              <div v-if="analysisResult.rubisco_motifs.catalytic_lysine.matches?.length" class="matches">
                <code v-for="(m, i) in analysisResult.rubisco_motifs.catalytic_lysine.matches.slice(0,3)" :key="i">
                  {{ m.start }}-{{ m.end }}: {{ m.sequence }}
                </code>
              </div>
            </div>
            <div class="motif-card">
              <h4>RuBisCO Signature (PS00157)</h4>
              <span v-if="analysisResult.rubisco_motifs.PS00157?.found" class="found-badge">Found</span>
              <span v-else class="not-found-badge">Not Found</span>
            </div>
            <div class="motif-card">
              <h4>Loop 6 Consensus</h4>
              <span v-if="analysisResult.rubisco_motifs.loop6?.found" class="found-badge">Found</span>
              <span v-else class="not-found-badge">Not Found</span>
            </div>
          </div>
        </div>
        
        <!-- Charts Tab -->
        <div v-if="activeTab === 'charts'">
          <button v-if="!chartsRendered" @click="doRenderCharts" class="btn-primary">📊 Load Interactive Charts</button>
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
/* Base Layout */
.analysis-container { max-width: 1400px; margin: 0 auto; padding: 30px 20px; }

/* Page Header */
.page-header { text-align: center; margin-bottom: 40px; }
.page-header h1 { font-size: 2.5rem; color: var(--color-secondary, #1a365d); margin-bottom: 10px; }
.page-header p { color: #718096; font-size: 1.1rem; }

/* Input Area */
.input-area { display: grid; grid-template-columns: 1.5fr 1fr; gap: 30px; }
.sequence-input { background: white; padding: 30px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
.sequence-input label { display: block; font-weight: 600; color: #2d3748; margin-bottom: 12px; }
.sequence-input textarea { width: 100%; padding: 16px; font-family: 'Monaco', 'Consolas', monospace; font-size: 13px; border: 2px solid #e2e8f0; border-radius: 12px; resize: vertical; transition: border-color 0.2s; }
.sequence-input textarea:focus { border-color: var(--color-primary, #38b2ac); outline: none; }
.file-upload { display: flex; align-items: center; gap: 15px; margin: 20px 0; }
.file-btn { display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; background: #f7fafc; border: 2px dashed #cbd5e0; border-radius: 10px; cursor: pointer; transition: all 0.2s; }
.file-btn:hover { border-color: var(--color-primary, #38b2ac); background: #e6fffa; }
.file-name { color: var(--color-primary, #38b2ac); font-weight: 500; }
.button-row { display: flex; gap: 12px; margin-top: 20px; }
.btn-primary { display: inline-flex; align-items: center; gap: 8px; padding: 14px 28px; background: linear-gradient(135deg, var(--color-primary, #38b2ac), #319795); color: white; border: none; border-radius: 12px; font-weight: 600; font-size: 15px; cursor: pointer; transition: all 0.2s; }
.btn-primary:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(56, 178, 172, 0.4); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-secondary { padding: 14px 28px; background: white; color: var(--color-secondary, #1a365d); border: 2px solid #e2e8f0; border-radius: 12px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
.btn-secondary:hover { border-color: var(--color-primary, #38b2ac); }
.btn-icon { width: 44px; height: 44px; border-radius: 10px; border: 2px solid #e2e8f0; background: white; cursor: pointer; font-size: 18px; }
.loading-box { display: flex; align-items: center; gap: 15px; margin-top: 20px; padding: 16px; background: linear-gradient(135deg, #e6fffa, #ebf8ff); border-radius: 12px; }
.spinner { width: 24px; height: 24px; border: 3px solid #81e6d9; border-top-color: var(--color-primary, #38b2ac); border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.error { color: #e53e3e; margin-top: 15px; padding: 12px; background: #fff5f5; border-radius: 10px; }

/* Info Panel */
.info-panel { background: white; padding: 30px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
.info-panel h3 { color: var(--color-secondary, #1a365d); margin-bottom: 20px; }
.pipeline-steps { display: flex; flex-direction: column; gap: 12px; }
.pipeline-step { display: flex; align-items: center; gap: 12px; padding: 12px 16px; background: #f7fafc; border-radius: 10px; border-left: 3px solid var(--color-primary, #38b2ac); }
.step-icon { font-size: 20px; }

/* Results Header */
.results-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 25px; }
.results-header h1 { color: var(--color-secondary, #1a365d); margin-bottom: 5px; }
.uniprot-badge { display: inline-block; padding: 4px 12px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-radius: 20px; font-size: 13px; font-weight: 500; }
.header-buttons { display: flex; gap: 10px; }

/* Summary Cards */
.summary-cards { display: flex; gap: 15px; margin-bottom: 25px; flex-wrap: wrap; }
.summary-card { display: flex; align-items: center; gap: 12px; background: white; padding: 16px 20px; border-radius: 14px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }
.summary-card.success { background: linear-gradient(135deg, #c6f6d5, #9ae6b4); }
.card-icon { font-size: 24px; }
.card-value { font-size: 22px; font-weight: 700; color: var(--color-secondary, #1a365d); }
.card-label { font-size: 12px; color: #718096; margin-left: 4px; }

/* Tabs */
.tabs { display: flex; gap: 6px; background: #edf2f7; padding: 6px; border-radius: 14px 14px 0 0; overflow-x: auto; }
.tab { display: flex; align-items: center; gap: 8px; padding: 12px 20px; border: none; background: transparent; cursor: pointer; border-radius: 10px; font-size: 14px; font-weight: 500; color: #4a5568; white-space: nowrap; transition: all 0.2s; }
.tab:hover { background: rgba(255,255,255,0.5); }
.tab.active { background: white; color: var(--color-secondary, #1a365d); box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
.tab-icon { font-size: 16px; }
.tab-content { background: white; padding: 30px; border-radius: 0 0 14px 14px; min-height: 450px; }

/* Properties Grid */
.properties-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 16px; }
.property-card { background: linear-gradient(135deg, #f7fafc, #edf2f7); padding: 24px; border-radius: 14px; text-align: center; }
.property-card h3 { font-size: 11px; color: #718096; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px; }
.property-card .value { font-size: 26px; font-weight: 700; color: var(--color-secondary, #1a365d); }
.property-card .value.stable { color: var(--color-success, #48bb78); }
.stability-label { display: block; font-size: 11px; color: #718096; margin-top: 5px; }

/* Composition */
.composition-chart { margin-bottom: 30px; }
.aa-bar { display: flex; align-items: center; margin-bottom: 12px; }
.aa-code { width: 35px; font-weight: 700; font-family: monospace; font-size: 16px; color: var(--color-secondary, #1a365d); }
.bar-track { flex: 1; height: 28px; background: #edf2f7; border-radius: 8px; margin: 0 15px; overflow: hidden; }
.bar-fill { height: 100%; background: linear-gradient(90deg, var(--color-primary, #38b2ac), #4fd1c5); border-radius: 8px; transition: width 0.5s ease; }
.aa-pct { width: 55px; font-weight: 600; text-align: right; }
.charge-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.charge-card { padding: 20px; border-radius: 12px; text-align: center; }
.charge-card.positive { background: linear-gradient(135deg, #ebf8ff, #bee3f8); }
.charge-card.negative { background: linear-gradient(135deg, #fff5f5, #fed7d7); }
.charge-card.neutral { background: linear-gradient(135deg, #f7fafc, #edf2f7); }
.charge-card h4 { font-size: 13px; margin-bottom: 8px; }
.charge-card p { font-size: 14px; color: #4a5568; }
.charge-card span { font-size: 20px; font-weight: 700; color: var(--color-secondary, #1a365d); }

/* Structure */
.structure-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 30px; }
.structure-card { padding: 28px; border-radius: 14px; text-align: center; }
.structure-card.helix { background: linear-gradient(135deg, #fef2f2, #fecaca); }
.structure-card.sheet { background: linear-gradient(135deg, #eff6ff, #bfdbfe); }
.structure-card.turn { background: linear-gradient(135deg, #fefce8, #fef08a); }
.struct-icon { font-size: 32px; margin-bottom: 10px; }
.structure-card h4 { font-size: 14px; margin-bottom: 8px; color: #374151; }
.structure-card p { font-size: 32px; font-weight: 700; color: var(--color-secondary, #1a365d); }

/* Molstar Viewer */
.alphafold-section { margin: 30px 0; }
.alphafold-section h2 { margin-bottom: 20px; }
.viewer-container { background: #f8fafc; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
.molstar-viewer { width: 100%; height: 500px; }
.molstar-loading, .molstar-error { display: flex; align-items: center; justify-content: center; height: 500px; color: #718096; }
.structure-actions { display: flex; gap: 12px; margin-top: 20px; flex-wrap: wrap; }
.action-btn { padding: 12px 24px; background: white; border: 2px solid #e2e8f0; border-radius: 10px; text-decoration: none; color: var(--color-secondary, #1a365d); font-weight: 500; transition: all 0.2s; }
.action-btn:hover { border-color: var(--color-primary, #38b2ac); }
.action-btn.primary { background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; }
.no-structure-box { padding: 40px; background: #f7fafc; border-radius: 14px; text-align: center; color: #718096; }

/* Regions */
.regions-list { display: grid; gap: 10px; }
.region-item { display: flex; align-items: center; gap: 20px; padding: 14px 18px; background: #f7fafc; border-radius: 10px; font-family: monospace; border-left: 4px solid var(--color-primary, #38b2ac); }
.region-pos { color: #718096; min-width: 80px; }
.region-seq { font-weight: 600; color: var(--color-secondary, #1a365d); }
.region-score { margin-left: auto; color: var(--color-primary, #38b2ac); }

/* Domain Cards */
.domain-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; margin-bottom: 30px; }
.domain-card { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; border-left: 4px solid #718096; }
.domain-card.pfam { border-left-color: var(--color-success, #48bb78); }
.domain-card.scop { border-left-color: #805ad5; }
.domain-card.cath { border-left-color: #ed8936; }
.domain-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.domain-id { font-weight: 700; color: var(--color-secondary, #1a365d); font-size: 15px; }
.domain-badge { font-size: 10px; padding: 3px 10px; background: #edf2f7; border-radius: 20px; text-transform: uppercase; font-weight: 600; }
.domain-badge.scop { background: #e9d8fd; color: #553c9a; }
.domain-badge.cath { background: #feebc8; color: #c05621; }
.domain-name { color: #4a5568; font-size: 14px; margin-bottom: 6px; }
.domain-location, .domain-type { font-size: 12px; color: #a0aec0; }
.evalue { font-size: 12px; color: var(--color-success, #48bb78); }
.interpro-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 14px; }
.empty-state { padding: 30px; background: #f7fafc; border-radius: 12px; text-align: center; color: #a0aec0; font-style: italic; margin-bottom: 30px; }

/* Motifs */
.motif-list { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 30px; }
.motif-badge { padding: 10px 20px; background: linear-gradient(135deg, #c6f6d5, #9ae6b4); color: #22543d; border-radius: 25px; font-weight: 600; }
.go-grid { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 30px; }
.go-card { display: flex; flex-direction: column; gap: 4px; padding: 14px 18px; border-radius: 12px; background: #f7fafc; border-left: 4px solid #718096; max-width: 350px; }
.go-card.f { border-left-color: #3182ce; background: #ebf8ff; }
.go-card.p { border-left-color: #38a169; background: #f0fff4; }
.go-card.c { border-left-color: #d69e2e; background: #fffff0; }
.go-id { font-size: 11px; font-family: monospace; color: #718096; }
.go-name { font-size: 13px; font-weight: 500; color: #2d3748; }
.go-category { font-size: 10px; color: #a0aec0; text-transform: uppercase; }
.motif-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px; }
.motif-card { background: #f7fafc; padding: 20px; border-radius: 12px; }
.motif-card h4 { margin-bottom: 12px; color: var(--color-secondary, #1a365d); }
.found-badge { display: inline-block; padding: 6px 14px; background: linear-gradient(135deg, #c6f6d5, #9ae6b4); color: #22543d; border-radius: 20px; font-size: 13px; font-weight: 600; }
.not-found-badge { display: inline-block; padding: 6px 14px; background: #edf2f7; color: #718096; border-radius: 20px; font-size: 13px; }
.matches { margin-top: 12px; display: flex; flex-direction: column; gap: 6px; }
.matches code { display: block; padding: 8px 12px; background: white; border-radius: 6px; font-size: 12px; }

/* Charts */
.charts-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-top: 20px; }
.chart-box { background: #fafafa; border: 1px solid #e2e8f0; border-radius: 12px; min-height: 380px; }

/* Responsive */
@media (max-width: 900px) {
  .input-area { grid-template-columns: 1fr; }
  .charts-grid { grid-template-columns: 1fr; }
  .structure-grid, .charge-cards { grid-template-columns: 1fr; }
  .tabs { flex-wrap: nowrap; }
  .tab-label { display: none; }
}
</style>
