<template>
    <div class="common-wrapper">
      <h2 class="h2">{{ this.heading }}</h2>
      <template class="flexbox">
        <FileUpload></FileUpload>
        <div class="search-slot-wrapper">
          <slot></slot>
        </div>
      </template>
      <common-button 
      :function="runSearch"
      :label=buttonLabel
      ></common-button>
    </div>
</template>
  
<script>
import FileUpload from './FileUpload.vue';
import CommonButton from './CommonButton.vue';
  
export default {
  name: "SearchMenu",
  components: { FileUpload, CommonButton },
  data() {
    return {
      buttonLabel: "Run Search"   
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
.search-slot-wrapper {
  margin-left: 100px;
}
</style>