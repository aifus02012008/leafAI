import { apiClient } from './client';
import type {
  ActiveIngredient,
  CropCode,
  DoseRequest,
  DoseResult,
  FollowupResult,
  HarvestResult,
  Treatment,
  TreatmentCreate,
} from '../types';

export async function apiGetActives(crop?: CropCode | null, disease?: string | null): Promise<ActiveIngredient[]> {
  const params: Record<string, string> = {};
  if (crop) params.crop = crop;
  if (disease) params.disease = disease;
  const res = await apiClient.get<ActiveIngredient[]>('/api/actives', { params });
  return res.data;
}

export async function apiCalcDose(payload: DoseRequest): Promise<DoseResult> {
  const res = await apiClient.post<DoseResult>('/api/tools/dose', payload);
  return res.data;
}

export async function apiCalcHarvest(sprays: { applied_on: string; phi_days: number }[]): Promise<HarvestResult> {
  const res = await apiClient.post<HarvestResult>('/api/tools/harvest-date', { sprays });
  return res.data;
}

export async function apiListTreatments(): Promise<Treatment[]> {
  const res = await apiClient.get<Treatment[]>('/api/treatments');
  return res.data;
}

export async function apiGetTreatment(id: number): Promise<Treatment> {
  const res = await apiClient.get<Treatment>(`/api/treatments/${id}`);
  return res.data;
}

export async function apiCreateTreatment(payload: TreatmentCreate): Promise<Treatment> {
  const res = await apiClient.post<Treatment>('/api/treatments', payload);
  return res.data;
}

export async function apiDeleteTreatment(id: number): Promise<void> {
  await apiClient.delete(`/api/treatments/${id}`);
}

export async function apiAddFollowup(treatmentId: number, diagnosisId: number): Promise<FollowupResult> {
  const res = await apiClient.post<FollowupResult>(`/api/treatments/${treatmentId}/followups`, {
    diagnosis_id: diagnosisId,
  });
  return res.data;
}
