import { apiClient } from './client';
import type { CropCode, GeoPoint, RadarResponse } from '../types';

export async function apiGetRadar(point: GeoPoint, radiusKm: number, crop?: CropCode | null): Promise<RadarResponse> {
  const params: Record<string, string> = {
    lat: String(point.lat),
    lng: String(point.lng),
    radius_km: String(radiusKm),
  };
  if (crop) params.crop = crop;
  const res = await apiClient.get<RadarResponse>('/api/radar', { params });
  return res.data;
}
