// frontend/benchtop-nextjs/src/lib/api/analysisAPI.ts
import { fetchApi } from './index';

// --- Start of Bulk RNA Seq ---
export function submitVolcanoAnalysis(submissionData: any) {
  return fetchApi('/api/analyses/volcano-plot/submit', {
    method: 'POST',
    body: JSON.stringify(submissionData),
  });
}

export function submitPcaAnalysis(submissionData: any) {
  return fetchApi('/api/analyses/pca-plot/submit', {
    method: 'POST',
    body: JSON.stringify(submissionData),
  });
}

export function submitHeatmapAnalysis(submissionData: any) {
  return fetchApi('/api/analyses/heatmap/submit', {
    method: 'POST',
    body: JSON.stringify(submissionData),
  });
}
// --- End of Bulk RNA Seq ---

// --- NEW: Start of Imaging ---
export function submitGaussianBlurAnalysis(submissionData: {
  projectId: string;
  primary_input_dataset_id: string;
  sigma: number;
  analysis_name?: string;
}) {
  return fetchApi('/analyses/imaging/filters/gaussian-blur/submit', {
    method: 'POST',
    body: JSON.stringify(submissionData),
  });
}
// --- NEW: End of Imaging ---

export function getAnalysisRunStatus(analysisRunId: string) {
  return fetchApi(`/api/analysis-runs/${analysisRunId}`);
}

export function getPresignedUrl(bucketName: string, objectKey: string) {
  return fetchApi(`/api/files/presigned-url/?bucket_name=${bucketName}&object_key=${objectKey}`);
}