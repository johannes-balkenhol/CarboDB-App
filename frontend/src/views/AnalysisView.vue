<template>
  <div class="analysis-view">
    <h1>🔬 Sequence Analysis</h1>
    <p class="subtitle">Predict carboxylase function, EC class, and Km values</p>

    <!-- Input Section -->
    <div class="input-section">
      <div class="input-header">
        <div class="input-tabs">
          <button 
            :class="{ active: inputMode === 'single' }" 
            @click="inputMode = 'single'"
          >Single Sequence</button>
          <button 
            :class="{ active: inputMode === 'batch' }" 
            @click="inputMode = 'batch'"
          >Batch (FASTA)</button>
        </div>
        <div class="example-buttons">
          <span class="example-label">Try example:</span>
          <button @click="loadExample('rubisco')" class="example-btn">RuBisCO</button>
          <button @click="loadExample('pepc')" class="example-btn">PEPC</button>
          <button @click="loadExample('ca')" class="example-btn">Carbonic Anhydrase</button>
        </div>
      </div>

      <div v-if="inputMode === 'single'" class="single-input">
        <textarea 
          v-model="singleSequence" 
          placeholder="Enter protein sequence (amino acids only)...

Example: MSPQTETKASVGFKAGVKDYKLTYYTPEYETKDTDILAAFRVTPQPG..."
          rows="6"
        ></textarea>
        <div class="mode-kingdom-row">
          <div class="mode-select">
            <label>Mode:</label>
            <select v-model="selectedMode">
              <option value="fast">⚡ Fast (~5s, ablation without ESM-2)</option>
              <option value="standard">◈ Standard (~15s, +ESM-2) — benchmark pipeline (R²=0.953)</option>
              <option value="pfam">◇ Pfam-only (~3s, ablation)</option>
              <option value="composite">✦ Composite (~25s, Best CI)</option>
            </select>
          </div>
          <div class="kingdom-select">
            <label>Kingdom:</label>
            <select v-model="selectedKingdom">
              <option value="plant">Plant / Algae</option>
              <option value="bacteria">Bacteria</option>
              <option value="archaea">Archaea</option>
              <option value="fungi">Fungi</option>
            </select>
          </div>
        </div>
        <button @click="predictSingle" :disabled="loading" class="predict-btn">
          {{ loading ? 'Analyzing...' : '🔬 Analyze Sequence' }}
        </button>
      </div>

      <div v-else class="batch-input">
        <textarea 
          v-model="fastaInput" 
          placeholder=">RuBisCO_spinach
