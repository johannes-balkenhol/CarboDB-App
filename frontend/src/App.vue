<script setup>
import Navigation from './components/Navigation.vue'
</script>

<template>
  <div class="app-container">
    <Navigation />
    <main class="main-content">
      <RouterView />
    </main>
    <footer class="app-footer">
      <p>CarboxylaseDB © 2025 | Protein Analysis Platform for CO₂-Fixing Enzymes</p>
    </footer>
  </div>
</template>

<style>
/* Global App Styles */
:root {
  --color-primary: #38b2ac;
  --color-primary-dark: #319795;
  --color-secondary: #1a365d;
  --color-accent: #ed8936;
  --color-success: #48bb78;
  --color-background: #f0f4f8;
  --color-card: #ffffff;
  --color-text: #2d3748;
  --color-text-light: #718096;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--color-background);
  color: var(--color-text);
  line-height: 1.6;
}

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  padding-bottom: 40px;
}

.app-footer {
  background: var(--color-secondary);
  color: rgba(255, 255, 255, 0.7);
  text-align: center;
  padding: 20px;
  font-size: 13px;
}

/* Scrollbar styling */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}

/* Selection color */
::selection {
  background: var(--color-primary);
  color: white;
}
</style>
