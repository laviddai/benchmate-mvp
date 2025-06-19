// frontend/benchtop-nextjs/src/types/analysis.types.ts

// --- Start of Bulk RNA Seq ---
import { type VolcanoPlotData } from "./volcano.types";
import { type PCAPlotData } from "./pca.types";
import { type HeatmapData } from "./heatmap.types";
// --- End of Bulk RNA Seq ---

// A discriminated union for all possible plot data types.
// To add a new plot type, import its data structure and add it to the union.
// e.g., | HeatmapPlotData
export type AnalysisPlotData = VolcanoPlotData | PCAPlotData | HeatmapData | null;