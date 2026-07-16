<template>
  <div class="analysis-view">
    <h1>🔬 Sequence Analysis</h1>
    <p class="subtitle">Predict carboxylase function, EC class, and Km values</p>

    <!-- Input Section -->
    <div class="input-section">
      <!-- Unified input: 1 sequence = single predict, 2+ = batch job -->
      <div class="unified-input">
        <div class="input-header">
          <div class="input-header">
            <span class="input-header-label">Sequence input</span>
            <span class="input-header-hint">
              Paste one sequence (raw or FASTA) or submit multiple FASTA sequences for batch analysis.
            </span>
          </div>
        </div>

        <textarea
          v-model="fastaInput"
          placeholder=">RuBisCO_spinach
MSPQTETKASVGFKAGVKDYKLTYYTPEYETKDTDILAAFRVTPQPG..."
          rows="8"
        ></textarea>
        
        <div class="example-buttons">
          <span class="example-label">Try an example:</span>
          <button type="button" class="example-btn" @click="loadExample('rubisco')" title="P00875 spinach RuBisCO, 469 aa, BRENDA Km 10 µM">RuBisCO</button>
          <button type="button" class="example-btn" @click="loadExample('ca_human')" title="P00918 human CA2, 260 aa, BRENDA Km 12 µM">Human CA2</button>
          <button type="button" class="example-btn" @click="loadExample('ca_pig')" title="A0A286ZZG4 pig CA, high-Km variant">Pig CA</button>
          <button type="button" class="example-btn" @click="loadExample('pepc_maize')" title="P04711 maize PEPC, 970 aa, EC 4.1.1.31">Maize PEPC</button>
          <button type="button" class="example-btn" @click="loadExample('batch_demo')" title="RuBisCO + CA2 (2-sequence FASTA, runs as batch)">Batch demo</button>
        
          <div class="file-upload-row">
            <span class="file-upload-text">Or upload a file:</span>

            <label class="file-upload">
              <input
                type="file"
                @change="handleFileUpload"
                accept=".fasta,.fa,.txt"
              />
              <span aria-hidden="true">📁</span>
              <span>Upload FASTA</span>
            </label>
          </div>
        </div>
        <div v-if="detectedSeqCount >= 2" class="seq-count-notice"
             :class="detectedSeqCount > 20 ? 'seq-count-warn' : 'seq-count-info'">
          <strong>{{ detectedSeqCount }} sequences detected.</strong>
          Will run as a batch job (~{{ Math.max(1, Math.round(detectedSeqCount * (selectedMode === 'standard' ? 90 : 3) / 60)) }} min).
          <span v-if="detectedSeqCount > 20"> You can leave this tab open.</span>
        </div>

        <div class="mode-kingdom-row">
          <div class="mode-select">
            <label>Mode:</label>
            <select v-model="selectedMode">
              <option value="fast">Fast (~5s, ablation without ESM-2)</option>
              <option value="standard">Standard (~15s, +ESM-2) benchmark pipeline (R2=0.953)</option>
              <option value="pfam">Pfam-only (~3s, ablation)</option>
              <option value="composite">Composite (~25s, Best CI)</option>
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

        <button @click="analyze" :disabled="loading" class="predict-btn">
          <span v-if="!loading">
            Analyze {{ detectedSeqCount >= 2 ? `${detectedSeqCount} sequences` : 'Sequence' }}
          </span>

          <span v-else-if="batchProgress">
            Analyzing batch: {{ batchProgress.processed }}/{{ batchProgress.total }} ({{ batchProgress.progressPct || 0 }}%)
          </span>

          <span v-else-if="predictStatus">
            Prediction {{ predictStatus }}...
          </span>

          <span v-else>
            Analyzing...
          </span>
        </button>

        <button
          v-if="loading && (predictJobId || batchProgress?.jobId)"
          type="button"
          class="cancel-btn"
          @click="cancelCurrentJob"
        >
          Cancel {{ batchProgress?.jobId ? 'batch prediction' : 'prediction' }}
        </button>
      </div>
    </div>

    <!-- Batch Results Summary -->
    <div v-if="batchResults && batchResults.length > 0" class="batch-results">
      <div class="results-header">
        <h2>Results ({{ batchResults.length }} sequences)</h2>
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
              <th>Predicted Km <span style="font-size: 0.8em;">(µM)</span></th>
              <!-- <th>Closest BLAST hit</th>
              <th>Experimental Km <span style="font-size: 0.8em;">(closest hit)</span></th> -->
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
              <!-- <td class="neighbor">
                <button
                  v-if="result.nearest_neighbor?.uniprot_id"
                  type="button"
                  class="neighbor-db-link"
                  @click="openCarboDbModal(result.nearest_neighbor.uniprot_id)"
                >
                  {{ result.nearest_neighbor.uniprot_id }}
                </button>

                <span v-else>-</span>
              </td>
              <td class="km-exp">
                <a v-if="result.nearest_neighbor?.km_experimental != null"
                   :href="'https://www.brenda-enzymes.org/enzyme.php?ecno=' + result.ec_predicted"
                   target="_blank" rel="noopener"
                   class="brenda-link"
                   :title="'Look up EC ' + result.ec_predicted + ' on BRENDA'">
                  {{ result.nearest_neighbor.km_experimental.toFixed(1) }} µM
                </a>
                <span v-else>—</span>
              </td> -->
              <td>
                <button
                  type="button"
                  class="view-btn"
                  :class="{ active: resultKey(selectedResult) === resultKey(result) }"
                  @click="viewDetail(result)"
                >
                  {{ resultKey(selectedResult) === resultKey(result)
                    ? 'Collapse'
                    : 'Details' }}
                </button>
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
    <!-- teleport for database view for top blast hit -->
    <Teleport to="body">
      <div
        v-if="databaseModalOpen"
        class="analysis-db-overlay"
        @click.self="closeCarboDbModal"
      >
        <div class="analysis-db-dialog">
          <button
            type="button"
            class="analysis-db-close"
            aria-label="Close database entry"
            @click="closeCarboDbModal"
          >
            ×
          </button>

          <div
            v-if="databaseModalLoading"
            class="analysis-db-state"
          >
            Loading CarboDB entry…
          </div>

          <div
            v-else-if="databaseModalError"
            class="analysis-db-state analysis-db-error"
          >
            {{ databaseModalError }}
          </div>

          <DatabaseResultDetail
            v-else-if="databaseModalResult"
            :result="databaseModalResult"
            :closable="false"
          />
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import ResultDetail from '@/components/ResultDetail.vue'
import DatabaseResultDetail from '../components/details/DatabaseResultDetail.vue'

