// frontend/benchtop-nextjs/src/components/analysis/tools/heatmap/HeatmapAnalysis.tsx
"use client";

import { Button } from "@/components/ui/button";
import { submitHeatmapAnalysis } from "@/lib/api";
import { toast } from "sonner";

interface HeatmapAnalysisProps {
  projectId: string;
  datasetId: string;
  onAnalysisSubmit: (runId: string) => void;
  isDisabled: boolean;
}

export function HeatmapAnalysis({ projectId, datasetId, onAnalysisSubmit, isDisabled }: HeatmapAnalysisProps) {
  
  const handleRunHeatmap = async () => {
    toast.info("Submitting Heatmap analysis job...");
    try {
      // For now, we use the default parameters defined in the backend.
      // In the future, a modal or form could be added here to let the user customize these.
      const submissionData = {
        project_id: projectId,
        primary_input_dataset_id: datasetId,
        // Using default parameters from heatmap.yaml for this initial implementation
        gene_selection_method: "top_n_variable",
        top_n_genes: 50,
        scaling_method: "z_score_row",
        cluster_genes: true,
        cluster_samples: true,
        clustering_method: "average",
        distance_metric: "euclidean",
      };
      const run = await submitHeatmapAnalysis(submissionData);
      onAnalysisSubmit(run.id);
    } catch (error) {
      toast.error(`Submission failed: ${error instanceof Error ? error.message : "Unknown error"}`);
    }
  };

  return (
    <Button onClick={handleRunHeatmap} disabled={isDisabled} variant="outline">
      Run Heatmap
    </Button>
  );
}