import Client from "../Client.js";

const ENDPOINT = "/validate-fasta";

async function validateFasta(){
  return await Client.post(ENDPOINT);
}

export default validateFasta;