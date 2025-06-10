// frontend/benchtop-nextjs/src/lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// A generic fetch function for robustness
async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    // Handle cases with no content
    if (response.status === 204) {
        return null;
    }
    return response.json();
  } catch (error) {
    console.error(`API call to ${endpoint} failed:`, error);
    throw error;
  }
}

export async function uploadAndCreateDataset(formData: FormData) {
    const url = `${API_BASE_URL}/api/datasets/upload-and-create/`;
    try {
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
            // Don't set Content-Type header, browser does it for FormData with boundary
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        return response.json();
    } catch (error) {
        console.error(`API call to upload-and-create failed:`, error);
        throw error;
    }
}


export function submitVolcanoAnalysis(submissionData: any) {
  return fetchApi('/api/analyses/volcano-plot/submit', {
    method: 'POST',
    body: JSON.stringify(submissionData),
  });
}

export function getAnalysisRunStatus(analysisRunId: string) {
  return fetchApi(`/api/analysis-runs/${analysisRunId}`);
}

export function getPresignedUrl(bucketName: string, objectKey: string) {
  return fetchApi(`/api/files/presigned-url/?bucket_name=${bucketName}&object_key=${objectKey}`);
}

// We can use a simple fetch for the S3 content since it's a public URL
export async function getJsonFromS3(presignedUrl: string) {
    try {
        const response = await fetch(presignedUrl);
        if (!response.ok) {
            throw new Error(`S3 fetch error! status: ${response.status}`);
        }
        return response.json();
    } catch (error) {
        console.error(`Failed to fetch JSON from S3:`, error);
        throw error;
    }
}

export function createProject(projectName: string) {
  return fetchApi('/api/projects/', {
    method: 'POST',
    body: JSON.stringify({ name: projectName }),
  });
}