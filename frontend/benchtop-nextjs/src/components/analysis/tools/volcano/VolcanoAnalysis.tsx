// frontend/benchtop-nextjs/src/components/analysis/tools/volcano/VolcanoAnalysis.tsx
"use client";

import { Button } from "@/components/ui/button";
import { submitVolcanoAnalysis } from "@/lib/api";
import { toast } from "sonner";

interface VolcanoAnalysisProps {
  projectId: string;
  datasetId: string;
  onAnalysisSubmit: (runId: string) => void;
  isDisabled: boolean;
}

export function VolcanoAnalysis({ projectId, datasetId, onAnalysisSubmit, isDisabled }: VolcanoAnalysisProps) {
  
  const handleRunVolcano = async () => {
    toast.info("Submitting Volcano Plot analysis job...");
    try {
      const submissionData = {
        project_id: projectId,
        primary_input_dataset_id: datasetId,
      };
      const run = await submitVolcanoAnalysis(submissionData);
      onAnalysisSubmit(run.id);
    } catch (error) {
      toast.error(`Submission failed: ${error instanceof Error ? error.message : "Unknown error"}`);
    }
  };

  return (
    <Button onClick={handleRunVolcano} disabled={isDisabled}>
      Run Volcano Plot
    </Button>
  );
}