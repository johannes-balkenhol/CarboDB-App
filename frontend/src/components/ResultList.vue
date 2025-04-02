<template>
    <div class="result-list-wrapper">
      <h2 class="h2">Results of your search</h2>
      <table>
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
  },
  data() {
    return {
            
    }
  },
  methods: {
    
            
  }

}
    
</script>