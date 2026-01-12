<template>
  <div class="database-view">
    <!-- Stats Header -->
    <div class="stats-header" v-if="stats">
      <div class="stat-card">
        <span class="stat-icon">🧬</span>
        <div class="stat-content">
          <span class="stat-value">{{ stats.co2_enzymes?.toLocaleString() }}</span>
          <span class="stat-label">CO₂ Enzymes</span>
        </div>
      </div>
      <div class="stat-card">
        <span class="stat-icon">✓</span>
        <div class="stat-content">
          <span class="stat-value">{{ stats.with_verified_ec?.toLocaleString() }}</span>
          <span class="stat-label">Verified EC</span>
        </div>
      </div>
      <div class="stat-card">
        <span class="stat-icon">🎯</span>
        <div class="stat-content">
          <span class="stat-value">{{ stats.with_features?.toLocaleString() }}</span>
          <span class="stat-label">With Features</span>
        </div>
      </div>
      <div class="stat-card">
        <span class="stat-icon">📊</span>
        <div class="stat-content">
          <span class="stat-value">{{ stats.with_experimental_km }}</span>
          <span class="stat-label">Experimental Km</span>
        </div>
      </div>
    </div>

    <!-- Search Section -->
    <div class="search-section">
      <h2>🔍 Search Carboxylase Database</h2>
      <div class="search-filters">
        <div class="filter-row">
          <input 
            v-model="filters.query" 
            type="text" 
            placeholder="Search by UniProt ID or organism..."
            class="search-input"
            @keyup.enter="search"
          />
          <select v-model="filters.ec_class" class="filter-select">
            <option value="">All EC Classes</option>
            <option v-for="ec in ecClasses" :key="ec.ec_number" :value="ec.ec_number">
              {{ ec.ec_number }} - {{ ec.ec_name }} ({{ ec.sequence_count }})
            </option>
          </select>
        </div>
        <div class="filter-row">
          <label class="checkbox-label">
            <input type="checkbox" v-model="filters.is_co2" />
            CO₂ enzymes only
          </label>
          <label class="checkbox-label">
            <input type="checkbox" v-model="filters.verified_only" />
            Verified EC only
          </label>
          <label class="checkbox-label">
            <input type="checkbox" v-model="filters.has_km" />
            Has Km data
          </label>
          <button @click="search" class="search-btn">Search</button>
          <button @click="resetFilters" class="reset-btn">Reset</button>
        </div>
      </div>
    </div>

    <!-- Results Table -->
    <div class="results-section" v-if="results.length > 0">
      <h3>Results ({{ results.length }} sequences)</h3>
      <div class="table-container">
        <table class="results-table">
          <thead>
            <tr>
              <th>UniProt ID</th>
              <th>Length</th>
              <th>Organism</th>
              <th>v3 Prob</th>
              <th>v5 Prob</th>
              <th>EC (Best)</th>
              <th>EC (Predicted)</th>
              <th>Km (Best)</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="seq in results" :key="seq.uniprot_id" 
                :class="{ 'consensus-positive': seq.is_consensus_positive }">
              <td class="uniprot-id">
                <a :href="'https://www.uniprot.org/uniprotkb/' + seq.uniprot_id" target="_blank">
                  {{ seq.uniprot_id }}
                </a>
              </td>
              <td>{{ seq.length }}</td>
              <td class="organism">{{ seq.organism || '-' }}</td>
              <td :class="getProbClass(seq.v3_prob)">
                {{ seq.v3_prob ? (seq.v3_prob * 100).toFixed(1) + '%' : '-' }}
              </td>
              <td :class="getProbClass(seq.v5_prob)">
                {{ seq.v5_prob ? (seq.v5_prob * 100).toFixed(1) + '%' : '-' }}
              </td>
              <td class="ec-verified">{{ seq.ec_best || seq.ec_verified || '-' }}</td>
              <td class="ec-predicted">{{ seq.ec_predicted || '-' }}</td>
              <td class="km-value">
                {{ seq.km_best ? seq.km_best.toFixed(1) + ' µM' : (seq.km_predicted ? seq.km_predicted.toFixed(1) + ' µM' : '-') }}
              </td>
              <td>
                <button @click="viewDetails(seq.id)" class="view-btn">View</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- EC Distribution Charts -->
    <div class="charts-section" v-if="stats && stats.ec_distribution">
      <div class="chart-card">
        <h3>🔬 Top EC Classes</h3>
        <div class="ec-bars">
          <div v-for="ec in stats.ec_distribution.slice(0, 8)" :key="ec.ec_number" class="ec-bar-row">
            <span class="ec-label">{{ ec.ec_number }}</span>
            <div class="ec-bar-container">
              <div class="ec-bar" :style="{ width: getBarWidth(ec.count, stats.ec_distribution) }"></div>
            </div>
            <span class="ec-count">{{ ec.count }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Sequence Detail Modal -->
    <div class="modal-overlay" v-if="selectedSequence" @click.self="selectedSequence = null">
      <div class="modal-content">
        <button class="modal-close" @click="selectedSequence = null">×</button>
        <h2>{{ selectedSequence.uniprot_id }}</h2>
        
        <div class="detail-grid">
          <div class="detail-section">
            <h3>📋 Basic Info</h3>
            <div class="detail-row"><span>Length:</span> {{ selectedSequence.length }} aa</div>
            <div class="detail-row"><span>Organism:</span> {{ selectedSequence.organism || 'Unknown' }}</div>
            <div class="detail-row"><span>Consensus CO₂:</span> 
              <span :class="selectedSequence.is_consensus_positive ? 'badge-yes' : 'badge-no'">
                {{ selectedSequence.is_consensus_positive ? 'Yes' : 'No' }}
              </span>
            </div>
          </div>
          
          <div class="detail-section">
            <h3>🎯 ML Predictions</h3>
            <div class="detail-row"><span>v3 Probability:</span> 
              <span :class="getProbClass(selectedSequence.v3_prob)">
                {{ selectedSequence.v3_prob ? (selectedSequence.v3_prob * 100).toFixed(2) + '%' : '-' }}
              </span>
            </div>
            <div class="detail-row"><span>v5 Probability:</span> 
              <span :class="getProbClass(selectedSequence.v5_prob)">
                {{ selectedSequence.v5_prob ? (selectedSequence.v5_prob * 100).toFixed(2) + '%' : '-' }}
              </span>
            </div>
          </div>
          
          <div class="detail-section">
            <h3>🧪 EC Classification</h3>
            <div class="detail-row"><span>Best EC:</span> {{ selectedSequence.ec_best || '-' }}</div>
            <div class="detail-row"><span>Source:</span> {{ selectedSequence.ec_best_source || '-' }}</div>
            <div class="detail-row"><span>Predicted:</span> {{ selectedSequence.ec_predicted || '-' }}</div>
          </div>
          
          <div class="detail-section">
            <h3>📊 Km Values</h3>
            <div class="detail-row"><span>Best Km:</span> {{ selectedSequence.km_best ? selectedSequence.km_best.toFixed(2) + ' µM' : '-' }}</div>
            <div class="detail-row"><span>Experimental:</span> {{ selectedSequence.km_experimental ? selectedSequence.km_experimental.toFixed(2) + ' µM' : '-' }}</div>
            <div class="detail-row"><span>Predicted:</span> {{ selectedSequence.km_predicted ? selectedSequence.km_predicted.toFixed(2) + ' µM' : '-' }}</div>
          </div>
        </div>
        
        <div class="modal-actions">
          <button @click="viewFeatures(selectedSequence.id)" class="action-btn">
            View Features (447)
          </button>
          <a :href="'https://www.uniprot.org/uniprotkb/' + selectedSequence.uniprot_id" 
             target="_blank" class="action-btn external">
            UniProt ↗
          </a>
        </div>
      </div>
    </div>

    <!-- Features Modal -->
    <div class="modal-overlay" v-if="showFeatures" @click.self="showFeatures = false">
      <div class="modal-content wide">
        <button class="modal-close" @click="showFeatures = false">×</button>
        <h2>Features (447)</h2>
        
        <div class="features-grid" v-if="features">
          <div class="feature-category">
            <h3>Invariant Features</h3>
            <div class="feature-list">
              <div v-for="(val, key) in getFeaturesByPrefix('inv_')" :key="key" class="feature-item">
                <span class="feature-name">{{ key }}</span>
                <span class="feature-value">{{ val.toFixed(4) }}</span>
              </div>
            </div>
          </div>
          <div class="feature-category">
            <h3>Amino Acid Composition</h3>
            <div class="feature-list">
              <div v-for="(val, key) in getFeaturesByPrefix('aa_')" :key="key" class="feature-item">
                <span class="feature-name">{{ key.replace('aa_', '') }}</span>
                <span class="feature-value">{{ (val * 100).toFixed(2) }}%</span>
              </div>
            </div>
          </div>
          <div class="feature-category">
            <h3>Motifs</h3>
            <div class="feature-list">
              <div v-for="(val, key) in getFeaturesByPrefix('motif_')" :key="key" class="feature-item">
                <span class="feature-name">{{ key.replace('motif_', '') }}</span>
                <span class="feature-value">{{ val.toFixed(4) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div class="loading" v-if="loading">Loading...</div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'

const API_URL = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'

const stats = ref(null)
const ecClasses = ref([])
const results = ref([])
const loading = ref(false)
const selectedSequence = ref(null)
const showFeatures = ref(false)
const features = ref(null)

const filters = ref({
  query: '',
  ec_class: '',
  is_co2: true,
  verified_only: false,
  has_km: false
})

async function loadStats() {
  try {
    const res = await fetch(`${API_URL}/db/stats`)
    const data = await res.json()
    if (data.success) {
      stats.value = data.stats
    }
  } catch (err) {
    console.error('Failed to load stats:', err)
  }
}

async function loadEcClasses() {
  try {
    const res = await fetch(`${API_URL}/db/ec-classes`)
    const data = await res.json()
    if (data.success) {
      ecClasses.value = data.ec_classes
    }
  } catch (err) {
    console.error('Failed to load EC classes:', err)
  }
}

async function search() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (filters.value.query) params.append('query', filters.value.query)
    if (filters.value.ec_class) params.append('ec_class', filters.value.ec_class)
    if (filters.value.is_co2) params.append('is_co2', 'true')
    if (filters.value.verified_only) params.append('verified_only', 'true')
    if (filters.value.has_km) params.append('has_km', 'true')
    params.append('limit', '100')
    
    const res = await fetch(`${API_URL}/db/search?${params}`)
    const data = await res.json()
    if (data.success) {
      results.value = data.results
    }
  } catch (err) {
    console.error('Search failed:', err)
  }
  loading.value = false
}

async function viewDetails(seqId) {
  try {
    const res = await fetch(`${API_URL}/db/sequence/${seqId}`)
    const data = await res.json()
    if (data.success) {
      selectedSequence.value = data.sequence
    }
  } catch (err) {
    console.error('Failed to load sequence:', err)
  }
}

async function viewFeatures(seqId) {
  try {
    const res = await fetch(`${API_URL}/db/sequence/${seqId}/features`)
    const data = await res.json()
    if (data.success) {
      features.value = data.features
      showFeatures.value = true
    }
  } catch (err) {
    console.error('Failed to load features:', err)
  }
}

function getFeaturesByPrefix(prefix) {
  if (!features.value) return {}
  return Object.fromEntries(
    Object.entries(features.value).filter(([k]) => k.startsWith(prefix))
  )
}

function resetFilters() {
  filters.value = {
    query: '',
    ec_class: '',
    is_co2: true,
    verified_only: false,
    has_km: false
  }
  results.value = []
}

function getProbClass(prob) {
  if (!prob) return ''
  if (prob >= 0.9) return 'prob-high'
  if (prob >= 0.5) return 'prob-medium'
  return 'prob-low'
}

function getBarWidth(count, distribution) {
  const max = Math.max(...distribution.map(d => d.count))
  return `${(count / max) * 100}%`
}

onMounted(() => {
  loadStats()
  loadEcClasses()
  search()
})
</script>

<style scoped>
.database-view {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.stats-header {
  display: flex;
  gap: 15px;
  margin-bottom: 30px;
  flex-wrap: wrap;
}

.stat-card {
  flex: 1;
  min-width: 150px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.stat-icon { font-size: 28px; }
.stat-content { display: flex; flex-direction: column; }
.stat-value { font-size: 24px; font-weight: 700; }
.stat-label { font-size: 12px; opacity: 0.9; }

.search-section {
  background: white;
  border-radius: 12px;
  padding: 25px;
  margin-bottom: 25px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.search-section h2 { margin: 0 0 20px 0; color: #2d3748; }

.search-filters { display: flex; flex-direction: column; gap: 15px; }
.filter-row { display: flex; gap: 15px; align-items: center; flex-wrap: wrap; }

.search-input {
  flex: 2;
  padding: 12px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  min-width: 250px;
}

.search-input:focus { border-color: #667eea; outline: none; }

.filter-select {
  flex: 1;
  padding: 12px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  min-width: 200px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #4a5568;
  cursor: pointer;
}

.search-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}

.reset-btn {
  padding: 12px 20px;
  background: #e2e8f0;
  color: #4a5568;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.results-section {
  background: white;
  border-radius: 12px;
  padding: 25px;
  margin-bottom: 25px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.table-container { overflow-x: auto; }

.results-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.results-table th {
  background: #f7fafc;
  padding: 12px 10px;
  text-align: left;
  font-weight: 600;
  color: #4a5568;
  border-bottom: 2px solid #e2e8f0;
}
.results-table td { padding: 10px; border-bottom: 1px solid #e2e8f0; }
.results-table tr:hover { background: #f7fafc; }
.results-table tr.consensus-positive { background: rgba(72, 187, 120, 0.05); }

.uniprot-id a { color: #667eea; text-decoration: none; font-weight: 600; }
.organism { max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.prob-high { color: #38a169; font-weight: 600; }
.prob-medium { color: #d69e2e; }
.prob-low { color: #e53e3e; }

.view-btn {
  padding: 6px 12px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
}

.charts-section { margin-bottom: 25px; }
.chart-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.ec-bars { display: flex; flex-direction: column; gap: 8px; }
.ec-bar-row { display: flex; align-items: center; gap: 10px; }
.ec-label { width: 80px; font-size: 12px; font-weight: 600; color: #4a5568; }
.ec-bar-container { flex: 1; height: 20px; background: #e2e8f0; border-radius: 10px; overflow: hidden; }
.ec-bar { height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); border-radius: 10px; }
.ec-count { width: 50px; text-align: right; font-size: 12px; color: #718096; }

.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 16px;
  padding: 30px;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  width: 90%;
  position: relative;
}

.modal-content.wide { max-width: 1000px; }

.modal-close {
  position: absolute; top: 15px; right: 15px;
  width: 30px; height: 30px;
  border: none; background: #e2e8f0;
  border-radius: 50%; font-size: 20px; cursor: pointer;
}

.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
.detail-section { background: #f7fafc; border-radius: 10px; padding: 15px; }
.detail-section h3 { margin: 0 0 10px 0; font-size: 14px; color: #4a5568; }
.detail-row { display: flex; justify-content: space-between; padding: 5px 0; font-size: 13px; }

.badge-yes { background: #48bb78; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; }
.badge-no { background: #e53e3e; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; }

.modal-actions { display: flex; gap: 10px; margin-top: 20px; }
.action-btn {
  padding: 10px 20px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
}
.action-btn.external { background: #4a5568; }

.features-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.feature-category { background: #f7fafc; border-radius: 10px; padding: 15px; }
.feature-list { max-height: 400px; overflow-y: auto; }
.feature-item { display: flex; justify-content: space-between; padding: 4px 0; font-size: 12px; border-bottom: 1px solid #e2e8f0; }
.feature-name { color: #4a5568; font-family: monospace; }
.feature-value { font-weight: 600; color: #2d3748; }

.loading { text-align: center; padding: 40px; color: #718096; }

@media (max-width: 768px) {
  .stats-header { flex-direction: column; }
  .detail-grid { grid-template-columns: 1fr; }
  .features-grid { grid-template-columns: 1fr; }
}
</style>
