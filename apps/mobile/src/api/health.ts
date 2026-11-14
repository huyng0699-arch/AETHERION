import { Availability, ObservationPage } from '../types';
import { request } from './client';

export function getAvailability(subjectId: string, token: string): Promise<Availability> {
  return request(`/api/v1/subjects/${encodeURIComponent(subjectId)}/summary`, { token });
}

export function getObservations(
  subjectId: string,
  token: string,
  cursor?: string | null,
): Promise<ObservationPage> {
  const base = `subject_id=${encodeURIComponent(subjectId)}&limit=50&order=desc&include_non_live=false`;
  const query = cursor ? `${base}&cursor=${encodeURIComponent(cursor)}` : base;
  return request(`/api/v1/observations?${query}`, { token });
}
