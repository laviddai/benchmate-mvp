// frontend/benchtop/src/components/common/column_mapping.js
import React, { useState, useEffect } from 'react';

const ColumnMapping = ({ detectedColumns, expectedFields = ["x", "y"], onMappingChange }) => {
  // Create initial mapping using the expected fields. If there are more expected fields than columns,
  // default to an empty string.
  const initializeMapping = () => {
    const mapping = {};
    expectedFields.forEach((field, idx) => {
      mapping[field] = detectedColumns[idx] || "";
    });
    return mapping;
  };

  const [mapping, setMapping] = useState(initializeMapping());

  // Update mapping state when detectedColumns changes
  useEffect(() => {
    setMapping(initializeMapping());
    // Notify parent about the updated mapping
    if (onMappingChange) onMappingChange(initializeMapping());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [detectedColumns, expectedFields]);

  const handleChange = (field, value) => {
    const newMapping = { ...mapping, [field]: value };
    setMapping(newMapping);
    if (onMappingChange) onMappingChange(newMapping);
  };

  return (
    <div style={{ margin: '1rem 0' }}>
      <h2>Column Mapping</h2>
      {expectedFields.map((field) => (
        <div key={field} style={{ marginBottom: '0.5rem' }}>
          <label>{`${field.toUpperCase()} Column: `}</label>
          <select
            value={mapping[field]}
            onChange={(e) => handleChange(field, e.target.value)}
          >
            {detectedColumns.map((col) => (
              <option key={col} value={col}>
                {col}
              </option>
            ))}
          </select>
        </div>
      ))}
    </div>
  );
};

export default ColumnMapping;
