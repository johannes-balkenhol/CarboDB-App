import Client from "../Client.js";
export async function predictSequence(sequence, mode, kingdom) {
  return await Client.post("/predict", { sequence, mode, kingdom });
}
