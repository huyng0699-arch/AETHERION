import React, { useMemo, useState } from 'react';
import { ScrollView, StyleSheet, Text, View, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AppHeader, AppPage, Body, Panel, StatusPill } from '../components/ui';
import { loadNasaMa7Demo, NasaMeasure } from '../api/demo';
import { Locale } from '../types';
import { MessageKey, t } from '../i18n';
import { colors } from '../theme';

const UNAVAILABLE_LABELS: Record<string, MessageKey> = {
  ecg_waveform: 'demoUnavailableEcg',
  spo2: 'demoUnavailableSpo2',
  sleep: 'demoUnavailableSleep',
  mood: 'demoUnavailableMood',
  serum_glucose: 'demoUnavailableGlucose',
  radiation_person_dose: 'demoUnavailableRadiation',
  continuous_ecg: 'demoUnavailableContinuousEcg',
  longitudinal_sensor_stream: 'demoUnavailableLongitudinal',
};

const QUALIFIER_LABELS: Record<string, MessageKey> = {
  reported: 'demoQualifierReported',
  phase_mean: 'demoQualifierPhaseMean',
  instrument_category_I_caveated: 'demoQualifierInstrumentCaveated',
  source_tabulated: 'demoQualifierSourceTabulated',
  reported_combined: 'demoQualifierReportedCombined',
  reported_range: 'demoQualifierReportedRange',
};

export function HackathonDemoDataScreen({ locale, onBack }: { locale: Locale; onBack: () => void }) {
  let loaded: ReturnType<typeof loadNasaMa7Demo> | null = null;
  try { loaded = loadNasaMa7Demo(); } catch { /* Source validation fails closed below. */ }
  const [selectedGroupId, setSelectedGroupId] = useState('flight');
  const selectedGroup = useMemo(
    () => loaded?.data.groups.find((group) => group.id === selectedGroupId) || loaded?.data.groups[0] || null,
    [loaded, selectedGroupId],
  );

  return (
    <AppPage>
      <AppHeader title={t(locale, 'demoTitle')} onBack={onBack} backLabel={t(locale, 'back')} />
      {loaded && selectedGroup ? (
        <>
          <View style={styles.statusRow}>
            <StatusPill label={t(locale, 'demoHistorical')} tone="neutral" />
            <Text style={styles.count}>{loaded.summary.timepoint_count} · {t(locale, 'demoTimepoints')}</Text>
          </View>

          <Panel style={styles.sourcePanel}>
            <Text style={styles.sourceTitle}>{loaded.data.source_title}</Text>
            <Text style={styles.sourceMeta}>{loaded.data.source_publisher} · {loaded.data.source_publication}</Text>
            <Text style={styles.sourceMeta}>{t(locale, 'demoReportedValues')}: {loaded.summary.reported_value_count}</Text>
          </Panel>

          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.tabs}>
            {loaded.data.groups.map((group) => {
              const active = group.id === selectedGroup.id;
              return (
                <Pressable
                  accessibilityRole="tab"
                  accessibilityState={{ selected: active }}
                  key={group.id}
                  onPress={() => setSelectedGroupId(group.id)}
                  style={[styles.tab, active && styles.tabActive]}
                >
                  <Text style={[styles.tabText, active && styles.tabTextActive]}>{group.title[locale]}</Text>
                </Pressable>
              );
            })}
          </ScrollView>

          <Panel style={styles.groupPanel}>
            <View style={styles.groupHeading}>
              <Ionicons name="document-text-outline" size={18} color={colors.cyan} />
              <Text style={styles.groupTitle}>{selectedGroup.title[locale]}</Text>
            </View>
            <Text style={styles.sourceRef}>{t(locale, 'demoSourceTable')}: {selectedGroup.table}</Text>
            <Body style={styles.groupNote}>{selectedGroup.note[locale]}</Body>
          </Panel>

          {selectedGroup.records.map((record) => (
            <Panel key={record.id} style={styles.recordPanel}>
              <View style={styles.recordHeading}>
                <View style={styles.recordIcon}><Ionicons name="time-outline" size={17} color={colors.cyan} /></View>
                <Text style={styles.recordTitle}>{record.title[locale]}</Text>
              </View>
              {Object.entries(record.measures).map(([metricKey, measure]) => (
                <MeasureRow key={metricKey} locale={locale} label={loaded!.data.metric_names[metricKey]?.[locale] || metricKey} measure={measure} />
              ))}
            </Panel>
          ))}

          <Panel style={styles.unavailablePanel}>
            <Text style={styles.unavailableHeading}>{t(locale, 'demoUnavailableTitle')}</Text>
            <View style={styles.unavailableList}>
              {loaded.data.unavailable_metrics.map((metric) => (
                <View key={metric} style={styles.unavailableItem}>
                  <Ionicons name="remove-circle-outline" size={15} color={colors.muted} />
                  <Text style={styles.unavailableText}>{t(locale, UNAVAILABLE_LABELS[metric] || 'demoUnavailableOther')}</Text>
                </View>
              ))}
            </View>
          </Panel>
        </>
      ) : (
        <Panel style={styles.errorPanel}>
          <StatusPill label={t(locale, 'demoSourceError')} tone="bad" />
        </Panel>
      )}
    </AppPage>
  );
}

