import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Locale } from '../types';
import { MessageKey, t } from '../i18n';
import { ThemeColors, useThemedStyles } from '../theme';
import { AppHeader, AppPage, Panel } from '../components/ui';
import type { MobileScreen } from './PortalScreen';

type MoreEntry = { route: MobileScreen; icon: keyof typeof Ionicons.glyphMap; title: MessageKey };

const entries: MoreEntry[] = [
  { route: 'science', icon: 'planet-outline', title: 'science' },
  { route: 'care', icon: 'heart-outline', title: 'careTitle' },
  { route: 'mission', icon: 'people-outline', title: 'missionTitle' },
  { route: 'connection', icon: 'server-outline', title: 'connectionTitle' },
  { route: 'settings', icon: 'settings-outline', title: 'settings' },
  { route: 'notifications', icon: 'notifications-outline', title: 'notifications' },
  { route: 'help', icon: 'help-circle-outline', title: 'helpTitle' },
  { route: 'privacy', icon: 'shield-checkmark-outline', title: 'privacyTitle' },
];

export function MoreScreen({ locale, onBack, onOpen }: { locale: Locale; onBack: () => void; onOpen: (route: MobileScreen) => void }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  return (
    <AppPage>
      <AppHeader title={t(locale, 'moreTitle')} onBack={onBack} backLabel={t(locale, 'back')} />
      <Panel style={styles.list}>
        {entries.map((entry, index) => (
          <Pressable key={entry.route} accessibilityRole="button" onPress={() => onOpen(entry.route)} style={({ pressed }) => [styles.row, index < entries.length - 1 && styles.divider, pressed && styles.pressed]}>
            <View style={styles.icon}><Ionicons name={entry.icon} size={20} color={colors.cyan} /></View>
            <Text style={styles.label}>{t(locale, entry.title)}</Text>
            <Ionicons name="chevron-forward" size={18} color={colors.faint} />
          </Pressable>
        ))}
      </Panel>
    </AppPage>
  );
}

const buildStyles = (colors: ThemeColors) => StyleSheet.create({
  list: { paddingHorizontal: 14, paddingVertical: 4 },
  row: { minHeight: 62, flexDirection: 'row', alignItems: 'center', gap: 12 },
  divider: { borderBottomWidth: 1, borderBottomColor: colors.border },
  icon: { width: 40, height: 40, borderRadius: 14, backgroundColor: colors.cardSoft, alignItems: 'center', justifyContent: 'center' },
  label: { flex: 1, color: colors.text, fontSize: 14, fontWeight: '800' },
  pressed: { opacity: 0.72 },
});

