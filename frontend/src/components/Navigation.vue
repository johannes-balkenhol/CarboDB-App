<script>
export default {
  name: "Navigation"
}
</script>

<template>
  <div class="navigation">
    <router-link class="navigation-button" to="/" >Home</router-link>
    <router-link class="navigation-button" to="/hmmer-search">Hmmer search</router-link>
    <router-link class="navigation-button" to="/blast-search">Blast search</router-link>
  </div>
</template>

<style scoped>
.navigation {
  height: 30px;
  display: flex;
  flex-direction: row;
  align-items: center;
  background-color: var(--color-navigation);
  
}

.navigation-button {
  height: 30px;
  color: var(--color-bright-white);
  font-size: medium;
  text-decoration: none;
  background: var(--color-navigation);
  border: none;
  margin-left: 10px;
}

.navigation-button:hover {
  color: var(--color-bright-white);
  background: var(--color-navigation-hover);
}
</style>