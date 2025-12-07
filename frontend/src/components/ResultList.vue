<template>
    <div class="common-wrapper">
      <div style="display: flex; justify-content: space-between;">
        <h2 class="h2">Results of your search</h2>
        <div>
          <slot></slot>
        </div>
      </div>
     
      <table class="full-width-table">
        <colgroup>
          <col style="width: 40%;">
          <col style="width: 20%;">
          <col style="width: 20%;">
          <col style="width: 20%;">
        </colgroup>
        <thead>
          <tr>
            <th>Sequence Id</th>
            <th>Pfam hits</th>
            <th>Prosite hits</th>
            <th>AnDom hits</th>
          </tr>
        </thead>
        <tbody>
          <result-list-item 
            v-for="(result, key) in searchResult" 
            :sequence-id="key"
            :result="result"
            @click="showDetails(key, result)"
            class="result-list-item"
          ></result-list-item>
        </tbody>
      </table>
      
       
    <CommonModal v-if="selectedResult" @close="selectedResult = null">
      <ResultDetail
        :sequenceId="this.sequenceId"
        :result="this.selectedResult"
      ></ResultDetail>
    </CommonModal>
    </div>
</template>
  
<script>
import CommonModal from './CommonModal.vue';
import ResultDetail from './ResultDetail.vue';
import ResultListItem from './ResultListItem.vue';
  
export default {
  name: "ResultList",
  components: {
    ResultListItem, CommonModal, ResultDetail
  },
  props:{
    searchResult: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      sequenceId: null,
      selectedResult: null
    }
  },
  methods: {
    showDetails(sequenceId, result) {
      this.sequenceId = sequenceId
      this.selectedResult = result
    }
  }
}   
</script>