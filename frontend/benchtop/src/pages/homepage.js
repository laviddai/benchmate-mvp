// frontend/benchtop/src/pages/homepage.js
import React from 'react';
import { Link } from 'react-router-dom';

const Homepage = () => {
  return (
    <div style={{ padding: '1rem' }}>
      <h1>Welcome to BenchTop</h1>
      <p>Select a tool below:</p>
      <ul>
        <li>
          <Link to="/volcano">Volcano Plot (Bulk RNA-seq)</Link>
        </li>
        {/* Add other tools here as you build them */}
      </ul>
    </div>
  );
};

export default Homepage;
