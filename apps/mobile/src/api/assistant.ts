import { request } from './client';

export type AssistantProvider = 'local' | 'cloud';
export type ChatRole = 'user' | 'assistant';

export type ChatLine = {
  role: ChatRole;
  content: string;
};

export type AssistantStatus = {
  local_available: boolean;
  local_model: string | null;
  cloud_available: boolean;
  cloud_model: string | null;
  cloud_requires_consent: boolean;
  stored_by_server: false;
  clinical_validation: false;
};

export type AssistantChatResult = {
  reply: string;
  model: string;
  provider: AssistantProvider;
  cloud_used: boolean;
  stored_by_server: false;
  clinical_validation: false;
  medical_decision: 'NOT_PERFORMED' | string;
  sources: unknown[];
  notice: string;
};

export type AssistantChatRequest = {
  messages: ChatLine[];
  provider: AssistantProvider;
  cloud_consent: boolean;
  locale: 'vi' | 'en';
  source_article_id?: string;
};

export function getAssistantStatus(token: string): Promise<AssistantStatus> {
  return request('/api/v1/assistant/status', { token, timeoutMs: 12000 });
}

export function sendAssistantChat(token: string, body: AssistantChatRequest): Promise<AssistantChatResult> {
  return request('/api/v1/assistant/chat', { method: 'POST', body, token, timeoutMs: 55000 });
}

