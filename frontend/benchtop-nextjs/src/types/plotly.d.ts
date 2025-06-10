// frontend/benchtop-nextjs/src/types/plotly.d.ts
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
        onPurge?: (figure: { data: Plotly.Data[]; layout: Partial<Plotly.Layout> }, graphDiv: HTMLElement) => void;
        onError?: (error: Error) => void;
        onAfterExport?: () => void;
        onAfterPlot?: () => void;
        onAnimated?: () => void;
        onAnimatingFrame?: (event: Plotly.FrameAnimationEvent) => void;
        onAnimationInterrupted?: () => void;
        onAutoSize?: () => void;
        onBeforeExport?: () => void;
        onButtonClicked?: (event: Plotly.ButtonClickEvent) => void;
        onClick?: (event: Plotly.PlotMouseEvent) => void;
        onClickAnnotation?: (event: Plotly.AnnotationClickEvent) => void;
        onDeselect?: () => void;
        onDoubleClick?: () => void;
        onFramework?: () => void;
        onHover?: (event: Plotly.PlotHoverEvent) => void;
        onLegendClick?: (event: Plotly.LegendClickEvent) => boolean;
        onLegendDoubleClick?: (event: Plotly.LegendClickEvent) => boolean;
        onRelayout?: (event: Plotly.RelayoutEvent) => void;
        onRestyle?: (event: Plotly.PlotRestyleEvent) => void;
        onRedraw?: () => void;
        onSelected?: (event: Plotly.PlotSelectionEvent) => void;
        onSelecting?: (event: Plotly.PlotSelectionEvent) => void;
        onSliderChange?: (event: Plotly.SliderChangeEvent) => void;
        onSliderEnd?: (event: Plotly.SliderChangeEvent) => void;
        onSliderStart?: (event: Plotly.SliderChangeEvent) => void;
        onTransitioning?: () => void;
        onTransitionInterrupted?: () => void;
        onUnhover?: (event: Plotly.PlotHoverEvent) => void;
        onWebGlContextLost?: () => void;
    }

    const Plot: React.FC<PlotProps>;
    export default Plot;
}