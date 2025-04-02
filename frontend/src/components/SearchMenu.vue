<template>
    <div class="common-search-wrapper">
      <h2 class="h2">{{ this.heading }}</h2>
      <template class="flexbox">
        <FileUpload></FileUpload>
        <div class="search-slot-wrapper">
          <slot></slot>
        </div>
      </template>
      <button class="button-action-big" @click.prevent="runSearch">Start search</button>
    </div>
</template>
  
<script>
import FileUpload from './FileUpload.vue';
  
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
    },
    searchMethod: {
      type: Function,
      required: true,
    }
  },
  methods: {
    async runSearch(){
      await this.searchMethod()
    }
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