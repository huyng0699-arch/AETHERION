import React from 'react';
import { Pressable, StyleSheet, Switch, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Locale } from '../types';
import { copy } from '../uiCopy';
import { accents, AccentColor, presets, ThemeColors, ThemeMode, ThemePreset, TextColor, textColorOptions, useThemedStyles } from '../theme';
import { AppHeader, AppPage, Panel } from '../components/ui';

const ACCENT_LABELS: Record<AccentColor, 'accentPurple' | 'accentTeal' | 'accentOrange' | 'accentBlack' | 'accentRose' | 'accentBlue' | 'accentGold'> = {
  purple: 'accentPurple', teal: 'accentTeal', orange: 'accentOrange', black: 'accentBlack', rose: 'accentRose', blue: 'accentBlue', gold: 'accentGold',
};
const TEXT_LABELS: Record<TextColor, 'textTheme' | 'textGraphite' | 'textNavy' | 'textPlum' | 'textWarm'> = {
  theme: 'textTheme', graphite: 'textGraphite', navy: 'textNavy', plum: 'textPlum', warm: 'textWarm',
};

export function AppearanceSettingsScreen({ locale, onBack }: { locale: Locale; onBack: () => void }) {
  const { colors, styles, appearance, updateAppearance, isDark } = useThemedStyles(buildStyles);
  const themeText = isDark ? presets[appearance.preset].dark.text : presets[appearance.preset].light.text;
  return <AppPage><AppHeader title={copy(locale, 'appearance')} onBack={onBack} />
    <Panel><Text style={styles.heading}>{copy(locale, 'mode')}</Text><View style={styles.segment}>
      {(['system', 'light', 'dark'] as ThemeMode[]).map(mode => <Pressable key={mode} accessibilityRole="radio" accessibilityLabel={copy(locale, mode)} accessibilityState={{ checked: appearance.mode === mode }} onPress={() => updateAppearance({ mode })} style={[styles.choice, appearance.mode === mode && styles.active]}><Text style={styles.text}>{copy(locale, mode)}</Text></Pressable>)}
    </View></Panel>
    <Panel><Text style={styles.heading}>{copy(locale, 'theme')}</Text><View style={styles.grid}>
      {(Object.keys(presets) as ThemePreset[]).map(preset => <Pressable key={preset} accessibilityRole="radio" accessibilityLabel={copy(locale, preset)} accessibilityState={{ checked: appearance.preset === preset }} onPress={() => updateAppearance({ preset })} style={[styles.swatch, appearance.preset === preset && styles.active]}><View style={[styles.dot, { backgroundColor: presets[preset].light.primary }]} /><Text style={styles.text}>{copy(locale, preset)}</Text>{appearance.preset === preset && <Ionicons name="checkmark" color={colors.primary} size={18} />}</Pressable>)}
    </View></Panel>
    <Panel><Text style={styles.heading}>{copy(locale, 'accentColor')}</Text><View style={styles.optionGrid}>
      {(Object.keys(accents) as AccentColor[]).map(accent => <Pressable key={accent} accessibilityRole="radio" accessibilityLabel={copy(locale, ACCENT_LABELS[accent])} accessibilityState={{ checked: appearance.accent === accent }} onPress={() => updateAppearance({ accent })} style={[styles.colorChoice, appearance.accent === accent && styles.active]}><View style={[styles.dot, { backgroundColor: accents[accent] }]} /><Text style={styles.text}>{copy(locale, ACCENT_LABELS[accent])}</Text>{appearance.accent === accent && <Ionicons name="checkmark" color={colors.primary} size={17} />}</Pressable>)}
    </View></Panel>
    <Panel><Text style={styles.heading}>{copy(locale, 'textColor')}</Text><View style={styles.grid}>
      {(Object.keys(TEXT_LABELS) as TextColor[]).map(textColor => {
        const preview = textColor === 'theme' ? themeText : textColorOptions[textColor][isDark ? 'dark' : 'light'];
        return <Pressable key={textColor} accessibilityRole="radio" accessibilityLabel={copy(locale, TEXT_LABELS[textColor])} accessibilityState={{ checked: appearance.textColor === textColor }} onPress={() => updateAppearance({ textColor })} style={[styles.colorChoice, appearance.textColor === textColor && styles.active]}><View style={styles.textSample}><Text style={[styles.textSampleLabel, { color: preview }]}>Aa</Text></View><Text style={styles.text}>{copy(locale, TEXT_LABELS[textColor])}</Text>{appearance.textColor === textColor && <Ionicons name="checkmark" color={colors.primary} size={17} />}</Pressable>;
      })}
    </View></Panel>
    <Panel><View style={styles.row}><Text style={styles.text}>{copy(locale, 'motion')}</Text><Switch accessibilityLabel={copy(locale, 'motion')} value={appearance.reduceMotion} onValueChange={reduceMotion => updateAppearance({ reduceMotion })} trackColor={{ true: colors.primary }} /></View></Panel>
  </AppPage>;
}
const buildStyles = (colors: ThemeColors) => StyleSheet.create({ heading: { color: colors.text, fontSize: 15, fontWeight: '800', marginBottom: 15 }, text: { color: colors.text, fontSize: 13, fontWeight: '700', flex: 1 }, segment: { flexDirection: 'row', gap: 7 }, choice: { flex: 1, alignItems: 'center', paddingVertical: 13, borderWidth: 1, borderColor: colors.border, borderRadius: 14 }, active: { borderColor: colors.primary, backgroundColor: colors.cardSoft }, grid: { gap: 8 }, optionGrid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', gap: 8 }, swatch: { minHeight: 55, flexDirection: 'row', alignItems: 'center', gap: 12, borderRadius: 14, borderWidth: 1, borderColor: colors.border, padding: 12 }, colorChoice: { width: '48%', minHeight: 48, flexDirection: 'row', alignItems: 'center', gap: 8, borderRadius: 14, borderWidth: 1, borderColor: colors.border, paddingHorizontal: 9 }, dot: { width: 22, height: 22, borderRadius: 11 }, textSample: { width: 26, height: 26, borderRadius: 9, backgroundColor: colors.card, alignItems: 'center', justifyContent: 'center' }, textSampleLabel: { fontSize: 12, fontWeight: '900' }, row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' } });

