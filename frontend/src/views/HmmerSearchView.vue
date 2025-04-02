<script setup>
import SearchMenu from '@/components/SearchMenu.vue';
import { useValidationStore } from '@/stores/validation';
import { useHmmerStore } from "@/stores/hmmer.js";

const validationStore = useValidationStore();

const runHmmerSearch = async () => {
  const hmmerStore = useHmmerStore();
      
  try {
    let searchResult = await hmmerStore.runHmmerSearch(validationStore.fileId);
    console.log(searchResult)
        
    
  } catch (error) {
      console.error("An error occurred during hmmerSearch:", error);
  }
  
};

</script>

<template>
  <main>
    <SearchMenu heading="Hmmer Search" :search-method="runHmmerSearch">
      <h1>Possibly insert settings for hmmer search</h1>
    </SearchMenu>
  </main>
</template>
