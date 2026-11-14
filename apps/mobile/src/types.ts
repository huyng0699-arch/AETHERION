export type Locale = 'vi' | 'en';

export type AuthUser = {
  username: string;
  role: string;
  allowed_subjects: string[];
};

export type AuthSession = {
  access_token: string;
  token_type: 'bearer' | string;
  expires_at: string;
  user: AuthUser;
};

export type SessionIdentity = {
  username: string;
  role: string;
  allowed_subjects: string[];
  expires_at: string;
};

export type Availability = {
  availability_status: 'NO_DATA' | 'READY' | 'STALE' | 'OFFLINE' | 'DENIED' | 'ERROR' | 'UNVERIFIED' | string;
  observation_count: number;
  latest_observed_at: string | null;
  age_seconds: number | null;
  metrics_present: string[];
  stale_after_seconds: number;
  clinical_interpretation?: string;
  note?: string;
};

export type Observation = {
  id: number | string;
  subject_id: string;
  metric: string;
  value: number;
  unit: string;
  source_id?: string | null;
  source?: string | null;
  observed_at: string;
  quality: string;
  verification_state?: string;
  scope?: string;
};

export type ObservationPage = {
  subject_id: string;
  observations: Observation[];
  has_more: boolean;
  next_cursor: string | null;
  note?: string;
};
