import { ref } from 'vue'
import { defineStore } from 'pinia'
import hmmerSearch from "../../utils/commands/HmmerSearch.js";
import downloadResults from '../../utils/commands/DownloadResults.js';
import allSearches from '../../utils/commands/AllSearches.js';

export const useSearchStore = defineStore('searchStore', () => {
    let errors = ref([]);

    async function runHmmerSearch(fileId) {
        try{
            let response = await hmmerSearch(fileId);
            return response.data;
        } catch (error) {
            errors.value.push("Unknown error");
            console.error('Error during hmmer search', error);
        }
    }

    async function runAllSearches(fileId) {
        try{
            let response = await allSearches(fileId);
            return response.data;
        } catch (error) {
            errors.value.push("Unknown error");
            console.error('Error during all searches', error);
        }   
    }

    async function runDownloadResults(fileId) {
        try{
            let response = await downloadResults(fileId);

            const blob = new Blob([response.data], { type: 'application/pdf' });

            const downloadUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = `${fileId}.pdf`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(downloadUrl);

        } catch (error) {
            errors.value.push("Unknown error");
            console.error('Error during data download', error);
        }
    }

    return { runHmmerSearch, runAllSearches, runDownloadResults, errors }
})