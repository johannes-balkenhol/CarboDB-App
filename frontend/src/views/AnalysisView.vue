<template>
  <div class="analysis-view">
    <!-- Input Section (shown when no results) -->
    <div v-if="!analysisResult && !batchResults.length" class="input-section">
      <div class="hero-section">
        <h1>🧬 Unified Sequence Analysis</h1>
        <p>Complete protein characterization: BioPython • HMMER • InterPro • AlphaFold • ML Predictions</p>
      </div>

      <div class="main-content">
        <div class="input-panel">
          <h3>Protein sequence (FASTA or plain):</h3>
          <textarea v-model="sequence" rows="12" placeholder=">RuBisCO_spinach
MSPQTETKASVGFKAGVKDYKLTYYTPEYETKDTDILAAFRVTPQPGVPPEEAGAAVAAE...

Paste one or more sequences in FASTA format"></textarea>
          
          <div class="input-actions">
            <button @click="uploadFile" class="upload-btn">📁 Upload FASTA</button>
            <input type="file" ref="fileInput" @change="handleFileUpload" accept=".fasta,.fa,.txt" hidden />
            <button @click="runAnalysis" class="analyze-btn" :disabled="isLoading">
              <span v-if="isLoading">⏳ {{ loadingStatus }}</span>
              <span v-else>🚀 Run Full Analysis</span>
            </button>
          </div>

          <p v-if="error" class="error">❌ {{ error }}</p>
        </div>

        <div class="pipeline-panel">
          <h3>Analysis Pipeline</h3>
          <div class="pipeline-steps">
            <div class="pipeline-step"><span class="step-icon">🤖</span><span>ML Predictions (EC, Km)</span></div>
            <div class="pipeline-step"><span class="step-icon">🔗</span><span>Database Nearest Neighbor</span></div>
            <div class="pipeline-step"><span class="step-icon">🧬</span><span>BioPython Analysis</span></div>
            <div class="pipeline-step"><span class="step-icon">🎯</span><span>HMMER/Pfam Search</span></div>
            <div class="pipeline-step"><span class="step-icon">🌐</span><span>InterPro Lookup</span></div>
            <div class="pipeline-step"><span class="step-icon">🔮</span><span>AlphaFold Structure</span></div>
          </div>
        </div>
      </div>

      <!-- Example Sequences Grid -->
      <div class="examples-section">
        <h3>🧪 Try Example Sequences</h3>
        <div class="examples-grid">
          <div v-for="(ex, key) in exampleSequences" :key="key" class="example-card" @click="loadExample(key)">
            <div class="example-header">
              <span class="example-icon">{{ ex.icon }}</span>
              <span class="example-name">{{ ex.name }}</span>
            </div>
            <div class="example-ec">EC {{ ex.ec }}</div>
            <div class="example-desc">{{ ex.description }}</div>
            <div class="example-meta">{{ ex.organism }} • {{ ex.length }} aa</div>
          </div>
        </div>
        <button @click="loadAllExamples" class="load-all-btn">📦 Load All Examples (Batch Analysis)</button>
      </div>
    </div>

    <!-- Batch Results Table (multiple sequences) -->
    <div v-else-if="batchResults.length > 1" class="batch-results">
      <div class="results-header">
        <h2>📊 Batch Results ({{ batchResults.length }} sequences)</h2>
        <div class="summary-stats">
          <span class="stat positive">✅ {{ summary.consensus_positive }} CO₂ positive</span>
          <span class="stat match">🔗 {{ summary.with_neighbor }} with DB match</span>
        </div>
        <div class="header-actions">
          <button @click="downloadResults" class="download-btn">📥 Download TSV</button>
          <button @click="newAnalysis" class="new-btn">🔄 New Analysis</button>
        </div>
      </div>

      <div class="results-table-container">
        <table class="results-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Length</th>
              <th>v3 Prob</th>
              <th>v5 Prob</th>
              <th>Consensus</th>
              <th>EC Predicted</th>
              <th>EC Conf</th>
              <th>Km Pred (µM)</th>
              <th>Nearest Match</th>
              <th>BRENDA Km</th>
              <th>BRENDA EC</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="result in batchResults" :key="result.id" 
                :class="{ 'consensus-positive': result.consensus }">
              <td class="seq-id">{{ result.id }}</td>
              <td>{{ result.length }}</td>
              <td :class="getProbClass(result.v3_prob)">{{ formatProb(result.v3_prob) }}</td>
              <td :class="getProbClass(result.v5_prob)">{{ formatProb(result.v5_prob) }}</td>
              <td>
                <span :class="['consensus-badge', result.consensus ? 'positive' : 'negative']">
                  {{ result.consensus ? '✓ Yes' : '✗ No' }}
                </span>
              </td>
              <td class="ec-cell">{{ result.ec_predicted || '-' }}</td>
              <td :class="getConfClass(result.ec_confidence)">{{ formatConf(result.ec_confidence) }}</td>
              <td class="km-cell">{{ formatKm(result.km_predicted_uM) }}</td>
              <td class="neighbor-cell">{{ result.nearest_neighbor?.id || '-' }}</td>
              <td class="brenda-km">{{ formatKm(result.nearest_neighbor?.km_experimental) }}</td>
              <td class="brenda-ec">{{ result.nearest_neighbor?.ec_verified || '-' }}</td>
              <td>
                <button @click="viewDetails(result)" class="view-btn">👁️ View</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Legend -->
      <div class="legend">
        <h4>Confidence Legend:</h4>
        <span class="legend-item"><span class="dot high"></span> High (≥80%)</span>
        <span class="legend-item"><span class="dot medium"></span> Medium (50-80%)</span>
        <span class="legend-item"><span class="dot low"></span> Low (&lt;50%)</span>
      </div>
    </div>

    <!-- Single Result Details View -->
    <div v-else-if="analysisResult || batchResults.length === 1" class="results-section">
      <!-- Use analysisResult or first batch result -->
      <div class="results-header">
        <div>
          <h1>Analysis Results</h1>
          <span v-if="uniprotId" class="uniprot-badge">UniProt: {{ uniprotId }}</span>
        </div>
        <div class="header-actions">
          <button @click="downloadResults" class="icon-btn" title="Download">📥</button>
          <button @click="newAnalysis" class="new-btn">🔄 New Analysis</button>
        </div>
      </div>

      <!-- ML Predictions Summary (NEW!) -->
      <div v-if="currentResult?.ml_predictions || currentResult?.ec_predicted" class="ml-summary">
        <div class="ml-card" :class="currentResult.consensus ? 'positive' : 'negative'">
          <span class="ml-icon">🎯</span>
          <div class="ml-content">
            <span class="ml-label">CO₂ Enzyme</span>
            <span class="ml-value">{{ currentResult.consensus ? 'Yes' : 'No' }}</span>
          </div>
        </div>
        <div class="ml-card">
          <span class="ml-icon">🔬</span>
          <div class="ml-content">
            <span class="ml-label">EC Class</span>
            <span class="ml-value">{{ currentResult.ec_predicted || '-' }}</span>
            <span class="ml-conf">{{ formatConf(currentResult.ec_confidence) }} conf</span>
          </div>
        </div>
        <div class="ml-card">
          <span class="ml-icon">⚗️</span>
          <div class="ml-content">
            <span class="ml-label">Km Predicted</span>
            <span class="ml-value">{{ formatKm(currentResult.km_predicted_uM) }} µM</span>
          </div>
        </div>
        <div class="ml-card" v-if="currentResult.nearest_neighbor">
          <span class="ml-icon">🔗</span>
          <div class="ml-content">
            <span class="ml-label">Nearest BRENDA</span>
            <span class="ml-value">{{ currentResult.nearest_neighbor.id }}</span>
            <span class="ml-conf">Km: {{ formatKm(currentResult.nearest_neighbor.km_experimental) }} µM</span>
          </div>
        </div>
      </div>

      <!-- Summary Cards -->
      <div class="summary-cards">
        <div class="summary-card"><span class="card-icon">⚖️</span><div><span class="card-value">{{ Math.round(displayResult.basic_properties?.molecular_weight || 0) }}</span><span class="card-label">Da</span></div></div>
        <div class="summary-card"><span class="card-icon">⚡</span><div><span class="card-value">{{ (displayResult.basic_properties?.isoelectric_point || 0).toFixed(1) }}</span><span class="card-label">pI</span></div></div>
        <div class="summary-card"><span class="card-icon">📏</span><div><span class="card-value">{{ displayResult.basic_properties?.length || 0 }}</span><span class="card-label">aa</span></div></div>
        <div v-if="alphafoldData?.has_structure" class="summary-card structure-ready"><span class="card-icon">🔮</span><div><span class="card-value">3D</span><span class="card-label">Ready</span></div></div>
      </div>

      <!-- Tabs -->
      <div class="tabs">
        <button v-for="tab in tabs" :key="tab.id" :class="['tab', { active: activeTab === tab.id }]" @click="selectTab(tab.id)">
          <span class="tab-icon">{{ tab.icon }}</span>
          {{ tab.label }}
        </button>
      </div>

      <!-- Tab Content -->
      <div class="tab-content">
        <!-- Properties Tab -->
        <div v-if="activeTab === 'properties'">
          <div class="properties-grid">
            <div class="property-card"><h3>Molecular Weight</h3><p class="value">{{ displayResult.basic_properties?.molecular_weight?.toFixed(2) }} Da</p></div>
            <div class="property-card"><h3>Isoelectric Point</h3><p class="value">{{ displayResult.basic_properties?.isoelectric_point?.toFixed(2) }}</p></div>
            <div class="property-card"><h3>Instability Index</h3><p class="value" :class="{ stable: displayResult.basic_properties?.instability_index < 40 }">{{ displayResult.basic_properties?.instability_index?.toFixed(1) }}<span class="stability-label">{{ displayResult.basic_properties?.instability_index < 40 ? 'Stable' : 'Unstable' }}</span></p></div>
            <div class="property-card"><h3>GRAVY Score</h3><p class="value">{{ displayResult.basic_properties?.gravy?.toFixed(3) }}<span class="stability-label">{{ displayResult.basic_properties?.gravy > 0 ? 'Hydrophobic' : 'Hydrophilic' }}</span></p></div>
            <div class="property-card"><h3>Aromaticity</h3><p class="value">{{ ((displayResult.basic_properties?.aromaticity || 0) * 100).toFixed(1) }}%</p></div>
            <div class="property-card"><h3>Charge at pH 7</h3><p class="value">{{ displayResult.basic_properties?.charge_at_pH7?.toFixed(1) }}</p></div>
          </div>
        </div>

        <!-- Composition Tab -->
        <div v-if="activeTab === 'composition'">
          <h2>Top Amino Acids</h2>
          <div class="aa-bars">
            <div v-for="(pct, aa) in displayResult.amino_acid_composition?.top_5" :key="aa" class="aa-bar">
              <span class="aa-label">{{ aa }}</span>
              <div class="bar-container"><div class="bar" :style="{ width: pct + '%' }"></div></div>
              <span class="aa-pct">{{ pct?.toFixed(1) }}%</span>
            </div>
          </div>
          <h2>Charge Distribution</h2>
          <div class="charge-grid">
            <div class="charge-card positive"><h4>Positive (R, K, H)</h4><p>{{ displayResult.charge_distribution?.positive_residues }} residues</p><span>{{ displayResult.charge_distribution?.positive_percent?.toFixed(1) }}%</span></div>
            <div class="charge-card negative"><h4>Negative (D, E)</h4><p>{{ displayResult.charge_distribution?.negative_residues }} residues</p><span>{{ displayResult.charge_distribution?.negative_percent?.toFixed(1) }}%</span></div>
            <div class="charge-card neutral"><h4>Neutral</h4><p>{{ displayResult.charge_distribution?.neutral_residues }} residues</p></div>
          </div>
        </div>

        <!-- 3D Structure Tab -->
        <div v-if="activeTab === 'structure'">
          <h2>Secondary Structure Prediction</h2>
          <div class="structure-grid">
            <div class="structure-card helix"><div class="struct-icon">🌀</div><h4>α-Helix</h4><p>{{ displayResult.secondary_structure?.helix_percent?.toFixed(1) }}%</p></div>
            <div class="structure-card sheet"><div class="struct-icon">📄</div><h4>β-Sheet</h4><p>{{ displayResult.secondary_structure?.sheet_percent?.toFixed(1) }}%</p></div>
            <div class="structure-card turn"><div class="struct-icon">↩️</div><h4>Turn</h4><p>{{ displayResult.secondary_structure?.turn_percent?.toFixed(1) }}%</p></div>
          </div>
          <div v-if="alphafoldData?.has_structure" class="alphafold-section">
            <h2>🔮 AlphaFold Predicted Structure</h2>
            <div class="viewer-container"><div id="molstar-viewer" class="molstar-viewer"></div></div>
            <div class="structure-actions">
              <a :href="alphafoldData.pdb_url" target="_blank" class="action-btn">📥 Download PDB</a>
              <a :href="alphafoldData.cif_url" target="_blank" class="action-btn">📥 Download mmCIF</a>
              <a :href="`https://alphafold.ebi.ac.uk/entry/${uniprotId}`" target="_blank" class="action-btn primary">🔗 AlphaFold DB</a>
            </div>
          </div>
          <div v-if="displayResult.hydrophobic_regions?.length" class="hydrophobic-section">
            <h2>Hydrophobic Regions</h2>
            <div v-for="(region, i) in displayResult.hydrophobic_regions" :key="i" class="hydro-region">
              <span class="region-pos">{{ region.start }}-{{ region.end }}</span>
              <code>{{ region.sequence }}</code>
              <span class="region-score">{{ region.score?.toFixed(2) }}</span>
            </div>
          </div>
        </div>

        <!-- Domains Tab -->
        <div v-if="activeTab === 'domains'">
          <h2>🎯 Pfam Domains (HMMER)</h2>
          <div v-if="domainResults?.pfam_hits?.length" class="domain-list">
            <div v-for="(hit, i) in domainResults.pfam_hits" :key="'pfam-'+i" class="domain-card pfam">
              <div class="domain-header"><span class="domain-id">{{ hit.accession }}</span><span class="domain-badge">Pfam</span></div>
              <div class="domain-info"><span class="evalue">E-value: {{ hit.e_value?.toExponential(2) }}</span></div>
            </div>
          </div>
          <p v-else class="no-results">No Pfam domains found</p>

          <h2>🏛️ SCOP Classification (Superfamily)</h2>
          <div v-if="getScop.length" class="domain-list">
            <div v-for="(item, i) in getScop" :key="'scop-'+i" class="domain-card scop">
              <div class="domain-header"><span class="domain-id">{{ item.accession }}</span><span class="domain-badge">SCOP</span></div>
              <p>{{ item.name }}</p>
            </div>
          </div>
          <p v-else class="no-results">No SCOP classifications found</p>

          <h2>🏛 CATH Classification</h2>
          <div v-if="getCath.length" class="domain-list">
            <div v-for="(item, i) in getCath" :key="'cath-'+i" class="domain-card cath">
              <div class="domain-header"><span class="domain-id">{{ item.accession }}</span><span class="domain-badge">CATH</span></div>
              <p>{{ item.name }}</p>
            </div>
          </div>
          <p v-else class="no-results">No CATH classifications found</p>

          <h2>🌐 Other Annotations</h2>
          <div v-if="getOtherAnnotations.length" class="domain-list">
            <div v-for="(item, i) in getOtherAnnotations" :key="'other-'+i" class="domain-card other">
              <div class="domain-header"><span class="domain-id">{{ item.accession }}</span><span class="domain-badge">{{ item.source_database }}</span></div>
              <p>{{ item.name }}</p>
            </div>
          </div>
          <p v-else class="no-results">No additional annotations</p>
        </div>

        <!-- Motifs Tab -->
        <div v-if="activeTab === 'motifs'">
          <h2>🔍 RuBisCO Motif Detection</h2>
          <div class="motifs-grid">
            <div class="motif-card">
              <h4>Catalytic Lysine (K..K)</h4>
              <span v-if="displayResult.rubisco_motifs?.catalytic_lysine?.found" class="found-badge">Found ({{ displayResult.rubisco_motifs.catalytic_lysine.count }})</span>
              <span v-else class="not-found-badge">Not Found</span>
              <div v-if="displayResult.rubisco_motifs?.catalytic_lysine?.matches?.length" class="matches">
                <code v-for="(m, i) in displayResult.rubisco_motifs.catalytic_lysine.matches.slice(0,3)" :key="i">{{ m.sequence }} ({{ m.start }}-{{ m.end }})</code>
              </div>
            </div>
            <div class="motif-card">
              <h4>PS00157 (RuBisCO signature)</h4>
              <span v-if="displayResult.rubisco_motifs?.PS00157?.found" class="found-badge">Found</span>
              <span v-else class="not-found-badge">Not Found</span>
            </div>
            <div class="motif-card">
              <h4>Loop 6 Region</h4>
              <span v-if="displayResult.rubisco_motifs?.loop6?.found" class="found-badge">Found</span>
              <span v-else class="not-found-badge">Not Found</span>
            </div>
          </div>
        </div>

        <!-- Charts Tab -->
        <div v-if="activeTab === 'charts'">
          <div class="charts-grid">
            <div class="chart-container"><canvas id="chart-composition"></canvas></div>
            <div class="chart-container"><canvas id="chart-structure"></canvas></div>
            <div class="chart-container"><canvas id="chart-hydropathy"></canvas></div>
            <div class="chart-container"><canvas id="chart-charge"></canvas></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue';

