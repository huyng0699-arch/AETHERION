import { useRequestGate } from '../hooks/useRequestGate';
import { copy } from '../uiCopy';
import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { Locale, Observation } from '../types';
import { t } from '../i18n';
import { ThemeColors, useThemedStyles } from '../theme';
import { ApiError } from '../api/client';
import { getObservations } from '../api/health';
import { ActionButton, AppHeader, AppPage, Body, Panel, StatusPill, Title } from '../components/ui';

export function MonitorScreen({ locale, token, subjectId, onBack, onUnauthorized }: {
  locale: Locale; token: string; subjectId?: string; onBack: () => void; onUnauthorized: () => void;
}) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  const [items, setItems] = useState<Observation[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refresh, setRefresh] = useState(0);
  const [cursor, setCursor] = useState<string | null>(null);
  const beginRequest = useRequestGate();
  const load = useCallback(async () => {
    const current = beginRequest();
    if (!subjectId) return;
    setBusy(true); setError(null);
    try { const page = await getObservations(subjectId, token); if (current()) { setItems(page.observations || []); setCursor(page.has_more ? page.next_cursor : null); } }
    catch (cause) {
      if (!current()) return;
      if (cause instanceof ApiError && cause.status === 401) onUnauthorized();
      else setError(cause instanceof ApiError && cause.status === 403 ? t(locale, 'forbidden') : cause instanceof ApiError && cause.status >= 500 ? t(locale, 'serverError') : t(locale, 'networkError'));
    } finally { if (current()) setBusy(false); }
  }, [locale, onUnauthorized, subjectId, token, refresh]);
  useEffect(() => { void load(); }, [load]);
  const more = async () => { if (!subjectId || !cursor || busy) return; const current = beginRequest(); setBusy(true); try { const page = await getObservations(subjectId, token, cursor); if (current()) { setItems(items => [...new Map([...items, ...page.observations].map(item => [item.id, item])).values()]); setCursor(page.has_more ? page.next_cursor : null); } } catch (cause) { if (current()) { if (cause instanceof ApiError && cause.status === 401) onUnauthorized(); else setError(t(locale, 'networkError')); } } finally { if (current()) setBusy(false); } };

  return (
    <AppPage>
      <AppHeader title={t(locale, 'monitorTitle')} onBack={onBack} backLabel={t(locale, 'back')} trailing={<Pressable accessibilityRole="button" onPress={() => setRefresh((v) => v + 1)}><Text style={styles.refresh}>{t(locale, 'refresh')}</Text></Pressable>} />
      <View style={styles.heading}><Title>{t(locale, 'monitorTitle')}</Title><Body>{t(locale, 'subject')}: {subjectId || '—'}</Body></View>
      <Panel style={styles.sensorNotice}><StatusPill label={copy(locale, token === 'aetherion-simulated-demo-session' ? 'demoSensorsOff' : 'sensorUnknown')} tone="neutral" /></Panel>
      {!subjectId ? <Panel><Body>{t(locale, 'noSubject')}</Body></Panel> : busy && items.length === 0 ? <View style={styles.loading}><ActivityIndicator color={colors.cyan} /><Body>{t(locale, 'loading')}</Body></View> : error ? <Panel><Text style={styles.error}>{error}</Text></Panel> : items.length === 0 ? <Panel><Text style={styles.panelTitle}>{t(locale, 'noData')}</Text><Body>{t(locale, 'noObservation')}</Body></Panel> : (
        <View style={styles.list}>
          {items.map((item) => <ObservationCard key={String(item.id)} item={item} locale={locale} />)}
          {cursor ? <ActionButton title={copy(locale, 'loadMore')} onPress={() => { void more(); }} loading={busy} secondary /> : null}
        </View>
      )}
    </AppPage>
  );
}

function ObservationCard({ item, locale }: { item: Observation; locale: Locale }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  const tone = item.quality === 'READY' ? 'good' : item.quality === 'STALE' ? 'warn' : item.quality === 'ERROR' || item.quality === 'DENIED' ? 'bad' : 'neutral';
  return <Panel style={styles.observation}>
    <View style={styles.observationTop}>
      <View style={{ flex: 1 }}><Text style={styles.metric}>{item.metric}</Text><Text style={styles.measurement}>{String(item.value)} <Text style={styles.unit}>{item.unit}</Text></Text></View>
      <StatusPill label={item.quality || 'UNVERIFIED'} tone={tone} />
    </View>
    <View style={styles.metaRow}><Text style={styles.metaLabel}>{t(locale, 'source')}</Text><Text numberOfLines={2} style={styles.metaValue}>{item.source || item.source_id || '—'}</Text></View>
    <View style={styles.metaRow}><Text style={styles.metaLabel}>{t(locale, 'recordedAt')}</Text><Text style={styles.metaValue}>{formatDate(item.observed_at, locale)}</Text></View>
    {!!item.verification_state && <View style={styles.metaRow}><Text style={styles.metaLabel}>{t(locale, 'verification')}</Text><Text style={styles.metaValue}>{item.verification_state}</Text></View>}
  </Panel>;
}

function formatDate(value: string, locale: Locale) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString(locale === 'vi' ? 'vi-VN' : 'en-US');
}

const buildStyles = (colors: ThemeColors) => StyleSheet.create({
  heading: { gap: 8, paddingTop: 8 },
  refresh: { color: colors.cyan, fontSize: 12, fontWeight: '800', padding: 8 },
  sensorNotice: { alignItems: 'flex-start' },
  panelTitle: { color: colors.text, fontWeight: '800', fontSize: 15, marginBottom: 6 },
  list: { gap: 10 },
  observation: { gap: 12 },
  observationTop: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  metric: { color: colors.text, fontSize: 15, fontWeight: '800' },
  measurement: { color: colors.cyan, fontSize: 23, fontWeight: '800', marginTop: 4 },
  unit: { color: colors.muted, fontSize: 14, fontWeight: '600' },
  metaRow: { flexDirection: 'row', justifyContent: 'space-between', gap: 12, borderTopWidth: 1, borderTopColor: colors.border, paddingTop: 9 },
  metaLabel: { color: colors.faint, fontSize: 11, fontWeight: '700' },
  metaValue: { flex: 1, color: colors.muted, fontSize: 11, textAlign: 'right' },
  loading: { flexDirection: 'row', gap: 10, alignItems: 'center', padding: 18 },
  error: { color: colors.red, lineHeight: 20 },
});

