<template>
  <div class="database-view">
    <!-- ═══ Stats banner ═══════════════════════════════════════════════════ -->
    <div v-if="stats" class="stats-banner">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_sequences.toLocaleString() }}</div>
        <div class="stat-label">Total sequences</div>
      </div>
      <div class="stat-card stat-card-primary">
        <div class="stat-value">{{ stats.predicted_carboxylases.toLocaleString() }}</div>
        <div class="stat-label">Predicted carboxylases</div>
      </div>
      <div class="stat-card stat-card-accent">
        <div class="stat-value">{{ stats.with_experimental_km.toLocaleString() }}</div>
        <div class="stat-label">With experimental Km</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.ec_classes_total }}</div>
        <div class="stat-label">EC classes</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.reviewed_count.toLocaleString() }}</div>
        <div class="stat-label">SwissProt-curated</div>
      </div>
    </div>

    <!-- ═══ Quick-pick example queries ═════════════════════════════════════ -->
    <div class="quick-picks">
      <span class="quick-picks-label">Try:</span>
      <button class="qp-btn" @click="applyExample('rubisco')">RuBisCO (4.1.1.39)</button>
      <button class="qp-btn" @click="applyExample('ca')">Carbonic anhydrases (4.2.1.1)</button>
      <button class="qp-btn" @click="applyExample('pepc')">PEPCases (4.1.1.31)</button>
      <button class="qp-btn" @click="applyExample('with_km')">With experimental Km</button>
      <button class="qp-btn" @click="applyExample('reviewed')">SwissProt only</button>
      <button class="qp-btn" @click="applyExample('low_km')">Low Km (&lt;10 µM)</button>
    </div>

    <!-- ═══ Search + filters ═══════════════════════════════════════════════ -->
    <div class="search-bar">
      <input
        v-model="filters.q"
        type="text"
        placeholder="Search by UniProt ID or organism (e.g. P00918, Homo sapiens, spinach)"
        class="search-input"
        @keyup.enter="search(0)"
      />
      <select v-model="filters.ec" class="filter-select" @change="search(0)">
        <option value="">All EC classes</option>
        <option v-for="ec in ecOptions" :key="ec.ec_number" :value="ec.ec_number">
          {{ ec.ec_number }} — {{ ec.ec_name }} ({{ ec.count.toLocaleString() }})
        </option>
      </select>
      <button class="search-btn" @click="search(0)">Search</button>
      <button class="reset-btn" @click="resetFilters">Reset</button>
    </div>
    <div class="filter-row">
      <label class="checkbox-label">
        <input type="checkbox" v-model="filters.has_experimental_km" @change="search(0)"/>
        Has experimental Km
      </label>
      <label class="checkbox-label">
        <input type="checkbox" v-model="filters.reviewed" @change="search(0)"/>
        SwissProt-curated only
      </label>
      <label class="checkbox-label">
        <input type="checkbox" v-model="filters.is_carboxylase" @change="search(0)"/>
        Predicted carboxylase
      </label>
      <span class="result-summary" v-if="totalResults > 0">
        {{ totalResults.toLocaleString() }} matches
        <span class="page-info">
          (showing {{ offset + 1 }}–{{ Math.min(offset + results.length, totalResults) }})
        </span>
      </span>
    </div>

    <!-- ═══ Results table ══════════════════════════════════════════════════ -->
    <div v-if="loading" class="loading">Loading…</div>

    <div v-else-if="results.length === 0 && hasSearched" class="empty">
      No sequences match your search. Try broadening the filters or hit Reset.
    </div>

    <div v-else-if="results.length > 0" class="table-wrap">
      <table class="db-table">
        <thead>
          <tr>
            <th @click="setSort('uniprot')" :class="{ active: filters.sort === 'uniprot' }">
              UniProt ID
            </th>
            <th>Organism</th>
            <th>EC</th>
            <th @click="setSort('length')" :class="{ active: sortIs('length') }">
              Length {{ sortArrow('length') }}
            </th>
            <th @click="setSort('km_pred')" :class="{ active: sortIs('km_pred') }">
              Predicted Km (µM) {{ sortArrow('km_pred') }}
            </th>
            <th>Experimental Km (µM)</th>
            <th>Source</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in results" :key="r.uniprot_id" @click="openDetail(r)" class="row-clickable">
            <td class="uniprot rd-mono">
              <a :href="'https://www.uniprot.org/uniprotkb/' + r.uniprot_id"
                 target="_blank" @click.stop>{{ r.uniprot_id }}</a>
              <span v-if="r.reviewed" class="reviewed-dot" title="SwissProt curated">✓</span>
            </td>
            <td class="organism">{{ r.organism || '—' }}</td>
            <td class="ec">
              <span class="ec-tag">{{ r.ec_predicted || r.ec_known || '—' }}</span>
              <span v-if="r.ec_name" class="ec-name">{{ r.ec_name }}</span>
            </td>
            <td>{{ r.length }}</td>
            <td class="km-pred">
              <span v-if="r.km_predicted_uM != null">{{ r.km_predicted_uM.toFixed(1) }}</span>
              <span v-else class="muted">—</span>
            </td>
            <td class="km-exp">
              <span v-if="r.km_experimental_uM != null">{{ r.km_experimental_uM.toFixed(1) }}</span>
              <span v-else class="muted">—</span>
            </td>
            <td class="source">
              <span class="source-tag" :class="'source-' + r.source">{{ r.source }}</span>
            </td>
            <td>
              <button class="detail-btn" @click.stop="openDetail(r)">Details</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ═══ Pagination ═════════════════════════════════════════════════════ -->
    <div class="pagination" v-if="totalResults > limit">
      <button @click="search(offset - limit)" :disabled="offset === 0">‹ Prev</button>
      <span>Page {{ Math.floor(offset / limit) + 1 }} / {{ Math.ceil(totalResults / limit) }}</span>
      <button @click="search(offset + limit)" :disabled="offset + limit >= totalResults">Next ›</button>
    </div>

    <!-- ═══ Detail modal — reuses ResultDetail component ═══════════════════ -->
    <div v-if="selectedDetail" class="detail-modal-overlay" @click.self="selectedDetail = null">
      <div class="detail-modal">
        <button class="detail-close" @click="selectedDetail = null">×</button>
        <ResultDetail :result="selectedDetail" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import ResultDetail from '../components/ResultDetail.vue'