const sequence = ref('');
const fileInput = ref(null);
const isLoading = ref(false);
const loadingStatus = ref('');
const error = ref(null);
const activeTab = ref('properties');

const analysisResult = ref(null);
const batchResults = ref([]);
const summary = ref({ total: 0, consensus_positive: 0, with_neighbor: 0 });
const selectedResult = ref(null);

const uniprotId = ref(null);
const alphafoldData = ref(null);
const domainResults = ref(null);
const interproData = ref(null);

// Example sequences - 10 diverse carboxylases
const exampleSequences = {
  rubisco: {
    name: 'RuBisCO',
    ec: '4.1.1.39',
    icon: '🌿',
    description: 'Ribulose-1,5-bisphosphate carboxylase - Calvin cycle',
    organism: 'Spinach',
    length: 475,
    sequence: 'MSPQTETKASVGFKAGVKDYKLTYYTPEYETKDTDILAAFRVTPQPGVPPEEAGAAVAAESSTGTWTTVWTDGLTSLDRYKGRCYHIEPVAGEENQYICYVAYPLDLFEEGSVTNMFTSIVGNVFGFKALRALRLEDLRIPVAYVKTFQGPPHGIQVERDKLNKYGRPLLGCTIKPKLGLSAKNYGRAVYECLRGGLDFTKDDENVNSQPFMRWRDRFLFCAEALYKAQAETGEIKGHYLNATAGTCEEMMKRAVFARELGVPIVMHDYLTGGFTANTSLSHYCRDNGLLLHIHRAMHAVIDRQKNHGMHFRVLAKALRLSGGDHIHSGTVVGKLEGERDITLGFVDLLRDDFIEKDRSRGIYFTQDWVSLPGVLPVASGGIHVWHMPALTEIFGDDSVLQFGGGTLGHPWGNAPGAVANRVALEACVQARNEGRDLAREGNTIIREATKVPELAAACEVWKEIKFEFD'
  },
  pepc: {
    name: 'PEPC',
    ec: '4.1.1.31',
    icon: '🌽',
    description: 'Phosphoenolpyruvate carboxylase - C4 photosynthesis',
    organism: 'Maize',
    length: 966,
    sequence: 'MASERHHSHLHQRTQDRFASAASKDLSSRLIDASITPELDQLLAEFDESHDEEVRKLMAKYGDPVHIAGDLISDGGHHEALFRGCVSDLGFQNIFKYSQVIYDDQIEKLIDWQRRSGLGAKLEERLDIITEIPQSTLAVHSHLITKPEELASLMAKFRAISELFRPDVVQATGKDIFEIALGDPGELVPPSKLPMVDKMDQFVLVSPLLQQILKDQQFMQIDSGQGSPNASEWVRQRISAMIKRLENLPEDKFQDAAKNRFSKPIPFCFSGAVKPSDVKDITKQVERQIYRLVPGYTFTEEFHSKQLLEAKQGTGSDVQEVLKAFFLSYLKQKMGHYKFFSDVKAEFEQQERLVARLAQRVLKSQGPVPSRAEQLDWILRTRQLISLEQLTREQLREMSRNLERMRDELNDDKRRYDTIERLLDEVNEIQRSGIDHYLGQSLLQSEYAAHYRGAAEAVFAKTLTRLTEDIDTAMIASFQKLATLLGCEVPVTGSYRLRNDLVFTMQFLGHAGGVLDGRPYDGSELVRKWLGELGVDIDTIAPQLSIPLFHHDAYTDEDPLLLVLGSSLLRGQVLQKVGGPLHIIGDRLVLCDGKVTSGNPSRLDALFQEHYKADLPAQNVSVLQIDGKEMVFSGTDPEAVAQAYRSLFPLLACNRPLTGLTALYNALQACDNPQAHVLLKKLLAAYTEGEPNPSNAQELFADSKYGVSEETLIASVAKQALEYAKSQGITLFATQKVLKQVGLQTSDSETQVTIEKFKNALGEQISEVKLSMKLTRDMSGISADFEYLLSRVKGKPFAAVPTLNTPFYLKGAFGKNFCKEIGPVPVDVWVLAACLVRDPSIPLEAAREILQENGIDHAFKYIEKVSMSPYSPTRMADLVQVTLSKNAGIINVAMGPVPDGEVWRTEAFGHFIEQFFSDLNVQAYPLVGLSITQRLVRNVSSRLAEESGIVVVAATGQMSKLPADMAETIQAAERKLGFNVLVPTNIGGTNVTQLQETLQLFDRLGSIHSYDLQFLLRLLREGANSFTTEGDPTTEAAGSQ'
  },
  ca: {
    name: 'Carbonic Anhydrase',
    ec: '4.2.1.1',
    icon: '💧',
    description: 'CO₂ hydration enzyme - CO₂ transport',
    organism: 'Human',
    length: 260,
    sequence: 'MSHHWGYGKHNGPEHWHKDFPIAKGERQSPVDIDTHTAKYDPSLKPLSVSYDQATSLRILNNGHAFNVEFDDSQDKAVLKGGPLDGTYRLIQFHFHWGSLDGQGSEHTVDKKKYAAELHLVHWNTKYGDFGKAVQQPDGLAVLGIFLKVGSAKPGLQKVVDVLDSIKTKGKSADFTNFDPRGLLPESLDYWTYPGSLTTPPLLECVTWIVLKEPISVSSEQVLKFRKLNFNGEGEPEELMVDNWRPAQPLKNRQIKASFK'
  },
  acc: {
    name: 'Acetyl-CoA Carboxylase',
    ec: '6.4.1.2',
    icon: '🧬',
    description: 'Fatty acid biosynthesis - biotin-dependent',
    organism: 'E. coli',
    length: 319,
    sequence: 'MLNVLQRHEAVTFDDPFVFMEGGACAGQRLPKGLADINKSRPAEAAHAIAKAWAQAGTTHIIISSGGSGGKGVRTAACDALQQAGERVDFVSLANADQMVDDLVNLSMGSSENVKQALRLMQQHGKQVFIGPDYVCRCGDNIGSIKSYMVNGTKLTNVFDDQMVNAVTVDDMEAFAKDLKPFVFIASGGGGRQEEGLRAIGKNLGGYQIFVLSQEQGNVKKEQIADVSARINAENPEIVVLVGGSGSGKEFLKTFGTHKDIQDVTKMVVDAQTILSKNLPIYHEKGLGLGNELEVLLVDDQQDFPGGDWPVLKNDVLLLDSRPRNPTANGTATTHVHLHDMLLPTILAQGYVVGTSDDNQARILKVLGIEPINAPVLAASDIRRSMMGEKQVECNVIGQKAQADLGFNLEGLEILSDLLDAVAETIKEE'
  },
  pcc: {
    name: 'Propionyl-CoA Carboxylase',
    ec: '6.4.1.3',
    icon: '🔬',
    description: 'Propionate metabolism - biotin-dependent',
    organism: 'Human',
    length: 728,
    sequence: 'MLRRSLWRLLLVCLASLTATAQTPPKPAVNSAVLQRRLITGFGANGFPSAALVQRLVADGHRVAITAPTSGGTTVLPTQPATTPVVSAPTVSHITPTAANPAHLSPGTPAAPAAAQAPPAQDTQAPAATARPSPAAAPPRWDPASPPGPRLLRVAAERGVPQLDLSRFSTPGGALIYGRARSGGVDLNTFRGQLLAALGCGVVLAAPRGTATAVISYDAYLPRSKLPVSQGVVVVGEPAGTGKTTTSVGLAQALHHDGFRVFCMHTPEYISGRIAEQLGVDFVIVASYSDSLEEPRNKRFIPTRAITAEVRREYEKQHPQVLDILTQCTTLVNGMTGHRVLVMKAEGETAALRNQGKVEAQVLVHGDRLYGLQIGIMVNRLGATHTAVVEGDEAEVFAALKKALQSGQEVLTARQSQILMGAAAKGCFAGMQGALLLENIKMLLNETPPAAPAVQILDKLKQLMAEQWKRLRDELLEFQPTCSHPKYAEPPQ'
  },
  pyr: {
    name: 'Pyruvate Carboxylase',
    ec: '6.4.1.1',
    icon: '⚗️',
    description: 'Gluconeogenesis - biotin-dependent',
    organism: 'Human',
    length: 1178,
    sequence: 'MLRAALVRRLCAASRAAVAASGRRPLLGTRGRAAVAVSPLRCSPGSPSKSPKHTSPQLKRLAAKRGEGPAQPSSVPPAAQSASGHLPLPPLHPQAPQPPPLSPQPMRSSILLAANAFLGCGHIYQGVMRELRSHSVHGFLALHPGKIVIADKGYRGTADGPKTHPGASAVQDSPALKDLETAVLGGKVNAFYTDNKQLGKTTKIVGKLANGSFPVSYLNFDDLIGMRDGPAEVPVGEPAPTSPLTVSKRSLLATLVAVGSAVLCGGLAVATVAEQQPEERVLAAPAEIRHFLESLKALRQANGTLVAGVVTGLNQLKQDQQLVLFEAYGSGNLCALGGRGCGAVVLANSPMPGSLPLSAAQQTRALRLAQELTVKSSEIVLYGPPGTGKTLLARAVAGQTSAFLDVPFLHSLMHALELRKYIRSGAALEQYYKINLEFSLFDNPQMADVLVNFLGSTAKYQFSAVNPKAAVVFLDSLPQTRLRSLLPTVREMLNQMHSADYLALVDDTGFSTSGVAMGGSMLAAGDPRDYVQPLHRDTKGVSEQALKVIATGEFAREQLRTMHRDVNGHGEVIAYLRYQGLGDVTVDTKGFIVQADPGKFAQVGPAVDIDPNLQFPVPMMRGGVLEEIAEMAKDYGYPVITKKQLVTAYNKSGVFIPVNAVGEDDLFFVNKGYQNNISGTTVHFNDDGETQFIASQCGAFGCYTASSQTVLMGLPQRLLSDIQQNAGLGLLHSLACKGTFQNVGLNQQFVESLVRNQNGTLHACRVKQTLEKVRQQLLAAEADGGGGGAAQLQRKNAEQVGDNETVNDLQKRFKELEKNGLL'
  },
  malic: {
    name: 'Malic Enzyme',
    ec: '1.1.1.40',
    icon: '🍎',
    description: 'Malate decarboxylation - NADP-dependent',
    organism: 'Human',
    length: 604,
    sequence: 'MAAAAAATLLRGVHGVPGSEAARVQGKQVVGALGTGINGFGLALAKEGKDVFITPDGQRLEVPKGLLRVTPNDGGITVPVATTTAIALDGTINHPNYTMNRALAAFQKAGYNIRHYPRPVDYDVAKLLRENPKGLIGVTTNPVSTFLDSLRQQMTERDCRFINKNPAWSHFREIYTAYEHKTRLGISPATGKIVEYLKENPNVHLYLYDVYNMPSLILRPVGHENEDLLNPLKEIEKKLFIFHDNPVASVRSLTDLAHFVNNDEKRNFDIQVKQIFFPGAAIQLYTGYNLPTQPLPQAEAEKLLRKNPNVTVITAAICPEEKLTQLYQRVGALAKKLSSLFSGFLIFVGAGFPGIDTGEMFSQSGVLNRKMKQFGNEFIPDFKNELYRRNIQTIQSGPLAITGDEEKQFIDHIVNQVLQEDSLGPTVNIRPSILTCIQCLKLGNPTFEAYRRQDVMRVVTDMLKKMVTASLGRGIFTNSMVTDIFGVNNALDYSRAEEFFNLGCDVEVITSGDPRSKAKYIQDYVVEMGTEAFQDYGNMIFKLICQAINQYPFGGGVKVDVNGNPVILTGTNFGFSMTDPTLFPGLVFTEQAMIDKHGATMVPPPMSGSDPFGDPLLTFRGRMRRDDVQRLLRDPSVIQELLKEAPVKPTGQQQQALGKHILLNAKDYLGVADWFNRP'
  },
  isocit: {
    name: 'Isocitrate Dehydrogenase',
    ec: '1.1.1.42',
    icon: '🔄',
    description: 'TCA cycle - NADP-dependent decarboxylation',
    organism: 'Human',
    length: 414,
    sequence: 'MSAAKAAAVSGSGPGTPQNIQGRKEYTPQAIAKEIEKAFETAKAEYKDGKKSVNPNCLLGVIKVYGPLGSGFRELSPLGIKVMVEKPRDARVKQAGDNLGVEVGTIVKIIENERDIPVHSAFSGDCATNVGDEGGFAPNILENKEGLELLKTAIGGKLKGDTKILYQVEHPVLGGDVLVTTIPGGTETYITQLADTFKPGKFFFEVLKEDEHIEEVVIQPSWSGQLVASDTDEDAARKIANFKDEKIKLAQAKGTVITDNPRTTAQAVENFLEKIIERTYDGKTQLVLKNPITIQFSATKEMGLNCLVFDATHAIQQGLAPYVKSVRGNPFKLTMNTAKVVPVIGGHSGVTILPLLEQMINLGVIATDKEYIPQSMLLAIAQELGLNPIVTASTWQIDGNRELFQETLKKLVEAKQKNVLIKHLNPKFKSFVKAAIHQHTGNKVVTVHGESLTLTSNKIGFMFLVGMGHQFVSNQMVLLLKNGDDQKLLELSSNLSLNKTQSEIQSATRIQSNNK'
  },
  formate: {
    name: 'Formate Dehydrogenase',
    ec: '1.2.1.2',
    icon: '📗',
    description: 'Formate oxidation - NAD-dependent',
    organism: 'Candida boidinii',
    length: 364,
    sequence: 'MKIVLVLYDAGKHAADEEKLYGCTENKLGIANWLKDQGHELITTSDKEGETSELDKHIPDADIIITTPFHPAYITKERLDKAKNLKLVVVAGVGSDHIDLDYINQTGKKISVLEVTGSNVVSVAEHVVMTMLVLVRNFVPAHEQIINHDWEVAAIAKDAYDIEGKTIATIGAGRIGYRVLERLLPFNPKELLYYDYQALPKEAEEKVGARRVENIEELVAQADIVTVNAPLHAGTKGLINKELLSKFKKGAWLVNTARGAICVAEDVAAALESGQLRGYGGDVWFPQPAPKDHPWRDMRNKYGAGNAMTPHYSGTTLDAQTRYAEGTKNILESFFTGKFDYRPQDIILLNGEYVTKAYGKHDKK'
  },
  oxalate: {
    name: 'Oxalate Decarboxylase',
    ec: '4.1.1.2',
    icon: '🧪',
    description: 'Oxalate degradation - manganese-dependent',
    organism: 'Bacillus subtilis',
    length: 385,
    sequence: 'MKKHIVAVDNPFANFGHHAHWEVINHQEMVPVAVSFNFPHPYYAEGKDPENGYLLNKDLQNQFVMTSEFLHEYWLENPGHQVTNSSVLQTHFDDTNTTMFPEHLPFNLNSDQFLEGNETVALFHQGARGLGPAHVLVFNHGGQGGGVTYAYPGAQFNETFWLKEDRDDPNGEHIAVNEWEHDGQGIQVFSTQSTRNPGAEHITYSEDGTVQGHLNPFHPLNSNYEFEVGPHTTLDTTTANPGLPVKTSALNAFAHHAIIGVDNPFANHGHHTNWEFLNEQLVPVAVTFNFPHPYYAKGNDSENGYLENKSLQNQYVMTPEFLQEYWLANPGHSITNSSVLQTHYDDTRTTIFPENFPFDLNSDKFQQGNAKIALFLQGAAVKLSPEHVLVFNHGGQGGGVTYAYPGEKFNEQFWLKDDVDNANGEHIAVNEWEHDGTGIAVFSTQSTRNPAAHITYSENGKVVGHLAPFHPLNSDFEFRVGPHETLQTQTANPGAPAQQSTLNAFAHHAIIGVDNPFANHGHHTNWEFLNEQLVPVAVTFNFPHPYYAKGNDSENGYLENKSLQNQY'
  }
};

