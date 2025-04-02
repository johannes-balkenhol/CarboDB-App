<script setup>
import SearchMenu from '@/components/SearchMenu.vue';
import ResultList from '@/components/ResultList.vue';
import { useValidationStore } from '@/stores/validation';
import { ref } from 'vue';
import { useHmmerStore } from "@/stores/hmmer.js";


const validationStore = useValidationStore();
const searchCompleted = ref(false);
const searchResult = ref(null)

const runHmmerSearch = async () => {
  const hmmerStore = useHmmerStore();
      
  try {
    let result = await hmmerStore.runHmmerSearch(validationStore.fileId);
        
    if(searchResult){
      searchCompleted.value = true
      searchResult.value = result
    }
  } catch (error) {
      console.error("An error occurred during hmmerSearch:", error);
  }
  
};

</script>

<template>
  <main>
    <SearchMenu v-if="!searchCompleted" heading="Hmmer Search" :search-method="runHmmerSearch">
      <h1>Possibly insert settings for hmmer search</h1>
    </SearchMenu>
    <ResultList v-else :search-result="searchResult"></ResultList>
  </main>
</template>
