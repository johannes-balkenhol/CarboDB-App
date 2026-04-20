<template>
  <div class="home-view">
    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-content">
        <h1>🧬 CarboxyPred</h1>
        <p class="hero-subtitle">CO₂-Fixing Enzyme Prediction Platform</p>
        <p class="hero-description">
          Identify carboxylases and predict their EC class and Km values using machine learning models trained on 695,000+ sequences
        </p>
        <div class="hero-stats">
          <div class="hero-stat">
            <span class="stat-number">695K+</span>
            <span class="stat-label">Sequences Analyzed</span>
          </div>
          <div class="hero-stat">
            <span class="stat-number">25</span>
            <span class="stat-label">EC Classes</span>
          </div>
          <div class="hero-stat">
            <span class="stat-number">97.5%</span>
            <span class="stat-label">Km Correlation</span>
          </div>
        </div>
        <div class="hero-actions">
          <router-link to="/analysis" class="btn-primary">
            🔬 Start Analysis
          </router-link>
          <router-link to="/database" class="btn-secondary">
            📊 Browse Database
          </router-link>
        </div>
      </div>
    </section>

    <!-- Features Overview -->
    <section class="features-section">
      <h2>🎯 What CarboxyPred Can Do</h2>
      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon">🧪</div>
          <h3>Binary Classification</h3>
          <p>Two-stage prediction (v3 + v5) to identify CO₂-fixing enzymes with high confidence consensus</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">🏷️</div>
          <h3>EC Classification</h3>
          <p>Predict enzyme class from 25 carboxylase EC numbers with confidence scores</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">📈</div>
          <h3>Km Prediction</h3>
          <p>Estimate Michaelis constant (Km) values in µM using EC-conditional regression</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">🔗</div>
          <h3>Database Matching</h3>
          <p>Find similar sequences with experimental Km values from our curated database</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">📋</div>
          <h3>Batch Analysis</h3>
          <p>Upload FASTA files for batch prediction with downloadable TSV results</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">🗄️</div>
          <h3>Database Browser</h3>
          <p>Search and explore 690K+ predicted carboxylases with filters and evidence</p>
        </div>
      </div>
    </section>

    <!-- Example Sequences -->
    <section class="examples-section">
      <h2>🧬 Try Example Sequences</h2>
      <p class="section-subtitle">Click to copy and paste into the Analysis page</p>
      <div class="examples-grid">
        <div class="example-card" @click="copyExample('rubisco')">
          <div class="example-header">
            <span class="example-icon">🌿</span>
            <h3>RuBisCO (4.1.1.39)</h3>
          </div>
          <p class="example-description">Ribulose-1,5-bisphosphate carboxylase - Key enzyme in Calvin cycle</p>
          <div class="example-info">
            <span>475 aa</span>
            <span>Spinach</span>
          </div>
          <pre class="example-sequence">MSPQTETKASVGFKAGVKDYKLTYYTPEYETKDTDILAAFRVTPQPGVPPEEAGAAVAAESSTGTWTTVWTDGLTSLDRYKGRCYHIEPVAGEENQYICYVAYPLDLFEEGSVTNMFTSIVGNVFGFKALRALRLEDLRIPVAYVKTFQGPPHGIQVERDKLNKYGRPLLGCTIKPKLGLSAKNYGRAVYECLRGGLDFTKDDENVNSQPFMRWRDRFLFCAEALYKAQAETGEIKGHYLNATAGTCEEMMKRAVFARELGVPIVMHDYLTGGFTANTSLSHYCRDNGLLLHIHRAMHAVIDRQKNHGMHFRVLAKALRLSGGDHIHSGTVVGKLEGERDITLGFVDLLRDDFIEKDRSRGIYFTQDWVSLPGVLPVASGGIHVWHMPALTEIFGDDSVLQFGGGTLGHPWGNAPGAVANRVALEACVQARNEGRDLAREGNTIIREATKVPELAAACEVWKEIKFEFD</pre>
          <span class="copy-hint">📋 Click to copy</span>
        </div>
        
        <div class="example-card" @click="copyExample('pepc')">
          <div class="example-header">
            <span class="example-icon">🌾</span>
            <h3>PEPC (4.1.1.31)</h3>
          </div>
          <p class="example-description">Phosphoenolpyruvate carboxylase - C4 photosynthesis enzyme</p>
          <div class="example-info">
            <span>966 aa</span>
            <span>Maize</span>
          </div>
          <pre class="example-sequence">MASERHHSHLHQRTQDRFASAASKDLSSRLIDASITPELDQLLAEFDESHDEEVRKLMAKYGDPVHIAGDLISDGGHHEALFRGCVSDLGFQNIFKYSQVIYDDQIEKLIDWQRRSGLGAKLEERLDIITEIPQSTLAVHSHLITKPEELASLMAKFRAISELFRPDVVQATGKDIFEIALGDPGELVPPSKLPMVDKMDQFVLVSPLLQQILKDQQFMQIDSGQGSPNASEWVRQRISAMIKRLENLPEDKFQDAAKNRFSKPIPFCFSGAVKPSDVKDITKQVERQIYRLVPGYTFTEEFHSKQLLEAKQGTGSDVQEVLKAFFLSYLKQKMGHYKFFSDVKAEFEQQERLVARLAQRVLKSQGPVPSRAEQLDWILRTRQLISLEQLTREQLREMSRNLERMRDELNDDKRRYDTIERLLDEVNEIQRSGIDHYLGQSLLQSEYAAHYRGAAEAVFAKTLTRLTEDIDTAMIASFQKLATLLGCEVPVTGSYRLRNDLVFTMQFLGHAGGVLDGRPYDGSELVRKWLGELGVDIDTIAPQLSIPLFHHDAYTDEDPLLLVLGSSLLRGQVLQKVGGPLHIIGDRLVLCDGKVTSGNPSRLDALFQEHYKADLPAQNVSVLQIDGKEMVFSGTDPEAVAQAYRSLFPLLACNRPLTGLTALYNALQACDNPQAHVLLKKLLAAYTEGEPNPSNAQELFADSKYGVSEETLIASVAKQALEYAKSQGITLFATQKVLKQVGLQTSDSETQVTIEKFKNALGEQISEVKLSMKLTRDMSGISADFEYLLSRVKGKPFAAVPTLNTPFYLKGAFGKNFCKEIGPVPVDVWVLAACLVRDPSIPLEAAREILQENGIDHAFKYIEKVSMSPYSPTRMADLVQVTLSKNAGIINVAMGPVPDGEVWRTEAFGHFIEQFFSDLNVQAYPLVGLSITQRLVRNVSSRLAEESGIVVVAATGQMSKLPADMAETIQAAERKLGFNVLVPTNIGGTNVTQLQETLQLFDRLGSIHSYDLQFLLRLLREGANSFTTEGDPTTEAAGSQ</pre>
          <span class="copy-hint">📋 Click to copy</span>
        </div>

        <div class="example-card" @click="copyExample('ca')">
          <div class="example-header">
            <span class="example-icon">💧</span>
            <h3>Carbonic Anhydrase (4.2.1.1)</h3>
          </div>
          <p class="example-description">CO₂ hydration enzyme - Important in CO₂ transport</p>
          <div class="example-info">
            <span>260 aa</span>
            <span>Human</span>
          </div>
          <pre class="example-sequence">MSHHWGYGKHNGPEHWHKDFPIAKGERQSPVDIDTHTAKYDPSLKPLSVSYDQATSLRILNNGHAFNVEFDDSQDKAVLKGGPLDGTYRLIQFHFHWGSLDGQGSEHTVDKKKYAAELHLVHWNTKYGDFGKAVQQPDGLAVLGIFLKVGSAKPGLQKVVDVLDSIKTKGKSADFTNFDPRGLLPESLDYWTYPGSLTTPPLLECVTWIVLKEPISVSSEQVLKFRKLNFNGEGEPEELMVDNWRPAQPLKNRQIKASFK</pre>
          <span class="copy-hint">📋 Click to copy</span>
        </div>

        <div class="example-card" @click="copyExample('accA')">
          <div class="example-header">
            <span class="example-icon">🧫</span>
            <h3>Acetyl-CoA Carboxylase (6.4.1.2)</h3>
          </div>
          <p class="example-description">Biotin-dependent carboxylase - Fatty acid biosynthesis</p>
          <div class="example-info">
            <span>319 aa</span>
            <span>E. coli</span>
          </div>
          <pre class="example-sequence">MLNVLQRHEAVTFDDPFVFMEGGACAGQRLPKGLADINKSRPAEAALKLDTTLNKELRDIIVNLGIAERIEVKVIGPYPDRPEDPNLDKIARELGIQVADGVKTVTNGSGIMSVPIGATSQSVVKSMAEDKAGVMVIGPVPGKIGQVIRDVLAGRQGADMVFAGYQVQGGAGRVLKEDIDVAMEKFGYDWITGEFPRDQILQALNGQAIPLMVVEETKVHFSDTLAEPKLIIGPIGKLVEKSAEVGEKYKVEVEDGVLVTGMVSGTMGQEMTVNNHQFFITGEKGKAVGQTVRKTFHEDIHAALQHAATQIGEIAVIAMCPEEMSVSTYQAILDMIVQNV</pre>
          <span class="copy-hint">📋 Click to copy</span>
        </div>
      </div>
    </section>

    <!-- How It Works -->
    <section class="workflow-section">
      <h2>🔄 How It Works</h2>
      <div class="workflow-steps">
        <div class="workflow-step">
          <div class="step-number">1</div>
          <h3>Input Sequence</h3>
          <p>Paste your protein sequence or upload a FASTA file</p>
        </div>
        <div class="workflow-arrow">→</div>
        <div class="workflow-step">
          <div class="step-number">2</div>
          <h3>Feature Extraction</h3>
          <p>447 features computed: composition, dipeptides, motifs, catalytic residues</p>
        </div>
        <div class="workflow-arrow">→</div>
        <div class="workflow-step">
          <div class="step-number">3</div>
          <h3>ML Prediction</h3>
          <p>Random Forest models predict binary class, EC, and Km</p>
        </div>
        <div class="workflow-arrow">→</div>
        <div class="workflow-step">
          <div class="step-number">4</div>
          <h3>Results & Match</h3>
          <p>Get predictions with similar sequences from database</p>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="cta-section">
      <h2>Ready to Analyze?</h2>
      <p>Upload your sequences and get predictions in seconds</p>
      <router-link to="/analysis" class="btn-large">
        🚀 Start Prediction
      </router-link>
    </section>

    <!-- Copied notification -->
    <div v-if="showCopied" class="copied-notification">
      ✓ Sequence copied to clipboard!
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const showCopied = ref(false)