const API_URL = ''

const inputMode = ref('single')
const singleSequence = ref('')
const fastaInput = ref('')
const loading = ref(false)
const batchProgress = ref(null)
const error = ref(null)
const predictJobId = ref(null)
const predictStatus = ref(null)
const predictPollInterval = ref(null)
const predictAbortController = ref(null)
const batchAbortController = ref(null)

const selectedMode = ref('standard')
const selectedKingdom = ref('plant')
const batchResults = ref([])
const summary = ref({ total: 0, consensus_positive: 0, with_neighbor: 0 })
const selectedResult = ref(null)
const databaseModalOpen = ref(false)
const databaseModalLoading = ref(false)
const databaseModalResult = ref(null)
const databaseModalError = ref('')


const exampleSequences = {
  rubisco: `>RuBisCO_spinach_P00875_EC4.1.1.39_BRENDA_10uM
MSPQTETKASVGFKAGVKDYKLTYYTPEYETKDTDILAAFRVTPQPGVPPEEAGAAVAAESSTGTWTTVWTDGLTSLDRYKGRCYHIEPVAGEENQYICYVAYPLDLFEEGSVTNMFTSIVGNVFGFKALRALRLEDLRIPVAYVKTFQGPPHGIQVERDKLNKYGRPLLGCTIKPKLGLSAKNYGRAVYECLRGGLDFTKDDENVNSQPFMRWRDRFLFCAEALYKAQAETGEIKGHYLNATAGTCEEMMKRAVFARELGVPIVMHDYLTGGFTANTSLSHYCRDNGLLLHIHRAMHAVIDRQKNHGMHFRVLAKALRLSGGDHIHSGTVVGKLEGERDITLGFVDLLRDDFIEKDRSRGIYFTQDWVSLPGVLPVASGGIHVWHMPALTEIFGDDSVLQFGGGTLGHPWGNAPGAVANRVALEACVQARNEGRDLAREGNTIIREATKVPELAAACEVWKEIKFEFD`,
  ca_human: `>CA2_human_P00918_EC4.2.1.1_BRENDA_12uM
MSHHWGYGKHNGPEHWHKDFPIAKGERQSPVDIDTHTAKYDPSLKPLSVSYDQATSLRILNNGHAFNVEFDDSQDKAVLKGGPLDGTYRLIQFHFHWGSLDGQGSEHTVDKKKYAAELHLVHWNTKYGDFGKAVQQPDGLAVLGIFLKVGSAKPGLQKVVDVLDSIKTKGKSADFTNFDPRGLLPESLDYWTYPGSLTTPPLLECVTWIVLKEPISVSSEQVLKFRKLNFNGEGEPEELMVDNWRPAQPLKNRQIKASFK`,
  ca_pig: `>CA_pig_A0A286ZZG4_EC4.2.1.1_BRENDA_83mM
MTGHHGWGYGQNDGPSHWHKLYPIAQGDRQSPINIVSSQAVYSPSLKPLELSYESCTSLSIANNGHSVQVDFNDSDDRTVVTGGPLDGPYRLKQFHFHWGKKHSVGSEHTVDGKSFPSELHLVHWNAKKYSTFGEAASAPDGLAVVGVFLETGDEHPSMNRLTDALYMVRFKGTKAQFSCFNPKCLLPASRHYWTYPGSLTTPPLSESVTWIVLREPISISEKQGNAVWMWSFSLRTFSGILFHGPYFRKARVRLSFKLSPVLAQELEMRQAALAIKFKPFP`,
  pepc_maize: `>PEPC_maize_P04711_EC4.1.1.31
MASTKAPGPGEKHHSIDAQLRQLVPGKVSEDDKLIEYDALLVDRFLNILQDLHGPSLREFVQECYEVSADYEGKGDTTKLGELGAKLTGLAPADAILVASSILHMLNLANLAEEVQIAHRRRNSKLKKGGFADEGSATTESDIEETLKRLVSEVGKSPEEVFEALKNQTVDLVFTAHPTQSARRSLLQKNARIRNCLTQLNAKDITDDDKQELDEALQREIQAAFRTDEIRRAQPTPQAEMRYGMSYIHETVWKGVPKFLRRVDTALKNIGINERLPYNVSLIRFSSWMGGDRDGNPRVTPEVTRDVCLLARMMAANLYIDQIEELMFELSMWRCNDELRVRAEELHSSSGSKVTKYYIEFWKQIPPNEPYRVILGHVRDKLYNTRERARHLLASGVSEISAESSFTSIEEFLEPLELCYKSLCDCGDKAIADGSLLDLLRQVFTFGLSLVKLDIRQESERHTDVIDAITTHLGIGSYREWPEDKRQEWLLSELRGKRPLLPPDLPQTDEIADVIGAFHVLAELPPDSFGPYIISMATAPSDVLAVELLQRECGVRQPLPVVPLFERLADLQSAPASVERLFSVDWYMDRIKGKQQVMVGYSDSGKDAGRLSAAWQLYRAQEEMAQVAKRYGVKLTLFHGRGGTVGRGGGPTHLAILSQPPDTINGSIRVTVQGEVIEFCFGEEHLCFQTLQRFTAATLEHGMHPPVSPKPEWRKLMDEMAVVATEEYRSVVVKEARFVEYFRSATPETEYGRMNIGSRPAKRRPGGGITTLRAIPWIFSWTQTRFHLPVWLGVGAAFKFAIDKDVRNFQVLKEMYNEWPFFRVTLDLLEMVFAKGDPGIAGLYDELLVAEELKPFGKQLRDKYVETQQLLLQIAGHKDILEGDPFLKQGLVLRNPYITTLNVFQAYTLKRIRDPNFKVTPQPPLSKEFADENKPAGLVKLNPASEYPPGLEDTLILTMKGIAAGMQNTG`,
  batch_demo: `>RuBisCO_spinach_P00875
MSPQTETKASVGFKAGVKDYKLTYYTPEYETKDTDILAAFRVTPQPGVPPEEAGAAVAAESSTGTWTTVWTDGLTSLDRYKGRCYHIEPVAGEENQYICYVAYPLDLFEEGSVTNMFTSIVGNVFGFKALRALRLEDLRIPVAYVKTFQGPPHGIQVERDKLNKYGRPLLGCTIKPKLGLSAKNYGRAVYECLRGGLDFTKDDENVNSQPFMRWRDRFLFCAEALYKAQAETGEIKGHYLNATAGTCEEMMKRAVFARELGVPIVMHDYLTGGFTANTSLSHYCRDNGLLLHIHRAMHAVIDRQKNHGMHFRVLAKALRLSGGDHIHSGTVVGKLEGERDITLGFVDLLRDDFIEKDRSRGIYFTQDWVSLPGVLPVASGGIHVWHMPALTEIFGDDSVLQFGGGTLGHPWGNAPGAVANRVALEACVQARNEGRDLAREGNTIIREATKVPELAAACEVWKEIKFEFD
>CA2_human_P00918
MSHHWGYGKHNGPEHWHKDFPIAKGERQSPVDIDTHTAKYDPSLKPLSVSYDQATSLRILNNGHAFNVEFDDSQDKAVLKGGPLDGTYRLIQFHFHWGSLDGQGSEHTVDKKKYAAELHLVHWNTKYGDFGKAVQQPDGLAVLGIFLKVGSAKPGLQKVVDVLDSIKTKGKSADFTNFDPRGLLPESLDYWTYPGSLTTPPLLECVTWIVLKEPISVSSEQVLKFRKLNFNGEGEPEELMVDNWRPAQPLKNRQIKASFK`
}

