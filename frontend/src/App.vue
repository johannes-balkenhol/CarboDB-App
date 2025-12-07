<script setup>
import { RouterLink, RouterView } from 'vue-router'
import TheHeader from "@/components/TheHeader.vue";
import Navigation from './components/Navigation.vue';

</script>

<template>
  <TheHeader>
    <h1 class="h1">Carboxylases</h1>
  </TheHeader>
  <Navigation></Navigation>

  <RouterView />
</template>