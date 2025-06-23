// frontend/benchtop-nextjs/src/components/analysis/ClientOnlyPlot.tsx
"use client";

import React, { useEffect, useRef, useImperativeHandle, forwardRef } from 'react';
import Plotly from 'plotly.js-dist-min';
import { type Data, type Layout } from 'plotly.js';

interface ClientOnlyPlotProps {
  data: Data[];
  layout: Partial<Layout>;
  className?: string;
  style?: React.CSSProperties;
}

// --- FIX: Use forwardRef to allow parent components to get a ref to the div ---
const ClientOnlyPlot = forwardRef<HTMLDivElement, ClientOnlyPlotProps>(
  ({ data, layout, className, style }, ref) => {
    const internalRef = useRef<HTMLDivElement>(null);
    
    // This allows a parent to get the ref of the div
    useImperativeHandle(ref, () => internalRef.current!, []);

    useEffect(() => {
      if (internalRef.current) {
        Plotly.react(internalRef.current, data, layout, { responsive: true, displaylogo: false });
      }
    }, [data, layout]);

    useEffect(() => {
      const currentPlotRef = internalRef.current;
      return () => {
        if (currentPlotRef) {
          Plotly.purge(currentPlotRef);
        }
      };
    }, []);

    return <div ref={internalRef} className={className} style={style} />;
  }
);

ClientOnlyPlot.displayName = 'ClientOnlyPlot';

export default ClientOnlyPlot;