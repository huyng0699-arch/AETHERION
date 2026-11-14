import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Image, Linking, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Locale } from '../types';
import { MessageKey, t } from '../i18n';
import { colors } from '../theme';
import { ApiError } from '../api/client';
import { AssistantChatRequest, AssistantProvider, AssistantStatus, ChatLine, getAssistantStatus, sendAssistantChat } from '../api/assistant';
import { AppHeader, AppPage, Body, Panel, StatusPill } from '../components/ui';

const AI_ORB = require('../../assets/aetherion-ai-orb.png');

type ChatBubble = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  provider?: AssistantProvider;
  model?: string;
  sources?: unknown[];
  notice?: string;
};

export function AiScreen({ locale, token, onBack, onUnauthorized }: {
  locale: Locale; token: string; onBack: () => void; onUnauthorized: () => void;
}) {
  const [status, setStatus] = useState<AssistantStatus | null>(null);
  const [checking, setChecking] = useState(true);
  const [statusError, setStatusError] = useState<MessageKey | null>(null);
  const [provider, setProvider] = useState<AssistantProvider>('local');
  const [cloudConsent, setCloudConsent] = useState(false);
  const [messages, setMessages] = useState<ChatBubble[]>([]);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);
  const [chatError, setChatError] = useState<MessageKey | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const loadStatus = useCallback(async () => {
    setChecking(true);
    setStatusError(null);
    try {
      const result = await getAssistantStatus(token);
      setStatus(result);
    } catch (error) {
      setStatus(null);
      if (error instanceof ApiError && error.status === 401) onUnauthorized();
      else setStatusError(errorMessageKey(error));
    } finally {
      setChecking(false);
    }
  }, [onUnauthorized, token]);

  useEffect(() => { void loadStatus(); }, [loadStatus, refreshKey]);

  const canSend = useMemo(() => {
    if (!status || checking || sending) return false;
    if (provider === 'local') return status.local_available;
    return status.cloud_available && cloudConsent;
  }, [checking, cloudConsent, provider, sending, status]);

  const send = async () => {
    const content = draft.trim();
    if (!content || content.length > 3000 || !canSend || !status) return;
    setDraft('');
    setChatError(null);
    setSending(true);
    const userMessage: ChatBubble = { id: makeId(), role: 'user', content };
    const priorMessages = messages;
    setMessages((current) => [...current, userMessage]);
    const requestBody: AssistantChatRequest = {
      messages: boundedHistory(priorMessages, content),
      provider,
      cloud_consent: provider === 'cloud' && cloudConsent,
      locale,
    };
    try {
      const result = await sendAssistantChat(token, requestBody);
      setMessages((current) => [...current, {
        id: makeId(), role: 'assistant', content: result.reply,
        provider: result.provider, model: result.model,
        sources: Array.isArray(result.sources) ? result.sources : [], notice: result.notice,
      }]);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) onUnauthorized();
      else setChatError(errorMessageKey(error));
      if (error instanceof ApiError && error.status === 503) setStatus(null);
    } finally {
      setSending(false);
    }
  };

  const localAvailable = !!status?.local_available;
  const cloudAvailable = !!status?.cloud_available;
  const available = localAvailable || cloudAvailable;

  return (
    <AppPage>
      <AppHeader title={t(locale, 'ai')} onBack={onBack} backLabel={t(locale, 'back')} trailing={
        <Pressable accessibilityRole="button" accessibilityLabel={t(locale, 'refresh')} onPress={() => setRefreshKey((value) => value + 1)} style={styles.refreshButton}>
          <Ionicons name="refresh" size={18} color={colors.cyan} />
        </Pressable>
      } />
      <View style={styles.hero}>
        <Image source={AI_ORB} resizeMode="contain" style={styles.orb} />
        {checking ? <View style={styles.statusRow}><ActivityIndicator color={colors.cyan} /><Text style={styles.statusText}>{t(locale, 'aiChecking')}</Text></View>
          : statusError ? <StatusPill label={t(locale, statusError)} tone="warn" />
            : available ? <StatusPill label={t(locale, 'serverOnline')} tone="good" />
              : <StatusPill label={t(locale, 'aiUnavailableTitle')} tone="warn" />}
      </View>

      {status && !checking ? (
        <Panel style={styles.providerPanel}>
          <View style={styles.providerChoices}>
            <ProviderButton
              title={providerLabel(t(locale, 'aiLocal'), status.local_model)}
              selected={provider === 'local'} available={localAvailable}
              onPress={() => { setProvider('local'); setCloudConsent(false); setChatError(null); }}
            />
            <ProviderButton
              title={providerLabel(t(locale, 'aiCloud'), status.cloud_model)}
              selected={provider === 'cloud'} available={cloudAvailable}
              onPress={() => { setProvider('cloud'); setCloudConsent(false); setChatError(null); }}
            />
          </View>
          {provider === 'cloud' && cloudAvailable ? (
            <View style={styles.consentGroup}>
              <Pressable accessibilityRole="checkbox" accessibilityState={{ checked: cloudConsent }} onPress={() => setCloudConsent((value) => !value)} style={styles.consentRow}>
                <Ionicons name={cloudConsent ? 'checkbox' : 'square-outline'} size={20} color={cloudConsent ? colors.cyan : colors.muted} />
                <Text style={styles.consentText}>{t(locale, 'aiCloudConsent')}</Text>
              </Pressable>
              {!cloudConsent ? <Text style={styles.consentHint}>{t(locale, 'aiCloudConsentRequired')}</Text> : null}
            </View>
          ) : null}
        </Panel>
      ) : null}

      {!checking && !status && statusError ? <Panel><Body>{t(locale, statusError)}</Body></Panel> : null}
      {!checking && status && !available ? <Panel><Body>{t(locale, 'aiUnavailable')}</Body></Panel> : null}

      {messages.length > 0 ? <View style={styles.transcript}>
        {messages.map((message) => <MessageBubble key={message.id} message={message} locale={locale} />)}
      </View> : null}

      {chatError ? <Panel style={styles.errorPanel}><Text style={styles.errorText}>{t(locale, chatError)}</Text></Panel> : null}
      {status && available ? (
        <Panel style={styles.composer}>
          <TextInput
            accessibilityLabel={t(locale, 'aiPromptPlaceholder')}
            value={draft}
            onChangeText={setDraft}
            placeholder={t(locale, 'aiPromptPlaceholder')}
            placeholderTextColor={colors.faint}
            selectionColor={colors.cyan}
            multiline
            maxLength={3000}
            editable={!checking && !sending && (provider === 'local' ? localAvailable : cloudAvailable)}
            onSubmitEditing={() => { void send(); }}
            style={styles.input}
          />
          <Pressable accessibilityRole="button" onPress={() => { void send(); }} disabled={!canSend || !draft.trim()} style={({ pressed }) => [styles.sendButton, (!canSend || !draft.trim()) && styles.disabled, pressed && styles.pressed]}>
            {sending ? <ActivityIndicator color="#FFFFFF" size="small" /> : <><Text style={styles.sendText}>{t(locale, 'aiSend')}</Text><Ionicons name="arrow-up" size={17} color="#FFFFFF" /></>}
          </Pressable>
        </Panel>
      ) : null}
      {sending ? <View style={styles.sendingRow}><ActivityIndicator color={colors.cyan} /><Text style={styles.statusText}>{t(locale, 'aiSending')}</Text></View> : null}
    </AppPage>
  );
}

