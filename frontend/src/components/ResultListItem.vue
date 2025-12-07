<template>
  <tr>
    <td>{{ sequenceId }}</td>
    <td>
      <li v-for="item in this.result['Pfam hits']">
        {{ item ? item.pfam_accession : "" }}
      </li>
    </td>
    <td>
      <li v-for="item in this.result['Prosite hits']">
        {{ item ? item.prosite_accession : "" }}
      </li>
    </td>
    <td>
      <li v-for="item in this.result['Andom hits']">
        {{ item ? item.pfam_accession : "" }}
      </li>
    </td>
  </tr>
    
</template>

<script>
  export default {
    name: "ResultListItem", 
      props: {
        sequenceId: {
          type: String,
          required: true,
        },
        result: {
          type: Object,
          required: true,
        },
    }
   }
</script>