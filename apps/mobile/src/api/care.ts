import { request } from './client';

export type CarePhase = 'GATHER' | 'EVALUATE' | 'ACT' | 'RECHECK' | 'CLOSED';
export type CareDataState = 'READY' | 'NO_DATA' | 'STALE' | 'OFFLINE' | 'DENIED' | 'ERROR' | 'UNVERIFIED' | string;
export type CareActionStatus = 'DONE' | 'NOT_DONE' | 'CANNOT_DO';
export type CareOutcome = 'BETTER' | 'UNCHANGED' | 'WORSE' | 'UNKNOWN';

export type CareEpisodeEvent = {
  event_id: number;
  phase: CarePhase;
  actor_id: string;
  source: string;
  unit: string;
  data_state: CareDataState;
  summary: string;
  payload: Record<string, unknown>;
  human_confirmed: boolean;
  recorded_at_utc: string;
};

export type CareEpisode = {
  episode_id: string;
  subject_id: string;
  actor_id: string;
  chief_concern: string;
  current_phase: CarePhase;
  ai_assisted: boolean;
  human_confirmed: boolean;
  created_at_utc: string;
  updated_at_utc: string;
  events: CareEpisodeEvent[];
};

export type BeginCareInput = {
  subject_id: string;
  chief_concern: string;
  symptom_terms: string[];
  interview_answers: Record<string, string>;
  explicit_consent: true;
};

export type AdvanceCareInput = {
  next_phase: Exclude<CarePhase, 'GATHER'> | 'GATHER';
  summary: string;
  action_status?: CareActionStatus;
  outcome?: CareOutcome;
  human_confirmed: true;
};

type CareEpisodeResponse = {
  episode: CareEpisode;
  clinical_assessment: 'NOT_ASSESSED' | string;
};

export type CareEpisodeListResponse = {
  subject_id: string;
  episodes: CareEpisode[];
};

export function listCareEpisodes(subjectId: string, token: string, limit = 30): Promise<CareEpisodeListResponse> {
  const query = `subject_id=${encodeURIComponent(subjectId)}&limit=${Math.max(1, Math.min(100, Math.floor(limit)))}`;
  return request(`/api/v1/care/episodes?${query}`, { token });
}

export async function getCareEpisode(episodeId: string, token: string): Promise<CareEpisode> {
  const response = await request<{ episode: CareEpisode }>(`/api/v1/care/episodes/${encodeURIComponent(episodeId)}`, { token });
  return response.episode;
}

export function startCareEpisode(input: BeginCareInput, token: string): Promise<CareEpisodeResponse> {
  return request('/api/v1/care/episodes', { method: 'POST', body: input, token });
}

export function advanceCareEpisode(episodeId: string, input: AdvanceCareInput, token: string): Promise<CareEpisodeResponse> {
  return request(`/api/v1/care/episodes/${encodeURIComponent(episodeId)}/advance`, {
    method: 'POST', body: input, token,
  });
}
