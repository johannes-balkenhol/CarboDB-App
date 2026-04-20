<template>
  <header class="app-header">
    <div class="header-content">
      <div class="logo-section">
        <router-link to="/home" class="logo">
          <span class="logo-icon">🧬</span>
          <span class="logo-text">Carboxylase<span class="logo-highlight">DB</span></span>
        </router-link>
        <span class="tagline">CO₂ Fixation Analysis Platform</span>
      </div>
      <nav class="main-nav">
        <router-link to="/home" class="nav-link">
          <span class="nav-icon">🏠</span>
          <span>Home</span>
        </router-link>
        <router-link to="/analysis" class="nav-link">
          <span class="nav-icon">🔬</span>
          <span>Analysis</span>
        </router-link>
        <router-link to="/database" class="nav-link">
          <span class="nav-icon">📊</span>
          <span>Database</span>
        </router-link>
        
        <router-link to="/about" class="nav-link">
          <span class="nav-icon">ℹ️</span>
          <span>About</span>
        </router-link>
      </nav>
    </div>
  </header>
</template>

<script setup>
</script>

<style scoped>
.app-header {
  background: linear-gradient(135deg, #1a365d 0%, #234e82 50%, #2c5282 100%);
  padding: 0;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 70px;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 15px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: white;
}

.logo-icon {
  font-size: 28px;
}

.logo-text {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.logo-highlight {
  color: #48bb78;
}

.tagline {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  padding-left: 15px;
  border-left: 1px solid rgba(255, 255, 255, 0.3);
}

.main-nav {
  display: flex;
  gap: 5px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border-radius: 10px;
  text-decoration: none;
  color: rgba(255, 255, 255, 0.85);
  font-weight: 500;
  font-size: 14px;
  transition: all 0.2s ease;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-link.router-link-active {
  background: linear-gradient(135deg, #38b2ac, #319795);
  color: white;
  box-shadow: 0 4px 15px rgba(56, 178, 172, 0.4);
}

.nav-icon {
  font-size: 16px;
}

@media (max-width: 900px) {
  .header-content {
    flex-direction: column;
    height: auto;
    padding: 15px;
    gap: 15px;
  }
  .tagline {
    display: none;
  }
  .main-nav {
    flex-wrap: wrap;
    justify-content: center;
  }
  .nav-link span:not(.nav-icon) {
    display: none;
  }
  .nav-link {
    padding: 10px 14px;
  }
}
</style>
