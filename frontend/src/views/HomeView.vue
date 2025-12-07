<template>
  <main class="home-container">
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-content">
        <h1 class="hero-title">
          <span class="gradient-text">Carboxylase</span> Analysis Platform
        </h1>
        <p class="hero-subtitle">
          Comprehensive protein analysis for CO₂-fixing enzymes and carboxylases
        </p>
        <div class="hero-buttons">
          <router-link to="/analysis" class="btn btn-primary">
            🔬 Start Analysis
          </router-link>
          <a href="#about" class="btn btn-secondary">Learn More</a>
        </div>
      </div>
      <div class="hero-visual">
        <div class="molecule-animation">
          <div class="orbit orbit-1"><div class="electron"></div></div>
          <div class="orbit orbit-2"><div class="electron"></div></div>
          <div class="orbit orbit-3"><div class="electron"></div></div>
          <div class="nucleus">CO₂</div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="features" id="about">
      <h2 class="section-title">Analysis Features</h2>
      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon">🧬</div>
          <h3>Sequence Analysis</h3>
          <p>BioPython-powered analysis including molecular weight, isoelectric point, stability indices, and amino acid composition.</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">🎯</div>
          <h3>Domain Detection</h3>
          <p>HMMER search against Pfam HMM profiles to identify conserved protein domains and families.</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">🔍</div>
          <h3>Motif Scanning</h3>
          <p>Prosite pattern scanning for functional motifs, active sites, and post-translational modification sites.</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">📊</div>
          <h3>Visualizations</h3>
          <p>Interactive Plotly charts for amino acid composition, secondary structure, and hydrophobicity profiles.</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">🌐</div>
          <h3>InterPro Integration</h3>
          <p>Automatic lookup of domain annotations from Pfam, CATH, PANTHER, SMART, and more.</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">🔮</div>
          <h3>3D Structure</h3>
          <p>AlphaFold structure prediction viewer for visualizing protein architecture.</p>
        </div>
      </div>
    </section>

    <!-- Carboxylase Families Section -->
    <section class="families">
      <h2 class="section-title">Carboxylase Enzyme Families</h2>
      <div class="families-grid">
        <div class="family-card rubisco">
          <h3>RuBisCO</h3>
          <p class="family-full">Ribulose-1,5-bisphosphate carboxylase/oxygenase</p>
          <p class="family-desc">The most abundant enzyme on Earth, responsible for carbon fixation in the Calvin cycle.</p>
          <div class="family-stats">
            <span>🌱 Plants, Cyanobacteria</span>
            <span>📏 ~550 kDa (Form I)</span>
          </div>
        </div>
        <div class="family-card pepc">
          <h3>PEPC</h3>
          <p class="family-full">Phosphoenolpyruvate carboxylase</p>
          <p class="family-desc">Key enzyme in C4 and CAM photosynthesis, fixes CO₂ to phosphoenolpyruvate.</p>
          <div class="family-stats">
            <span>🌾 C4 Plants</span>
            <span>📏 ~400 kDa</span>
          </div>
        </div>
        <div class="family-card acc">
          <h3>ACC</h3>
          <p class="family-full">Acetyl-CoA carboxylase</p>
          <p class="family-desc">Catalyzes the first committed step of fatty acid synthesis.</p>
          <div class="family-stats">
            <span>🦠 All organisms</span>
            <span>📏 ~250 kDa</span>
          </div>
        </div>
        <div class="family-card pcc">
          <h3>PCC</h3>
          <p class="family-full">Propionyl-CoA carboxylase</p>
          <p class="family-desc">Involved in odd-chain fatty acid and branched-chain amino acid metabolism.</p>
          <div class="family-stats">
            <span>🧫 Mitochondria</span>
            <span>📏 ~750 kDa</span>
          </div>
        </div>
        <div class="family-card vkgc">
          <h3>VKGC</h3>
          <p class="family-full">Vitamin K-dependent γ-carboxylase</p>
          <p class="family-desc">Post-translational modification enzyme for blood clotting factors.</p>
          <div class="family-stats">
            <span>🩸 ER membrane</span>
            <span>📏 ~94 kDa</span>
          </div>
        </div>
        <div class="family-card pc">
          <h3>PC</h3>
          <p class="family-full">Pyruvate carboxylase</p>
          <p class="family-desc">Anaplerotic enzyme replenishing TCA cycle intermediates.</p>
          <div class="family-stats">
            <span>🔋 Mitochondria</span>
            <span>📏 ~500 kDa</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Quick Start Section -->
    <section class="quickstart">
      <h2 class="section-title">Quick Start</h2>
      <div class="steps">
        <div class="step">
          <div class="step-number">1</div>
          <h4>Input Sequence</h4>
          <p>Paste your protein sequence in FASTA format or upload a file</p>
        </div>
        <div class="step-arrow">→</div>
        <div class="step">
          <div class="step-number">2</div>
          <h4>Run Analysis</h4>
          <p>Click "Run Full Analysis" to process with all tools</p>
        </div>
        <div class="step-arrow">→</div>
        <div class="step">
          <div class="step-number">3</div>
          <h4>Explore Results</h4>
          <p>Browse interactive results across multiple tabs</p>
        </div>
      </div>
      <router-link to="/analysis" class="btn btn-primary btn-large">
        🚀 Get Started Now
      </router-link>
    </section>
  </main>