function ProviderButton({ title, selected, available, onPress }: { title: string; selected: boolean; available: boolean; onPress: () => void }) {
  return <Pressable accessibilityRole="radio" accessibilityState={{ checked: selected, disabled: !available }} disabled={!available} onPress={onPress} style={[styles.providerButton, selected && styles.providerSelected, !available && styles.providerUnavailable]}>
    <Ionicons name={selected ? 'radio-button-on' : 'radio-button-off'} size={18} color={selected ? colors.cyan : colors.muted} />
    <Text numberOfLines={2} style={styles.providerText}>{title}</Text>
  </Pressable>;
}

function MessageBubble({ message, locale }: { message: ChatBubble; locale: Locale }) {
  return <View style={[styles.messageBubble, message.role === 'user' ? styles.userBubble : styles.assistantBubble]}>
    {message.role === 'assistant' && message.provider ? <Text style={styles.messageMeta}>{providerLabel(message.provider === 'local' ? t(locale, 'aiLocal') : t(locale, 'aiCloud'), message.model)}</Text> : null}
    <Text selectable style={[styles.messageText, message.role === 'user' && styles.userMessageText]}>{message.content}</Text>
    {message.role === 'assistant' && message.sources?.length ? <View style={styles.sources}>
      <Text style={styles.messageMeta}>{t(locale, 'source')}</Text>
      {message.sources.map((source, index) => <SourceLine key={`${message.id}-source-${index}`} value={source} />)}
    </View> : null}
    {message.role === 'assistant' && !message.sources?.length ? <Text style={styles.noticeText}>{t(locale, 'aiNoSources')}</Text> : null}
    {message.role === 'assistant' && message.notice ? <Text style={styles.noticeText}>{message.notice}</Text> : null}
  </View>;
}

