import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import Papa from "papaparse";
import * as XLSX from "xlsx";
import { listTools, runTool } from "../../../../services/biology/omics/transcriptomics/bulk_rna_seq/bulkRnaSeqApi";

export default function ToolPage() {
  const { tool } = useParams();
  const [tools, setTools] = useState([]);
  const [file, setFile] = useState(null);
  const [cols, setCols] = useState([]);
  const [mapping, setMapping] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    listTools().then(setTools).catch(console.error);
  }, []);

  // parse headers for CSV/Excel
  const populate = (headers) => {
    setCols(headers);
    setMapping({
      gene: headers.find(h => /gene/i.test(h))||"",
      log2fc: headers.find(h => /log2.*fold/i.test(h))||"",
      pvalue: headers.find(h => /p[-_]?value/i.test(h))||"",
    });
  };

  const onFile = ({ target: { files }}) => {
    const f = files[0];
    setFile(f);
    setResult(null);
    setError("");
    const ext = f.name.split(".").pop().toLowerCase();

    if (ext === "csv") {
      Papa.parse(f, {
        preview: 1, header: true, skipEmptyLines: true,
        complete: r => populate(r.meta.fields || []),
        error: () => setError("CSV parse error")
      });
    } else if (ext === "xls" || ext === "xlsx") {
      const reader = new FileReader();
      reader.onload = e => {
        try {
          const data = new Uint8Array(e.target.result);
          const wb = XLSX.read(data, { type: "array" });
          const ws = wb.Sheets[wb.SheetNames[0]];
          const rows = XLSX.utils.sheet_to_json(ws, { header:1, range:0 });
          populate(rows[0]||[]);
        } catch {
          setError("Excel parse error");
        }
      };
      reader.onerror = () => setError("Excel read error");
      reader.readAsArrayBuffer(f);
    } else {
      setError("Unsupported file type");
    }
  };

  const onMap = (field) => (e) =>
    setMapping(m => ({ ...m, [field]: e.target.value }));

  const onRun = async () => {
    if (!file) return setError("Upload a file");
    if (!mapping.gene || !mapping.log2fc || !mapping.pvalue)
      return setError("Map all three columns");
    setLoading(true);
    setError("");
    try {
      const data = await runTool(tool, file, mapping);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!tools.includes(tool)) {
    return <p>Unknown tool: {tool}</p>;
  }

  return (
    <div className="p-4">
      <h1 className="text-2xl mb-4">{tool.replace(/-/g," ").toUpperCase()}</h1>

      <input
        type="file"
        accept=".csv,.xls,.xlsx"
        onChange={onFile}
        className="mb-4"
      />

      {cols.length > 0 && (
        <div className="space-y-3 mb-4">
          {["gene","log2fc","pvalue"].map(f => (
            <div key={f}>
              <label className="block mb-1">{f} column</label>
              <select
                value={mapping[f]||""}
                onChange={onMap(f)}
                className="border p-1 w-full rounded"
              >
                <option value="">-- select --</option>
                {cols.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          ))}
        </div>
      )}

      <button
        onClick={onRun}
        disabled={loading}
        className="bg-blue-600 text-white px-4 py-2 rounded mb-4"
      >
        {loading ? "Running…" : "Run"}
      </button>

      {error && <p className="text-red-600 mb-4">Error: {error}</p>}

      {result?.plot_image && (
        <div>
          <img src={result.plot_image} alt={tool} className="max-w-full" />
          {result.summary && <p>Total: {result.summary.n_genes}</p>}
        </div>
      )}
    </div>
  );
}
