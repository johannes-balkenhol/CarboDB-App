<script>
export default {
  name: "TheHeader"
}
</script>

<template>
  <div class="header">
    <slot></slot>
  </div>
</template>

<style scoped>
.header {
  background: var(--color-header);
  min-height: 8vh;
  display: flex;
  align-items: center;
}
</style>