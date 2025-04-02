<template>
  <tr>
    <td>{{ sequenceId }}</td>
    <td>
      <li v-for="item in this.pfamHits">
        {{ item ? item.pfamAccession : "" }}
      </li>
    </td>
    <td>
      <li v-for="item in this.prositeHits">
        {{ item ? item.prositeAccession : "" }}
      </li>
    </td>
    <td>
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
        pfamHits: Array,
        prositeHits: Array, 
        andomHits: Array,
    }
   }
</script>