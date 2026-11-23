import { apiClient } from './client';
import type { CropCode, DiagnosisResult, DiagnosisListItem, FeedbackValue, GeoPoint } from '../types';

export async function apiPredict(file: File, crop: CropCode, location?: GeoPoint | null): Promise<DiagnosisResult> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('crop', crop);
  if (location) {
    // Sent only when the user opted in to the disease radar; the server coarsens it (~110 m).
    formData.append('latitude', String(location.lat));
    formData.append('longitude', String(location.lng));
    formData.append('share_to_radar', 'true');
  }

  const res = await apiClient.post<DiagnosisResult>('/api/predict', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return res.data;
}

export async function apiGetHistory(
  status?: string,
  search?: string,
  crop?: CropCode | null
): Promise<DiagnosisListItem[]> {
  const params: Record<string, string> = {};
  if (status && status !== 'all') params.status = status;
  if (search && search.trim()) params.search = search.trim();
  if (crop) params.crop = crop;

  const res = await apiClient.get<DiagnosisListItem[]>('/api/history', { params });
  return res.data;
}

export async function apiGetHistoryDetail(id: number): Promise<DiagnosisResult> {
  const res = await apiClient.get<DiagnosisResult>(`/api/history/${id}`);
  return res.data;
}

export async function apiDeleteHistory(id: number): Promise<{ message: string; id: number }> {
  const res = await apiClient.delete<{ message: string; id: number }>(`/api/history/${id}`);
  return res.data;
}

interface FeedbackResult {
  id: number;
  user_feedback: FeedbackValue;
  feedback_at: string;
}

export async function apiSubmitFeedback(id: number, feedback: FeedbackValue): Promise<FeedbackResult> {
  const res = await apiClient.post<FeedbackResult>(`/api/history/${id}/feedback`, { feedback });
  return res.data;
}