const tabs = [
  { id: 'properties', label: 'Properties', icon: '📊' },
  { id: 'composition', label: 'Composition', icon: '🧬' },
  { id: 'structure', label: '3D Structure', icon: '🔮' },
  { id: 'domains', label: 'Domains', icon: '🎯' },
  { id: 'motifs', label: 'Motifs', icon: '🔍' },
  { id: 'charts', label: 'Charts', icon: '📈' }
];

// Computed
const currentResult = computed(() => {
  if (analysisResult.value) return analysisResult.value;
  if (batchResults.value.length === 1) return batchResults.value[0];
  return selectedResult.value;
});

const displayResult = computed(() => {
  return currentResult.value || {};
});

const getScop = computed(() => {
  if (!interproData.value?.results) return [];
  return interproData.value.results.filter(r => r.source_database === 'superfamily');
});

const getCath = computed(() => {
  if (!interproData.value?.results) return [];
  return interproData.value.results.filter(r => r.source_database === 'cathgene3d');
});

const getOtherAnnotations = computed(() => {
  if (!interproData.value?.results) return [];
  return interproData.value.results.filter(r => 
    !['superfamily', 'cathgene3d', 'pfam'].includes(r.source_database)
  );
});

// Methods
function loadExample(key) {
  sequence.value = `>${exampleSequences[key].name}_${exampleSequences[key].organism}\n${exampleSequences[key].sequence}`;
}

