// frontend/benchtop-nextjs/src/components/analysis/ClientOnlyPlot.tsx
"use client";

import React, { useEffect, useRef } from 'react';
import Plotly from 'plotly.js';
import { type Data, type Layout } from 'plotly.js';

interface ClientOnlyPlotProps {
  data: Data[];
  layout: Partial<Layout>;
  className?: string;
}

const ClientOnlyPlot = ({ data, layout, className }: ClientOnlyPlotProps) => {
  const plotRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (plotRef.current) {
      Plotly.react(plotRef.current, data, layout, { responsive: true });
    }
  }, [data, layout]);

  useEffect(() => {
    const handleResize = () => {
      if (plotRef.current) {
        Plotly.Plots.resize(plotRef.current);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      if (plotRef.current) {
        Plotly.purge(plotRef.current);
      }
    };
  }, []);

  return <div ref={plotRef} className={className} />;
};

export default ClientOnlyPlot;