MSPQTETKASVGFKAGVKDYKLTYYTPEYETKDTDILAAFRVTPQPG...
>PEPC_maize
MASERHHSHLHQRTQDRFASAASKDLSSRLIDASITPELDQLLAEF..."
          rows="10"
        ></textarea>
        <div class="batch-actions">
          <label class="file-upload">
            <input type="file" @change="handleFileUpload" accept=".fasta,.fa,.txt" />
            📁 Upload FASTA
          </label>
          <button @click="predictBatch" :disabled="loading" class="predict-btn">
            {{ loading ? 'Analyzing...' : '🔬 Analyze Batch' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Batch Results Summary -->
    <div v-if="batchResults && batchResults.length > 0" class="batch-results">
      <div class="results-header">
        <h2>📊 Batch Results ({{ batchResults.length }} sequences)</h2>
        <div class="summary-stats">
          <span class="stat">
            <strong>{{ summary.consensus_positive }}</strong> CO₂ positive
          </span>
          <span class="stat">
            <strong>{{ summary.with_neighbor }}</strong> with DB match
          </span>
        </div>
        <button @click="downloadResults" class="download-btn">📥 Download TSV</button>
      </div>

      <div class="results-table-container">
        <table class="results-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Length</th>
              <th>CO₂ Prob</th>
              <th>Consensus</th>
              <th>EC Predicted</th>
              <th>EC Conf</th>
              <th>Km (µM)</th>
              <th>Nearest Match</th>
              <th>Match Km</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="result in batchResults" :key="result.id" 
                :class="{ 'consensus-positive': result.consensus }">
              <td class="seq-id">{{ result.id }}</td>
              <td>{{ result.length }}</td>
              <td :class="getProbClass(result.co2_prob_v3)">{{ (result.co2_prob_v3 * 100).toFixed(1) }}%</td>
              <td>
                <span :class="result.consensus ? 'badge-yes' : 'badge-no'">
                  {{ result.consensus ? 'Yes' : 'No' }}
                </span>
              </td>
              <td class="ec-pred">{{ result.ec_predicted }}</td>
              <td>{{ (result.ec_confidence * 100).toFixed(0) }}%</td>
              <td class="km-pred">{{ result.km_predicted_uM?.toFixed(1) || '-' }}</td>
              <td class="neighbor">
                <a v-if="result.nearest_neighbor" 
                   :href="'https://www.uniprot.org/uniprotkb/' + result.nearest_neighbor.uniprot_id" 
                   target="_blank">
                  {{ result.nearest_neighbor.uniprot_id }}
                </a>
                <span v-else>-</span>
              </td>
              <td class="km-exp">
                {{ result.nearest_neighbor?.km_experimental?.toFixed(1) || '-' }}
              </td>
              <td>
                <button @click="viewDetail(result)" class="view-btn">Details</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Single Result / Detail View -->
    <ResultDetail
      v-if="selectedResult"
      :result="selectedResult"
      class="detail-view-component"
      @close="selectedResult = null"
    />

    <!-- Error Message -->
    <div v-if="error" class="error-message">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ResultDetail from '@/components/ResultDetail.vue'

const API_URL = ''

const inputMode = ref('single')
const singleSequence = ref('')
const fastaInput = ref('')
const loading = ref(false)
const error = ref(null)

const selectedMode = ref('standard')
const selectedKingdom = ref('plant')
const batchResults = ref([])
const summary = ref({ total: 0, consensus_positive: 0, with_neighbor: 0 })
const selectedResult = ref(null)

const exampleSequences = {
  rubisco: 'MSPQTETKASVGFKAGVKDYKLTYYTPEYETKDTDILAAFRVTPQPGVPPEEAGAAVAAESSTGTWTTVWTDGLTSLDRYKGRCYHIEPVAGEENQYICYVAYPLDLFEEGSVTNMFTSIVGNVFGFKALRALRLEDLRIPVAYVKTFQGPPHGIQVERDKLNKYGRPLLGCTIKPKLGLSAKNYGRAVYECLRGGLDFTKDDENVNSQPFMRWRDRFLFCAEALYKAQAETGEIKGHYLNATAGTCEEMMKRAVFARELGVPIVMHDYLTGGFTANTSLSHYCRDNGLLLHIHRAMHAVIDRQKNHGMHFRVLAKALRLSGGDHIHSGTVVGKLEGERDITLGFVDLLRDDFIEKDRSRGIYFTQDWVSLPGVLPVASGGIHVWHMPALTEIFGDDSVLQFGGGTLGHPWGNAPGAVANRVALEACVQARNEGRDLAREGNTIIREATKVPELAAACEVWKEIKFEFD',
  pepc: 'MASERHHSHLHQRTQDRFASAASKDLSSRLIDASITPELDQLLAEFDESHDEEVRKLMAKYGDPVHIAGDLISDGGHHEALFRGCVSDLGFQNIFKYSQVIYDDQIEKLIDWQRRSGLGAKLEERLDIITEIPQSTLAVHSHLITKPEELASLMAKFRAISELFRPDVVQATGKDIFEIALGDPGELVPPSKLPMVDKMDQFVLVSPLLQQILKDQQFMQIDSGQGSPNASEWVRQRISAMIKRLENLPEDKFQDAAKNRFSKPIPFCFSGAVKPSDVKDITKQVERQIYRLVPGYTFTEEFHSKQLLEAKQGTGSDVQEVLKAFFLSYLKQKMGHYKFFSDVKAEFEQQERLVARLAQRVLKSQGPVPSRAEQLDWILRTRQLISLEQLTREQLREMSRNLERMRDELNDDKRRYDTIERLLDEVNEIQRSGIDHYLGQSLLQSEYAAHYRGAAEAVFAKTLTRLTEDIDTAMIASFQKLATLLGCEVPVTGSYRLRNDLVFTMQFLGHAGGVLDGRPYDGSELVRKWLGELGVDIDTIAPQLSIPLFHHDAYTDEDPLLLVLGSSLLRGQVLQKVGGPLHIIGDRLVLCDGKVTSGNPSRLDALFQEHYKADLPAQNVSVLQIDGKEMVFSGTDPEAVAQAYRSLFPLLACNRPLTGLTALYNALQACDNPQAHVLLKKLLAAYTEGEPNPSNAQELFADSKYGVSEETLIASVAKQALEYAKSQGITLFATQKVLKQVGLQTSDSETQVTIEKFKNALGEQISEVKLSMKLTRDMSGISADFEYLLSRVKGKPFAAVPTLNTPFYLKGAFGKNFCKEIGPVPVDVWVLAACLVRDPSIPLEAAREILQENGIDHAFKYIEKVSMSPYSPTRMADLVQVTLSKNAGIINVAMGPVPDGEVWRTEAFGHFIEQFFSDLNVQAYPLVGLSITQRLVRNVSSRLAEESGIVVVAATGQMSKLPADMAETIQAAERKLGFNVLVPTNIGGTNVTQLQETLQLFDRLGSIHSYDLQFLLRLLREGANSFTTEGDPTTEAAGSQ',
  ca: 'MSHHWGYGKHNGPEHWHKDFPIAKGERQSPVDIDTHTAKYDPSLKPLSVSYDQATSLRILNNGHAFNVEFDDSQDKAVLKGGPLDGTYRLIQFHFHWGSLDGQGSEHTVDKKKYAAELHLVHWNTKYGDFGKAVQQPDGLAVLGIFLKVGSAKPGLQKVVDVLDSIKTKGKSADFTNFDPRGLLPESLDYWTYPGSLTTPPLLECVTWIVLKEPISVSSEQVLKFRKLNFNGEGEPEELMVDNWRPAQPLKNRQIKASFK'
}

function loadExample(key) {
  singleSequence.value = exampleSequences[key]
  inputMode.value = 'single'
}

async function predictSingle() {
  if (!singleSequence.value.trim()) {
    error.value = 'Please enter a sequence'
    return
  }

  loading.value = true
  error.value = null

  try {
    const res = await fetch('/api/v1/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sequence: singleSequence.value.trim(),
        mode: selectedMode.value || 'standard',
        kingdom: selectedKingdom.value || 'plant'
      })
    })

    const data = await res.json()

    if (data.ec_predicted) {
      // Keep all backend fields (features_computed, shap, warnings, etc.);
      // add the aliases that the batch table still expects.
      const result = {
        ...data,
        id: data.cdb_query_id || 'query',
        length: data.sequence_length,
        co2_prob_v3: data.carboxylase_probability,
        co2_prob_v5: data.carboxylase_probability,
        consensus: data.is_carboxylase,
        nearest_neighbor: data.top_similar?.[0] || null,
        similar_with_km: data.top_similar || [],
      }
      batchResults.value = [result]
      summary.value = { total: 1, consensus_positive: data.is_carboxylase ? 1 : 0, with_neighbor: data.top_similar?.length > 0 ? 1 : 0 }
      selectedResult.value = result
    } else {
      error.value = data.detail || 'Prediction failed'
    }
  } catch (e) {
    error.value = `Request failed: ${e.message}`
  }

  loading.value = false
}

