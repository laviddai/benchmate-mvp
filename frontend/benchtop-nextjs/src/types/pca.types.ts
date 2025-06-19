// frontend/benchtop-nextjs/src/types/pca.types.ts

// Represents a single data point (a sample) in the PCA plot data array
export interface PCAPoint {
    sample: string;
    group: string;
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