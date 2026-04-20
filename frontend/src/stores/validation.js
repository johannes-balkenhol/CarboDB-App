import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import validateFasta from "../../utils/commands/ValidateFasta.js";

export const useValidationStore = defineStore('validation', () => {
    let isValid = ref(false);
    let fileId = ref("");
    let errors = ref([]);

    async function validateFastaInput(file) {
        errors.value = [];
        isValid.value = false;
        try{
            const response = await validateFasta(file);
            if(response.data.is_valid === true){
                isValid.value = response.data.is_valid;
                fileId.value = response.data.file_id;
            }else{
                isValid.value = false;
                errors.value.push(response.data.is_valid)
            }
        } catch (error) {
            if (error.response) {
                const errorMessage = error.response.data.error || "An unknown error occurred";
                errors.value.push(errorMessage);
                console.error('Error during file upload:', errorMessage);
            } else {
                errors.value.push("Network or server error.");
                console.error('Error during file upload:', error);
            }
        }
    }

    return { validateFastaInput, isValid, fileId, errors }
})