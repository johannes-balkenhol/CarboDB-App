<template>
    <div class="common-search-wrapper">
      <h2 class="h2">{{ this.heading }}</h2>
      <template class="flexbox">
        <FileUpload></FileUpload>
        <div class="search-slot-wrapper">
          <slot></slot>
        </div>
      </template>
      <button class="button-action-big" @click.prevent="runHmmerSearch">Start search</button>
    </div>
</template>
  
<script>
import { useValidationStore } from '@/stores/validation';
import FileUpload from './FileUpload.vue';
import { useHmmerStore } from "@/stores/hmmer.js";
  
export default {
  name: "SearchMenu",
  components: { FileUpload },
  data() {
    return {
            
    }
  },
  props: {
    heading: {
      type: String, 
      required: true,
    }
  },
  setup() {
    const validationStore = useValidationStore();

    return { validationStore };
  },
  methods: {
    async runHmmerSearch() {
      const hmmerStore = useHmmerStore();
      
      try {
        let response = await hmmerStore.runHmmerSearch(this.validationStore.fileId);
        this.errors = hmmerStore.errors;
      } catch (error) {
        console.error("An error occurred during validation:", error);
      }
    },
            
  }

}
    
</script>
<style>
.common-search-wrapper {
  margin: 20px 0 0 30px;
}

.search-slot-wrapper {
  margin-left: 100px;
}
</style>