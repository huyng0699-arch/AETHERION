import { Platform } from 'react-native';
import { ApiError, readServerUrl, request } from './client';
import { readSession } from '../storage/session';

export type CloudProvider = 'gemini' | 'openai';
export type CloudSettings = {
  enabled: boolean;
  provider: CloudProvider | null;
  model: string | null;
  key_configured: boolean;
  secret_storage: 'none' | 'memory_only' | 'environment';
  source: 'none' | 'admin_memory' | 'environment';
  requires_user_consent: boolean;
  tested: boolean;
};
export type CloudTestResult = {
  status: 'READY';
  provider: CloudProvider;
  model: string;
  latency_ms: number;
  actual_inference: boolean;
};
export type CloudSettingsInput = {
  provider: CloudProvider;
  model: string;
  api_key?: string;
  enabled: true;
};

const CLOUD_SETTINGS = '/api/v1/admin/ai/cloud/settings';
const CLOUD_TEST = '/api/v1/admin/ai/cloud/test';

export function getCloudSettings(token: string): Promise<CloudSettings> {
  return request(CLOUD_SETTINGS, { token });
}

export async function saveCloudSettings(token: string, input: CloudSettingsInput): Promise<CloudSettings> {
  // Pin the verified session to its original server before transmitting a key.
  const baseUrl = await readServerUrl();
  const session = await readSession();
  if (session?.access_token !== token || session.server_url !== baseUrl) {
    throw new ApiError(401, 'SESSION_SERVER_MISMATCH');
  }
  const origin = new URL(baseUrl);
  const loopback = ['127.0.0.1', 'localhost', '[::1]'].includes(origin.hostname);
  const emulator = Platform.OS === 'android' && __DEV__ && origin.hostname === '10.0.2.2';
  if (origin.protocol !== 'https:' && !loopback && !emulator) {
    throw new Error('HTTPS_REQUIRED_FOR_API_KEY');
  }
  return request(CLOUD_SETTINGS, { method: 'PUT', token, baseUrl, body: input });
}

export function clearCloudSettings(token: string): Promise<CloudSettings> {
  return request(CLOUD_SETTINGS, { method: 'DELETE', token });
}

export function testCloudSettings(token: string): Promise<CloudTestResult> {
  return request(CLOUD_TEST, { method: 'POST', token, timeoutMs: 55000 });
}
