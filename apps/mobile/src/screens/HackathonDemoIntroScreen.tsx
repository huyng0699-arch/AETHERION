import React from 'react';
import { Linking, Pressable, StyleSheet, Text, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { Locale } from '../types';
import { MessageKey, t } from '../i18n';
import { colors } from '../theme';
import { ActionButton, AppHeader, AppPage, Body, Panel, StatusPill, Title } from '../components/ui';
import { loadNasaMa7Demo } from '../api/demo';

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

export function HackathonDemoIntroScreen({ locale, onBack, onLoad }: { locale: Locale; onBack: () => void; onLoad: () => void }) {
  let source: ReturnType<typeof loadNasaMa7Demo> | null = null;
  let sourceError = false;
  try { source = loadNasaMa7Demo(); } catch { sourceError = true; }

  return (
    <AppPage>
      <AppHeader title={t(locale, 'demoTitle')} onBack={onBack} backLabel={t(locale, 'back')} />
      <LinearGradient colors={['#5D43E8', '#8975F7', '#B6A9FF']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
        <View style={styles.heroIcon}><Ionicons name="planet-outline" size={24} color="#FFFFFF" /></View>
        <Text style={styles.heroKicker}>{t(locale, 'demoKicker')}</Text>
        <Title size={23}>{t(locale, 'demoIntroTitle')}</Title>
        <StatusPill label={t(locale, 'demoHistorical')} tone="neutral" />
      </LinearGradient>

      {source ? (
        <>
          <Panel style={styles.sourcePanel}>
            <Text style={styles.reportTitle}>{source.data.source_title}</Text>
            <MetaRow label={t(locale, 'demoPublisher')} value={source.data.source_publisher} />
            <MetaRow label={t(locale, 'demoPublished')} value={source.data.source_publication} />
            <MetaRow label={t(locale, 'demoTimepoints')} value={String(source.summary.timepoint_count)} />
            <MetaRow label={t(locale, 'demoMetrics')} value={String(source.summary.metric_count)} />
            <MetaRow label={t(locale, 'demoReportedValues')} value={String(source.summary.reported_value_count)} />
            {source.data.groups.map((group) => (
              <View key={group.id} style={styles.sourceGroup}>
                <Text style={styles.groupTitle}>{group.title[locale]}</Text>
                <Text style={styles.tableRef}>{group.table}</Text>
              </View>
            ))}
            <Pressable accessibilityRole="link" onPress={() => void Linking.openURL(source!.data.source_url)} style={styles.sourceLink}>
              <Ionicons name="open-outline" size={16} color={colors.cyan} />
              <Text style={styles.sourceLinkText}>{t(locale, 'demoOpenNasaSource')}</Text>
            </Pressable>
            <Pressable accessibilityRole="link" onPress={() => void Linking.openURL(source!.data.challenge_link)} style={styles.sourceLink}>
              <Ionicons name="open-outline" size={16} color={colors.cyan} />
              <Text style={styles.sourceLinkText}>{t(locale, 'demoOpenChallenge')}</Text>
            </Pressable>
          </Panel>

          <Panel style={styles.limitsPanel}>
            <Text style={styles.sectionTitle}>{t(locale, 'demoLimitations')}</Text>
            <Body>{t(locale, 'demoHistoricalLimit')}</Body>
            <Text style={styles.unavailableHeading}>{t(locale, 'demoUnavailableTitle')}</Text>
            <View style={styles.unavailableList}>
              {source.data.unavailable_metrics.map((metric) => (
                <View key={metric} style={styles.unavailableChip}>
                  <Text style={styles.unavailableText}>{t(locale, UNAVAILABLE_LABELS[metric] || 'demoUnavailableOther')}</Text>
                </View>
              ))}
            </View>
          </Panel>

          <ActionButton title={t(locale, 'demoLoadData')} onPress={onLoad} />
        </>
      ) : (
        <Panel style={styles.errorPanel}>
          <StatusPill label={t(locale, 'demoSourceError')} tone="bad" />
        </Panel>
      )}
    </AppPage>
  );
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return <View style={styles.metaRow}><Text style={styles.metaLabel}>{label}</Text><Text style={styles.metaValue}>{value}</Text></View>;
}

const styles = StyleSheet.create({
  hero: { borderRadius: 27, padding: 18, gap: 9, shadowColor: '#4D2CCB', shadowOpacity: 0.16, shadowRadius: 14, shadowOffset: { width: 0, height: 8 }, elevation: 5 },
  heroIcon: { width: 46, height: 46, borderRadius: 16, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,0.2)' },
  heroKicker: { color: 'rgba(255,255,255,0.86)', fontWeight: '900', fontSize: 10, letterSpacing: 1.2 },
  sourcePanel: { gap: 12 },
  reportTitle: { color: colors.text, fontSize: 15, fontWeight: '900', lineHeight: 21 },
  metaRow: { flexDirection: 'row', justifyContent: 'space-between', gap: 10 },
  metaLabel: { color: colors.muted, fontSize: 12, fontWeight: '700' },
  metaValue: { color: colors.text, fontSize: 12, fontWeight: '800', textAlign: 'right' },
  sourceGroup: { borderTopWidth: 1, borderTopColor: colors.border, paddingTop: 9, gap: 3 },
  groupTitle: { color: colors.text, fontSize: 12, fontWeight: '800' },
  tableRef: { color: colors.muted, fontSize: 11 },
  sourceLink: { minHeight: 38, flexDirection: 'row', alignItems: 'center', gap: 8 },
  sourceLinkText: { color: colors.cyan, fontSize: 12, fontWeight: '800' },
  limitsPanel: { gap: 11 },
  sectionTitle: { color: colors.text, fontSize: 15, fontWeight: '900' },
  unavailableHeading: { color: colors.muted, fontSize: 12, fontWeight: '800' },
  unavailableList: { flexDirection: 'row', flexWrap: 'wrap', gap: 7 },
  unavailableChip: { paddingHorizontal: 9, paddingVertical: 6, borderRadius: 12, backgroundColor: '#F4F0FF' },
  unavailableText: { color: colors.muted, fontSize: 11, fontWeight: '700' },
  errorPanel: { alignItems: 'flex-start' },
});
