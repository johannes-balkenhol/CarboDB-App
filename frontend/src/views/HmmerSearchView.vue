<script setup>
import SearchMenu from '@/components/SearchMenu.vue';
import ResultList from '@/components/ResultList.vue';
import CommonButton from '@/components/CommonButton.vue';
import { useValidationStore } from '@/stores/validation';
import { ref, computed } from 'vue';
import { useHmmerStore } from "@/stores/hmmer.js";


const validationStore = useValidationStore();
const hmmerStore = useHmmerStore();
let hasFileId = computed(() => validationStore.fileId.length > 0)
const searchCompleted = ref(false);
const searchResult = ref(null)
const newSearchButtonLabel = "New Hmmer search"
const downloadButtonLabel = "Download Results"

const runHmmerSearch = async () => { 
  try {
    let result = await hmmerStore.runHmmerSearch(validationStore.fileId);
        
    if(searchResult){
      searchCompleted.value = true;
      searchResult.value = result;
    }
  } catch (error) {
      console.error("An error occurred during hmmerSearch:", error);
  }
  
};

const runDownloadResults = async () => {
  await hmmerStore.runDownloadResults(validationStore.fileId)
};

const prepareToRunNewHmmerSearch = () => {
  searchCompleted.value = false;
  searchResult.value = null;
  validationStore.fileId = "";
};

</script>

<template>
  <main>
    <SearchMenu 
    v-if="!searchCompleted" 
      heading="Hmmer Search"
      :search-method="runHmmerSearch"
      :button-disabled="!hasFileId"
    >
      <h1>Possibly insert settings for hmmer search</h1>
    </SearchMenu>
    <ResultList v-else :search-result="searchResult">
      <CommonButton
        :label="newSearchButtonLabel"
        :function="prepareToRunNewHmmerSearch"
      ></CommonButton>
      <CommonButton 
        :label="downloadButtonLabel"
        :function="runDownloadResults"
      ></CommonButton>
    </ResultList>
  </main>
</template>