function loadAllExamples() {
  sequence.value = Object.entries(exampleSequences)
    .map(([key, ex]) => `>${ex.name}_${ex.organism}\n${ex.sequence}`)
    .join('\n');
}

function uploadFile() {
  fileInput.value?.click();
}

function handleFileUpload(event) {
  const file = event.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = (e) => { sequence.value = e.target.result; };
    reader.readAsText(file);
  }
}

function extractUniprotId(header) {
  const match = header.match(/sp\|([A-Z0-9]+)\|/) || header.match(/([A-Z][0-9][A-Z0-9]{3}[0-9])/);
  return match ? match[1] : null;
}

function parseSequences(input) {
  const sequences = [];
  const lines = input.trim().split('\n');
  let currentId = null;
  let currentSeq = [];

  for (const line of lines) {
    if (line.startsWith('>')) {
      if (currentId) sequences.push({ id: currentId, sequence: currentSeq.join('') });
      currentId = line.slice(1).split(/\s+/)[0];
      currentSeq = [];
    } else {
      currentSeq.push(line.replace(/\s/g, ''));
    }
  }
  if (currentId) sequences.push({ id: currentId, sequence: currentSeq.join('') });
  
  // Handle plain sequence (no header)
  if (sequences.length === 0 && input.trim()) {
    sequences.push({ id: 'query', sequence: input.replace(/\s/g, '') });
  }
  
  return sequences;
}