const exampleSequences = {
  rubisco: 'MSPQTETKASVGFKAGVKDYKLTYYTPEYETKDTDILAAFRVTPQPGVPPEEAGAAVAAESSTGTWTTVWTDGLTSLDRYKGRCYHIEPVAGEENQYICYVAYPLDLFEEGSVTNMFTSIVGNVFGFKALRALRLEDLRIPVAYVKTFQGPPHGIQVERDKLNKYGRPLLGCTIKPKLGLSAKNYGRAVYECLRGGLDFTKDDENVNSQPFMRWRDRFLFCAEALYKAQAETGEIKGHYLNATAGTCEEMMKRAVFARELGVPIVMHDYLTGGFTANTSLSHYCRDNGLLLHIHRAMHAVIDRQKNHGMHFRVLAKALRLSGGDHIHSGTVVGKLEGERDITLGFVDLLRDDFIEKDRSRGIYFTQDWVSLPGVLPVASGGIHVWHMPALTEIFGDDSVLQFGGGTLGHPWGNAPGAVANRVALEACVQARNEGRDLAREGNTIIREATKVPELAAACEVWKEIKFEFD',
  pepc: 'MASERHHSHLHQRTQDRFASAASKDLSSRLIDASITPELDQLLAEFDESHDEEVRKLMAKYGDPVHIAGDLISDGGHHEALFRGCVSDLGFQNIFKYSQVIYDDQIEKLIDWQRRSGLGAKLEERLDIITEIPQSTLAVHSHLITKPEELASLMAKFRAISELFRPDVVQATGKDIFEIALGDPGELVPPSKLPMVDKMDQFVLVSPLLQQILKDQQFMQIDSGQGSPNASEWVRQRISAMIKRLENLPEDKFQDAAKNRFSKPIPFCFSGAVKPSDVKDITKQVERQIYRLVPGYTFTEEFHSKQLLEAKQGTGSDVQEVLKAFFLSYLKQKMGHYKFFSDVKAEFEQQERLVARLAQRVLKSQGPVPSRAEQLDWILRTRQLISLEQLTREQLREMSRNLERMRDELNDDKRRYDTIERLLDEVNEIQRSGIDHYLGQSLLQSEYAAHYRGAAEAVFAKTLTRLTEDIDTAMIASFQKLATLLGCEVPVTGSYRLRNDLVFTMQFLGHAGGVLDGRPYDGSELVRKWLGELGVDIDTIAPQLSIPLFHHDAYTDEDPLLLVLGSSLLRGQVLQKVGGPLHIIGDRLVLCDGKVTSGNPSRLDALFQEHYKADLPAQNVSVLQIDGKEMVFSGTDPEAVAQAYRSLFPLLACNRPLTGLTALYNALQACDNPQAHVLLKKLLAAYTEGEPNPSNAQELFADSKYGVSEETLIASVAKQALEYAKSQGITLFATQKVLKQVGLQTSDSETQVTIEKFKNALGEQISEVKLSMKLTRDMSGISADFEYLLSRVKGKPFAAVPTLNTPFYLKGAFGKNFCKEIGPVPVDVWVLAACLVRDPSIPLEAAREILQENGIDHAFKYIEKVSMSPYSPTRMADLVQVTLSKNAGIINVAMGPVPDGEVWRTEAFGHFIEQFFSDLNVQAYPLVGLSITQRLVRNVSSRLAEESGIVVVAATGQMSKLPADMAETIQAAERKLGFNVLVPTNIGGTNVTQLQETLQLFDRLGSIHSYDLQFLLRLLREGANSFTTEGDPTTEAAGSQ',
  ca: 'MSHHWGYGKHNGPEHWHKDFPIAKGERQSPVDIDTHTAKYDPSLKPLSVSYDQATSLRILNNGHAFNVEFDDSQDKAVLKGGPLDGTYRLIQFHFHWGSLDGQGSEHTVDKKKYAAELHLVHWNTKYGDFGKAVQQPDGLAVLGIFLKVGSAKPGLQKVVDVLDSIKTKGKSADFTNFDPRGLLPESLDYWTYPGSLTTPPLLECVTWIVLKEPISVSSEQVLKFRKLNFNGEGEPEELMVDNWRPAQPLKNRQIKASFK',
  accA: 'MLNVLQRHEAVTFDDPFVFMEGGACAGQRLPKGLADINKSRPAEAALKLDTTLNKELRDIIVNLGIAERIEVKVIGPYPDRPEDPNLDKIARELGIQVADGVKTVTNGSGIMSVPIGATSQSVVKSMAEDKAGVMVIGPVPGKIGQVIRDVLAGRQGADMVFAGYQVQGGAGRVLKEDIDVAMEKFGYDWITGEFPRDQILQALNGQAIPLMVVEETKVHFSDTLAEPKLIIGPIGKLVEKSAEVGEKYKVEVEDGVLVTGMVSGTMGQEMTVNNHQFFITGEKGKAVGQTVRKTFHEDIHAALQHAATQIGEIAVIAMCPEEMSVSTYQAILDMIVQNV'
}

