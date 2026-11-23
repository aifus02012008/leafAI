export interface User {
  id: number;
  email: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export type CropCode = string;

export type FeedbackValue = 'correct' | 'incorrect' | 'unsure';

export interface Crop {
  code: CropCode;
  name_vi: string;
  name_en: string;
  scientific_name: string;
  is_available: boolean;
  model_version: string | null;
  disease_count: number;
}

export interface Detection {
  id: number;
  class_name: string;
  confidence: number;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface DiagnosisResult {
  id: number;
  crop_code: CropCode;
  model_version?: string | null;
  original_image_url: string;
  result_image_url: string | null;
  status: 'detected' | 'no_detection';
  inference_time: number | null;
  created_at: string;
  detections: Detection[];
  user_feedback?: FeedbackValue | null;
  severity_pct?: number | null;
  summary: string;
}

export interface DiagnosisListItem {
  id: number;
  crop_code: CropCode;
  original_image_url: string;
  result_image_url: string | null;
  status: string;
  inference_time: number | null;
  created_at: string;
  detection_count: number;
  primary_disease: string | null;
  max_confidence: number | null;
  user_feedback?: FeedbackValue | null;
}

export interface Disease {
  id: number;
  crop_code: CropCode;
  class_name: string;
  display_name: string;
  description: string | null;
  symptoms: string | null;
  prevention: string | null;
  treatment: string | null;
  treatment_steps: string | null;
  recovery_info: string | null;
  image_path: string | null;
}

export interface RecentDiagnosisItem {
  id: number;
  status: string;
  created_at: string;
  detection_count: number;
  primary_disease: string | null;
  crop_code?: CropCode;
  original_image_url: string;
}

export interface DashboardStats {
  total_diagnoses: number;
  detected_count: number;
  no_detection_count: number;
  disease_distribution: Record<string, number>;
  crop_counts?: Record<CropCode, number>;
  recent_diagnoses: RecentDiagnosisItem[];
}

// ---------- Treatments & tools ----------

export interface ActiveIngredient {
  code: string;
  name: string;
  kind: string;
  moa_scheme: string;
  moa_code: string | null;
  banned: boolean;
  note: string | null;
  recommended: boolean;
}

export type AreaUnit = 'm2' | 'ha' | 'sao_bac_bo' | 'sao_trung_bo' | 'cong';
export type DoseBasis = 'per_tank' | 'per_ha';

export interface DoseRequest {
  area: number;
  area_unit: AreaUnit;
  tank_l: number;
  label_dose: number;
  label_dose_basis: DoseBasis;
  label_tank_l?: number | null;
  water_l_per_ha: number;
  pack_size?: number | null;
  pack_price?: number | null;
}

export interface DoseResult {
  area_m2: number;
  total_water_l: number;
  tanks_needed: number;
  product_per_tank: number;
  total_product: number;
  packs_needed: number | null;
  estimated_cost: number | null;
}

export interface HarvestResult {
  harvest_safe_on: string | null;
  days_remaining: number | null;
}

export type Verdict = 'effective' | 'unclear' | 'ineffective' | 'inconclusive';

export interface TreatmentFollowup {
  id: number;
  diagnosis_id: number | null;
  severity_after: number | null;
  relative_change: number | null;
  verdict: Verdict;
  created_at: string;
}

export interface FollowupResult extends TreatmentFollowup {
  severity_before: number | null;
  message: string;
  checklist: string[];
  rotation_suggestions: ActiveIngredient[];
}

export interface Treatment {
  id: number;
  diagnosis_id: number | null;
  crop_code: CropCode;
  disease_name: string | null;
  active_code: string;
  active_name: string;
  moa_code: string | null;
  product_name: string | null;
  applied_on: string;
  phi_days: number | null;
  harvest_safe_on: string | null;
  followup_due_on: string;
  area_m2: number | null;
  total_product: number | null;
  estimated_cost: number | null;
  severity_before: number | null;
  status: 'awaiting_followup' | 'evaluated';
  original_image_url: string | null;
  followups: TreatmentFollowup[];
  created_at: string;
}

export interface TreatmentCreate {
  diagnosis_id: number;
  active_code: string;
  product_name?: string | null;
  disease_name?: string | null;
  applied_on?: string | null;
  phi_days?: number | null;
  followup_days?: number;
  area_m2?: number | null;
  total_product?: number | null;
  estimated_cost?: number | null;
}

export interface AssistantAnswer {
  answer: string;
  source: 'ai' | 'library';
  related: { id: number; crop_code: CropCode; class_name: string }[];
}

// ---------- Disease radar ----------

export type RiskLevel = 'low' | 'medium' | 'high';

export interface DayWeather {
  day: string;
  humid_hours: number;
  rh_max: number;
  t_min: number;
  t_max: number;
  precip_mm: number;
}

export interface RadarAlert {
  crop_code: CropCode;
  disease: string;
  level: RiskLevel;
  score: number;
  cases: number;
  message: string;
  spray_before: string | null;
}

export interface RadarGridCell {
  lat: number;
  lng: number;
  cases: number;
  top_disease: string;
}

export interface RadarResponse {
  radius_km: number;
  lookback_days: number;
  total_cases: number;
  weather: DayWeather[] | null;
  alerts: RadarAlert[];
  grid: RadarGridCell[];
}

export interface GeoPoint {
  lat: number;
  lng: number;
}

// ---------- Farms, notifications, push ----------

export interface WatchedFarm {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  radius_km: number;
  crop_code: CropCode | null;
  alerts_enabled: boolean;
  created_at: string;
}

export interface FarmCreate {
  name: string;
  latitude: number;
  longitude: number;
  radius_km?: number;
  crop_code?: CropCode | null;
}

export interface AppNotification {
  id: number;
  kind: 'radar' | 'followup' | string;
  title: string;
  body: string;
  link: string | null;
  read_at: string | null;
  created_at: string;
}

export interface NotificationList {
  unread_count: number;
  items: AppNotification[];
}

export interface PushConfig {
  enabled: boolean;
  public_key: string | null;
}
