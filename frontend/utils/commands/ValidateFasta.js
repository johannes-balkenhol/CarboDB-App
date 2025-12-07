import Client from "../Client.js";

const ENDPOINT = "/validate-fasta";

async function validateFasta(file){
  const formData = new FormData();
  formData.append('file', file);
  return await Client.post(ENDPOINT, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    }
  });
}

export default validateFasta;