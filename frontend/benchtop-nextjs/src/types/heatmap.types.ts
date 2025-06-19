// frontend/benchtop-nextjs/src/types/heatmap.types.ts

// Represents the core data needed to render the heatmap plot.
export interface HeatmapPlotDataPayload {
    heatmap_values: number[][]; // A 2D array of the scaled expression values
    gene_labels: string[];      // The labels for the rows (genes), ordered by clustering
    sample_labels: string[];    // The labels for the columns (samples), ordered by clustering
    sample_annotations: string[]; // Group information for each sample to draw color bars
}

// Represents the default configuration for the heatmap plot, sent from the backend.
export interface HeatmapPlotConfig {
    title: string;
    subtitle: string;
    color_map: string;
    show_gene_labels: boolean;
    show_sample_labels: boolean;
    show_sample_annotation: boolean;
    hover_template: string;
}

// The complete structure of the JSON object returned by the backend for a heatmap analysis.
export interface HeatmapData {
    plot_type: 'heatmap';
    plot_data: HeatmapPlotDataPayload;
    default_plot_config: HeatmapPlotConfig;
    summary_stats: {
        genes_plotted: number;
        samples_plotted: number;
        parameters_used: any;
        gene_selection_reason: string;
    };
}