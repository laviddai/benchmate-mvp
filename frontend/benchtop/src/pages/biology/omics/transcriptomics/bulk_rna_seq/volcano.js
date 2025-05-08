// frontend/benchtop/src/pages/biology/omics/transcriptomics/bulk_rna_seq/volcano.js
import React, { useState } from 'react';
import Papa from 'papaparse';
import * as XLSX from 'xlsx';
import { submitVolcanoData } from '../../../../../services/biology/omics/transcriptomics/bulk_rna_seq/volcanoapi';

export default function Volcano() {
  const [file, setFile] = useState(null);
  const [cols, setCols] = useState([]);
  const [mapping, setMapping] = useState({ gene: '', log2fc: '', pvalue: '' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const populateColumns = (headers) => {
    setCols(headers);
    setMapping({
      gene: headers.find(h => /gene/i.test(h)) || '',
      log2fc: headers.find(h => /log2.*fold/i.test(h)) || '',
      pvalue: headers.find(h => /p[-_]?value/i.test(h)) || ''
    });
  };

  const handleFile = (e) => {
    const f = e.target.files[0];
    setFile(f);
    setResult(null);
    setError('');
    const ext = f.name.split('.').pop().toLowerCase();

    if (ext === 'csv') {
      Papa.parse(f, {
        preview: 1,
        header: true,
        skipEmptyLines: true,
        complete: r => populateColumns(r.meta.fields || []),
        error: () => setError('Failed to parse CSV headers'),
      });
    } else if (ext === 'xls' || ext === 'xlsx') {
      const reader = new FileReader();
      reader.onload = e => {
        try {
          const wb = XLSX.read(new Uint8Array(e.target.result), { type: 'array' });
          const ws = wb.Sheets[wb.SheetNames[0]];
          const rows = XLSX.utils.sheet_to_json(ws, { header:1, range:0 });
          populateColumns(rows[0] || []);
        } catch {
          setError('Failed to parse Excel headers');
        }
      };
      reader.onerror = () => setError('Failed to read Excel file');
      reader.readAsArrayBuffer(f);
    } else {
      setError('Unsupported file type');
    }
  };

  const handleChange = (field) => (e) => {
    setMapping(prev => ({ ...prev, [field]: e.target.value }));
  };

  const handleRun = async () => {
    if (!file) return setError('Please upload a file');
    if (!mapping.gene || !mapping.log2fc || !mapping.pvalue) 
      return setError('Please map all three columns');
    setLoading(true);
    setError('');
    try {
      const data = await submitVolcanoData(file, {
        gene_col: mapping.gene,
        log2fc_col: mapping.log2fc,
        pvalue_col: mapping.pvalue
      });
      setResult(data);
    } catch (err) {
      setError(err.message || 'Error processing data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4">
      <h1 className="text-xl mb-4">Volcano Plot Tool</h1>

      <input
        type="file"
        accept=".csv,.xls,.xlsx"
        onChange={handleFile}
        className="mb-4"
      />

      {cols.length > 0 && (
        <div className="mb-4 space-y-3">
          <div>
            <label className="block mb-1">Gene column</label>
            <select
              value={mapping.gene}
              onChange={handleChange('gene')}
              className="border rounded p-1 w-full"
            >
              <option value="">-- select --</option>
              {cols.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="block mb-1">Log2FC column</label>
            <select
              value={mapping.log2fc}
              onChange={handleChange('log2fc')}
              className="border rounded p-1 w-full"
            >
              <option value="">-- select --</option>
              {cols.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="block mb-1">P-value column</label>
            <select
              value={mapping.pvalue}
              onChange={handleChange('pvalue')}
              className="border rounded p-1 w-full"
            >
              <option value="">-- select --</option>
              {cols.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
        </div>
      )}

      <button
        onClick={handleRun}
        disabled={loading || !file}
        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded mb-4"
      >
        {loading ? 'Processing…' : 'Run Volcano'}
      </button>

      {error && <p className="text-red-600 mb-4">{error}</p>}

      {result?.plot_image && (
        <div>
          <h2 className="text-lg mb-2">Result</h2>
          <img src={result.plot_image} alt="Volcano" className="max-w-full" />
          {result.summary && <p>Total genes: {result.summary.n_genes}</p>}
        </div>
      )}
    </div>
  );
}
