<template>
  <h2>Detailed Results for {{ this.sequenceId }}</h2>
  <h3>Hmmer Search Results</h3>
  <ResultDetailItem 
    v-for="item in this.result['Pfam hits']"
    :accession-number="item.pfam_accession"
    :e-value="item.e_value"
  ></ResultDetailItem>
  
</template>

<script>
import ResultDetailItem from './ResultDetailItem.vue';

  export default {
    name: "ResultDetail",
    components: {
      ResultDetailItem
    },
      props: {
        sequenceId: {
          type: String,
          required: true,
        },
        result: {
          type: Object,
          required: true
        },
    },
   }
</script>