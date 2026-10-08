<template>
  <main class="database-entry-view">
    <div v-if="loading">Loading database entry…</div>

    <div v-else-if="error">
      {{ error }}
    </div>

    <DatabaseResultDetail
      v-else-if="result"
      :result="result"
      :closable="true"
      @close="router.push('/database')"
    />
  </main>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DatabaseResultDetail from '../components/details/DatabaseResultDetail.vue'

const API_URL = import.meta.env.VITE_API_URL || ''

const route = useRoute()
const router = useRouter()

const result = ref(null)
const loading = ref(false)
const error = ref('')

async function loadEntry(uniprotId) {
  if (!uniprotId) return

  loading.value = true
  result.value = null
  error.value = ''

  try {
    const res = await fetch(
      `${API_URL}/api/v1/db/seq/${encodeURIComponent(uniprotId)}`
    )

    if (!res.ok) {
      throw new Error(`Database entry request failed: ${res.status}`)
    }

    result.value = await res.json()
  } catch (e) {
    console.error(e)
    error.value = `Could not load database entry ${uniprotId}.`
  } finally {
    loading.value = false
  }
}

watch(
  () => route.params.uniprotId,
  uniprotId => {
    if (typeof uniprotId === 'string') {
      loadEntry(uniprotId)
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.database-entry-view {
  padding: 24px;
}
</style>