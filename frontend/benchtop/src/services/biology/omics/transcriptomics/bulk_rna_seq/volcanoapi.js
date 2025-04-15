// frontend/benchtop/src/services/biology/omics/transcriptomics/bulk_rna_seq/volcanoapi.js
const API_BASE_URL = "http://127.0.0.1:8000";

export async function submitVolcanoData(formData) {
  const response = await fetch(`${API_BASE_URL}/api/benchtop/biology/omics/transcriptomics/bulk-rna-seq/run`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || errorData.detail || "Error processing data");
  }
  return await response.json();
}
