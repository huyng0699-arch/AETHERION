import { useRequestGate } from '../hooks/useRequestGate';
import { copy } from '../uiCopy';
import React, { useCallback, useEffect, useMemo, useState } from 'react';
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
  const metricSeries = useMemo(() => {
    const grouped = new Map<string, { metric: string; unit: string; sourceId: string | null; observations: Observation[] }>();
    items.forEach(item => {
      const sourceId = item.source_id?.trim() || null;
      const key = JSON.stringify([item.metric, item.unit, sourceId]);
      const current = grouped.get(key);
      if (current) current.observations.push(item);
      else grouped.set(key, { metric: item.metric, unit: item.unit, sourceId, observations: [item] });
    });
    return [...grouped.values()]
      .map(series => ({
        ...series,
        observations: [...series.observations].sort((left, right) => Date.parse(left.observed_at) - Date.parse(right.observed_at)),
      }))
      .sort((left, right) => Date.parse(right.observations[right.observations.length - 1]?.observed_at || '') - Date.parse(left.observations[left.observations.length - 1]?.observed_at || ''));
  }, [items]);
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
      {token !== 'aetherion-simulated-demo-session' ? <Panel style={styles.sensorNotice}><StatusPill label={copy(locale, 'sensorUnknown')} tone="neutral" /></Panel> : null}
      {!subjectId ? <Panel><Body>{t(locale, 'noSubject')}</Body></Panel> : busy && items.length === 0 ? <View style={styles.loading}><ActivityIndicator color={colors.primary} /><Body>{t(locale, 'loading')}</Body></View> : error ? <Panel><Text style={styles.error}>{error}</Text></Panel> : items.length === 0 ? <Panel><Text style={styles.panelTitle}>{t(locale, 'noData')}</Text><Body>{t(locale, 'noObservation')}</Body></Panel> : (
        <>
          <View style={styles.sectionHeading}>
            <Text style={styles.sectionTitle}>{locale === 'vi' ? 'Chỉ số theo thời gian' : 'Metrics over time'}</Text>
            <Text style={styles.sectionCaption}>{metricSeries.length} {locale === 'vi' ? 'chỉ số' : 'metrics'}</Text>
          </View>
          <View style={styles.metricGrid}>
            {metricSeries.map(series => <MetricTrendCard key={JSON.stringify([series.metric, series.unit, series.sourceId])} metric={series.metric} sourceId={series.sourceId} showSource={token !== 'aetherion-simulated-demo-session'} observations={series.observations} locale={locale} />)}
          </View>
          <View style={[styles.sectionHeading, styles.recordsHeading]}>
            <Text style={styles.sectionTitle}>{locale === 'vi' ? 'Bản ghi' : 'Records'}</Text>
            <Text style={styles.sectionCaption}>{items.length}</Text>
          </View>
          <View style={styles.list}>
            {items.map((item) => <ObservationCard key={String(item.id)} item={item} locale={locale} simulated={token === 'aetherion-simulated-demo-session'} />)}
          </View>
          {cursor ? <ActionButton title={copy(locale, 'loadMore')} onPress={() => { void more(); }} loading={busy} secondary /> : null}
        </>
      )}
    </AppPage>
  );
}

function ObservationCard({ item, locale, simulated }: { item: Observation; locale: Locale; simulated: boolean }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  const tone = item.quality === 'READY' ? 'good' : item.quality === 'STALE' ? 'warn' : item.quality === 'ERROR' || item.quality === 'DENIED' ? 'bad' : 'neutral';
  return <Panel style={styles.observation}>
    <View style={styles.observationTop}>
      <View style={{ flex: 1 }}><Text style={styles.metric}>{metricLabel(item.metric, locale)}</Text><Text style={styles.measurement}>{String(item.value)} <Text style={styles.unit}>{item.unit}</Text></Text></View>
      {!simulated ? <StatusPill label={item.quality || 'UNVERIFIED'} tone={tone} /> : null}
    </View>
    {!simulated ? <View style={styles.metaRow}><Text style={styles.metaLabel}>{t(locale, 'source')}</Text><Text numberOfLines={2} style={styles.metaValue}>{item.source || item.source_id || '—'}</Text></View> : null}
    <View style={styles.metaRow}><Text style={styles.metaLabel}>{t(locale, 'recordedAt')}</Text><Text style={styles.metaValue}>{formatDate(item.observed_at, locale)}</Text></View>
    {!simulated && !!item.verification_state ? <View style={styles.metaRow}><Text style={styles.metaLabel}>{t(locale, 'verification')}</Text><Text style={styles.metaValue}>{item.verification_state}</Text></View> : null}
  </Panel>;
}

