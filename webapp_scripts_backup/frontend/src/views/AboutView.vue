<template>
  <div class="about-view">
    <h1>ℹ️ About CarboxyPred</h1>
    
    <div class="about-content">
      <section class="about-section">
        <h2>🧬 What is CarboxyPred?</h2>
        <p>
          CarboxyPred is a machine learning-based platform for predicting CO₂-fixing carboxylase enzymes 
          from protein sequences. It can classify sequences into 25 different EC classes and predict 
          Michaelis constant (Km) values for bicarbonate.
        </p>
      </section>

      <section class="about-section">
        <h2>🔬 Models</h2>
        <div class="model-list">
          <div class="model-item">
            <h3>Binary Classifier v3</h3>
            <p>Random Forest model trained on all carboxylase sequences to identify CO₂-fixing enzymes</p>
          </div>
          <div class="model-item">
            <h3>Binary Classifier v5</h3>
            <p>Specialized model trained only on 14 EC classes with consensus predictions</p>
          </div>
          <div class="model-item">
            <h3>EC Classifier</h3>
            <p>Multi-class classifier for 25 carboxylase EC numbers</p>
          </div>
          <div class="model-item">
            <h3>Km Predictor</h3>
            <p>EC-conditional regression model for Km prediction (Pearson R = 0.975)</p>
          </div>
        </div>
      </section>

      <section class="about-section">
        <h2>📊 Features</h2>
        <p>447 sequence features are extracted including:</p>
        <ul>
          <li>Amino acid composition (20 features)</li>
          <li>Dipeptide frequencies (400 features)</li>
          <li>Catalytic residue distribution (invariant features)</li>
          <li>Enzyme-specific motifs</li>
          <li>Physicochemical properties</li>
        </ul>
      </section>

      <section class="about-section">
        <h2>📚 Database</h2>
        <p>
          The database contains 695,384 carboxylase sequences from UniProt with:
        </p>
        <ul>
          <li>690,130 high-confidence CO₂ enzyme predictions</li>
          <li>Evidence-based EC annotations from multiple sources</li>
          <li>Experimental Km values from BRENDA</li>
          <li>Predicted Km values for all sequences</li>
        </ul>
      </section>

      <section class="about-section">
        <h2>📖 Citation</h2>
        <p class="citation">
          If you use CarboxyPred in your research, please cite:<br>
          <em>[Citation pending publication]</em>
        </p>
      </section>

      <section class="about-section">
        <h2>📧 Contact</h2>
        <p>
          University of Würzburg<br>
          Department of Bioinformatics<br>
          Germany
        </p>
      </section>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.about-view {
  max-width: 900px;
  margin: 0 auto;
  padding: 40px 20px;
}

h1 {
  color: #2d3748;
  margin-bottom: 30px;
}

.about-content {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.about-section {
  margin-bottom: 30px;
  padding-bottom: 30px;
  border-bottom: 1px solid #e2e8f0;
}

.about-section:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.about-section h2 {
  color: #2d3748;
  font-size: 1.3rem;
  margin-bottom: 15px;
}

.about-section p {
  color: #4a5568;
  line-height: 1.7;
}

.about-section ul {
  color: #4a5568;
  padding-left: 25px;
  line-height: 1.8;
}

.model-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.model-item {
  background: #f7fafc;
  padding: 15px;
  border-radius: 8px;
}

.model-item h3 {
  color: #667eea;
  font-size: 0.95rem;
  margin: 0 0 8px 0;
}

.model-item p {
  font-size: 0.85rem;
  margin: 0;
  color: #718096;
}

.citation {
  background: #f7fafc;
  padding: 15px;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}
</style>
