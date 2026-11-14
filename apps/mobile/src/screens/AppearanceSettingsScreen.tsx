import React from 'react';
import { Pressable, StyleSheet, Switch, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Locale } from '../types';
import { copy } from '../uiCopy';
import { presets, ThemeColors, ThemeMode, ThemePreset, useThemedStyles } from '../theme';
import { AppHeader, AppPage, Panel } from '../components/ui';
export function AppearanceSettingsScreen({ locale, onBack }: { locale: Locale; onBack: () => void }) {
  const { colors, styles, appearance, updateAppearance } = useThemedStyles(buildStyles);
  return <AppPage><AppHeader title={copy(locale, 'appearance')} onBack={onBack} />
    <Panel><Text style={styles.heading}>{copy(locale, 'mode')}</Text><View style={styles.segment}>
      {(['system', 'light', 'dark'] as ThemeMode[]).map(mode => <Pressable key={mode} accessibilityRole="radio" accessibilityLabel={copy(locale, mode)} accessibilityState={{ checked: appearance.mode === mode }} onPress={() => updateAppearance({ mode })} style={[styles.choice, appearance.mode === mode && styles.active]}><Text style={styles.text}>{copy(locale, mode)}</Text></Pressable>)}
    </View></Panel>
    <Panel><Text style={styles.heading}>{copy(locale, 'theme')}</Text><View style={styles.grid}>
      {(Object.keys(presets) as ThemePreset[]).map(preset => <Pressable key={preset} accessibilityRole="radio" accessibilityLabel={copy(locale, preset)} accessibilityState={{ checked: appearance.preset === preset }} onPress={() => updateAppearance({ preset })} style={[styles.swatch, appearance.preset === preset && styles.active]}><View style={[styles.dot, { backgroundColor: presets[preset].accent }]} /><Text style={styles.text}>{copy(locale, preset)}</Text>{appearance.preset === preset && <Ionicons name="checkmark" color={colors.cyan} size={18} />}</Pressable>)}
    </View></Panel>
    <Panel><View style={styles.row}><Text style={styles.text}>{copy(locale, 'motion')}</Text><Switch accessibilityLabel={copy(locale, 'motion')} value={appearance.reduceMotion} onValueChange={reduceMotion => updateAppearance({ reduceMotion })} trackColor={{ true: colors.cyan }} /></View></Panel>
  </AppPage>;
}
const buildStyles = (colors: ThemeColors) => StyleSheet.create({ heading: { color: colors.text, fontSize: 15, fontWeight: '800', marginBottom: 15 }, text: { color: colors.text, fontSize: 13, fontWeight: '700' }, segment: { flexDirection: 'row', gap: 7 }, choice: { flex: 1, alignItems: 'center', paddingVertical: 13, borderWidth: 1, borderColor: colors.border, borderRadius: 14 }, active: { borderColor: colors.cyan, backgroundColor: colors.cardSoft }, grid: { gap: 8 }, swatch: { minHeight: 55, flexDirection: 'row', alignItems: 'center', gap: 12, borderRadius: 14, borderWidth: 1, borderColor: colors.border, padding: 12 }, dot: { width: 25, height: 25, borderRadius: 9 }, row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' } });