function SourceLine({ value }: { value: unknown }) {
  const row = value && typeof value === 'object' ? value as Record<string, unknown> : null;
  const title = typeof value === 'string' ? value : String(row?.title || row?.citation || row?.source_id || '');
  const url = typeof row?.url === 'string' ? row.url : typeof row?.source_url === 'string' ? row.source_url : '';
  if (!title && !url) return null;
  return url ? <Pressable accessibilityRole="link" onPress={() => { void Linking.openURL(url); }}><Text style={styles.sourceLink}>{title || url}</Text></Pressable>
    : <Text style={styles.sourceText}>{title}</Text>;
}

function providerLabel(label: string, model: string | null | undefined) {
  return model ? `${label} · ${model}` : label;
}

function boundedHistory(prior: ChatBubble[], latest: string): ChatLine[] {
  const lines: ChatLine[] = prior.map(({ role, content }) => ({ role, content }));
  lines.push({ role: 'user', content: latest });
  while (lines.length > 16 || lines.reduce((total, item) => total + item.content.length, 0) > 12000) lines.shift();
  return lines;
}

function errorMessageKey(error: unknown): MessageKey {
  if (!(error instanceof ApiError)) return 'networkError';
  if (error.status === 401) return 'unauthorized';
  if (error.status === 403) return 'forbidden';
  if (error.status === 503) return 'aiUnavailable';
  if (error.status === 0 || error.status === 408) return 'networkError';
  if (error.status >= 500) return 'serverError';
  return 'aiRequestUnavailable';
}

function makeId() { return `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`; }

const styles = StyleSheet.create({
  refreshButton: { width: 38, height: 38, alignItems: 'center', justifyContent: 'center' },
  hero: { alignItems: 'center', gap: 8, paddingTop: 8, paddingBottom: 3 },
  orb: { width: 76, height: 76 },
  statusRow: { flexDirection: 'row', alignItems: 'center', gap: 9, minHeight: 31 },
  statusText: { color: colors.muted, fontSize: 12, fontWeight: '700' },
  providerPanel: { gap: 12 },
  providerChoices: { flexDirection: 'row', gap: 8 },
  providerButton: { flex: 1, minHeight: 50, flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 10, borderRadius: 14, borderWidth: 1, borderColor: colors.border, backgroundColor: '#FFFFFF' },
  providerSelected: { borderColor: colors.cyan, backgroundColor: '#F4F0FF' },
  providerUnavailable: { opacity: 0.42 },
  providerText: { flex: 1, color: colors.text, fontSize: 12, fontWeight: '800' },
  consentGroup: { gap: 5, borderTopWidth: 1, borderTopColor: colors.border, paddingTop: 11 },
  consentRow: { flexDirection: 'row', alignItems: 'center', gap: 8, minHeight: 30 },
  consentText: { flex: 1, color: colors.text, fontSize: 12, fontWeight: '700', lineHeight: 18 },
  consentHint: { color: colors.muted, fontSize: 11, marginLeft: 28 },
  transcript: { gap: 9 },
  messageBubble: { maxWidth: '92%', borderRadius: 19, padding: 13, gap: 8 },
  userBubble: { alignSelf: 'flex-end', backgroundColor: '#5D43E8', borderBottomRightRadius: 6 },
  assistantBubble: { alignSelf: 'flex-start', backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: colors.border, borderBottomLeftRadius: 6 },
  messageText: { color: colors.text, fontSize: 14, lineHeight: 21 },
  userMessageText: { color: '#FFFFFF' },
  messageMeta: { color: colors.cyan, fontSize: 10, fontWeight: '900', textTransform: 'uppercase', letterSpacing: 0.4 },
  noticeText: { color: colors.muted, fontSize: 11, lineHeight: 16 },
  sources: { gap: 5, borderTopWidth: 1, borderTopColor: colors.border, paddingTop: 8 },
  sourceText: { color: colors.text, fontSize: 11, lineHeight: 16 },
  sourceLink: { color: colors.cyan, fontSize: 11, lineHeight: 16, textDecorationLine: 'underline' },
  errorPanel: { borderColor: `${colors.red}44` },
  errorText: { color: colors.red, fontSize: 13, lineHeight: 19 },
  composer: { gap: 9 },
  input: { minHeight: 48, maxHeight: 130, paddingHorizontal: 12, paddingVertical: 10, color: colors.text, fontSize: 14, lineHeight: 20, borderWidth: 1, borderColor: colors.border, backgroundColor: '#FFFFFF', borderRadius: 14, textAlignVertical: 'top' },
  sendButton: { minHeight: 44, alignSelf: 'flex-end', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, paddingHorizontal: 16, borderRadius: 14, backgroundColor: colors.cyan },
  disabled: { opacity: 0.45 },
  pressed: { opacity: 0.82, transform: [{ scale: 0.98 }] },
  sendText: { color: '#FFFFFF', fontSize: 13, fontWeight: '900' },
  sendingRow: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 9, padding: 4 },
});
