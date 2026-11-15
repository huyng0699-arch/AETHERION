import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { ApiError } from '../api/client';
import { clearCloudSettings, CloudProvider, CloudSettings, getCloudSettings, saveCloudSettings, testCloudSettings } from '../api/adminAi';
import { ActionButton, AppHeader, AppPage, Field, Panel, StatusPill } from '../components/ui';
import { useRequestGate } from '../hooks/useRequestGate';
import { ThemeColors, useThemedStyles } from '../theme';
import { Locale } from '../types';

const words = {
  en: {
    title: 'Server AI', back: 'Back', loading: 'Loading server settings',
    ready: 'Connection tested', configured: 'Configured · not tested', offline: 'Not configured',
    provider: 'Provider', model: 'Model ID', key: 'API key', keyOptional: 'API key · leave blank to keep current key',
    keyHint: 'The key stays in server memory until restart.', envHint: 'Environment settings are managed on the server.',
    configure: 'Save settings', test: 'Test saved settings', clear: 'Clear session settings', retry: 'Retry',
    saved: 'Settings saved. Test the connection.', tested: 'Connection test passed.', removed: 'Session settings cleared.',
    changed: 'The settings changed during the test. Test again.', badInput: 'Check the model ID and API key.',
    denied: 'Administrator access required.', unavailable: 'Server or provider unavailable.', network: 'Unable to reach the server.',
    secure: 'Use HTTPS for the server before saving an API key.', timeout: 'The request timed out.',
    testHint: 'The connection test sends no patient information.',
  },
  vi: {
    title: 'AI máy chủ', back: 'Quay lại', loading: 'Đang tải cấu hình máy chủ',
    ready: 'Đã kiểm tra kết nối', configured: 'Đã cấu hình · chưa kiểm tra', offline: 'Chưa cấu hình',
    provider: 'Nhà cung cấp', model: 'Mã mô hình', key: 'Khóa API', keyOptional: 'Khóa API · để trống để giữ khóa hiện tại',
    keyHint: 'Khóa chỉ ở trong bộ nhớ máy chủ đến khi khởi động lại.', envHint: 'Cấu hình môi trường được quản lý trên máy chủ.',
    configure: 'Lưu cấu hình', test: 'Kiểm tra cấu hình đã lưu', clear: 'Xóa cấu hình phiên', retry: 'Thử lại',
    saved: 'Đã lưu cấu hình. Hãy kiểm tra kết nối.', tested: 'Kiểm tra kết nối thành công.', removed: 'Đã xóa cấu hình phiên.',
    changed: 'Cấu hình đã thay đổi trong lúc kiểm tra. Hãy thử lại.', badInput: 'Kiểm tra mã mô hình và khóa API.',
    denied: 'Cần quyền quản trị viên.', unavailable: 'Máy chủ hoặc nhà cung cấp không khả dụng.', network: 'Không kết nối được máy chủ.',
    secure: 'Dùng HTTPS cho máy chủ trước khi lưu khóa API.', timeout: 'Yêu cầu đã hết thời gian.',
    testHint: 'Kiểm tra kết nối không gửi thông tin bệnh nhân.',
  },
} as const;

type Props = { locale: Locale; token: string; onBack: () => void; onUnauthorized: () => void };
type Busy = 'load' | 'save' | 'test' | 'clear' | null;

