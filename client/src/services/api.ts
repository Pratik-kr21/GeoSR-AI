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

// ─── New Intelligence API Functions ───────────────────────────────────────────

export const analyzeIntelligence = async (projectId: number, objectName: string) => {
  const response = await api.post(`/intelligence/${projectId}/analyze`, null, {
    params: { object_name: objectName },
    timeout: 120000, // analysis can take time
  });
  return response.data;
};

export const getIntelligenceSummary = async (projectId: number) => {
  const response = await api.get(`/intelligence/${projectId}/summary`);
  return response.data;
};

export const getSpectralIndices = async (projectId: number) => {
  const response = await api.get(`/intelligence/${projectId}/indices`);
  return response.data;
};

export const runChangeDetection = async (
  projectId: number,
  beforeObjectName: string,
  afterObjectName: string
) => {
  const response = await api.post(`/change-detection/${projectId}`, {
    before_object_name: beforeObjectName,
    after_object_name: afterObjectName,
  });
  return response.data;
};

export const getChangeDetection = async (projectId: number) => {
  const response = await api.get(`/change-detection/${projectId}`);
  return response.data;
};

export const getAnomalies = async (projectId: number) => {
  const response = await api.get(`/anomalies/${projectId}`);
  return response.data;
};

export const getRiskAssessment = async (projectId: number) => {
  const response = await api.get(`/risk/${projectId}`);
  return response.data;
};

// ─── Real-Time Satellite Data (CDSE + Open-Meteo) API Functions ───────────────

export interface RealtimeFetchParams {
  latitude?: number;
  longitude?: number;
  buffer_km?: number;    // default 5
  bbox?: [number, number, number, number];
  days_back?: number;    // default 30
  max_cloud_cover?: number; // default 20
}

export interface RealtimeFetchResult {
  observation_id: number;
  object_name: string;
  filename: string;
  acquisition_date: string | null;
  cloud_cover: number | null;
  bounds: [number, number, number, number] | null;
  weather_summary: {
    available: boolean;
    current_precip_mm: number | null;
    total_7d_rain_mm: number | null;
    daily_breakdown: { date: string; precip_mm: number }[];
  };
  message: string;
}

export interface FetchAndProcessResult {
  observation_id: number;
  object_name: string;
  sr_job_id: string;
  acquisition_date: string | null;
  cloud_cover: number | null;
  weather_summary: {
    available: boolean;
    current_precip_mm: number | null;
    total_7d_rain_mm: number | null;
  };
  message: string;
}

/** Check if CDSE credentials are configured on the backend. */
export const fetchRealtimeStatus = async () => {
  const response = await api.get('/realtime/status');
  return response.data as { cdse_enabled: boolean; message: string };
};

/**
 * Non-destructive catalog check: find out if a scene exists at these
 * coordinates without downloading anything. Fast (< 3s).
 */
export const checkSceneAvailability = async (params: RealtimeFetchParams) => {
  const response = await api.get('/realtime/check-availability', { params });
  return response.data;
};

/**
 * Download the latest Sentinel-2 scene for the given location and store
 * it in MinIO + PostgreSQL. Returns scene + weather metadata.
 * Does NOT start the SR pipeline.
 */
export const fetchRealtimeImagery = async (
  projectId: number,
  params: RealtimeFetchParams
): Promise<RealtimeFetchResult> => {
  const response = await api.post(
    `/realtime/fetch/${projectId}`,
    {
      latitude: params.latitude,
      longitude: params.longitude,
      buffer_km: params.buffer_km ?? 5,
      bbox: params.bbox,
      days_back: params.days_back ?? 30,
      max_cloud_cover: params.max_cloud_cover ?? 20,
    },
    { timeout: 300000 } // CDSE download can take up to 5 minutes
  );
  return response.data;
};

/** Get the most recently fetched real-time observation for a project. */
export const getLatestRealtimeObservation = async (projectId: number) => {
  const response = await api.get(`/realtime/latest/${projectId}`);
  return response.data;
};

/**
 * Full pipeline: download latest Sentinel-2 scene → upload → queue SR job.
 * Returns sr_job_id to poll with checkJobStatus().
 */
export const fetchAndProcessRealtime = async (
  projectId: number,
  params: RealtimeFetchParams
): Promise<FetchAndProcessResult> => {
  const response = await api.post(
    `/realtime/fetch-and-process/${projectId}`,
    {
      latitude: params.latitude,
      longitude: params.longitude,
      buffer_km: params.buffer_km ?? 5,
      bbox: params.bbox,
      days_back: params.days_back ?? 30,
      max_cloud_cover: params.max_cloud_cover ?? 20,
    },
    { timeout: 360000 } // download + SR queue
  );
  return response.data;
};

export default api;