function MetricTrendCard({ metric, sourceId, showSource, observations, locale }: { metric: string; sourceId?: string | null; showSource: boolean; observations: Observation[]; locale: Locale }) {
  const { colors, styles } = useThemedStyles(buildStyles);
  const [plotWidth, setPlotWidth] = useState(0);
  const plotHeight = 74;
  const numeric = observations.map(item => ({ item, value: Number(item.value), time: Date.parse(item.observed_at) })).filter(point => Number.isFinite(point.value));
  const minValue = Math.min(...numeric.map(point => point.value));
  const maxValue = Math.max(...numeric.map(point => point.value));
  const firstTime = numeric[0]?.time;
  const lastTime = numeric[numeric.length - 1]?.time;
  const observedSourceId = observations[0]?.source_id?.trim() || '';
  const hasSingleSource = Boolean(observedSourceId) && observations.every(item => item.source_id?.trim() === observedSourceId);
  const unit = observations[0]?.unit;
  const hasSingleUnit = observations.every(item => item.unit === unit);
  const hasDistinctTimes = new Set(numeric.map(point => point.time)).size > 1;
  const hasTimeSpan = numeric.length > 1 && hasSingleSource && hasSingleUnit && hasDistinctTimes && Number.isFinite(firstTime) && Number.isFinite(lastTime) && lastTime > firstTime;
  const plotPoints = numeric.map(point => {
    const x = plotWidth > 0 ? 8 + (hasTimeSpan ? (point.time - firstTime) / (lastTime - firstTime) : 0.5) * Math.max(0, plotWidth - 16) : 0;
    const range = maxValue - minValue;
    const y = range > 0 ? plotHeight - 8 - ((point.value - minValue) / range) * (plotHeight - 16) : plotHeight / 2;
    return { x, y, key: String(point.item.id) };
  });
  const segments = hasTimeSpan ? plotPoints.slice(1).map((point, index) => {
    const previous = plotPoints[index];
    const dx = point.x - previous.x;
    const dy = point.y - previous.y;
    const length = Math.sqrt(dx * dx + dy * dy);
    return { key: `${previous.key}-${point.key}`, left: (previous.x + point.x - length) / 2, top: (previous.y + point.y - 1) / 2, width: length, rotate: `${Math.atan2(dy, dx)}rad` };
  }) : [];
  const latest = observations[observations.length - 1];

  return (
    <Panel style={styles.chartCard}>
      <View style={styles.chartHeading}>
        <View style={styles.chartTitle}><Text numberOfLines={2} style={styles.chartMetric}>{metricLabel(metric, locale)}</Text>{showSource && sourceId ? <Text numberOfLines={1} style={styles.chartSource}>{sourceId}</Text> : null}</View>
        {latest ? <Text numberOfLines={1} style={styles.chartValue}>{String(latest.value)} <Text style={styles.chartUnit}>{latest.unit}</Text></Text> : null}
      </View>
      <View style={styles.chartPlot} onLayout={event => setPlotWidth(event.nativeEvent.layout.width)}>
        <View style={[styles.chartGuide, { top: plotHeight * 0.25 }]} />
        <View style={[styles.chartGuide, { top: plotHeight * 0.75 }]} />
        {segments.map(segment => <View key={segment.key} style={[styles.chartSegment, { left: segment.left, top: segment.top, width: segment.width, transform: [{ rotate: segment.rotate }] }]} />)}
        {plotPoints.map(point => <View key={point.key} style={[styles.chartPoint, { left: point.x - 4, top: point.y - 4 }]} />)}
      </View>
      <View style={styles.chartFooter}>
        <Text numberOfLines={1} style={styles.chartTime}>{numeric[0] ? formatDate(numeric[0].item.observed_at, locale) : '—'}</Text>
        <Text numberOfLines={1} style={styles.chartTime}>{latest ? formatDate(latest.observed_at, locale) : '—'}</Text>
      </View>
      {!hasTimeSpan ? <Text style={styles.chartNote}>{numeric.length < 2 ? (locale === 'vi' ? '1 bản ghi · chưa có xu hướng' : '1 record · no trend yet') : !hasSingleSource ? (locale === 'vi' ? 'Thiếu mã nguồn · không nối xu hướng' : 'Source ID missing · no connecting line') : !hasSingleUnit ? (locale === 'vi' ? 'Đơn vị không đồng nhất · không nối xu hướng' : 'Mixed units · no connecting line') : !hasDistinctTimes ? (locale === 'vi' ? 'Các bản ghi cùng thời điểm' : 'Records share the same timestamp') : (locale === 'vi' ? 'Không đủ mốc thời gian hợp lệ' : 'Insufficient valid timestamps')}</Text> : null}
    </Panel>
  );
}

