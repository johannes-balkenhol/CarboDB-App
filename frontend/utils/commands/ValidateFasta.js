import Client from "../client.js";

const ENDPOINT = "/validate-fasta";

async function validateFasta(){
  return await Client.post(ENDPOINT);
}

export default validateFasta;