<template>
  <DatabaseResultDetail
    v-if="isDatabaseResult"
    :result="result"
    :closable="closable"
    @close="$emit('close')"
  />

  <PredictionResultDetail
    v-else
    :result="result"
    :closable="closable"
    @close="$emit('close')"
  />
</template>

<script setup>
import { computed } from 'vue'
import DatabaseResultDetail from './details/DatabaseResultDetail.vue'
import PredictionResultDetail from './details/PredictionResultDetail.vue'

const props = defineProps({
  result: { type: Object, required: true },
  closable: { type: Boolean, default: true },
})

defineEmits(['close'])

const isDatabaseResult = computed(() => {
  return props.result?.mode === 'db_lookup'
})
</script>