async function runAnalysis() {
  const seqs = parseSequences(sequence.value);
  if (seqs.length === 0) {
    error.value = 'Please enter a valid sequence';
    return;
  }

  isLoading.value = true;
  error.value = null;
  batchResults.value = [];
  analysisResult.value = null;

  try {
    if (seqs.length === 1) {
      // Single sequence - full analysis
      await runSingleAnalysis(seqs[0]);
    } else {
      // Multiple sequences - batch analysis
      await runBatchAnalysis(seqs);
    }
  } catch (e) {
    error.value = e.message;
  } finally {
    isLoading.value = false;
    loadingStatus.value = '';
  }
}

async function runSingleAnalysis(seq) {
  const cleanSeq = seq.sequence.replace(/[^A-Za-z]/g, '');
  uniprotId.value = extractUniprotId(seq.id);

  loadingStatus.value = 'Running BioPython analysis...';
  const res = await fetch('/api/analyze-sequence', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sequence: cleanSeq, id: seq.id })
  });
  const data = await res.json();
  if (!data.success) throw new Error(data.error);
  analysisResult.value = data.analysis;

  // Fetch AlphaFold
  if (uniprotId.value) {
    loadingStatus.value = 'Checking AlphaFold...';
    try {
      const afRes = await fetch(`/api/alphafold/${uniprotId.value}`);
      alphafoldData.value = await afRes.json();
    } catch (e) { console.warn('AlphaFold:', e); }

    loadingStatus.value = 'Fetching InterPro...';
    try {
      const ipRes = await fetch(`/api/interpro/${uniprotId.value}`);
      interproData.value = await ipRes.json();
    } catch (e) { console.warn('InterPro:', e); }
  }

  // Render 3D if available
  if (alphafoldData.value?.has_structure) {
    await nextTick();
    setTimeout(() => render3D(), 500);
  }
}

