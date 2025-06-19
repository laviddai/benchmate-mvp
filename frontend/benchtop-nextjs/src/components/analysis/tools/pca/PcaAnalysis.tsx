// frontend/benchtop-nextjs/src/components/analysis/tools/pca/PcaAnalysis.tsx
"use client";

import { Button } from "@/components/ui/button";
import { submitPcaAnalysis } from "@/lib/api";
import { toast } from "sonner";

interface PcaAnalysisProps {
  projectId: string;
  datasetId: string;
  onAnalysisSubmit: (runId: string) => void;
  isDisabled: boolean;
}

export function PcaAnalysis({ projectId, datasetId, onAnalysisSubmit, isDisabled }: PcaAnalysisProps) {
  
  const handleRunPca = async () => {
    toast.info("Submitting PCA Plot analysis job...");
    try {
      const submissionData = {
        project_id: projectId,
        primary_input_dataset_id: datasetId,
      };
      const run = await submitPcaAnalysis(submissionData);
      onAnalysisSubmit(run.id);
    } catch (error) {
      toast.error(`Submission failed: ${error instanceof Error ? error.message : "Unknown error"}`);
    }
  };

  return (
    <Button onClick={handleRunPca} disabled={isDisabled} variant="secondary">
      Run PCA Plot
    </Button>
  );
}