async function predictBatch() {
  if (!fastaInput.value.trim()) {
    error.value = 'Please enter FASTA sequences'
    return
  }

  loading.value = true
  error.value = null

  try {
    const res = await fetch(`${API_URL}/api/v1/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        fasta: fastaInput.value.trim(),
        mode:    selectedMode.value || 'standard',
        kingdom: selectedKingdom.value || 'plant',
      })
    })

    const data = await res.json()
    
    if (data.success) {
      batchResults.value = data.results
      summary.value = data.summary || { total: data.results.length, consensus_positive: 0, with_neighbor: 0 }
    } else {
      error.value = data.error || 'Batch prediction failed'
    }
  } catch (e) {
    error.value = `Request failed: ${e.message}`
  }

  loading.value = false
}

function handleFileUpload(event) {
  const file = event.target.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      fastaInput.value = e.target.result
    }
    reader.readAsText(file)
  }
}

function viewDetail(result) {
  selectedResult.value = result
}

function downloadResults() {
  const headers = ['ID', 'Length', 'v3_Prob', 'v5_Prob', 'Consensus', 'EC_Predicted', 'EC_Conf', 'Km_uM', 'Nearest_Match', 'Match_Km']
  const rows = batchResults.value.map(r => [
    r.id,
    r.length,
    r.carboxylase_probability?.toFixed(4),
    r.carboxylase_probability?.toFixed(4),
    r.consensus ? 'Yes' : 'No',
    r.ec_predicted,
    r.ec_confidence?.toFixed(4),
    r.km_predicted_uM?.toFixed(2),
    r.nearest_neighbor?.uniprot_id || '',
    r.nearest_neighbor?.km_experimental?.toFixed(2) || ''
  ])

  const tsv = [headers.join('\t'), ...rows.map(r => r.join('\t'))].join('\n')
  
  const blob = new Blob([tsv], { type: 'text/tab-separated-values' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'carboxypred_results.tsv'
  a.click()
  URL.revokeObjectURL(url)
}

function getProbClass(prob) {
  if (prob == null) return ''
  if (prob >= 0.9) return 'prob-high'
  if (prob >= 0.5) return 'prob-medium'
  return 'prob-low'
}
</script>

<style scoped>
.analysis-view {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

h1 { margin: 0; color: #2d3748; }
.subtitle { color: #718096; margin-bottom: 30px; }

.input-section {
  background: white;
  border-radius: 12px;
  padding: 25px;
  margin-bottom: 25px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.input-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.input-tabs {
  display: flex;
  gap: 10px;
}

.input-tabs button {
  padding: 10px 20px;
  border: 2px solid #e2e8f0;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}

.input-tabs button.active {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border-color: transparent;
}

.example-buttons {
  display: flex;
  align-items: center;
  gap: 10px;
}

.example-label {
  color: #718096;
  font-size: 0.9rem;
}

.example-btn {
  padding: 6px 12px;
  background: #e2e8f0;
  border: none;
  border-radius: 6px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: background 0.2s;
}

.example-btn:hover {
  background: #cbd5e0;
}

textarea {
  width: 100%;
  padding: 15px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 14px;
  resize: vertical;
}

textarea:focus {
  border-color: #667eea;
  outline: none;
}

.predict-btn {
  margin-top: 15px;
  padding: 12px 30px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  font-size: 16px;
}

.predict-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.batch-actions {
  display: flex;
  gap: 15px;
  align-items: center;
  margin-top: 15px;
}

.file-upload {
  padding: 10px 20px;
  background: #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
}

.file-upload input { display: none; }

.batch-results {
  background: white;
  border-radius: 12px;
  padding: 25px;
  margin-bottom: 25px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.results-header h2 { margin: 0; color: #2d3748; }

.summary-stats {
  display: flex;
  gap: 20px;
}

.summary-stats .stat {
  color: #4a5568;
}

.download-btn {
  padding: 8px 16px;
  background: #48bb78;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.results-table-container { overflow-x: auto; }

.results-table { width: 100%; border-collapse: collapse; font-size: 13px; }

.results-table th {
  background: #f7fafc;
  padding: 12px 8px;
  text-align: left;
  font-weight: 600;
  color: #4a5568;
  border-bottom: 2px solid #e2e8f0;
  white-space: nowrap;
}

.results-table td {
  padding: 10px 8px;
  border-bottom: 1px solid #e2e8f0;
}

.results-table tr:hover { background: #f7fafc; }
.results-table tr.consensus-positive { background: rgba(72, 187, 120, 0.05); }

.seq-id { font-weight: 600; color: #2d3748; }
.prob-high { color: #38a169; font-weight: 600; }
.prob-medium { color: #d69e2e; }
.prob-low { color: #e53e3e; }

.badge-yes {
  background: #48bb78;
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
}

.badge-no {
  background: #e53e3e;
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
}

.neighbor a { color: #667eea; text-decoration: none; }

.view-btn {
  padding: 4px 10px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.detail-view {
  background: white;
  border-radius: 12px;
  padding: 25px;
  margin-bottom: 25px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.detail-header h2 { margin: 0; color: #2d3748; }

.close-btn {
  width: 30px;
  height: 30px;
  border: none;
  background: #e2e8f0;
  border-radius: 50%;
  font-size: 20px;
  cursor: pointer;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.detail-card {
  background: #f7fafc;
  border-radius: 10px;
  padding: 15px;
}

.detail-card h3 {
  margin: 0 0 15px 0;
  font-size: 14px;
  color: #4a5568;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #e2e8f0;
  font-size: 13px;
}

.info-row:last-child { border-bottom: none; }
.info-row span:first-child { color: #718096; }
.info-row a { color: #667eea; text-decoration: none; }

.similar-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #e2e8f0;
  font-size: 12px;
}

.similar-item a { color: #667eea; }

.error-message {
  background: #fed7d7;
  color: #c53030;
  padding: 15px;
  border-radius: 8px;
  margin-top: 20px;
}

.mode-kingdom-row {
  display: flex;
  gap: 20px;
  margin-top: 12px;
  flex-wrap: wrap;
}
.mode-select, .kingdom-select {
  display: flex;
  align-items: center;
  gap: 8px;
}
.mode-select select, .kingdom-select select {
  padding: 8px 12px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 13px;
  background: white;
}

.detail-view-component { margin-bottom: 25px; }
</style>