function loadExample(key) {
  fastaInput.value = exampleSequences[key]
}

function clearPredictPoll() {
  if (predictPollInterval.value) {
    clearInterval(predictPollInterval.value)
    predictPollInterval.value = null
  }
}

async function cancelPrediction() {
  const jobId = predictJobId.value

  clearPredictPoll()

  if (predictAbortController.value) {
    predictAbortController.value.abort()
    predictAbortController.value = null
  }

  if (jobId) {
    try {
      await fetch(`/api/v1/predict/${jobId}`, {
        method: 'DELETE',
      })
    } catch (e) {
      console.warn('Failed to cancel backend job:', e)
    }
  }

  loading.value = false
  predictStatus.value = 'cancelled'
  error.value = 'Prediction cancelled.'
}

async function cancelBatchPrediction() {
  const jobId = batchProgress.value?.jobId

  clearBatchPoll()

  if (batchAbortController.value) {
    batchAbortController.value.abort()
    batchAbortController.value = null
  }

  if (jobId) {
    try {
      await fetch(`${API_URL}/api/v1/batch/${jobId}`, {
        method: 'DELETE',
      })
    } catch (e) {
      console.warn('Failed to cancel backend batch job:', e)
    }
  }

  loading.value = false
  batchProgress.value = batchProgress.value
    ? { ...batchProgress.value, status: 'cancelled' }
    : null
  error.value = 'Batch prediction cancelled.'
}

