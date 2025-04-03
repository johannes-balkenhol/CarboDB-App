<template>
    <div class="common-wrapper">
      <h2 class="h2">Results of your search</h2>
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
          <result-list-item v-for="(result, key) in searchResult" 
          :sequence-id="key"
          :result="result"></result-list-item>
        </tbody>
      </table>
      

    </div>
</template>
  
<script>
import ResultListItem from './ResultListItem.vue';
  
export default {
  name: "ResultList",
  components: {
    ResultListItem
  },
  props:{
    searchResult: {
      type: Object,
      required: true
    }
  }
}
    
</script>
<style>
.full-width-table {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
}

.full-width-table th,
.full-width-table td {
    text-align: left;
    border: 1px solid #ddd;
    padding: 8px;
}
</style>