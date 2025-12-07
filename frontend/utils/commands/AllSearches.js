import Client from "../Client.js";

const ENDPOINT = "/all-searches";

async function allSearches(fileId){
  return await Client.post(ENDPOINT, { fileId });
}

export default allSearches;