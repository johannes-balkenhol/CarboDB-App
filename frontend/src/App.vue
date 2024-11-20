<script setup>
import { RouterLink, RouterView } from 'vue-router'
import TheHeader from "@/components/TheHeader.vue";

</script>

<template>
  <TheHeader>
    <h1 class="h1">Carboxylases</h1>
  </TheHeader>
  <div class="page-margin">
    <h1>Hmmer search</h1>
    <RouterView />
  </div>
</template>

<style scoped>
.page-margin {
  text-align: left;
  width: 80vw;
  margin: 0 auto;
}
</style>
