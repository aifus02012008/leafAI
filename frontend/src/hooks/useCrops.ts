import { useEffect, useState } from 'react';
import { apiGetCrops } from '../api/crops';
import type { Crop, CropCode } from '../types';

/** Fallback shown while the API loads or if it is unreachable (tea is always supported). */
const FALLBACK_CROPS: readonly Crop[] = [
  {
    code: 'tea',
    name_vi: 'Chè',
    name_en: 'Tea',
    scientific_name: 'Camellia sinensis',
    is_available: true,
    model_version: null,
    disease_count: 0,
  },
];

let cachedRequest: Promise<Crop[]> | null = null;

function loadCrops(): Promise<Crop[]> {
  if (!cachedRequest) {
    cachedRequest = apiGetCrops().catch((err) => {
      cachedRequest = null; // allow a retry on next mount
      throw err;
    });
  }
  return cachedRequest;
}

export interface UseCropsResult {
  crops: readonly Crop[];
  loading: boolean;
  error: boolean;
  cropName: (code: CropCode | null | undefined) => string;
}

export function useCrops(): UseCropsResult {
  const [crops, setCrops] = useState<readonly Crop[]>(FALLBACK_CROPS);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<boolean>(false);

  useEffect(() => {
    let active = true;
    loadCrops()
      .then((data) => {
        if (active && data.length > 0) setCrops(data);
      })
      .catch(() => {
        if (active) setError(true);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const cropName = (code: CropCode | null | undefined): string =>
    crops.find((c) => c.code === code)?.name_vi ?? (code === 'tea' || !code ? 'Chè' : code);

  return { crops, loading, error, cropName };
}
