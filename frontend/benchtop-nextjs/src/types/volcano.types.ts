// frontend/benchtop-nextjs/src/types/volcano.types.ts

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
    default_plot_config: VolcanoPlotConfig;
    summary_stats: {
        total_genes: number;
        initial_upregulated: number;
        initial_downregulated: number;
        initial_neutral: number;
        parameters_used: any;
    };
}