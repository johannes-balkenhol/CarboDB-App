import Client from "../Client.js";

const ENDPOINT = "/download-results";

async function downloadResults(fileId){
  return await Client.get(ENDPOINT, {
    params: { fileId },
    responseType: 'blob'
});
}

export default downloadResults;