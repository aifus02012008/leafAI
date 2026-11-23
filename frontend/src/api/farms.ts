import { apiClient } from './client';
import type { FarmCreate, NotificationList, PushConfig, WatchedFarm } from '../types';

export async function apiListFarms(): Promise<WatchedFarm[]> {
  return (await apiClient.get<WatchedFarm[]>('/api/farms')).data;
}

export async function apiCreateFarm(payload: FarmCreate): Promise<WatchedFarm> {
  return (await apiClient.post<WatchedFarm>('/api/farms', payload)).data;
}

export async function apiUpdateFarm(
  id: number,
  payload: Partial<Pick<WatchedFarm, 'name' | 'radius_km' | 'alerts_enabled'>>
): Promise<WatchedFarm> {
  return (await apiClient.patch<WatchedFarm>(`/api/farms/${id}`, payload)).data;
}

export async function apiDeleteFarm(id: number): Promise<void> {
  await apiClient.delete(`/api/farms/${id}`);
}

export async function apiListNotifications(): Promise<NotificationList> {
  return (await apiClient.get<NotificationList>('/api/notifications')).data;
}

export async function apiMarkNotificationRead(id: number): Promise<void> {
  await apiClient.post(`/api/notifications/${id}/read`);
}

export async function apiMarkAllNotificationsRead(): Promise<void> {
  await apiClient.post('/api/notifications/read-all');
}

export async function apiGetPushConfig(): Promise<PushConfig> {
  return (await apiClient.get<PushConfig>('/api/push/config')).data;
}

export async function apiSubscribePush(sub: PushSubscriptionJSON): Promise<void> {
  await apiClient.post('/api/push/subscriptions', { endpoint: sub.endpoint, keys: sub.keys });
}

export async function apiUnsubscribePush(endpoint: string): Promise<void> {
  await apiClient.delete('/api/push/subscriptions', { data: { endpoint } });
}

export async function apiPurgeLocation(): Promise<{ diagnoses_cleared: number; farms_deleted: number }> {
  return (await apiClient.delete('/api/privacy/location')).data;
}
