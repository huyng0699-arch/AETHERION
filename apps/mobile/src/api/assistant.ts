import { ApiError, request } from './client';

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
  runtime_configured: boolean;
  runtime_provider: string;
  runtime_model: string | null;
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
};

type InterviewAiStatus = { configured: boolean; provider: string; model: string | null };

export async function getAssistantStatus(token: string): Promise<AssistantStatus> {
  const runtime = await request<InterviewAiStatus>('/api/v1/knowledge/interview/ai-status', { token, timeoutMs: 12000 });
  return {
    // The server exposes interview runtime status, but does not expose a chat route.
    local_available: false, local_model: null,
    cloud_available: false, cloud_model: null,
    cloud_requires_consent: false, stored_by_server: false, clinical_validation: false,
    runtime_configured: runtime.configured === true,
    runtime_provider: runtime.provider || 'disabled', runtime_model: runtime.model || null,
  };
}

export async function sendAssistantChat(_token: string, _body: AssistantChatRequest): Promise<AssistantChatResult> {
  throw new ApiError(503, 'AI_CHAT_UNAVAILABLE');
}
