// frontend/benchtop-nextjs/src/types/plotly.d.ts

// This declaration handles any plotly.js distribution bundle
// (e.g., 'plotly.js-dist-min', 'plotly.js-basic-dist-min')
declare module 'plotly.js-dist-min' {
  import * as Plotly from 'plotly.js';
  export default Plotly;
}

declare module 'plotly.js-basic-dist-min' {
  import * as Plotly from 'plotly.js';
  export default Plotly;
}

// This declaration handles the 'react-plotly.js' wrapper if we ever use it.
declare module 'react-plotly.js' {
    import * as Plotly from 'plotly.js';
    import * as React from 'react';

    interface PlotProps extends React.HTMLAttributes<HTMLDivElement> {
        data: Plotly.Data[];
        layout?: Partial<Plotly.Layout>;
        config?: Partial<Plotly.Config>;
        useResizeHandler?: boolean;
        style?: React.CSSProperties;
        onInitialized?: (figure: { data: Plotly.Data[]; layout: Partial<Plotly.Layout> }, graphDiv: HTMLElement) => void;
        onUpdate?: (figure: { data: Plotly.Data[]; layout: Partial<Plotly.Layout> }, graphDiv: HTMLElement) => void;
        [key: string]: any;
    }

    const Plot: React.FC<PlotProps>;
    export default Plot;
}