function MeasureRow({ locale, label, measure }: { locale: Locale; label: string; measure: NasaMeasure }) {
  const missingKey: MessageKey = measure.missing === 'not_reported'
    ? 'demoMissingNotReported'
    : measure.missing === 'not_obtained'
      ? 'demoMissingNotObtained'
      : 'demoValueUnavailable';
  const qualifierKey = QUALIFIER_LABELS[measure.qualifier] || 'demoQualifierOther';
  const value = measure.value === null ? t(locale, missingKey) : String(measure.value);
  const qualifier = t(locale, qualifierKey);

  return (
    <View style={styles.measureRow}>
      <View style={styles.measureTop}>
        <Text style={styles.metricName}>{label}</Text>
        <Text style={[styles.value, measure.value === null && styles.missingValue]}>{value}{measure.unit ? ` ${measure.unit}` : ''}</Text>
      </View>
      <View style={styles.measureMeta}>
        <Text style={styles.qualifier}>{qualifier}</Text>
        {measure.range !== null && <Text style={styles.metaText}>{t(locale, 'demoRange')}: {measure.range}</Text>}
        {measure.sample_count !== null && <Text style={styles.metaText}>{t(locale, 'demoSamples')}: {measure.sample_count}</Text>}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  statusRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8 },
  count: { color: colors.muted, fontSize: 11, fontWeight: '700' },
  sourcePanel: { gap: 6, paddingVertical: 13 },
  sourceTitle: { color: colors.text, fontSize: 13, fontWeight: '900', lineHeight: 18 },
  sourceMeta: { color: colors.muted, fontSize: 11, lineHeight: 15 },
  tabs: { gap: 8, paddingVertical: 1 },
  tab: { maxWidth: 210, minHeight: 38, paddingHorizontal: 12, paddingVertical: 8, justifyContent: 'center', borderRadius: 13, backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: colors.border },
  tabActive: { backgroundColor: '#EDE7FF', borderColor: '#CFC2FF' },
  tabText: { color: colors.muted, fontSize: 10, fontWeight: '800' },
  tabTextActive: { color: colors.cyan },
  groupPanel: { gap: 6, paddingVertical: 13 },
  groupHeading: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  groupTitle: { flex: 1, color: colors.text, fontSize: 13, fontWeight: '900' },
  sourceRef: { color: colors.cyan, fontSize: 11, fontWeight: '800', lineHeight: 15 },
  groupNote: { fontSize: 12, lineHeight: 17 },
  recordPanel: { gap: 0, paddingVertical: 13 },
  recordHeading: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 4, paddingBottom: 8, borderBottomWidth: 1, borderBottomColor: colors.border },
  recordIcon: { width: 28, height: 28, borderRadius: 10, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F1EDFF' },
  recordTitle: { flex: 1, color: colors.text, fontSize: 13, fontWeight: '900' },
  measureRow: { paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: '#F0EDF6', gap: 4 },
  measureTop: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 },
  metricName: { flex: 1, color: colors.text, fontSize: 12, fontWeight: '700', lineHeight: 16 },
  value: { flex: 1, color: colors.text, fontSize: 12, fontWeight: '900', textAlign: 'right', lineHeight: 16 },
  missingValue: { color: colors.muted, fontStyle: 'italic', fontWeight: '700' },
  measureMeta: { flexDirection: 'row', flexWrap: 'wrap', columnGap: 10, rowGap: 3 },
  qualifier: { color: colors.cyan, fontSize: 10, fontWeight: '800' },
  metaText: { color: colors.muted, fontSize: 10 },
  unavailablePanel: { gap: 9 },
  unavailableHeading: { color: colors.text, fontSize: 13, fontWeight: '900' },
  unavailableList: { gap: 7 },
  unavailableItem: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  unavailableText: { flex: 1, color: colors.muted, fontSize: 11, fontWeight: '700' },
  errorPanel: { alignItems: 'flex-start' },
});
