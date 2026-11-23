import { apiClient } from './client';
import type { Crop } from '../types';

export async function apiGetCrops(): Promise<Crop[]> {
  const res = await apiClient.get<Crop[]>('/api/crops');
  return res.data;
}