const API_URL = import.meta.env.VITE_API_URL || ''

// ─── reactive state ──────────────────────────────────────────────────────
const stats = ref(null)
const results = ref([])
const totalResults = ref(0)
const offset = ref(0)
const limit = 50
const loading = ref(false)
const hasSearched = ref(false)
const selectedDetail = ref(null)

const filters = reactive({
  q: '',
  ec: '',
  has_experimental_km: false,
  reviewed: false,
  is_carboxylase: true,   // default-on; most users want positives
  sort: 'default',
})

const ecOptions = computed(() => stats.value?.ec_distribution || [])

// ─── lifecycle ───────────────────────────────────────────────────────────
onMounted(async () => {
  await fetchStats()
  await search(0)   // populate the table immediately on first visit
})

// ─── fetchers ────────────────────────────────────────────────────────────
async function fetchStats() {
  try {
    const res = await fetch(`${API_URL}/api/v1/stats`)
    if (res.ok) stats.value = await res.json()
  } catch (e) {
    console.error('stats fetch failed', e)
  }
}

async function search(newOffset) {
  loading.value = true
  hasSearched.value = true
  offset.value = Math.max(0, newOffset)

  const params = new URLSearchParams({ limit: String(limit), offset: String(offset.value) })
  if (filters.q) params.set('q', filters.q)
  if (filters.ec) params.set('ec', filters.ec)
  if (filters.has_experimental_km) params.set('has_experimental_km', 'true')
  if (filters.reviewed) params.set('reviewed', 'true')
  if (filters.is_carboxylase) params.set('is_carboxylase', 'true')
  if (filters.sort !== 'default') params.set('sort', filters.sort)

  try {
    const res = await fetch(`${API_URL}/api/v1/browse?${params}`)
    const data = await res.json()
    results.value = data.results || []
    totalResults.value = data.total || 0
  } catch (e) {
    console.error('browse failed', e)
    results.value = []
    totalResults.value = 0
  } finally {
    loading.value = false
  }
}

