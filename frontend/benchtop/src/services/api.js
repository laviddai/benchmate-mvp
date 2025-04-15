// frontend/benchtop/src/services/api.js
const API_BASE_URL = "http://127.0.0.1:8000";

export async function submitData(endpoint, formData) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || errorData.detail || "Error processing data");
  }
  return await response.json();
}

export default {
  submitData,
};
