import Client from "../Client.js";
export async function submitBatchJob(file, mode, kingdom, email) {
  const fd = new FormData();
  fd.append('file', file);
  fd.append('mode', mode);
  fd.append('kingdom', kingdom);
  if (email) fd.append('email', email);
  return await Client.post("/batch", fd, { headers: { 'Content-Type': 'multipart/form-data' }});
}
export async function getJobStatus(jobId) {
  return await Client.get(`/jobs/${jobId}`);
}