async function runBatchAnalysis(seqs) {
  loadingStatus.value = `Analyzing ${seqs.length} sequences...`;
  
  const fasta = seqs.map(s => `>${s.id}\n${s.sequence}`).join('\n');
  const res = await fetch('/api/predict-batch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ fasta })
  });
  const data = await res.json();
  
  if (!data.success) throw new Error(data.error);
  
  batchResults.value = data.results;
  summary.value = {
    total: data.results.length,
    consensus_positive: data.results.filter(r => r.consensus).length,
    with_neighbor: data.results.filter(r => r.nearest_neighbor).length
  };
}

async function viewDetails(result) {
  selectedResult.value = result;
  batchResults.value = [result]; // Switch to single view
  
  // Try to get more details
  uniprotId.value = extractUniprotId(result.id);
  if (uniprotId.value) {
    try {
      const afRes = await fetch(`/api/alphafold/${uniprotId.value}`);
      alphafoldData.value = await afRes.json();
    } catch (e) {}
  }
}

function render3D() {
  const container = document.getElementById('molstar-viewer');
  if (!container || !alphafoldData.value?.pdb_url) return;
  
  try {
    const viewer = window.$3Dmol.createViewer(container, { backgroundColor: 'white' });
    viewer.addModel(null, 'pdb');
    fetch(alphafoldData.value.pdb_url)
      .then(r => r.text())
      .then(pdb => {
        viewer.addModel(pdb, 'pdb');
        viewer.setStyle({}, { cartoon: { color: 'spectrum' } });
        viewer.zoomTo();
        viewer.render();
      });
  } catch (e) {
    console.error('3Dmol error:', e);
  }
}

function selectTab(tabId) {
  activeTab.value = tabId;
  if (tabId === 'structure' && alphafoldData.value?.has_structure) {
    nextTick(() => setTimeout(render3D, 100));
  }
}

function newAnalysis() {
  sequence.value = '';
  analysisResult.value = null;
  batchResults.value = [];
  selectedResult.value = null;
  alphafoldData.value = null;
  interproData.value = null;
  domainResults.value = null;
  error.value = null;
  activeTab.value = 'properties';
}