function metricLabel(metric: string, locale: Locale) {
  const labels: Record<string, { en: string; vi: string }> = {
    heart_rate: { en: 'Heart rate', vi: 'Nhịp tim' },
    blood_pressure_systolic: { en: 'Systolic pressure', vi: 'Huyết áp tâm thu' },
    blood_pressure_diastolic: { en: 'Diastolic pressure', vi: 'Huyết áp tâm trương' },
    body_temperature: { en: 'Temperature', vi: 'Nhiệt độ' },
    oxygen_saturation: { en: 'O₂ saturation', vi: 'SpO₂' },
    respiratory_rate: { en: 'Respiratory rate', vi: 'Nhịp thở' },
    blood_glucose: { en: 'Glucose', vi: 'Đường huyết' },
    sleep_duration: { en: 'Sleep', vi: 'Giấc ngủ' },
    mood_self_report: { en: 'Mood', vi: 'Tâm trạng' },
    fatigue_self_report: { en: 'Fatigue', vi: 'Mệt mỏi' },
    steps: { en: 'Steps', vi: 'Bước chân' },
  };
  return labels[metric]?.[locale] || metric.replace(/_/g, ' ');
}

function formatDate(value: string, locale: Locale) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString(locale === 'vi' ? 'vi-VN' : 'en-US');
}

const buildStyles = (colors: ThemeColors) => StyleSheet.create({
  heading: { gap: 8, paddingTop: 8 },
  sectionHeading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingTop: 4 },
  sectionTitle: { color: colors.text, fontSize: 13, fontWeight: '900', letterSpacing: 0.4 },
  sectionCaption: { color: colors.muted, fontSize: 10, fontWeight: '700' },
  recordsHeading: { paddingTop: 10 },
  refresh: { color: colors.primary, fontSize: 12, fontWeight: '800', padding: 8 },
  sensorNotice: { alignItems: 'flex-start' },
  panelTitle: { color: colors.text, fontWeight: '800', fontSize: 15, marginBottom: 6 },
  list: { gap: 10 },
  metricGrid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', rowGap: 10 },
  chartCard: { width: '48%', minWidth: 0, gap: 5, padding: 10, borderRadius: 18 },
  chartHeading: { minHeight: 42, justifyContent: 'space-between' },
  chartTitle: { gap: 2 },
  chartMetric: { color: colors.text, fontSize: 11, lineHeight: 14, fontWeight: '800' },
  chartSource: { color: colors.muted, fontSize: 8, lineHeight: 10 },
  chartValue: { color: colors.primary, fontSize: 15, lineHeight: 18, fontWeight: '900', marginTop: 2 },
  chartUnit: { color: colors.muted, fontSize: 9, fontWeight: '700' },
  chartPlot: { height: 74, overflow: 'hidden', borderRadius: 10, backgroundColor: colors.cardSoft, position: 'relative' },
  chartGuide: { position: 'absolute', left: 4, right: 4, height: StyleSheet.hairlineWidth, backgroundColor: colors.border },
  chartSegment: { position: 'absolute', height: 2, borderRadius: 1, backgroundColor: colors.primary },
  chartPoint: { position: 'absolute', width: 8, height: 8, borderRadius: 4, borderWidth: 1.5, borderColor: colors.card, backgroundColor: colors.primary },
  chartFooter: { flexDirection: 'row', justifyContent: 'space-between', gap: 6 },
  chartTime: { flex: 1, color: colors.faint, fontSize: 8, lineHeight: 11 },
  chartNote: { color: colors.muted, fontSize: 9, lineHeight: 12 },
  observation: { gap: 12 },
  observationTop: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  metric: { color: colors.text, fontSize: 15, fontWeight: '800' },
  measurement: { color: colors.primary, fontSize: 23, fontWeight: '800', marginTop: 4 },
  unit: { color: colors.muted, fontSize: 14, fontWeight: '600' },
  metaRow: { flexDirection: 'row', justifyContent: 'space-between', gap: 12, borderTopWidth: 1, borderTopColor: colors.border, paddingTop: 9 },
  metaLabel: { color: colors.faint, fontSize: 11, fontWeight: '700' },
  metaValue: { flex: 1, color: colors.muted, fontSize: 11, textAlign: 'right' },
  loading: { flexDirection: 'row', gap: 10, alignItems: 'center', padding: 18 },
  error: { color: colors.red, lineHeight: 20 },
});

