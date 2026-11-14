import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Locale } from '../types';
import { t } from '../i18n';
import { copy } from '../uiCopy';
import { ThemeColors, useThemedStyles } from '../theme';
import { AppHeader, AppPage, Panel } from '../components/ui';

export type SettingsSection = 'account' | 'connection' | 'language' | 'notifications' | 'privacy' | 'appearance';

export function SettingsScreen({ locale, onBack, onOpen }: {
  locale: Locale;
  onBack: () => void;
  onOpen: (section: SettingsSection) => void;
}) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  return (
    <AppPage>
      <AppHeader title={t(locale, 'settingsTitle')} onBack={onBack} backLabel={t(locale, 'back')} />
      <Panel style={styles.menu}>
        <SettingsRow icon="person-circle-outline" title={t(locale, 'accountTitle')} onPress={() => onOpen('account')} />
        <SettingsRow icon="server-outline" title={t(locale, 'connectionTitle')} onPress={() => onOpen('connection')} />
        <SettingsRow icon="language-outline" title={t(locale, 'language')} value={locale.toUpperCase()} onPress={() => onOpen('language')} />
        <SettingsRow icon="color-palette-outline" title={copy(locale, 'appearance')} onPress={() => onOpen('appearance')} />
        <SettingsRow icon="notifications-outline" title={t(locale, 'notifications')} onPress={() => onOpen('notifications')} />
        <SettingsRow icon="shield-checkmark-outline" title={t(locale, 'privacyTitle')} onPress={() => onOpen('privacy')} last />
      </Panel>
    </AppPage>
  );
}

function SettingsRow({ icon, title, value, onPress, last }: { icon: keyof typeof Ionicons.glyphMap; title: string; value?: string; onPress: () => void; last?: boolean }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  return (
    <Pressable accessibilityRole="button" onPress={onPress} style={({ pressed }) => [styles.row, !last && styles.rowBorder, pressed && styles.pressed]}>
      <View style={styles.icon}><Ionicons name={icon} size={20} color={colors.cyan} /></View>
      <Text style={styles.rowTitle}>{title}</Text>
      {value ? <Text style={styles.value}>{value}</Text> : null}
      <Ionicons name="chevron-forward" size={18} color={colors.faint} />
    </Pressable>
  );
}

const buildStyles = (colors: ThemeColors) => StyleSheet.create({
  menu: { paddingHorizontal: 14, paddingVertical: 4 },
  row: { minHeight: 64, flexDirection: 'row', alignItems: 'center', gap: 12 },
  rowBorder: { borderBottomWidth: 1, borderBottomColor: colors.border },
  icon: { width: 40, height: 40, borderRadius: 14, backgroundColor: colors.cardSoft, alignItems: 'center', justifyContent: 'center' },
  rowTitle: { flex: 1, color: colors.text, fontSize: 14, fontWeight: '800' },
  value: { color: colors.muted, fontSize: 12, fontWeight: '800' },
  pressed: { opacity: 0.72 },
});

