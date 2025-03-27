import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import validateFasta from "../../utils/commands/ValidateFasta.js";

export const useValidationStore = defineStore('validation', () => {
    let isValid = ref(false);
    let fileId = ref("");
    let errors = ref([]);

    async function validateFastaInput(file) {
        try{
            let response = await validateFasta(file);
            isValid.value = response.data.is_valid;
            if(isValid.value){
                fileId.value = response.data.file_id;
            }
        } catch (error) {
            errors.value.push("Unknown error");
            console.error('Error during file upload', error);
        }
    }

    return { validateFastaInput, isValid, fileId, errors }
})