import React, { useEffect, useRef, useState } from 'react';
import { Animated, Linking, Platform, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { AppHeader, AppPage, Body, Panel, StatusPill } from '../components/ui';
import { loadNasaMa7Demo, syncNasaMa7Demo, NasaMeasure } from '../api/demo';
import { Locale } from '../types';
import { MessageKey, t } from '../i18n';
import { copy } from '../uiCopy';
import { ThemeColors, useThemedStyles } from '../theme';
const tabs = ['phases', 'clinical', 'blood', 'pressure'] as const;
const qualifiers: Record<string, MessageKey> = { reported: 'demoQualifierReported', phase_mean: 'demoQualifierPhaseMean', instrument_category_I_caveated: 'demoQualifierInstrumentCaveated', source_tabulated: 'demoQualifierSourceTabulated', reported_combined: 'demoQualifierReportedCombined', reported_range: 'demoQualifierReportedRange' };
export function HackathonDemoDataScreen({ locale, onBack }: { locale: Locale; onBack: () => void }) {
  const { colors, styles, appearance } = useThemedStyles(buildStyles);
  const [groupIndex, setGroupIndex] = useState(0), [recordIndex, setRecordIndex] = useState(0), [details, setDetails] = useState(false);
  const [loaded, setLoaded] = useState<ReturnType<typeof loadNasaMa7Demo> | null>(() => {
    try { return loadNasaMa7Demo(); } catch { return null; }
  });
  const recordFade = useRef(new Animated.Value(1)).current;
  useEffect(() => {
    if (appearance.reduceMotion) { recordFade.setValue(1); return; }
    recordFade.setValue(0.4);
    const animation = Animated.timing(recordFade, { toValue: 1, duration: 200, useNativeDriver: Platform.OS !== 'web' });
    animation.start();
    return () => animation.stop();
  }, [groupIndex, recordIndex, appearance.reduceMotion, recordFade]);
  useEffect(() => {
    let active = true;
    void syncNasaMa7Demo().then(value => { if (active) setLoaded(value); }).catch(() => {});
    return () => { active = false; };
  }, []);
  const group = loaded?.data.groups[groupIndex], record = group?.records[recordIndex];
  return <AppPage><AppHeader title={copy(locale, 'archive')} onBack={onBack} backLabel={t(locale, 'back')} />
    {loaded && group && record ? <>
      <LinearGradient colors={['#4830BB', '#765DE0', '#9B88EF']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.summary}>
        <View style={styles.summaryTop}><Text style={styles.summaryEyebrow}>NASA FLIGHT ARCHIVE</Text><Ionicons name="planet-outline" size={22} color="#FFFFFF" /></View>
        <Text style={styles.summaryTitle}>{copy(locale, 'demoCaption')}</Text>
        <Text style={styles.summaryMeta}>{loaded.summary.timepoint_count} {t(locale, 'demoTimepoints').toLowerCase()} · {loaded.summary.reported_value_count} {t(locale, 'demoReportedValues').toLowerCase()}</Text>
        <View style={styles.summaryBadges}><Text style={styles.summaryBadge}>{copy(locale, 'noLive')}</Text><Text style={styles.summaryBadge}>{copy(locale, loaded.origin === 'server' ? 'serverArchive' : 'bundledArchive')}</Text></View>
      </LinearGradient>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.tabs}>{loaded.data.groups.map((entry, index) => <Pressable key={entry.id} accessibilityRole="tab" accessibilityLabel={copy(locale, tabs[index])} accessibilityState={{ selected: index === groupIndex }} onPress={() => { setGroupIndex(index); setRecordIndex(0); }} style={[styles.tab, index === groupIndex && styles.active]}><Text style={[styles.tabText, index === groupIndex && styles.activeText]}>{copy(locale, tabs[index])}</Text></Pressable>)}</ScrollView>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.records}>{group.records.map((entry, index) => <Pressable key={entry.id} accessibilityRole="button" accessibilityState={{ selected: index === recordIndex }} onPress={() => setRecordIndex(index)} style={[styles.recordChip, index === recordIndex && styles.active]}><Text style={[styles.chipText, index === recordIndex && styles.activeText]}>{entry.title[locale]}</Text></Pressable>)}</ScrollView>
      <View style={styles.recordHeader}><View style={{ flex: 1 }}><Text style={styles.heading}>{record.title[locale]}</Text><Text style={styles.meta}>{recordIndex + 1} / {group.records.length}</Text></View><Pressable accessibilityRole="button" accessibilityLabel={copy(locale, 'previous')} disabled={recordIndex === 0} style={[styles.step, recordIndex === 0 && styles.disabled]} onPress={() => setRecordIndex(value => value - 1)}><Ionicons name="chevron-back" color={colors.primary} size={22} /></Pressable><Pressable accessibilityRole="button" accessibilityLabel={copy(locale, 'next')} disabled={recordIndex >= group.records.length - 1} style={[styles.step, recordIndex >= group.records.length - 1 && styles.disabled]} onPress={() => setRecordIndex(value => value + 1)}><Ionicons name="chevron-forward" color={colors.primary} size={22} /></Pressable></View>
      <Animated.View style={[styles.grid, { opacity: recordFade }]}>{Object.entries(record.measures).map(([metric, measure]) => <Measure key={`${record.id}:${metric}`} label={loaded!.data.metric_names[metric]?.[locale] || metric} measure={measure} locale={locale} />)}</Animated.View>
      <Panel style={styles.note}><Text style={styles.sourceLabel}>{t(locale, 'demoSourceTable')}</Text><Text selectable style={styles.sourceText}>{group.table}</Text><Body style={styles.sourceText}>{group.note[locale]}</Body></Panel>
      <Pressable accessibilityRole="button" onPress={() => setDetails(value => !value)} style={styles.disclosure}><Text style={styles.activeText}>{copy(locale, 'sourceDetails')}</Text><Ionicons name={details ? 'chevron-up' : 'chevron-down'} color={colors.primary} size={18} /></Pressable>
      {details ? <Panel style={styles.note}><Text style={styles.sourceText}>{loaded.data.source_title}</Text><Text style={styles.meta}>{loaded.data.source_publisher} · {loaded.data.source_publication}</Text><Body>{t(locale, 'demoHistoricalLimit')}</Body><Text style={styles.sourceLabel}>{t(locale, 'demoUnavailableTitle')}</Text><Body>{loaded.data.unavailable_metrics.join(' · ')}</Body><Pressable accessibilityRole="link" onPress={() => { void Linking.openURL(loaded!.data.source_url); }}><Text style={styles.activeText}>{t(locale, 'demoOpenNasaSource')}</Text></Pressable></Panel> : null}
    </> : <Panel><StatusPill label={t(locale, 'demoSourceError')} tone="bad" /></Panel>}
  </AppPage>;
}
function Measure({ label, measure, locale }: { label: string; measure: NasaMeasure; locale: Locale }) {
  const { colors, styles } = useThemedStyles(buildStyles);
  const missing = measure.missing === 'not_reported' ? 'demoMissingNotReported' : measure.missing === 'not_obtained' ? 'demoMissingNotObtained' : 'demoValueUnavailable';
  return <Panel style={styles.measure}><Text style={styles.metric}>{label}</Text><Text selectable style={[styles.value, measure.value === null && styles.missing]}>{measure.value === null ? t(locale, missing) : String(measure.value)}</Text>{measure.value !== null && measure.unit ? <Text style={styles.unit}>{measure.unit}</Text> : null}<Text style={styles.qualifier}>{t(locale, qualifiers[measure.qualifier] || 'demoQualifierOther')}</Text>{measure.range !== null ? <Text style={styles.meta}>{t(locale, 'demoRange')}: {measure.range}</Text> : null}{measure.sample_count !== null ? <Text style={styles.meta}>{t(locale, 'demoSamples')}: {measure.sample_count}</Text> : null}</Panel>;
}
const buildStyles = (colors: ThemeColors) => StyleSheet.create({
  summary: { borderRadius: 21, padding: 16, gap: 5 },
  summaryTop: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  summaryEyebrow: { color: '#E8E0FF', fontSize: 9, letterSpacing: 1.2, fontWeight: '900' },
  summaryTitle: { color: '#FFFFFF', fontSize: 22, lineHeight: 27, letterSpacing: -0.4, fontWeight: '800' },
  summaryMeta: { color: '#F0ECFF', fontSize: 11, lineHeight: 16 },
  summaryBadges: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 5 },
  summaryBadge: { color: '#FFFFFF', overflow: 'hidden', fontSize: 9, fontWeight: '700', paddingHorizontal: 8, paddingVertical: 5, borderRadius: 10, backgroundColor: 'rgba(18,13,73,0.2)' },
  heading: { color: colors.text, fontSize: 20, lineHeight: 27, fontWeight: '800', letterSpacing: -0.4 },
  meta: { color: colors.muted, fontSize: 11, lineHeight: 17 },
  tabs: { gap: 7, paddingVertical: 2 },
  tab: { minHeight: 42, borderRadius: 14, paddingHorizontal: 14, justifyContent: 'center', backgroundColor: colors.card, borderWidth: 1, borderColor: colors.border },
  active: { backgroundColor: colors.cardSoft, borderColor: colors.primary },
  tabText: { color: colors.muted, fontSize: 12, fontWeight: '700' },
  activeText: { color: colors.primary, fontSize: 12, fontWeight: '800' },
  records: { gap: 7, paddingVertical: 2 },
  recordChip: { minHeight: 38, justifyContent: 'center', borderRadius: 11, paddingHorizontal: 12, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.card },
  chipText: { color: colors.muted, fontSize: 11, fontWeight: '700' },
  recordHeader: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  step: { width: 38, height: 38, borderRadius: 13, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.card, borderWidth: 1, borderColor: colors.border },
  disabled: { opacity: 0.3 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 9 },
  measure: { width: '48%', flexGrow: 1, gap: 5, minHeight: 150, padding: 14, borderRadius: 20 },
  metric: { color: colors.muted, fontSize: 12, fontWeight: '700', minHeight: 30 },
  value: { color: colors.text, fontSize: 28, lineHeight: 35, fontWeight: '800', letterSpacing: -0.7 },
  missing: { fontSize: 17, lineHeight: 24, color: colors.faint },
  unit: { color: colors.primary, fontSize: 12, fontWeight: '700' },
  qualifier: { color: colors.faint, fontSize: 10, lineHeight: 15, marginTop: 3 },
  note: { gap: 8 },
  sourceLabel: { color: colors.text, fontSize: 12, fontWeight: '800' },
  sourceText: { color: colors.muted, fontSize: 12, lineHeight: 18 },
  disclosure: { minHeight: 44, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 3 },
});

