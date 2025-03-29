import Client from "../Client.js";

const ENDPOINT = "/hmmer-search";

async function hmmerSearch(fileId){
  return await Client.post(ENDPOINT, { fileId });
}

export default hmmerSearch;