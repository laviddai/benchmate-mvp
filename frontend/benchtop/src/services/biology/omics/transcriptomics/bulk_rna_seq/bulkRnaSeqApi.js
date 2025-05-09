// bulkRnaSeqApi.js
const API_BASE = process.env.REACT_APP_API_BASE_URL || "http://localhost:8000";

export async function listTools() {
  const res = await fetch(
    `${API_BASE}/api/benchtop/biology/omics/transcriptomics/bulk-rna-seq/tools`
  );
  if (!res.ok) throw new Error("Could not fetch tool list");
  return res.json();
}

export async function runTool(tool, file, mapping) {
  const form = new FormData();
  form.append("file", file);
  Object.entries(mapping).forEach(([key, val]) => {
    if (val) form.append(`${key}_col`, val);
  });

  const res = await fetch(
    `${API_BASE}/api/benchtop/biology/omics/transcriptomics/bulk-rna-seq/${tool}/run`,
    { method: "POST", body: form }
  );
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || JSON.stringify(err));
  }
  return res.json();
}

export default { listTools, runTool };
