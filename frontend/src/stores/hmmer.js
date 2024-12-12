import { ref } from 'vue'
import { defineStore } from 'pinia'
import hmmerSearch from "../../utils/commands/HmmerSearch.js";

export const useHmmerStore = defineStore('hmmer', () => {
    let errors = ref([]);

    async function runHmmerSearch() {
        try{
            let response = await hmmerSearch();
            return response.data;
        } catch (error) {
            errors.value.push("Unknown error");
            console.error('Error during file upload', error);
        }
    }

    return { runHmmerSearch, errors }
})