async function cancelCurrentJob() {
  if (batchProgress.value?.jobId) {
    await cancelBatchPrediction()
  } else {
    await cancelPrediction()
  }
}

async function predictSingle() {
  const raw = (fastaInput.value || '').trim()

  if (!raw) {
    error.value = 'Please enter a sequence'
    return
  }

  const seq = raw.startsWith('>')
    ? raw.split('\n').slice(1).join('').replace(/\s+/g, '')
    : raw.replace(/\s+/g, '')

  loading.value = true
  error.value = null
  batchResults.value = []
  selectedResult.value = null
  predictJobId.value = null
  predictStatus.value = 'submitting'
  clearPredictPoll()

  predictAbortController.value = new AbortController()

  try {
    const submitRes = await fetch('/api/v1/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: predictAbortController.value.signal,
      body: JSON.stringify({
        sequence: seq,
        mode: selectedMode.value || 'standard',
        kingdom: selectedKingdom.value || 'plant',
        seq_id: 'query',
      }),
    })

    if (!submitRes.ok) {
      const errText = await submitRes.text()
      throw new Error(`Submit failed (HTTP ${submitRes.status}): ${errText}`)
    }

    const submitData = await submitRes.json()
    const jobId = submitData.job_id

    if (!jobId) {
      throw new Error('Backend did not return a job_id')
    }

    predictJobId.value = jobId
    predictStatus.value = submitData.status || 'queued'

    predictPollInterval.value = setInterval(async () => {
      try {
        const pollRes = await fetch(`/api/v1/predict/${jobId}`, {
          signal: predictAbortController.value?.signal,
        })

        if (!pollRes.ok) {
          const errText = await pollRes.text()
          throw new Error(`Polling failed (HTTP ${pollRes.status}): ${errText}`)
        }

        const pollData = await pollRes.json()
        predictStatus.value = pollData.status

        if (['queued', 'running', 'started', 'deferred', 'scheduled'].includes(pollData.status)) {
          return
        }

        clearPredictPoll()
        loading.value = false
        predictAbortController.value = null

        if (pollData.status === 'cancelled' || pollData.status === 'canceled') {
          error.value = 'Prediction cancelled.'
          return
        }

        if (pollData.status === 'failed') {
          error.value =
            pollData.error?.message ||
            pollData.error?.detail ||
            'Prediction failed'
          return
        }

        if (pollData.status !== 'completed' || !pollData.result) {
          error.value = 'Prediction finished without a result'
          return
        }

        const data = pollData.result

        const result = {
          ...data,
          id: data.cdb_query_id || 'query',
          length: data.sequence_length,
          co2_prob_v3: data.carboxylase_probability,
          co2_prob_v5: data.carboxylase_probability,
          consensus: data.is_carboxylase,
          nearest_neighbor: data.top_similar?.[0]
            ? {
                ...data.top_similar[0],
                km_experimental: data.top_similar[0].km_experimental_uM,
              }
            : null,
          similar_with_km: data.top_similar || [],
        }

        batchResults.value = [result]

        summary.value = {
          total: 1,
          consensus_positive: data.is_carboxylase ? 1 : 0,
          with_neighbor: data.top_similar?.length > 0 ? 1 : 0,
        }

        selectedResult.value = result
        predictStatus.value = 'completed'
      } catch (e) {
        if (e.name === 'AbortError') {
          return
        }

        clearPredictPoll()
        loading.value = false
        predictAbortController.value = null
        error.value = `Polling error: ${e.message}`
      }
    }, 2000)
  } catch (e) {
    if (e.name === 'AbortError') {
      error.value = 'Prediction request cancelled'
    } else {
      error.value = `Request failed: ${e.message}`
    }

    clearPredictPoll()
    loading.value = false
    predictAbortController.value = null
  }
}

