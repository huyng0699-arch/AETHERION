import { Availability, Observation, ObservationPage } from '../types';

export const DEMO_TOKEN = 'aetherion-simulated-demo-session';
export const DEMO_SUBJECT_ID = 'demo-crew';
export const isDemoToken = (token: string) => token === DEMO_TOKEN;

const observedAt = new Date(Date.now() - 2 * 60_000).toISOString();
const source = 'AETHERION Demo Simulator · SIMULATED';
const readings: Array<{ metric: string; value: number; unit: string }> = [
  { metric: 'heart_rate', value: 72, unit: 'bpm' },
  { metric: 'blood_pressure_systolic', value: 118, unit: 'mmHg' },
  { metric: 'blood_pressure_diastolic', value: 76, unit: 'mmHg' },
  { metric: 'body_temperature', value: 36.7, unit: '°C' },
  { metric: 'oxygen_saturation', value: 98, unit: '%' },
  { metric: 'respiratory_rate', value: 16, unit: 'breaths/min' },
  { metric: 'blood_glucose', value: 92, unit: 'mg/dL' },
  { metric: 'sleep_duration', value: 7.5, unit: 'h' },
  { metric: 'mood_self_report', value: 4, unit: '/5' },
  { metric: 'fatigue_self_report', value: 2, unit: '/5' },
  { metric: 'steps', value: 6842, unit: 'steps' },
];

export function getDemoAvailability(subjectId: string): Availability {
  return {
    availability_status: 'UNVERIFIED',
    observation_count: readings.length,
    latest_observed_at: observedAt,
    age_seconds: 120,
    metrics_present: readings.map(({ metric }) => metric),
    stale_after_seconds: 0,
    note: 'SIMULATED DEMO DATA. No sensor or person supplied these values.',
  };
}

export function getDemoObservations(subjectId: string): ObservationPage {
  const observations: Observation[] = readings.map(({ metric, value, unit }, index) => ({
    id: `demo-${index + 1}`,
    subject_id: subjectId,
    metric,
    value,
    unit,
    source_id: 'aetherion-demo-simulator',
    source,
    observed_at: observedAt,
    quality: 'SIMULATED',
    verification_state: 'DEMO_ONLY · NOT A DEVICE READING',
    scope: 'DEMO',
  }));
  return { subject_id: subjectId, observations, has_more: false, next_cursor: null, note: 'SIMULATED DEMO DATA' };
}
