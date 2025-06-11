// frontend/benchtop-nextjs/src/types/plotly.d.ts

// This declaration handles the 'plotly.js-basic-dist-min' module.
declare module 'plotly.js-basic-dist-min' {
  // It tells TypeScript that the types for this small bundle are the same
  // as the official, full 'plotly.js' types.
  import * as Plotly from 'plotly.js';
  export default Plotly;
}

// This declaration handles the 'react-plotly.js' wrapper module.
// It is a more robust version of the file you already had.
declare module 'react-plotly.js' {
    import * as Plotly from 'plotly.js';
    import * as React from 'react';

    interface PlotProps extends React.HTMLAttributes<HTMLDivElement> {
        data: Plotly.Data[];
        layout?: Partial<Plotly.Layout>;
        config?: Partial<Plotly.Config>;
        useResizeHandler?: boolean;
        style?: React.CSSProperties;
        // This is the key prop to pass our specific plotly bundle
        plotly?: any; 
        onInitialized?: (figure: { data: Plotly.Data[]; layout: Partial<Plotly.Layout> }, graphDiv: HTMLElement) => void;
        onUpdate?: (figure: { data: Plotly.Data[]; layout: Partial<Plotly.Layout> }, graphDiv: HTMLElement) => void;
        [key: string]: any; // Allow other props
    }

    const Plot: React.FC<PlotProps>;
    export default Plot;
}