let batchPollInterval = null

function clearBatchPoll() {
  if (batchPollInterval) {
    clearInterval(batchPollInterval)
    batchPollInterval = null
  }
}

async function predictBatch() {
  if (!fastaInput.value.trim()) {
    error.value = 'Please enter FASTA sequences'
    return
  }
  loading.value = true
  error.value = null
  batchProgress.value = null
  clearBatchPoll()

  batchAbortController.value = new AbortController()

  let mode = selectedMode.value || 'standard'
  if (mode !== 'fast' && mode !== 'standard') mode = 'standard'
  const kingdom = selectedKingdom.value || 'plant'

  try {
    const formData = new FormData()
    const fastaBlob = new Blob([fastaInput.value.trim()], { type: 'text/plain' })
    formData.append('file', fastaBlob, 'batch.fasta')
    formData.append('mode', mode)
    formData.append('kingdom', kingdom)

    const submitRes = await fetch(`${API_URL}/api/v1/batch`, {
      method: 'POST',
      body: formData,
      signal: batchAbortController.value.signal,
    })
    if (!submitRes.ok) {
      const errText = await submitRes.text()
      throw new Error(`Submit failed (HTTP ${submitRes.status}): ${errText}`)
    }
    const submitData = await submitRes.json()
    const jobId = submitData.job_id
    if (!jobId) throw new Error('Backend did not return a job_id')

    batchProgress.value = {
      jobId, status: 'queued', processed: 0,
      total: submitData.n_sequences, progressPct: 0,
      estimatedMinutes: submitData.estimated_minutes
    }

    batchPollInterval = setInterval(async () => {
    try {
      const pollRes = await fetch(`${API_URL}/api/v1/batch/${jobId}`, {
        signal: batchAbortController.value?.signal,
      })

      if (!pollRes.ok) {
        const errText = await pollRes.text()
        throw new Error(`Poll failed (HTTP ${pollRes.status}): ${errText}`)
      }

      const meta = await pollRes.json()

      const total = meta.n_sequences || submitData.n_sequences || 1
      const completed = meta.status === 'completed'
      const running = ['queued', 'running', 'started', 'deferred', 'scheduled'].includes(meta.status)

      batchProgress.value = {
        jobId,
        status: meta.status,
        processed: completed ? total : 0,
        total,
        progressPct: completed ? 100 : 0,
      }

      if (running) {
        return
      }

      clearBatchPoll()
      loading.value = false

      if (meta.status === 'cancelled' || meta.status === 'canceled') {
        error.value = 'Batch prediction cancelled.'
        return
      }

      if (meta.status === 'failed') {
        error.value =
          meta.error?.message ||
          meta.error?.detail ||
          'Batch job failed'
        return
      }

      if (meta.status !== 'completed') {
        error.value = `Unexpected batch status: ${meta.status}`
        return
      }

      loadBatchResultsFromPayload(jobId, meta)
    } catch (e) {
      if (e.name === 'AbortError') {
        return
      }

      clearBatchPoll()
      error.value = `Polling error: ${e.message}`
      loading.value = false
      batchAbortController.value = null
    }
  }, 3000)
  } catch (e) {
    if (e.name === 'AbortError') {
      error.value = 'Batch prediction request cancelled'
    } else {
      error.value = `Request failed: ${e.message}`
    }

    clearBatchPoll()
    loading.value = false
    batchAbortController.value = null
  }
}

