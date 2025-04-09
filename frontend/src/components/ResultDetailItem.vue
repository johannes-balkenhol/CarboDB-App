<template>
  <p>{{ this.accessionNumber }}</p>
  <div>
    {{ this.eValue }}
  </div>
  <img :src="image">     
</template>

<script>
  export default {
    name: "ResultDetailItem", 
      props: {
        accessionNumber: {
          type: String,
          required: true,
        },
        eValue: {
          type: Number,
        },
        image: {
          type: Blob
        }
    },
   }
</script>