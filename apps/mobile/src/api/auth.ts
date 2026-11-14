import { AuthSession, SessionIdentity } from '../types';
import { readServerUrl, request } from './client';
import { deleteSession, readSession } from '../storage/session';

export async function signIn(username: string, password: string): Promise<AuthSession> {
  const response = await request<AuthSession>('/api/v1/auth/login', {
    method: 'POST',
    body: { username: username.trim(), password },
    timeoutMs: 15000,
  });
  if (!response?.access_token || !response.user?.username) throw new Error('INVALID_LOGIN_RESPONSE');
  return { ...response, server_url: await readServerUrl() };
}

export async function validateSession(token: string): Promise<SessionIdentity> {
  return request('/api/v1/auth/me', { token, timeoutMs: 8000 });
}

export async function signOut(): Promise<void> {
  const session = await readSession();
  await deleteSession();
  if (session?.access_token && session.server_url) {
    try { await request('/api/v1/auth/logout', { method: 'POST', token: session.access_token, baseUrl: session.server_url, timeoutMs: 5000 }); } catch { /* Local sign-out must still complete offline. */ }
  }
}

