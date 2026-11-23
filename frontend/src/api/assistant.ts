import { apiClient } from './client';
import type { AssistantAnswer, CropCode } from '../types';

export async function apiAskAssistant(
  question: string,
  crop?: CropCode | null,
  diagnosisId?: number | null,
): Promise<AssistantAnswer> {
  const res = await apiClient.post<AssistantAnswer>('/api/assistant/ask', {
    question,
    crop: crop || null,
    diagnosis_id: diagnosisId ?? null,
  });
  return res.data;
}