async function loadBatchResults(jobId) {
  const tsvRes = await fetch(`${API_URL}/api/v1/jobs/${jobId}/results.tsv`)
  if (!tsvRes.ok) throw new Error(`Download failed (HTTP ${tsvRes.status})`)
  const tsv = await tsvRes.text()
  const textLines = tsv.split('\n').filter(l => l.trim())
  if (textLines.length < 2) {
    error.value = 'Batch job completed but produced no results'
    return
  }
  const headers = textLines[0].split('\t')
  const rows = textLines.slice(1).map(line => {
    const cells = line.split('\t')
    const row = {}
    headers.forEach((h, i) => { row[h] = cells[i] || '' })
    const nnUid = row.nearest_uniprot || ''
    const nnKm = parseFloat(row.nearest_km_exp_uM || '')
    return {
      id: row.seq_id || row.id || 'query',
      length: parseInt(row.length || '0', 10),
      co2_prob_v3: parseFloat(row.prob_binary || row.carboxylase_probability || '0'),
      carboxylase_probability: parseFloat(row.prob_binary || row.carboxylase_probability || '0'),
      consensus: (row.is_carboxylase || '').toLowerCase() === 'true' || (row.consensus || '').toLowerCase() === 'yes',
      is_carboxylase: (row.is_carboxylase || '').toLowerCase() === 'true' || (row.consensus || '').toLowerCase() === 'yes',
      ec_predicted: row.ec_predicted || '',
      ec_confidence: parseFloat(row.ec_confidence || '0'),
      km_predicted_uM: parseFloat(row.km_predicted_uM || ''),
      nearest_neighbor: nnUid ? {
        uniprot_id: nnUid,
        km_experimental: isFinite(nnKm) ? nnKm : null,
        organism: row.nearest_organism || '',
        identity_pct: parseFloat(row.nearest_pident || ''),
        tier: row.nearest_tier || ''
      } : null,
      _tsvRow: row
    }
  })
  batchResults.value = rows.map(r => ({ ...r, _jobId: jobId }))
  summary.value = {
    total: rows.length,
    consensus_positive: rows.filter(r => r.consensus).length,
    with_neighbor: rows.filter(r => r.nearest_neighbor).length
  }
}

function loadBatchResultsFromPayload(jobId, payload) {
  const rows = payload.result || []

  batchResults.value = rows.map(r => ({
    ...r,
    id: r.id || r.cdb_query_id || 'query',
    length: r.length || r.sequence_length || 0,
    co2_prob_v3: r.co2_prob_v3 ?? r.carboxylase_probability ?? 0,
    co2_prob_v5: r.co2_prob_v5 ?? r.carboxylase_probability ?? 0,
    consensus: r.consensus ?? r.is_carboxylase ?? false,
    is_carboxylase: r.is_carboxylase ?? r.consensus ?? false,
    ec_predicted: r.ec_predicted || '',
    ec_confidence: r.ec_confidence ?? 0,
    km_predicted_uM: r.km_predicted_uM ?? null,
    nearest_neighbor: r.nearest_neighbor || null,
    similar_with_km: r.top_similar || [],
    _jobId: jobId,
  }))

  summary.value = payload.summary || {
    total: batchResults.value.length,
    consensus_positive: batchResults.value.filter(r => r.consensus).length,
    with_neighbor: batchResults.value.filter(r => r.nearest_neighbor).length,
  }
}

const detectedSeqCount = computed(() => {
  const text = fastaInput.value || ''
  const n = (text.match(/^>/gm) || []).length
  if (n === 0) return text.trim().length > 0 ? 1 : 0
  return n
})

