import { apiClient } from './client';
import type { CropCode, Disease } from '../types';

export async function apiGetDiseases(search?: string, crop?: CropCode | null): Promise<Disease[]> {
  const params: Record<string, string> = {};
  if (search && search.trim()) params.search = search.trim();
  if (crop) params.crop = crop;

  const res = await apiClient.get<Disease[]>('/api/diseases', { params });
  return res.data;
}

export async function apiGetDiseaseDetail(id: number): Promise<Disease> {
  const res = await apiClient.get<Disease>(`/api/diseases/${id}`);
  return res.data;
}
