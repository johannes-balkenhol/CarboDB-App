<script>
export default {
  name: "TheHeader"
}
</script>

<template>
  <div class="header-spacer"></div>
  <div class="header">
    <slot></slot>
  </div>
</template>

<style scoped>
.header-spacer {
  background: var(--color-header-spacer);
  min-height: 3vh;
}

.header {
  background: var(--color-header);
  min-height: 10vh;
  display: flex;
  align-items: center;
}
</style>