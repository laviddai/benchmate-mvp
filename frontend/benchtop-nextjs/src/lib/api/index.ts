// frontend/benchtop-nextjs/src/lib/api/index.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// A generic fetch function for robustness
export async function fetchApi(endpoint: string, options: RequestInit = {}) {
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
    if (response.status === 204) {
        return null;
    }
    return response.json();
  } catch (error) {
    console.error(`API call to ${endpoint} failed:`, error);
    throw error;
  }
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