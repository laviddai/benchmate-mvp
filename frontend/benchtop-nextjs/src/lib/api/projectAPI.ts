// frontend/benchtop-nextjs/src/lib/api/projectAPI.ts
import { fetchApi } from './index';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function createProject(projectName: string) {
  return fetchApi('/api/projects/', {
    method: 'POST',
    body: JSON.stringify({ name: projectName }),
  });
}

export async function uploadAndCreateDataset(formData: FormData) {
    const url = `${API_BASE_URL}/api/datasets/upload-and-create/`;
    try {
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
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