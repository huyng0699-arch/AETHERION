import React, { useEffect, useState } from 'react';
import { Linking, Pressable, StyleSheet, Text, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { Locale } from '../types';
import { MessageKey, t } from '../i18n';
import { ThemeColors, useThemedStyles } from '../theme';
import { ActionButton, AppHeader, AppPage, Body, Panel, StatusPill, Title } from '../components/ui';
import { loadNasaMa7Demo, syncNasaMa7Demo } from '../api/demo';
import { copy } from '../uiCopy';
import { OrbitEarth } from '../components/home/OrbitEarth';

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

export function HackathonDemoIntroScreen({ locale, onBack, onLoad, onLibrary }: { locale: Locale; onBack: () => void; onLoad: () => void; onLibrary?: () => void }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  const [details, setDetails] = useState(false);
  const [source, setSource] = useState<ReturnType<typeof loadNasaMa7Demo> | null>(() => {
    try { return loadNasaMa7Demo(); } catch { return null; }
  });
  useEffect(() => {
    let active = true;
    void syncNasaMa7Demo().then(value => { if (active) setSource(value); }).catch(() => {});
    return () => { active = false; };
  }, []);

  return (
    <AppPage>
      <AppHeader title={t(locale, 'demoTitle')} onBack={onBack} backLabel={t(locale, 'back')} />
      <LinearGradient colors={['#111733', '#1D2C58', '#42568A']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
        <View style={styles.heroEarth}><OrbitEarth size={205} /></View>
        <View style={styles.heroTop}><View style={styles.heroIcon}><Ionicons name="planet-outline" size={18} color="#C9EAFF" /></View><Text style={styles.heroKicker}>NASA · 1962</Text></View>
        <View style={styles.heroText}><Text style={styles.heroTitle}>{t(locale, 'demoIntroTitle')}</Text><Text style={styles.heroSub}>{locale === 'en' ? 'A mission in data.' : 'Hành trình qua dữ liệu.'}</Text></View>
        <View style={styles.heroBadge}><View style={styles.heroDot} /><Text style={styles.heroBadgeText}>{t(locale, 'demoHistorical')}</Text></View>
      </LinearGradient>

      {source ? (
        <>
          <View style={styles.briefing}>
            <View style={styles.briefingHeader}><View><Text style={styles.sectionKicker}>{locale === 'en' ? 'THE ARCHIVE' : 'DỮ LIỆU'}</Text><Text style={styles.briefingTitle}>{locale === 'en' ? 'A real flight, in focus' : 'Một chuyến bay thực'}</Text></View><Ionicons name="document-text-outline" size={22} color={colors.cyan} /></View>
            <Text style={styles.briefingText}>{locale === 'en' ? 'Explore the measurements recorded in NASA’s postflight report.' : 'Khám phá số liệu trong báo cáo sau chuyến bay của NASA.'}</Text>
            <View style={styles.factRow}>
              <View style={styles.fact}><Text style={styles.factValue}>{source.summary.timepoint_count}</Text><Text style={styles.factLabel}>{t(locale, 'demoTimepoints')}</Text></View>
              <View style={styles.fact}><Text style={styles.factValue}>{source.summary.metric_count}</Text><Text style={styles.factLabel}>{t(locale, 'demoMetrics')}</Text></View>
              <View style={styles.fact}><Text style={styles.factValue}>{source.summary.reported_value_count}</Text><Text style={styles.factLabel}>{t(locale, 'demoReportedValues')}</Text></View>
            </View>
            <Text style={styles.sourceMeta}>{source.summary.reported_value_count} {t(locale, 'demoReportedValues').toLowerCase()} · {copy(locale, source.origin === 'server' ? 'serverArchive' : 'bundledArchive')}</Text>
          </View>
          <ActionButton title={copy(locale, 'demoStart')} onPress={onLoad} />
          {onLibrary ? <Pressable accessibilityRole="button" onPress={onLibrary} style={styles.libraryAction}>
            <Ionicons name="book-outline" size={18} color={colors.cyan} /><Text style={styles.libraryText}>{locale === 'en' ? 'Explore NASA Library' : 'Khám phá thư viện NASA'}</Text><Ionicons name="arrow-forward" size={17} color={colors.cyan} />
          </Pressable> : null}
          <Pressable accessibilityRole="button" accessibilityState={{ expanded: details }} onPress={() => setDetails(value => !value)} style={styles.sourceLink}><Text style={styles.sourceLinkText}>{copy(locale, 'sourceDetails')}</Text><Ionicons name={details ? 'chevron-up' : 'chevron-down'} size={18} color={colors.cyan} /></Pressable>
          {details ? <>
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

          </> : null}
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
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  return <View style={styles.metaRow}><Text style={styles.metaLabel}>{label}</Text><Text style={styles.metaValue}>{value}</Text></View>;
}

const buildStyles = (colors: ThemeColors) => StyleSheet.create({
  hero: { borderRadius: 24, minHeight: 228, padding: 19, overflow: 'hidden', justifyContent: 'space-between' },
  heroEarth: { position: 'absolute', right: -24, top: 18, opacity: 0.95 },
  heroTop: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  heroIcon: { width: 32, height: 32, borderRadius: 11, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,0.11)' },
  heroText: { maxWidth: '66%', gap: 5, marginTop: 20 },
  heroTitle: { color: '#FFFFFF', fontSize: 25, lineHeight: 29, letterSpacing: -0.5, fontWeight: '800' },
  heroSub: { color: '#C1D1ED', fontSize: 12, lineHeight: 17 },
  heroBadge: { alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: 6, borderWidth: 1, borderColor: 'rgba(255,255,255,0.25)', borderRadius: 20, paddingHorizontal: 10, paddingVertical: 6, backgroundColor: 'rgba(7,15,39,0.28)' },
  heroDot: { width: 5, height: 5, borderRadius: 3, backgroundColor: '#9BDAEF' },
  heroBadgeText: { color: '#E3EDFF', fontSize: 10, fontWeight: '700' },
  badges: { flexDirection: 'row', flexWrap: 'wrap', gap: 7 },
  heroKicker: { color: '#D1DDF3', fontWeight: '800', fontSize: 10, letterSpacing: 1.2 },
  briefing: { paddingHorizontal: 3, paddingVertical: 3, gap: 9 },
  briefingHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  sectionKicker: { color: colors.cyan, fontSize: 9, fontWeight: '800', letterSpacing: 1.2, marginBottom: 4 },
  briefingTitle: { color: colors.text, fontSize: 19, lineHeight: 24, fontWeight: '800', letterSpacing: -0.4 },
  briefingText: { color: colors.muted, fontSize: 12, lineHeight: 18 },
  factRow: { flexDirection: 'row', gap: 8 },
  fact: { flex: 1, padding: 11, minHeight: 70, backgroundColor: colors.card, borderWidth: 1, borderColor: colors.border, borderRadius: 15 },
  factValue: { color: colors.text, fontSize: 20, fontWeight: '800' },
  factLabel: { color: colors.muted, fontSize: 9, lineHeight: 13, marginTop: 2 },
  sourceMeta: { color: colors.muted, fontSize: 10, lineHeight: 15 },
  libraryAction: { minHeight: 48, flexDirection: 'row', alignItems: 'center', paddingHorizontal: 13, gap: 9, borderRadius: 13, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.card },
  libraryText: { flex: 1, color: colors.text, fontSize: 13, fontWeight: '800' },
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
  unavailableChip: { paddingHorizontal: 9, paddingVertical: 6, borderRadius: 12, backgroundColor: colors.cardSoft },
  unavailableText: { color: colors.muted, fontSize: 11, fontWeight: '700' },
  errorPanel: { alignItems: 'flex-start' },
});

