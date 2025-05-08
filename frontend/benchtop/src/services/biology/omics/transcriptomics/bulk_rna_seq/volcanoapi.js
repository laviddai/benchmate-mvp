// frontend/benchtop/src/services/biology/omics/transcriptomics/bulk_rna_seq/volcanoapi.js

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

/**
 * Submit the uploaded file and column mappings to the backend volcano endpoint.
 * @param {File} file       The CSV/XLS/XLSX file selected by the user.
 * @param {Object} mapping  An object with keys { gene, log2fc, pvalue } and their column names.
 * @returns {Promise<Object>} The JSON response containing plot_image and summary.
 */
export async function submitVolcanoData(file, mapping) {
  const formData = new FormData();
  formData.append('file', file);

  // Include only the mappings the user has set
  if (mapping.gene)   formData.append('gene_col', mapping.gene);
  if (mapping.log2fc) formData.append('log2fc_col', mapping.log2fc);
  if (mapping.pvalue) formData.append('pvalue_col', mapping.pvalue);

  const res = await fetch(
    `${API_BASE_URL}/api/benchtop/biology/omics/transcriptomics/bulk-rna-seq/run`,
    {
      method: 'POST',
      body: formData,
    }
  );

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.error || 'Server error');
  }

  return res.json();
}

// Named default export to satisfy ESLint import/no-anonymous-default-export
const VolcanoAPI = {
  submitVolcanoData,
};

export default VolcanoAPI;