function downloadResults() {
  const rows = batchResults.value.map(r => [
    r.id, r.length, r.v3_prob, r.v5_prob, r.consensus,
    r.ec_predicted, r.ec_confidence, r.km_predicted_uM,
    r.nearest_neighbor?.id, r.nearest_neighbor?.km_experimental
  ]);
  const header = 'ID\tLength\tv3_prob\tv5_prob\tConsensus\tEC_pred\tEC_conf\tKm_pred\tNearest\tBRENDA_Km\n';
  const tsv = header + rows.map(r => r.join('\t')).join('\n');
  const blob = new Blob([tsv], { type: 'text/tsv' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'carboxypred_results.tsv';
  a.click();
}

// Formatting helpers
const formatProb = (p) => p != null ? (p * 100).toFixed(1) + '%' : '-';
const formatConf = (c) => c != null ? (c * 100).toFixed(0) + '%' : '-';
const formatKm = (k) => k != null ? k.toFixed(1) : '-';

const getProbClass = (p) => {
  if (p == null) return '';
  if (p >= 0.8) return 'prob-high';
  if (p >= 0.5) return 'prob-medium';
  return 'prob-low';
};

const getConfClass = (c) => {
  if (c == null) return '';
  if (c >= 0.8) return 'conf-high';
  if (c >= 0.5) return 'conf-medium';
  return 'conf-low';
};
</script>

<style scoped>
.analysis-view { max-width: 1400px; margin: 0 auto; padding: 20px; }

/* Hero */
.hero-section { text-align: center; margin-bottom: 30px; }
.hero-section h1 { font-size: 2.5rem; color: #1a365d; margin-bottom: 10px; }
.hero-section p { color: #718096; font-size: 1.1rem; }

/* Main content grid */
.main-content { display: grid; grid-template-columns: 2fr 1fr; gap: 30px; margin-bottom: 40px; }
.input-panel { background: white; border-radius: 16px; padding: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }
.input-panel h3 { margin-bottom: 15px; color: #2d3748; }
.input-panel textarea { width: 100%; border: 2px solid #e2e8f0; border-radius: 10px; padding: 15px; font-family: monospace; font-size: 12px; resize: vertical; }
.input-panel textarea:focus { border-color: #667eea; outline: none; }

.input-actions { display: flex; gap: 15px; margin-top: 20px; }
.upload-btn { background: #f7fafc; border: 2px dashed #cbd5e0; padding: 12px 20px; border-radius: 10px; cursor: pointer; }
.analyze-btn { background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; padding: 12px 30px; border-radius: 10px; font-weight: 600; cursor: pointer; flex: 1; }
.analyze-btn:disabled { opacity: 0.7; cursor: not-allowed; }

/* Pipeline panel */
.pipeline-panel { background: white; border-radius: 16px; padding: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }
.pipeline-steps { display: flex; flex-direction: column; gap: 12px; }
.pipeline-step { display: flex; align-items: center; gap: 12px; padding: 12px 16px; background: #f7fafc; border-radius: 10px; border-left: 3px solid #667eea; }
.step-icon { font-size: 1.2rem; }

/* Examples */
.examples-section { background: white; border-radius: 16px; padding: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }
.examples-section h3 { text-align: center; margin-bottom: 20px; }
.examples-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
.example-card { background: #f7fafc; border-radius: 12px; padding: 15px; cursor: pointer; transition: all 0.2s; border: 2px solid transparent; }
.example-card:hover { border-color: #667eea; transform: translateY(-2px); }
.example-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.example-icon { font-size: 1.5rem; }
.example-name { font-weight: 600; color: #2d3748; }
.example-ec { color: #667eea; font-size: 0.9rem; font-weight: 500; }
.example-desc { color: #718096; font-size: 0.8rem; margin: 5px 0; }
.example-meta { color: #a0aec0; font-size: 0.75rem; }
.load-all-btn { display: block; margin: 0 auto; background: #667eea; color: white; border: none; padding: 12px 30px; border-radius: 10px; cursor: pointer; font-weight: 500; }

/* Batch Results */
.batch-results { background: white; border-radius: 16px; padding: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }
.results-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 15px; }
.results-header h2 { margin: 0; color: #2d3748; }
.summary-stats { display: flex; gap: 20px; }
.stat { padding: 8px 16px; border-radius: 20px; font-size: 0.9rem; }
.stat.positive { background: #c6f6d5; color: #22543d; }
.stat.match { background: #bee3f8; color: #2a4365; }
.header-actions { display: flex; gap: 10px; }
.download-btn, .new-btn { padding: 10px 20px; border-radius: 8px; border: none; cursor: pointer; font-weight: 500; }
.download-btn { background: #edf2f7; color: #4a5568; }
.new-btn { background: #667eea; color: white; }

/* Table */
.results-table-container { overflow-x: auto; }
.results-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.results-table th { background: #f7fafc; padding: 12px 10px; text-align: left; font-weight: 600; color: #4a5568; border-bottom: 2px solid #e2e8f0; white-space: nowrap; }
.results-table td { padding: 12px 10px; border-bottom: 1px solid #e2e8f0; }
.results-table tr:hover { background: #f7fafc; }
.results-table tr.consensus-positive { background: rgba(72, 187, 120, 0.05); }
.seq-id { font-weight: 600; color: #2d3748; }
.prob-high { color: #38a169; font-weight: 600; }
.prob-medium { color: #d69e2e; font-weight: 500; }
.prob-low { color: #e53e3e; }
.conf-high { color: #38a169; font-weight: 600; }
.conf-medium { color: #d69e2e; }
.conf-low { color: #e53e3e; }
.consensus-badge { padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 500; }
.consensus-badge.positive { background: #c6f6d5; color: #22543d; }
.consensus-badge.negative { background: #fed7d7; color: #822727; }
.view-btn { background: #667eea; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 0.85rem; }

/* Legend */
.legend { margin-top: 20px; display: flex; align-items: center; gap: 20px; color: #718096; font-size: 0.85rem; }
.legend h4 { margin: 0; }
.legend-item { display: flex; align-items: center; gap: 6px; }
.dot { width: 12px; height: 12px; border-radius: 50%; }
.dot.high { background: #38a169; }
.dot.medium { background: #d69e2e; }
.dot.low { background: #e53e3e; }

/* ML Summary */
.ml-summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 25px; }
.ml-card { display: flex; align-items: center; gap: 12px; background: white; border-radius: 12px; padding: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border-left: 4px solid #667eea; }
.ml-card.positive { border-left-color: #38a169; background: #f0fff4; }
.ml-card.negative { border-left-color: #e53e3e; background: #fff5f5; }
.ml-icon { font-size: 1.5rem; }
.ml-content { display: flex; flex-direction: column; }
.ml-label { font-size: 0.75rem; color: #718096; text-transform: uppercase; }
.ml-value { font-size: 1.1rem; font-weight: 600; color: #2d3748; }
.ml-conf { font-size: 0.8rem; color: #a0aec0; }

/* Details Results Section */
.results-section { background: white; border-radius: 16px; padding: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }
.results-section .results-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.results-section h1 { color: #1a365d; margin: 0 0 5px 0; }
.uniprot-badge { display: inline-block; background: #667eea; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; }
.icon-btn { background: #f7fafc; border: none; padding: 10px 15px; border-radius: 8px; cursor: pointer; font-size: 1.2rem; }

/* Summary Cards */
.summary-cards { display: flex; gap: 15px; margin-bottom: 25px; flex-wrap: wrap; }
.summary-card { display: flex; align-items: center; gap: 12px; background: #f7fafc; padding: 15px 20px; border-radius: 12px; min-width: 120px; }
.summary-card.structure-ready { background: #c6f6d5; }
.card-icon { font-size: 1.5rem; }
.card-value { font-size: 1.5rem; font-weight: 700; color: #2d3748; }
.card-label { font-size: 0.85rem; color: #718096; margin-left: 5px; }

/* Tabs */
.tabs { display: flex; gap: 6px; background: #edf2f7; padding: 6px; border-radius: 14px 14px 0 0; overflow-x: auto; margin-bottom: 0; }
.tab { display: flex; align-items: center; gap: 6px; padding: 10px 16px; border: none; background: transparent; border-radius: 10px; cursor: pointer; font-weight: 500; color: #718096; white-space: nowrap; }
.tab:hover { background: rgba(255,255,255,0.5); }
.tab.active { background: white; color: #667eea; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
.tab-icon { font-size: 1rem; }

/* Tab Content */
.tab-content { background: white; border-radius: 0 0 16px 16px; padding: 25px; border: 1px solid #e2e8f0; border-top: none; }
.tab-content h2 { color: #2d3748; margin: 0 0 20px 0; font-size: 1.3rem; }

/* Properties Grid */
.properties-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; }
.property-card { background: #f7fafc; padding: 20px; border-radius: 12px; }
.property-card h3 { font-size: 0.85rem; color: #718096; margin: 0 0 8px 0; text-transform: uppercase; }
.property-card .value { font-size: 1.5rem; font-weight: 700; color: #2d3748; margin: 0; }
.property-card .value.stable { color: #38a169; }
.stability-label { display: block; font-size: 0.8rem; color: #a0aec0; font-weight: normal; }

/* AA Bars */
.aa-bars { margin-bottom: 30px; }
.aa-bar { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.aa-label { width: 30px; font-weight: 600; color: #4a5568; }
.bar-container { flex: 1; height: 24px; background: #edf2f7; border-radius: 12px; overflow: hidden; }
.bar { height: 100%; background: linear-gradient(90deg, #667eea, #48bb78); border-radius: 12px; }
.aa-pct { width: 50px; text-align: right; color: #718096; font-size: 0.9rem; }

/* Charge Grid */
.charge-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }
.charge-card { padding: 20px; border-radius: 12px; text-align: center; }
.charge-card.positive { background: #c6f6d5; }
.charge-card.negative { background: #fed7d7; }
.charge-card.neutral { background: #e2e8f0; }
.charge-card h4 { margin: 0 0 10px 0; font-size: 0.9rem; }
.charge-card p { margin: 0; font-size: 0.85rem; color: #4a5568; }
.charge-card span { font-size: 1.3rem; font-weight: 700; }

/* Structure Grid */
.structure-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 30px; }
.structure-card { padding: 25px; border-radius: 12px; text-align: center; }
.structure-card.helix { background: linear-gradient(135deg, #ffecd2, #fcb69f); }
.structure-card.sheet { background: linear-gradient(135deg, #a1c4fd, #c2e9fb); }
.structure-card.turn { background: linear-gradient(135deg, #ffeaa7, #fdcb6e); }
.struct-icon { font-size: 2rem; margin-bottom: 10px; }
.structure-card h4 { margin: 0 0 5px 0; }
.structure-card p { font-size: 1.8rem; font-weight: 700; margin: 0; }

/* AlphaFold Viewer */
.alphafold-section { margin-top: 30px; }
.viewer-container { background: #f7fafc; border-radius: 12px; overflow: hidden; margin: 20px 0; }
.molstar-viewer { width: 100%; height: 450px; }
.structure-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.action-btn { padding: 10px 20px; border-radius: 8px; text-decoration: none; color: #4a5568; background: #edf2f7; font-size: 0.9rem; }
.action-btn.primary { background: #667eea; color: white; }

/* Hydrophobic Regions */
.hydrophobic-section { margin-top: 30px; }
.hydro-region { display: flex; align-items: center; gap: 15px; padding: 10px 15px; background: #f7fafc; border-radius: 8px; margin-bottom: 8px; border-left: 3px solid #667eea; }
.region-pos { font-weight: 600; color: #667eea; min-width: 60px; }
.hydro-region code { flex: 1; font-size: 0.9rem; color: #4a5568; }
.region-score { color: #e53e3e; font-weight: 500; }

/* Domains */
.domain-list { display: grid; gap: 12px; margin-bottom: 30px; }
.domain-card { background: #f7fafc; padding: 15px; border-radius: 10px; }
.domain-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.domain-id { font-weight: 600; color: #2d3748; }
.domain-badge { font-size: 0.75rem; padding: 3px 8px; border-radius: 10px; background: #667eea; color: white; }
.domain-info { font-size: 0.85rem; color: #718096; }
.no-results { color: #a0aec0; font-style: italic; text-align: center; padding: 20px; }

/* Motifs */
.motifs-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px; }
.motif-card { background: #f7fafc; padding: 20px; border-radius: 12px; }
.motif-card h4 { margin: 0 0 10px 0; color: #2d3748; }
.found-badge { background: #c6f6d5; color: #22543d; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; }
.not-found-badge { background: #fed7d7; color: #822727; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; }
.matches { margin-top: 10px; }
.matches code { display: block; background: white; padding: 5px 10px; border-radius: 5px; margin-bottom: 5px; font-size: 0.85rem; }

/* Charts */
.charts-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
.chart-container { background: #f7fafc; border-radius: 12px; padding: 20px; min-height: 250px; }

/* Error */
.error { color: #e53e3e; margin-top: 15px; padding: 12px; background: #fff5f5; border-radius: 10px; }

/* Responsive */
@media (max-width: 768px) {
  .main-content { grid-template-columns: 1fr; }
  .examples-grid { grid-template-columns: repeat(2, 1fr); }
  .structure-grid, .charge-grid { grid-template-columns: 1fr; }
  .charts-grid { grid-template-columns: 1fr; }
}
</style>