export function AiServerSettingsScreen({ locale, token, onBack, onUnauthorized }: Props) {
  const { colors, styles } = useThemedStyles(buildStyles);
  const text = words[locale];
  const [status, setStatus] = useState<CloudSettings | null>(null);
  const [provider, setProvider] = useState<CloudProvider>('gemini');
  const [model, setModel] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [busy, setBusy] = useState<Busy>('load');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const lock = useRef(false);
  const beginRequest = useRequestGate();

  const showFailure = useCallback((cause: unknown) => {
    if (cause instanceof ApiError && cause.status === 401) { onUnauthorized(); return; }
    if (cause instanceof Error && cause.message === 'HTTPS_REQUIRED_FOR_API_KEY') setError(text.secure);
    else if (cause instanceof ApiError && cause.status === 403) setError(text.denied);
    else if (cause instanceof ApiError && cause.status === 422) setError(text.badInput);
    else if (cause instanceof ApiError && cause.status === 408) setError(text.timeout);
    else if (cause instanceof ApiError && cause.status >= 500) setError(text.unavailable);
    else setError(text.network);
  }, [onUnauthorized, text]);

  const load = useCallback(async () => {
    if (lock.current) return;
    lock.current = true;
    const current = beginRequest();
    setBusy('load'); setError(''); setNotice('');
    try {
      const result = await getCloudSettings(token);
      if (current()) {
        setStatus(result);
        setProvider(result.provider || 'gemini');
        setModel(result.model || '');
      }
    } catch (cause) { if (current()) showFailure(cause); }
    finally { lock.current = false; if (current()) setBusy(null); }
  }, [beginRequest, showFailure, token]);

  useEffect(() => { void load(); }, [load]);

  const canReuseKey = status?.source === 'admin_memory' && status.provider === provider && status.key_configured;
  const save = async () => {
    if (lock.current || !model.trim() || (!apiKey.trim() && !canReuseKey)) return;
    lock.current = true;
    const current = beginRequest();
    const key = apiKey.trim();
    // Do not retain a secret in the input after an attempted configure.
    setApiKey(''); setBusy('save'); setError(''); setNotice('');
    try {
      const result = await saveCloudSettings(token, { provider, model: model.trim(), api_key: key || undefined, enabled: true });
      if (current()) { setStatus(result); setProvider(result.provider || provider); setModel(result.model || ''); setNotice(text.saved); }
    } catch (cause) { if (current()) showFailure(cause); }
    finally { lock.current = false; if (current()) setBusy(null); }
  };

  const test = async () => {
    if (lock.current || !status?.enabled) return;
    lock.current = true;
    const current = beginRequest();
    setBusy('test'); setError(''); setNotice('');
    try {
      const result = await testCloudSettings(token);
      const actual = await getCloudSettings(token);
      if (current()) {
        setStatus(actual);
        if (result.actual_inference && actual.tested && actual.provider === result.provider && actual.model === result.model) setNotice(text.tested);
        else setError(text.changed);
      }
    } catch (cause) { if (current()) showFailure(cause); }
    finally { lock.current = false; if (current()) setBusy(null); }
  };

  const clear = async () => {
    if (lock.current || status?.source !== 'admin_memory') return;
    lock.current = true;
    const current = beginRequest();
    setApiKey(''); setBusy('clear'); setError(''); setNotice('');
    try {
      const result = await clearCloudSettings(token);
      if (current()) { setStatus(result); setProvider(result.provider || 'gemini'); setModel(result.model || ''); setNotice(text.removed); }
    } catch (cause) { if (current()) showFailure(cause); }
    finally { lock.current = false; if (current()) setBusy(null); }
  };

  const selectProvider = (next: CloudProvider) => {
    if (busy) return;
    setProvider(next); setApiKey(''); setModel(status?.provider === next ? status.model || '' : '');
    setError(''); setNotice('');
  };
  const back = () => { setApiKey(''); onBack(); };
  const statusLabel = status?.tested ? text.ready : status?.enabled ? text.configured : text.offline;
  return <AppPage>
    <AppHeader title={text.title} onBack={back} backLabel={text.back} />
    {busy === 'load' && !status ? <View style={styles.loading}><ActivityIndicator color={colors.primary} /><Text style={styles.hint}>{text.loading}</Text></View> : null}
    {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
    {notice ? <Text accessibilityLiveRegion="polite" style={styles.notice}>{notice}</Text> : null}
    {!status && !busy ? <ActionButton title={text.retry} onPress={() => void load()} secondary /> : null}
    {status ? <>
      <Panel style={styles.panel}>
        <StatusPill label={statusLabel} tone={status.tested ? 'good' : status.enabled ? 'warn' : 'neutral'} />
        {status.provider && status.model ? <Text style={styles.current}>{status.provider === 'gemini' ? 'Gemini' : 'OpenAI'} · {status.model}</Text> : null}
        {status.source === 'environment' ? <Text style={styles.hint}>{text.envHint}</Text> : null}
      </Panel>
      <Panel style={styles.panel}>
        <Text style={styles.label}>{text.provider}</Text>
        <View style={styles.providers}>
          {(['gemini', 'openai'] as const).map(item => <Pressable key={item} accessibilityRole="radio" accessibilityState={{ checked: provider === item, disabled: !!busy }} disabled={!!busy} onPress={() => selectProvider(item)} style={[styles.provider, provider === item && styles.selected]}>
            <Ionicons name={provider === item ? 'radio-button-on' : 'radio-button-off'} size={18} color={provider === item ? colors.primary : colors.muted} />
            <Text style={styles.providerText}>{item === 'gemini' ? 'Gemini' : 'OpenAI'}</Text>
          </Pressable>)}
        </View>
        <Field label={text.model} value={model} onChangeText={setModel} editable={!busy} autoCapitalize="none" autoCorrect={false} maxLength={120} />
        <Field label={canReuseKey ? text.keyOptional : text.key} value={apiKey} onChangeText={setApiKey} editable={!busy} secureTextEntry autoCapitalize="none" autoCorrect={false} autoComplete="off" textContentType="none" importantForAutofill="no" maxLength={4096} />
        <Text style={styles.hint}>{text.keyHint}</Text>
        <ActionButton title={text.configure} onPress={() => void save()} loading={busy === 'save'} disabled={!!busy || !model.trim() || (!apiKey.trim() && !canReuseKey)} />
      </Panel>
      <Panel style={styles.panel}>
        <ActionButton title={text.test} onPress={() => void test()} loading={busy === 'test'} disabled={!!busy || !status.enabled} secondary />
        <Text style={styles.hint}>{text.testHint}</Text>
        {status.source === 'admin_memory' ? <ActionButton title={text.clear} onPress={() => void clear()} loading={busy === 'clear'} disabled={!!busy} secondary /> : null}
      </Panel>
    </> : null}
  </AppPage>;
}

const buildStyles = (colors: ThemeColors) => StyleSheet.create({
  panel: { gap: 12 },
  loading: { flexDirection: 'row', alignItems: 'center', gap: 9, padding: 14 },
  providers: { flexDirection: 'row', gap: 8 },
  provider: { flex: 1, minHeight: 47, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, borderWidth: 1, borderColor: colors.border, borderRadius: 13, backgroundColor: colors.card },
  selected: { borderColor: colors.primary, backgroundColor: colors.cardSoft },
  providerText: { color: colors.text, fontSize: 13, fontWeight: '800' },
  current: { color: colors.text, fontSize: 13, fontWeight: '700' },
  label: { color: colors.muted, fontSize: 12, fontWeight: '700' },
  hint: { color: colors.muted, fontSize: 12, lineHeight: 18 },
  error: { color: colors.red, fontSize: 13, lineHeight: 19, fontWeight: '700' },
  notice: { color: colors.green, fontSize: 13, lineHeight: 19, fontWeight: '700' },
});

