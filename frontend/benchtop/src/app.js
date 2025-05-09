// frontend/benchtop/src/app.js
// sets up routing via React Router
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Homepage from './pages/homepage'; // a homepage view (optional)
import ToolPage from "./pages/biology/omics/transcriptomics/bulk_rna_seq/ToolPage";

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Homepage />} />
        <Route
          path="/bulk-rna-seq/:tool"
          element={<ToolPage />}
        />
      </Routes>
    </Router>
  );
};

export default App;
