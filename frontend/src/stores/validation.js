import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import validateFasta from "../../utils/commands/ValidateFasta.js";

export const useValidationStore = defineStore('validation', () => {
    let isValid = ref(false);
    let errors = ref([]);

    async function validateFastaInput(file) {
        try{
            let response = await validateFasta(file);
            isValid.value = response.data;
        } catch (error) {
            errors.value.push("Unknown error");
            console.error('Error during file upload', error);
        }
    }

    return { validateFastaInput, isValid, errors }
})