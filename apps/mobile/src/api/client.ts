import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

const BASE_URL_KEY = 'aetherion.mobile.apiBaseUrl.v1';

export class ApiError extends Error {
  constructor(public readonly status: number, public readonly code: string, public readonly requestId?: string) {
    super(code);
    this.name = 'ApiError';
  }
}

export function normalizeBaseUrl(value: string): string {
  const normalized = value.trim().replace(/\/+$/, '');
  let url: URL;
  try {
    url = new URL(normalized);
  } catch {
    throw new Error('INVALID_SERVER_URL');
  }
  if (url.protocol !== 'https:' && url.protocol !== 'http:') throw new Error('INVALID_SERVER_URL');
  if (!__DEV__ && url.protocol !== 'https:') throw new Error('HTTPS_REQUIRED');
  if (url.username || url.password || url.search || url.hash) throw new Error('INVALID_SERVER_URL');
  return normalized;
}

export async function readServerUrl(): Promise<string> {
  const value = await AsyncStorage.getItem(BASE_URL_KEY);
  if (!value) throw new Error('SERVER_URL_MISSING');
  return normalizeBaseUrl(value);
}

export async function saveServerUrl(value: string): Promise<string> {
  const normalized = normalizeBaseUrl(value);
  await AsyncStorage.setItem(BASE_URL_KEY, normalized);
  return normalized;
}

export async function request<T>(
  path: string,
  options: { method?: string; body?: unknown; token?: string; timeoutMs?: number } = {},
): Promise<T> {
  const baseUrl = await readServerUrl();
  const requestId = `mob_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), options.timeoutMs ?? 15000);
  const headers: Record<string, string> = {
    Accept: 'application/json',
    'X-Request-Id': requestId,
  };
  if (options.token) headers.Authorization = `Bearer ${options.token}`;
  if (typeof options.body !== 'undefined') headers['Content-Type'] = 'application/json';

  try {
    const response = await fetch(`${baseUrl}${path.startsWith('/') ? path : `/${path}`}`, {
      method: options.method ?? 'GET',
      headers,
      body: typeof options.body === 'undefined' ? undefined : JSON.stringify(options.body),
      signal: controller.signal,
    });
    const raw = await response.text();
    let payload: any = undefined;
    if (raw.trim()) {
      try { payload = JSON.parse(raw); } catch { throw new ApiError(502, 'INVALID_RESPONSE', requestId); }
    }
    if (!response.ok) {
      const code = payload?.error?.code || (response.status === 401 ? 'UNAUTHORIZED' : response.status === 403 ? 'FORBIDDEN' : response.status === 404 ? 'NOT_FOUND' : 'SERVER_ERROR');
      throw new ApiError(response.status, code, response.headers.get('X-Request-Id') || requestId);
    }
    return payload as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if ((error as Error)?.name === 'AbortError') throw new ApiError(408, 'TIMEOUT', requestId);
    throw new ApiError(0, Platform.OS === 'web' ? 'NETWORK_OR_CORS' : 'NETWORK_ERROR', requestId);
  } finally {
    clearTimeout(timer);
  }
}

export type ServerReadiness = { service: string; status: string; database?: string };

export async function checkServer(): Promise<ServerReadiness> {
  const readiness = await request<ServerReadiness>('/ready', { timeoutMs: 5000 });
  if (readiness.status !== 'ready' || readiness.database !== 'ok') throw new ApiError(503, 'SERVER_NOT_READY');
  return readiness;
}