// ─── interaction ─────────────────────────────────────────────────────────
async function openDetail(row) {
  selectedDetail.value = { ...row, _loading: true }
  try {
    const res = await fetch(`${API_URL}/api/v1/db/seq/${row.uniprot_id}`)
    if (res.ok) {
      selectedDetail.value = await res.json()
    } else {
      // Fall back: keep the row data so the modal at least shows the basics
      selectedDetail.value = {
        ...row,
        id: row.uniprot_id,
        sequence_length: row.length,
      }
    }
  } catch (e) {
    selectedDetail.value = {
      ...row,
      id: row.uniprot_id,
      sequence_length: row.length,
    }
  }
}

function applyExample(kind) {
  resetFilters({ keepDefaults: true })
  if (kind === 'rubisco')   { filters.ec = '4.1.1.39' }
  if (kind === 'ca')        { filters.ec = '4.2.1.1' }
  if (kind === 'pepc')      { filters.ec = '4.1.1.31' }
  if (kind === 'with_km')   { filters.has_experimental_km = true }
  if (kind === 'reviewed')  { filters.reviewed = true }
  if (kind === 'low_km')    { filters.sort = 'km_asc'; filters.has_experimental_km = true }
  search(0)
}

function resetFilters(opts = {}) {
  filters.q = ''
  filters.ec = ''
  filters.has_experimental_km = false
  filters.reviewed = false
  filters.is_carboxylase = true
  filters.sort = 'default'
  if (!opts.keepDefaults) search(0)
}

// ─── sort helpers ────────────────────────────────────────────────────────
function setSort(col) {
  if (col === 'uniprot') {
    filters.sort = 'uniprot'
  } else if (col === 'length') {
    filters.sort = filters.sort === 'length_asc' ? 'length_desc' : 'length_asc'
  } else if (col === 'km_pred') {
    filters.sort = filters.sort === 'km_asc' ? 'km_desc' : 'km_asc'
  }
  search(0)
}
function sortIs(col) {
  if (col === 'length') return filters.sort.startsWith('length')
  if (col === 'km_pred') return filters.sort.startsWith('km_')
  return filters.sort === col
}
function sortArrow(col) {
  if (col === 'length') return filters.sort === 'length_asc' ? '↑' : filters.sort === 'length_desc' ? '↓' : ''
  if (col === 'km_pred') return filters.sort === 'km_asc' ? '↑' : filters.sort === 'km_desc' ? '↓' : ''
  return ''
}
</script>

<style scoped>
.database-view {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px 16px;
}