</template>

<script setup>
</script>

<style scoped>
.home-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 20px;
}

/* Hero Section */
.hero {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
  padding: 60px 0;
  align-items: center;
  min-height: 70vh;
}

.hero-title {
  font-size: 3.5rem;
  font-weight: 800;
  line-height: 1.1;
  margin-bottom: 20px;
  color: #1a365d;
}

.gradient-text {
  background: linear-gradient(135deg, #2b6cb0, #38b2ac, #48bb78);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 1.3rem;
  color: #4a5568;
  margin-bottom: 30px;
  line-height: 1.6;
}

.hero-buttons {
  display: flex;
  gap: 15px;
}

.btn {
  padding: 14px 28px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 16px;
  text-decoration: none;
  transition: all 0.3s ease;
  display: inline-block;
}

.btn-primary {
  background: linear-gradient(135deg, #2b6cb0, #3182ce);
  color: white;
  box-shadow: 0 4px 15px rgba(43, 108, 176, 0.4);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(43, 108, 176, 0.5);
}

.btn-secondary {
  background: white;
  color: #2b6cb0;
  border: 2px solid #2b6cb0;
}

.btn-secondary:hover {
  background: #ebf8ff;
}

.btn-large {
  padding: 18px 40px;
  font-size: 18px;
}

/* Molecule Animation */
.hero-visual {
  display: flex;
  justify-content: center;
  align-items: center;
}

.molecule-animation {
  position: relative;
  width: 300px;
  height: 300px;
}

.nucleus {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #48bb78, #38b2ac);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  color: white;
  font-size: 20px;
  box-shadow: 0 0 30px rgba(72, 187, 120, 0.5);
}

.orbit {
  position: absolute;
  top: 50%;
  left: 50%;
  border: 2px dashed #cbd5e0;
  border-radius: 50%;
  animation: rotate 10s linear infinite;
}

.orbit-1 { width: 150px; height: 150px; margin: -75px 0 0 -75px; }
.orbit-2 { width: 220px; height: 220px; margin: -110px 0 0 -110px; animation-duration: 15s; animation-direction: reverse; }
.orbit-3 { width: 280px; height: 280px; margin: -140px 0 0 -140px; animation-duration: 20s; }

.electron {
  position: absolute;
  width: 16px;
  height: 16px;
  background: linear-gradient(135deg, #4299e1, #3182ce);
  border-radius: 50%;
  top: -8px;
  left: 50%;
  margin-left: -8px;
  box-shadow: 0 0 10px rgba(66, 153, 225, 0.6);
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Features Section */
.section-title {
  text-align: center;
  font-size: 2.2rem;
  color: #1a365d;
  margin-bottom: 40px;
}

.features {
  padding: 60px 0;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 25px;
}

.feature-card {
  background: white;
  padding: 30px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 30px rgba(0,0,0,0.12);
}

.feature-icon {
  font-size: 40px;
  margin-bottom: 15px;
}

.feature-card h3 {
  color: #1a365d;
  margin-bottom: 10px;
  font-size: 1.2rem;
}

.feature-card p {
  color: #718096;
  line-height: 1.6;
  font-size: 14px;
}

/* Families Section */
.families {
  padding: 60px 0;
  background: linear-gradient(180deg, transparent, #f7fafc);
  margin: 0 -20px;
  padding-left: 20px;
  padding-right: 20px;
}

.families-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.family-card {
  background: white;
  padding: 25px;
  border-radius: 12px;
  border-left: 4px solid #3182ce;
  box-shadow: 0 2px 10px rgba(0,0,0,0.06);
}

.family-card.rubisco { border-left-color: #48bb78; }
.family-card.pepc { border-left-color: #ed8936; }
.family-card.acc { border-left-color: #9f7aea; }
.family-card.pcc { border-left-color: #f56565; }
.family-card.vkgc { border-left-color: #ed64a6; }
.family-card.pc { border-left-color: #4299e1; }

.family-card h3 {
  font-size: 1.5rem;
  color: #1a365d;
  margin-bottom: 5px;
}

.family-full {
  font-size: 12px;
  color: #718096;
  font-style: italic;
  margin-bottom: 10px;
}

.family-desc {
  color: #4a5568;
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 15px;
}

.family-stats {
  display: flex;
  gap: 15px;
  font-size: 12px;
  color: #718096;
}

/* Quick Start */
.quickstart {
  padding: 60px 0;
  text-align: center;
}

.steps {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-bottom: 40px;
}

.step {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.08);
  width: 220px;
}

.step-number {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #2b6cb0, #3182ce);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: bold;
  margin: 0 auto 15px;
}

.step h4 {
  color: #1a365d;
  margin-bottom: 8px;
}

.step p {
  color: #718096;
  font-size: 13px;
}

.step-arrow {
  font-size: 30px;
  color: #cbd5e0;
}

/* Responsive */
@media (max-width: 1000px) {
  .hero { grid-template-columns: 1fr; text-align: center; }
  .hero-visual { display: none; }
  .features-grid, .families-grid { grid-template-columns: repeat(2, 1fr); }
  .steps { flex-direction: column; }
  .step-arrow { transform: rotate(90deg); }
}

@media (max-width: 600px) {
  .hero-title { font-size: 2.5rem; }
  .features-grid, .families-grid { grid-template-columns: 1fr; }
}
</style>
