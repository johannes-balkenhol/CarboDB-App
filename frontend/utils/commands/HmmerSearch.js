import Client from "../Client.js";

const ENDPOINT = "/hmmer-search";

async function hmmerSearch(){
  return await Client.post(ENDPOINT);
}

export default hmmerSearch;