async function analyze() {
  const n = detectedSeqCount.value
  if (n === 0) {
    error.value = 'Please enter a sequence'
    return
  }
  if (n === 1) {
    await predictSingle()
  } else {
    await predictBatch()
  }
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

function parseFastaMap(fasta) {
  // Parse FASTA text into { seq_id: raw_aa_sequence }
  const map = {}
  const chunks = (fasta || '').split(/^>/m).filter(s => s.trim())
  for (const c of chunks) {
    const [header, ...rest] = c.split('\n')
    const id = header.trim().split(/\s+/)[0]
    map[id] = rest.join('').replace(/\s+/g, '')
  }
  return map
}
function resultKey(result) {
  return (
    result?.id ||
    result?.cdb_query_id ||
    result?.sequence_id ||
    result?.uniprot_id
  )
}

async function viewDetail(result) {
  const clickedKey = resultKey(result)
  const selectedKey = resultKey(selectedResult.value)

  // Clicking the currently open sequence closes its detail panel
  if (clickedKey && clickedKey === selectedKey) {
    selectedResult.value = null
    return
  }

  // Full per-sequence data already available
  if (result.features_computed || result.shap) {
    selectedResult.value = result
    return
  }

  // Batch row: find the submitted raw sequence
  const seqMap = parseFastaMap(fastaInput.value)
  const rawSeq = seqMap[result.id]

  if (!rawSeq) {
    selectedResult.value = result
    return
  }

  // Immediately switch the panel to the newly selected sequence
  selectedResult.value = {
    ...result,
    _loadingDetails: true,
  }

  try {
    let data = null

    const res = await fetch(`${API_URL}/api/v1/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sequence: rawSeq,
        mode: selectedMode.value || 'standard',
        kingdom: selectedKingdom.value || 'plant',
      }),
    })

    if (!res.ok) {
      throw new Error(`Detail request failed: ${res.status}`)
    }

    data = await res.json()

    if (data?.ec_predicted) {
      // Make sure the user has not selected a different row while waiting
      if (resultKey(selectedResult.value) !== clickedKey) {
        return
      }

      selectedResult.value = {
        ...data,
        id: result.id,
        length: data.sequence_length,
        co2_prob_v3: data.carboxylase_probability,
        co2_prob_v5: data.carboxylase_probability,
        consensus: data.is_carboxylase,
        nearest_neighbor: data.top_similar?.[0]
          ? {
              ...data.top_similar[0],
              km_experimental:
                data.top_similar[0].km_experimental_uM,
            }
          : null,
      }
    }
  } catch (e) {
    // Only restore this row if the user has not selected another one
    if (resultKey(selectedResult.value) === clickedKey) {
      selectedResult.value = result
    }
  }
}

async function downloadResults() {
  const jobId = batchProgress.value?.jobId || batchResults.value?.[0]?._jobId

  if (jobId) {
    try {
      const res = await fetch(`${API_URL}/api/v1/batch/${jobId}/results.tsv`)

      if (res.ok) {
        const blob = await res.blob()
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `carbodb_batch_${jobId}.tsv`
        a.click()
        URL.revokeObjectURL(url)
        return
      }
    } catch (e) {
      console.warn('Backend TSV download failed, falling back to frontend TSV:', e)
    }
  }

  const headers = ['ID', 'Length', 'v3_Prob', 'v5_Prob', 'Consensus', 'EC_Predicted', 'EC_Conf', 'Km_uM', 'Nearest_Match', 'Match_Km']
  const rows = batchResults.value.map(r => [
    r.id,
    r.length,
    r.carboxylase_probability?.toFixed?.(4) || r.co2_prob_v3?.toFixed?.(4) || '',
    r.carboxylase_probability?.toFixed?.(4) || r.co2_prob_v5?.toFixed?.(4) || '',
    r.consensus ? 'Yes' : 'No',
    r.ec_predicted,
    r.ec_confidence?.toFixed?.(4) || '',
    r.km_predicted_uM?.toFixed?.(2) || '',
    r.nearest_neighbor?.uniprot_id || '',
    r.nearest_neighbor?.km_experimental?.toFixed?.(2) || ''
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

onUnmounted(() => {
  clearBatchPoll()
  clearPredictPoll()

  if (predictAbortController.value) {
    predictAbortController.value.abort()
  }
  if (batchAbortController.value) {
    batchAbortController.value.abort()
  }
})

// loader for database view for top blast hit
async function openCarboDbModal(uniprotId) {
  if (!uniprotId) return

  databaseModalOpen.value = true
  databaseModalLoading.value = true
  databaseModalResult.value = null
  databaseModalError.value = ''

  try {
    const res = await fetch(
      `${API_URL}/api/v1/db/seq/${encodeURIComponent(uniprotId)}`
    )

    if (!res.ok) {
      throw new Error(`Database entry request failed: ${res.status}`)
    }

    databaseModalResult.value = await res.json()
  } catch (error) {
    console.error('Could not load CarboDB entry:', error)
    databaseModalError.value = `Could not load CarboDB entry ${uniprotId}.`
  } finally {
    databaseModalLoading.value = false
  }
}

function closeCarboDbModal() {
  databaseModalOpen.value = false
  databaseModalLoading.value = false
  databaseModalResult.value = null
  databaseModalError.value = ''
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
  flex-wrap: nowrap;
  gap: 6px;
  width: 100%;
  margin-top: 12px;
  margin-bottom: 12px;
}

.example-label {
  margin-right: 2px;
  font-size: 12px;
  color: #a0aec0;
}

.example-btn {
  padding: 5px 10px;

  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 999px;

  color: #64748b;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.2;

  cursor: pointer;
  transition:
    background 0.15s ease,
    border-color 0.15s ease,
    color 0.15s ease,
    transform 0.15s ease;
}

.example-btn:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
  color: #334155;
  transform: translateY(-1px);
}

.example-btn:active {
  transform: translateY(0);
}

.example-btn:focus-visible {
  outline: 2px solid #818cf8;
  outline-offset: 2px;
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
  background: linear-gradient(135deg, #6366f1, #4f46e5);
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

.file-upload-row {
  display: flex;
  align-items: center;
  gap: 8px;

  width: auto;
  margin-top: 0;
  margin-left: auto;
  flex-shrink: 0;
}

.file-upload-text {
  font-size: 12px;
  color: #a0aec0;
}

.file-upload {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 9px;

  background: transparent;
  border: 1px solid #e2e8f0;
  border-radius: 5px;

  color: #718096;
  font-size: 14px;
  line-height: 1.5;
  cursor: pointer;
}

.file-upload:hover {
  background: #f7fafc;
  border-color: #cbd5e0;
  color: #4a5568;
}

.file-upload input {
  display: none;
}

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

.brenda-link {
  color: #dd6b20;
  text-decoration: none;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  border-bottom: 1px dotted #dd6b2055;
}
.brenda-link:hover {
  text-decoration: none;
  border-bottom-color: #dd6b20;
  color: #c05621;
}

.cancel-btn {
  margin-left: 0.75rem;
  padding: 0.75rem 1.25rem;
  border: 1px solid #c44;
  border-radius: 8px;
  background: white;
  color: #c44;
  cursor: pointer;
  font-weight: 600;
}

.cancel-btn:hover {
  background: #fff0f0;
}

.unified-input .input-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; flex-wrap: wrap; }

.input-header {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  width: 100%;
  margin-bottom: 8px;
  text-align: left;
}

.input-header-label {
  flex-shrink: 0;
  display: inline-block;
  padding: 4px 8px;
  background: #edf2f7;
  border-radius: 4px;

  font-size: 13px;
  font-weight: 600;
  color: #2d3748;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.input-header-hint {
  font-size: 12px;
  line-height: 1.5;
  color: #a0aec0;
}

.seq-count-notice { margin: 10px 0; padding: 8px 12px; border-radius: 6px; font-size: 13px; line-height: 1.5; }
.seq-count-info { background: #ebf8ff; color: #2c5282; border-left: 3px solid #4299e1; }
.seq-count-warn { background: #fffaf0; color: #744210; border-left: 3px solid #ecc94b; }

.neighbor-db-link {
  padding: 0;
  border: 0;
  background: transparent;
  color: #667eea;
  font: inherit;
  font-weight: 500;
  cursor: pointer;
}

.neighbor-db-link:hover {
  text-decoration: underline;
}

.neighbor-db-link {
  padding: 0;
  border: 0;
  background: transparent;
  color: #667eea;
  font: inherit;
  font-weight: 500;
  cursor: pointer;
}

.neighbor-db-link:hover {
  text-decoration: underline;
}

.analysis-db-overlay {
  position: fixed !important;
  inset: 0 !important;
  z-index: 99999 !important;

  display: flex !important;
  align-items: flex-start !important;
  justify-content: center !important;

  width: 100vw !important;
  height: 100vh !important;
  padding: 3rem 1.5rem;
  box-sizing: border-box;

  overflow: auto;
  background: rgba(15, 23, 42, 0.55);
  backdrop-filter: blur(2px);
}

.analysis-db-dialog {
  position: relative !important;
  display: block !important;
  flex: none !important;

  width: min(1100px, calc(100vw - 3rem)) !important;
  max-width: 1100px !important;
  min-width: 0;
  max-height: calc(100vh - 6rem);

  margin: 0 auto !important;
  overflow-y: auto;

  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.3);
}

.analysis-db-close {
  position: sticky;
  top: 12px;
  z-index: 20;

  display: block;
  width: 32px;
  height: 32px;
  margin: 12px 14px -40px auto;
  padding: 0;

  border: 0;
  border-radius: 50%;
  background: #f1f5f9;
  color: #475569;

  font-size: 24px;
  line-height: 1;
  cursor: pointer;
}

.analysis-db-close:hover {
  background: #e2e8f0;
  color: #0f172a;
}

.analysis-db-state {
  padding: 3rem;
  text-align: center;
  color: #64748b;
}

.analysis-db-error {
  color: #b91c1c;
}

</style>
