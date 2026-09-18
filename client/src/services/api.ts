import axios from 'axios';

// Configure the base URL for the FastAPI backend
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const createProject = async (data: { name: string; location: string; description?: string }) => {
  const response = await api.post('/projects/', data);
  return response.data;
};

export const uploadGeoTIFF = async (projectId: number, file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post(`/projects/${projectId}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const triggerSuperResolution = async (projectId: number, objectName: string) => {
  const response = await api.post(`/projects/${projectId}/super-resolution`, null, {
    params: { object_name: objectName }
  });
  return response.data;
};

export const fetchMapBounds = async (projectId: number, objectName: string) => {
  // Extract file_id from object_name (projects/{id}/outputs/{file_id})
  // For super resolution, the output is projects/{id}/outputs/sr_{filename}
  const fileId = objectName.split("/").pop();
  const srFileId = `sr_${fileId}`;
  const response = await api.get(`/map/${projectId}/outputs/${srFileId}/bounds`);
  return response.data;
};

export const fetchInputMapBounds = async (projectId: number, objectName: string) => {
  const fileId = objectName.split("/").pop();
  const response = await api.get(`/map/${projectId}/inputs/${fileId}/bounds`);
  return response.data;
};

export const checkJobStatus = async (jobId: string) => {
  const response = await api.get(`/projects/jobs/${jobId}`);
  return response.data;
};

export const fetchValidationMetrics = async (projectId: number) => {
  const response = await api.get(`/validation/${projectId}/metrics`);
  return response.data;
};

export const queryGeoAssist = async (projectId: number, message: string) => {
  const response = await api.post(`/projects/${projectId}/assistant`, {
    message,
    project_id: projectId
  });
  return response.data;
};

export const listProjects = async () => {
  const response = await api.get('/projects/');
  return response.data;
};

export default api;
