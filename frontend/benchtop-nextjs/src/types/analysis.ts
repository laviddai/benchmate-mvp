// frontend/benchtop-nextjs/src/types/analysis.ts

// --- VOLCANO PLOT TYPES (Existing and Unchanged) ---

// Represents a single data point in the volcano plot data array
export interface VolcanoPoint {
    _gene: string;
    _log2fc: number;
    _pvalue: number;
    _minus_log10_pvalue_: number;
    _classification: 'up' | 'down' | 'neutral';
}

// Represents the default configuration for the volcano plot, sent from the backend
export interface VolcanoPlotConfig {
    title: string;
    x_axis_label: string;
    y_axis_label: string;
    fold_change_threshold: number;
    p_value_threshold: number;
    colors: {
        up: string;
        down: string;
        neutral: string;
    };
    legend_labels: {
        up?: string;
        down?: string;
        neutral?: string;
    };
}

// The complete structure of the JSON object returned by the backend for a volcano plot
export interface VolcanoPlotData {
    plot_type: 'volcano';
    plot_data: VolcanoPoint[];
    default_plot_config: VolcanoPlotConfig; // Uses the specific VolcanoPlotConfig
    summary_stats: {
        total_genes: number;
        initial_upregulated: number;
        initial_downregulated: number;
        initial_neutral: number;
        parameters_used: any;
    };
}


// --- PCA PLOT TYPES (New Addition) ---

// Represents a single data point (a sample) in the PCA plot data array
export interface PCAPoint {
    sample: string;
    group: string;
    // This allows for dynamic keys like "PC1", "PC2", etc.
    // The value can be a number (for PC coordinates) or a string (for sample/group name).
    [key: string]: number | string;
}

// Represents the default configuration for the PCA plot, sent from the backend
export interface PCAPlotConfig {
    title: string;
    x_axis_label: string;
    y_axis_label: string;
    pc_x_axis: number;
    pc_y_axis: number;
    point_size: number;
}

// The complete structure of the JSON object returned by the backend for a PCA plot
export interface PCAPlotData {
    plot_type: 'pca';
    plot_data: PCAPoint[];
    default_plot_config: PCAPlotConfig;
    summary_stats: {
        total_samples: number;
        total_genes: number;
        explained_variance_ratio: number[];
        parameters_used: any;
    };
}


// --- DISCRIMINATED UNION FOR ALL PLOT TYPES ---
// This allows TypeScript to intelligently know which data structure we have
// based on the `plot_type` field.
export type AnalysisPlotData = VolcanoPlotData | PCAPlotData | null;