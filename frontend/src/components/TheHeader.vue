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
  height: 100px;
  display: flex;
  align-items: center;
  margin-top: 10px;
}
</style>