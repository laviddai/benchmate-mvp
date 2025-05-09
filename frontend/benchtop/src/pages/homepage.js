// frontend/benchtop/src/pages/homepage.js
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listTools } from "../services/biology/omics/transcriptomics/bulk_rna_seq/bulkRnaSeqApi";

export default function Homepage() {
  const [tools, setTools] = useState([]);

  useEffect(() => {
    listTools().then(setTools).catch(console.error);
  }, []);

  return (
    <div className="p-4">
      <h1 className="text-2xl mb-4">BenchMate</h1>
      <h2 className="text-xl mb-2">Bulk RNA-seq Tools</h2>
      <ul className="list-disc pl-5">
        {tools.map(t => (
          <li key={t}>
            <Link to={`/bulk-rna-seq/${t}`} className="text-blue-600">
              {t.replace(/-/g, " ").toUpperCase()}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
