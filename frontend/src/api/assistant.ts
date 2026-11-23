import { apiClient } from './client';
import type { AssistantAnswer, CropCode } from '../types';

export async function apiAskAssistant(question: string, crop?: CropCode | null): Promise<AssistantAnswer> {
  const res = await apiClient.post<AssistantAnswer>('/api/assistant/ask', { question, crop: crop || null });
  return res.data;
}
