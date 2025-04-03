<template>
  <button 
    class="button-action-big"
    :class="isLoading ? 'disabled' : ''"
    @click.prevent="runFunction"
  >
    <span class="loader" v-if="this.isLoading"></span>
    <span v-else>{{ this.label }}</span>
  </button>
</template>
  
<script>
  
export default {
  name: "CommonButton",
  data() {
    return {
      isLoading: false,    
    }
  },
  props: {
    function: {
      type: Function, 
      required: true,
    },
    label: {
      type: String,
      required: true,  
    }
  },
  methods: {
    async runFunction(){
      this.isLoading = true;
      try{
        await this.function();
      } finally {
        this.isLoading = false;
      }
    }
  }
}
    
</script>

<style>
.loader {
  width: 20px;
  height: 20px;
  border: 3px solid white;
  border-top: 3px solid transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  display: inline-block;
}

/* Loader Animation */
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>