// frontend/benchtop/src/pages/biology/omics/transcriptomics/bulk_rna_seq/volcano.js
import React, { useState } from 'react';
import ColumnMapping from '../../../components/common/ColumnMapping';
import { submitVolcanoData } from '../../../services/biology/omics/transcriptomics/bulk_rna_seq/volcanoapi';

const Volcano = () => {
  const [file, setFile] = useState(null);
  const [detectedColumns, setDetectedColumns] = useState([]);
  const [mapping, setMapping] = useState({
    pvalue: '',
    log2fc: '',
    gene: ''
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    // For testing, simulate detected columns.
    // In production, might call an API endpoint to analyze the file and return its headers.
    setDetectedColumns(['gene', 'logfc', 'pvalue']); // adapt based on data
  };

  const handleMappingChange = (newMapping) => {
    setMapping(newMapping);
  };

  const handleSubmit = async () => {
    if (!file) {
      alert("Please upload a file.");
      return;
    }
    setLoading(true);
    setError("");
    const formData = new FormData();
    formData.append("file", file);
    formData.append("pvalue_col", mapping.pvalue);
    formData.append("log2fc_col", mapping.log2fc);
    formData.append("gene_col", mapping.gene);

    try {
      const data = await submitVolcanoData(formData);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '1rem' }}>
      <h1>Volcano Plot Tool</h1>
      <input type="file" onChange={handleFileChange} />
      {detectedColumns.length > 0 && (
        <ColumnMapping 
          detectedColumns={detectedColumns} 
          onMappingChange={handleMappingChange} 
        />
      )}
      <button onClick={handleSubmit} disabled={loading}>
        {loading ? "Processing..." : "Submit Data"}
      </button>
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      {result && (
        <div>
          <h2>Results</h2>
          {result.plot_image && (
            <img
              src={`data:image/png;base64,${result.plot_image}`}
              alt="Volcano Plot"
              style={{ maxWidth: "100%" }}
            />
          )}
          {result.summary && (
            <div>
              <p>Total Genes: {result.summary.total_genes}</p>
              <p>Processed Genes: {result.summary.processed_genes}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Volcano;