async function copyExample(key) {
  const seq = exampleSequences[key]
  try {
    await navigator.clipboard.writeText(seq)
    showCopied.value = true
    setTimeout(() => showCopied.value = false, 2000)
  } catch (err) {
    console.error('Copy failed:', err)
  }
}
</script>

<style scoped>
.home-view {
  min-height: 100vh;
}

/* Hero */
.hero-section {
  background: linear-gradient(135deg, #1a365d 0%, #2c5282 50%, #38a169 100%);
  color: white;
  padding: 80px 20px;
  text-align: center;
}

.hero-content {
  max-width: 900px;
  margin: 0 auto;
}

.hero-section h1 {
  font-size: 3.5rem;
  margin: 0 0 15px 0;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
}

.hero-subtitle {
  font-size: 1.5rem;
  opacity: 0.95;
  margin-bottom: 20px;
}

.hero-description {
  font-size: 1.1rem;
  opacity: 0.9;
  max-width: 700px;
  margin: 0 auto 40px;
  line-height: 1.6;
}

.hero-stats {
  display: flex;
  justify-content: center;
  gap: 60px;
  margin-bottom: 40px;
}

.hero-stat {
  display: flex;
  flex-direction: column;
}

.stat-number {
  font-size: 2.5rem;
  font-weight: 700;
}

.stat-label {
  font-size: 0.9rem;
  opacity: 0.8;
}

.hero-actions {
  display: flex;
  gap: 20px;
  justify-content: center;
}

.btn-primary, .btn-secondary {
  padding: 15px 35px;
  border-radius: 10px;
  font-size: 1.1rem;
  font-weight: 600;
  text-decoration: none;
  transition: transform 0.2s, box-shadow 0.2s;
}

.btn-primary {
  background: linear-gradient(135deg, #48bb78, #38a169);
  color: white;
  box-shadow: 0 4px 15px rgba(72, 187, 120, 0.4);
}

.btn-secondary {
  background: rgba(255,255,255,0.15);
  color: white;
  border: 2px solid rgba(255,255,255,0.3);
}

.btn-primary:hover, .btn-secondary:hover {
  transform: translateY(-3px);
}

/* Features */
.features-section {
  padding: 60px 20px;
  background: #f7fafc;
}

.features-section h2 {
  text-align: center;
  font-size: 2rem;
  color: #2d3748;
  margin-bottom: 40px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 25px;
  max-width: 1200px;
  margin: 0 auto;
}

.feature-card {
  background: white;
  border-radius: 16px;
  padding: 30px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
  transition: transform 0.2s, box-shadow 0.2s;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}

.feature-icon {
  font-size: 2.5rem;
  margin-bottom: 15px;
}

.feature-card h3 {
  margin: 0 0 10px 0;
  color: #2d3748;
  font-size: 1.2rem;
}

.feature-card p {
  color: #718096;
  font-size: 0.95rem;
  line-height: 1.5;
  margin: 0;
}

/* Examples */
.examples-section {
  padding: 60px 20px;
  background: white;
}

.examples-section h2 {
  text-align: center;
  font-size: 2rem;
  color: #2d3748;
  margin-bottom: 10px;
}

.section-subtitle {
  text-align: center;
  color: #718096;
  margin-bottom: 40px;
}

.examples-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 25px;
  max-width: 1200px;
  margin: 0 auto;
}

.example-card {
  background: #f7fafc;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
  position: relative;
}

.example-card:hover {
  border-color: #667eea;
  background: #edf2f7;
}

.example-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.example-icon {
  font-size: 1.5rem;
}

.example-header h3 {
  margin: 0;
  color: #2d3748;
  font-size: 1.1rem;
}

.example-description {
  color: #718096;
  font-size: 0.9rem;
  margin-bottom: 10px;
}

.example-info {
  display: flex;
  gap: 15px;
  font-size: 0.8rem;
  color: #a0aec0;
  margin-bottom: 10px;
}

.example-sequence {
  background: #1a202c;
  color: #68d391;
  padding: 10px;
  border-radius: 6px;
  font-family: 'Monaco', monospace;
  font-size: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin: 0;
}

.copy-hint {
  position: absolute;
  bottom: 10px;
  right: 15px;
  font-size: 0.8rem;
  color: #667eea;
  opacity: 0;
  transition: opacity 0.2s;
}

.example-card:hover .copy-hint {
  opacity: 1;
}

/* Workflow */
.workflow-section {
  padding: 60px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.workflow-section h2 {
  text-align: center;
  font-size: 2rem;
  margin-bottom: 40px;
}

.workflow-steps {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
  flex-wrap: wrap;
}

.workflow-step {
  background: rgba(255,255,255,0.1);
  border-radius: 12px;
  padding: 25px;
  text-align: center;
  min-width: 180px;
  max-width: 220px;
}

.step-number {
  width: 40px;
  height: 40px;
  background: white;
  color: #667eea;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.2rem;
  margin: 0 auto 15px;
}

.workflow-step h3 {
  margin: 0 0 10px 0;
  font-size: 1rem;
}

.workflow-step p {
  margin: 0;
  font-size: 0.85rem;
  opacity: 0.9;
}

.workflow-arrow {
  font-size: 2rem;
  opacity: 0.5;
}

/* CTA */
.cta-section {
  padding: 80px 20px;
  text-align: center;
  background: #f7fafc;
}

.cta-section h2 {
  font-size: 2rem;
  color: #2d3748;
  margin-bottom: 10px;
}

.cta-section p {
  color: #718096;
  margin-bottom: 30px;
}

.btn-large {
  padding: 18px 50px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border-radius: 12px;
  font-size: 1.2rem;
  font-weight: 600;
  text-decoration: none;
  display: inline-block;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
  transition: transform 0.2s;
}

.btn-large:hover {
  transform: translateY(-3px);
}

/* Notification */
.copied-notification {
  position: fixed;
  bottom: 30px;
  right: 30px;
  background: #48bb78;
  color: white;
  padding: 15px 25px;
  border-radius: 10px;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(72, 187, 120, 0.4);
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from { transform: translateX(100px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

@media (max-width: 768px) {
  .hero-section h1 { font-size: 2.5rem; }
  .hero-stats { flex-direction: column; gap: 20px; }
  .hero-actions { flex-direction: column; }
  .workflow-arrow { display: none; }
  .workflow-steps { flex-direction: column; }
}
</style>