/* ═══ Stats banner ═══════════════════════════════════════════════════════ */
.stats-banner {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}
.stat-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 14px 16px;
}
.stat-card-primary { border-color: #4f46e5; background: linear-gradient(135deg, #fff 60%, #eef2ff); }
.stat-card-accent  { border-color: #10b981; background: linear-gradient(135deg, #fff 60%, #ecfdf5); }
.stat-value {
  font-size: 22px;
  font-weight: 600;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}
.stat-card-primary .stat-value { color: #4f46e5; }
.stat-card-accent  .stat-value { color: #047857; }
.stat-label {
  font-size: 11px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-top: 4px;
}

/* ═══ Quick-picks ════════════════════════════════════════════════════════ */
.quick-picks {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}
.quick-picks-label {
  font-size: 13px;
  color: #475569;
  margin-right: 4px;
}
.qp-btn {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  color: #334155;
  border-radius: 999px;
  padding: 6px 14px;
  font-size: 13px;
  cursor: pointer;
  transition: all 120ms;
}
.qp-btn:hover {
  background: #e0e7ff;
  border-color: #818cf8;
  color: #3730a3;
}

/* ═══ Search bar ═════════════════════════════════════════════════════════ */
.search-bar {
  display: grid;
  grid-template-columns: 2fr 1fr auto auto;
  gap: 8px;
  margin-bottom: 8px;
}
.search-input, .filter-select {
  padding: 9px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
}
.search-input:focus, .filter-select:focus {
  outline: 2px solid #818cf8;
  outline-offset: -1px;
  border-color: #4f46e5;
}
.search-btn, .reset-btn {
  padding: 9px 18px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}
.search-btn {
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  color: white;
}
.search-btn:hover { background: linear-gradient(135deg, #4f46e5, #4338ca); }
.reset-btn { background: #e2e8f0; color: #475569; }
.reset-btn:hover { background: #cbd5e1; }

.filter-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 16px;
  font-size: 13px;
}
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #475569;
  cursor: pointer;
}
.result-summary {
  margin-left: auto;
  color: #475569;
}
.page-info { color: #94a3b8; font-size: 12px; }

/* ═══ Table ══════════════════════════════════════════════════════════════ */
.loading, .empty {
  text-align: center;
  padding: 60px 0;
  color: #64748b;
}
.table-wrap {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 16px;
}
.db-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.db-table thead th {
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  user-select: none;
}
.db-table thead th:hover { background: #eef2ff; }
.db-table thead th.active { color: #4f46e5; }
.db-table tbody td {
  padding: 10px 12px;
  border-bottom: 1px solid #f1f5f9;
}
.row-clickable { cursor: pointer; transition: background 100ms; }
.row-clickable:hover { background: #f8fafc; }
.uniprot a { color: #4f46e5; text-decoration: none; font-weight: 500; }
.uniprot a:hover { text-decoration: underline; }
.reviewed-dot { color: #10b981; margin-left: 4px; font-weight: 700; }
.organism { color: #475569; font-style: italic; max-width: 220px;
            overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ec-tag {
  background: #eef2ff;
  color: #4338ca;
  padding: 2px 8px;
  border-radius: 4px;
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-size: 12px;
  margin-right: 6px;
}
.ec-name { color: #64748b; font-size: 12px; }
.muted { color: #cbd5e1; }
.km-pred, .km-exp { font-variant-numeric: tabular-nums; }
.km-exp { color: #047857; font-weight: 500; }
.source-tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 3px;
  background: #f1f5f9;
  color: #64748b;
  text-transform: lowercase;
}
.source-tag.source-swissprot { background: #fef3c7; color: #92400e; }
.source-tag.source-brenda { background: #dbeafe; color: #1e40af; }
.detail-btn {
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
  color: #334155;
}
.detail-btn:hover { background: #4f46e5; color: white; border-color: #4f46e5; }
.rd-mono { font-family: ui-monospace, SFMono-Regular, monospace; }

/* ═══ Pagination ═════════════════════════════════════════════════════════ */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin: 12px 0;
  font-size: 13px;
  color: #475569;
}
.pagination button {
  padding: 6px 14px;
  border: 1px solid #cbd5e1;
  background: white;
  border-radius: 6px;
  cursor: pointer;
}
.pagination button:disabled { opacity: 0.4; cursor: not-allowed; }
.pagination button:hover:not(:disabled) { background: #eef2ff; border-color: #818cf8; }

/* ═══ Detail modal ═══════════════════════════════════════════════════════ */
.detail-modal-overlay {
  position: fixed; inset: 0;
  background: rgba(15, 23, 42, 0.55);
  display: flex; align-items: flex-start; justify-content: center;
  z-index: 1000;
  padding: 32px 16px;
  overflow-y: auto;
}
.detail-modal {
  background: white;
  border-radius: 12px;
  max-width: 1200px; width: 100%;
  position: relative;
  padding: 16px;
}
.detail-close {
  position: absolute;
  right: 14px; top: 10px;
  background: transparent; border: none;
  font-size: 28px;
  color: #64748b;
  cursor: pointer;
  z-index: 1;
}
.detail-close:hover { color: #0f172a; }

@media (max-width: 900px) {
  .stats-banner { grid-template-columns: repeat(2, 1fr); }
  .search-bar { grid-template-columns: 1fr; }
}
</style>
