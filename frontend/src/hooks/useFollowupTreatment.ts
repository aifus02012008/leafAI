import { useCallback, useEffect, useState } from 'react';
import { apiAddFollowup, apiGetTreatment } from '../api/treatments';
import { showToast } from '../components/Toast';
import type { FollowupResult, Treatment } from '../types';

/**
 * Re-photo mode for the diagnosis page (`/diagnose?followup=<treatmentId>`):
 * loads the treatment being checked and links the next diagnosis to it.
 */
export function useFollowupTreatment(treatmentId: number | null) {
  const [treatment, setTreatment] = useState<Treatment | null>(null);
  const [result, setResult] = useState<FollowupResult | null>(null);

  useEffect(() => {
    if (treatmentId === null) {
      setTreatment(null);
      return;
    }
    let active = true;
    apiGetTreatment(treatmentId)
      .then((t) => active && setTreatment(t))
      .catch(() => showToast('error', 'Không tìm thấy lần điều trị cần tái khám.'));
    return () => {
      active = false;
    };
  }, [treatmentId]);

  const submit = useCallback(
    async (diagnosisId: number) => {
      if (!treatment || result) return; // one follow-up per visit; retakes need a new visit
      try {
        setResult(await apiAddFollowup(treatment.id, diagnosisId));
      } catch (err: any) {
        const detail = err.response?.data?.detail;
        showToast('error', typeof detail === 'string' ? detail : 'Không đánh giá được hiệu quả điều trị.');
      }
    },
    [treatment, result]
  );

  const reset = useCallback(() => setResult(null), []);

  return { treatment, result, submit, reset };
}
