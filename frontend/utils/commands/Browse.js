import Client from "../Client.js";
export async function browseDatabase(params) {
  return await Client.get("/browse", { params });
}
export async function getDatabaseStats() {
  return await Client.get("/stats");
}
