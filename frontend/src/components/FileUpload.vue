<template>
  <template v-if="!this.isValid">
    <div class="upload-error-wrapper">
      <div class="upload-wrapper"
           @drop.prevent="handleDrop"
           @dragenter.prevent
           @dragleave.prevent
           @dragover.prevent
      >
        <font-awesome-icon :icon="faFileCsv()" class="icon upload-icon"></font-awesome-icon>
        <span class="upload-text">Drop file</span>
        <span class="upload-text">or</span>
        <button class="button-action" @click="openFile">Upload File</button>
        <input @input="handleInput" id="importFile" type="file" style="display: none" />
      </div>
      <div :class="{ 'visible': this.errors.length > 0 }" class="error-wrapper">
        <ul>
          <li v-for="(error, index) in errors" :key="index">{{ error }}</li>
        </ul>
      </div>
    </div>
  </template>
  <template v-else>
    <div>
      <h2>Your input was valid, please press the button to start hmmer search</h2>
      <button class="button-action-big" @click="runHmmerSearch">Start Search</button>
    </div>
  </template>
</template>

<script>
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
import { faFile } from '@fortawesome/free-solid-svg-icons';
import { useValidationStore } from "@/stores/validation.js";
import { useHmmerStore } from "@/stores/hmmer.js";

export default {
  name: "FileUpload",
  data() {
    return {
      file: null,
      loadedFasta: {},
      linesOfCSV: [],
      errors: [],
      isValid: false,
    }
  },
  methods: {
    /**
     * Return the font-awesome faFile Icon
     * @return {IconDefinition} faFile
     */
    faFileCsv() {
      return faFile;
    },
    /**
     * Triggers the click on the hidden input element.
     */
    openFile() {
      const input = document.getElementById("importFile");
      if (input !== null) {
        input.click();
      }
    },
    /**
     * Handles the upload in the hidden input element.
     * @param {Event} event The InputEvent containing the file.
     * @return {Promise<void>} Promise that resolves when the CSV is successfully imported.
     */
    handleInput: async function(event) {
      const input = document.getElementById("importFile");
      if (input !== null) {
        const files = event.target.files ?? [];
        if (files.length > 0) {
          await this.importFasta(files[0]);
        }
      }
    },
    /**
     * Handles the drop in the dropzone.
     * @param {DragEvent} event The DropEvent containing the file.
     * @return {Promise<void>} Promise that resolves when the CSV is successfully imported.
     */
    handleDrop: async function(event) {
      const dropZone = document.getElementsByName("drop-zone")[0];
      if (dropZone !== null) {
        const files = event.dataTransfer.files;
        if (files.length > 0) {
          await this.importFasta(files[0]);
        }
      }
    },
    async validateInput() {
      const validationStore = useValidationStore();
      try {
        await validationStore.validateFastaInput();

        this.isValid = validationStore.isValid;
        this.errors = validationStore.errors;
      } catch (error) {
        console.error("An error occurred during validation:", error);
      }
    },
    async runHmmerSearch() {
      const hmmerStore = useHmmerStore()
      try {
        await hmmerStore.runHmmerSearch();

        this.errors = hmmerStore.errors;
      } catch (error) {
        console.error("An error occurred during validation:", error);
      }
    },
    /**
     * Imports the FASTA file.
     * Error handling with the errors array.
     * @param {Blob} file
     */
    async importFasta(file) {
      await this.validateInput();
      this.errors = [];
      /** Use FileReader to read the file */
      const reader = new FileReader();

      reader.onload = (event) => {
        this.loadedFasta = (event.target.result || "{}");
        if(this.loadedFasta) {
          reader.readAsText(file);
        } else {
          this.errors.push('There was an error while reading the data.')
        }

      };
      reader.onerror = () => {
        console.error("Error reading file: " + file.name);
      };
    },
  },
  components: { FontAwesomeIcon }
}
</script>


<style scoped>

.upload-wrapper {
  background-color: var(--color-white);
  width: 25vw;
  height: 30vh;
  border: 1px dashed var(--color-border);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.upload-icon {
  margin-bottom: 7px;
}

.upload-text {
  margin-bottom: 3px;
}

</style>