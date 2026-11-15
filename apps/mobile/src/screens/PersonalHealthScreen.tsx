import { useRequestGate } from '../hooks/useRequestGate';
import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { Locale } from '../types';
import { Availability } from '../types';
import { t } from '../i18n';
import { ThemeColors, useThemedStyles } from '../theme';
import { getAvailability } from '../api/health';
import { ApiError } from '../api/client';
import { AppHeader, AppPage, Body, Panel, StatusPill, Title } from '../components/ui';

export function PersonalHealthScreen({ locale, token, subjectId, onBack, onUnauthorized }: {
  locale: Locale; token: string; subjectId?: string; onBack: () => void; onUnauthorized: () => void;
}) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  const [data, setData] = useState<Availability | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refresh, setRefresh] = useState(0);

  const beginRequest = useRequestGate();
  const load = useCallback(async () => {
    const current = beginRequest();
    if (!subjectId) return;
    setBusy(true); setError(null);
    try { const result = await getAvailability(subjectId, token); if (current()) setData(result); }
    catch (cause) {
      if (!current()) return;
      if (cause instanceof ApiError && cause.status === 401) onUnauthorized();
      else setError(errorText(locale, cause));
    } finally { if (current()) setBusy(false); }
  }, [locale, onUnauthorized, subjectId, token, refresh]);

  useEffect(() => { void load(); }, [load]);
  const status = data?.availability_status;
  const statusLabel = status === 'READY' ? t(locale, 'statusReady')
    : status === 'STALE' ? t(locale, 'statusStale')
      : status === 'NO_DATA' ? t(locale, 'statusNoData')
        : status === 'OFFLINE' ? t(locale, 'statusOffline')
          : status === 'DENIED' ? t(locale, 'statusDenied')
            : status === 'ERROR' ? t(locale, 'statusError')
              : status === 'UNVERIFIED' ? t(locale, 'statusUnverified')
                : t(locale, 'statusOther');
  const tone = status === 'READY' ? 'good'
    : status === 'STALE' || status === 'OFFLINE' ? 'warn'
      : status === 'NO_DATA' || status === 'UNVERIFIED' ? 'neutral'
        : 'bad';

  return (
    <AppPage>
      <AppHeader title={t(locale, 'healthTitle')} onBack={onBack} backLabel={t(locale, 'back')} trailing={<Pressable accessibilityRole="button" onPress={() => setRefresh((v) => v + 1)}><Text style={styles.refresh}>{t(locale, 'refresh')}</Text></Pressable>} />
      <View style={styles.heading}><Title>{t(locale, 'healthTitle')}</Title><Body>{t(locale, 'subject')}: {subjectId || '—'}</Body></View>
      {!subjectId ? <Panel><Body>{t(locale, 'noSubject')}</Body></Panel> : busy && !data ? <Loading label={t(locale, 'loading')} /> : error ? <Panel><Text style={styles.error}>{error}</Text></Panel> : data ? (
        <>
          <Panel style={styles.statusPanel}>
            <Text style={styles.label}>{t(locale, 'availability')}</Text>
            <StatusPill label={statusLabel} tone={tone} />
            {status === 'NO_DATA' ? <Body>{t(locale, 'noDataNote')}</Body> : null}
          </Panel>
          <View style={styles.stats}>
            <Metric label={t(locale, 'observations')} value={String(data.observation_count)} />
            <Metric label={t(locale, 'metrics')} value={String(data.metrics_present.length)} />
          </View>
          <Panel>
            <Text style={styles.label}>{t(locale, 'latest')}</Text>
            <Text style={styles.value}>{data.latest_observed_at ? formatDate(data.latest_observed_at, locale) : t(locale, 'noData')}</Text>
          </Panel>
          {data.metrics_present.length > 0 ? <Panel>
            <Text style={styles.label}>{t(locale, 'metrics')}</Text>
            <View style={styles.metricList}>{data.metrics_present.map((metric) => <Text key={metric} style={styles.metricTag}>{metric}</Text>)}</View>
          </Panel> : null}
        </>
      ) : null}
    </AppPage>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  return <Panel style={styles.metricCard}><Text style={styles.label}>{label}</Text><Text style={styles.bigValue}>{value}</Text></Panel>;
}
function Loading({ label }: { label: string }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles); return <View style={styles.loading}><ActivityIndicator color={colors.primary} /><Text style={styles.loadingText}>{label}</Text></View>; }
function formatDate(value: string, locale: Locale) { const date = new Date(value); return Number.isNaN(date.getTime()) ? value : date.toLocaleString(locale === 'vi' ? 'vi-VN' : 'en-US'); }
function errorText(locale: Locale, cause: unknown) {
  if (cause instanceof ApiError && cause.status === 403) return t(locale, 'forbidden');
  if (cause instanceof ApiError && cause.status === 404) return t(locale, 'notFound');
  if (cause instanceof ApiError && cause.status >= 500) return t(locale, 'serverError');
  return t(locale, 'networkError');
}

const buildStyles = (colors: ThemeColors) => StyleSheet.create({
  heading: { gap: 8, paddingTop: 8 },
  refresh: { color: colors.primary, fontSize: 12, fontWeight: '800', padding: 8 },
  statusPanel: { gap: 12 },
  label: { color: colors.muted, fontSize: 12, fontWeight: '700', letterSpacing: 0.3 },
  value: { color: colors.text, fontSize: 16, fontWeight: '700', marginTop: 8 },
  stats: { flexDirection: 'row', gap: 10 },
  metricCard: { flex: 1, minHeight: 95, justifyContent: 'space-between' },
  bigValue: { color: colors.text, fontSize: 28, fontWeight: '800' },
  metricList: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 10 },
  metricTag: { color: colors.primary, backgroundColor: 'rgba(104,217,242,0.10)', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 999, overflow: 'hidden', fontSize: 12, fontWeight: '700' },
  loading: { flexDirection: 'row', alignItems: 'center', gap: 10, padding: 18 },
  loadingText: { color: colors.muted },
  error: { color: colors.red, lineHeight: 20 },
});


