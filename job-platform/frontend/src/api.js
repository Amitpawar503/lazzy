// Thin API client. All calls go through the Vite dev proxy to the backend.
const BASE = "/api";

async function j(res) {
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

export const api = {
  health: () => fetch(`${BASE}/health`).then(j),

  listJobs: (params) => {
    const q = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== "" && v != null)
    );
    return fetch(`${BASE}/jobs?${q}`).then(j);
  },

  facets: () => fetch(`${BASE}/jobs/meta/facets`).then(j),

  listResumes: () => fetch(`${BASE}/resumes`).then(j),

  uploadResume: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return fetch(`${BASE}/resumes`, { method: "POST", body: fd }).then(j);
  },

  matches: (resumeId, useAi) =>
    fetch(`${BASE}/resumes/${resumeId}/matches?limit=30&use_ai=${useAi ? "true" : "false"}`).then(j),

  enhance: (resumeId, jobId) =>
    fetch(`${BASE}/resumes/enhance`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume_id: resumeId, job_id: jobId }),
    }).then(j),

  loadSample: () => fetch(`${BASE}/sources/load-sample`, { method: "POST" }).then(j),

  triggerIngest: () => fetch(`${BASE}/sources/ingest/async`, { method: "POST" }).then(j),

  listSources: () => fetch(`${BASE}/sources`).then(j),

  addSource: (provider, slug, display_name) =>
    fetch(`${BASE}/sources`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider, slug, display_name }),
    }).then(j),
};
