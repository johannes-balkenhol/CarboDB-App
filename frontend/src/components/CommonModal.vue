<template>
    <div class="overlay" @click.self="$emit('close')">
      <div class="modal-content">
        <div class="modal-button-wrapper">
            <button class="button-cancel" @click="$emit('close')">Close</button>
        </div>
        <slot></slot>       
      </div>
    </div>
</template>
  
<script>
  export default {
    name: "CommonModal"
  }
</script>
  