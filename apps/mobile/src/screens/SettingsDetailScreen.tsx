import React, { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Locale } from '../types';
import { t } from '../i18n';
import { ThemeColors, useThemedStyles } from '../theme';
import { ActionButton, AppHeader, AppPage, Field, Panel, StatusPill } from '../components/ui';
import type { SettingsSection } from './SettingsScreen';
type SettingsDetailSection = Extract<SettingsSection, 'account' | 'connection' | 'language'>;

export function SettingsDetailScreen({
  section, locale, onChangeLocale, onBack, serverUrl, onChangeServerUrl, onSaveServerUrl, onSignOut, onSignIn, username, role,
}: {
  section: SettingsDetailSection;
  locale: Locale;
  onChangeLocale: (locale: Locale) => void;
  onBack: () => void;
  serverUrl: string;
  onChangeServerUrl: (value: string) => void;
  onSaveServerUrl: () => void | Promise<void>;
  onSignOut: () => void | Promise<void>;
  onSignIn: () => void;
  username?: string;
  role?: string;
}) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState('');
  useEffect(() => { setSaved(false); }, [serverUrl]);
  const title = section === 'account' ? t(locale, 'accountTitle') : section === 'connection' ? t(locale, 'connectionTitle') : t(locale, 'language');
  const save = async () => { setSaved(false); setSaveError(''); try { await onSaveServerUrl(); setSaved(true); } catch { setSaveError(t(locale, 'urlInvalid')); } };

  return (
    <AppPage>
      <AppHeader title={title} onBack={onBack} backLabel={t(locale, 'back')} />
      {section === 'account' ? (
        <Panel style={styles.panel}>
          <InfoRow label={t(locale, 'username')} value={username || t(locale, 'notSignedIn')} />
          {username ? <InfoRow label={t(locale, 'role')} value={role || '—'} /> : null}
          {username
            ? <ActionButton title={t(locale, 'signOut')} onPress={() => void onSignOut()} secondary />
            : <ActionButton title={t(locale, 'signIn')} onPress={onSignIn} />}
        </Panel>
      ) : null}
      {section === 'connection' ? (
        <Panel style={styles.panel}>
          <Field label={t(locale, 'serverUrl')} value={serverUrl} onChangeText={onChangeServerUrl} autoCapitalize="none" autoCorrect={false} keyboardType="url" placeholder="https://" />
          {saved ? <StatusPill label={t(locale, 'saved')} tone="good" /> : null}
          {saveError ? <Text accessibilityRole="alert" style={{ color: colors.red }}>{saveError}</Text> : null}
          <ActionButton title={t(locale, 'save')} onPress={() => void save()} secondary />
        </Panel>
      ) : null}
      {section === 'language' ? (
        <Panel style={styles.languagePanel}>
          <LocaleRow label={t(locale, 'english')} selected={locale === 'en'} onPress={() => onChangeLocale('en')} />
          <LocaleRow label={t(locale, 'vietnamese')} selected={locale === 'vi'} onPress={() => onChangeLocale('vi')} last />
        </Panel>
      ) : null}
    </AppPage>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  return <View style={styles.infoRow}><Text style={styles.meta}>{label}</Text><Text numberOfLines={1} style={styles.value}>{value}</Text></View>;
}

function LocaleRow({ label, selected, onPress, last }: { label: string; selected: boolean; onPress: () => void; last?: boolean }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  return (
    <Pressable accessibilityRole="radio" accessibilityState={{ selected }} onPress={onPress} style={[styles.localeRow, !last && styles.rowBorder]}>
      <View style={[styles.radio, selected && styles.radioSelected]}>{selected ? <View style={styles.radioDot} /> : null}</View>
      <Text style={styles.localeText}>{label}</Text>
      {selected ? <Ionicons name="checkmark" size={18} color={colors.primary} /> : null}
    </Pressable>
  );
}

const buildStyles = (colors: ThemeColors) => StyleSheet.create({
  panel: { gap: 18 },
  infoRow: { minHeight: 28, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 14 },
  meta: { color: colors.muted, fontSize: 13, fontWeight: '700' },
  value: { flex: 1, textAlign: 'right', color: colors.text, fontSize: 14, fontWeight: '800' },
  languagePanel: { paddingHorizontal: 16, paddingVertical: 4 },
  localeRow: { minHeight: 58, flexDirection: 'row', alignItems: 'center', gap: 12 },
  rowBorder: { borderBottomWidth: 1, borderBottomColor: colors.border },
  radio: { width: 21, height: 21, borderRadius: 11, borderWidth: 1.5, borderColor: colors.faint, alignItems: 'center', justifyContent: 'center' },
  radioSelected: { borderColor: colors.primary },
  radioDot: { width: 11, height: 11, borderRadius: 6, backgroundColor: colors.primary },
  localeText: { flex: 1, color: colors.text, fontWeight: '800', fontSize: 14 },
});


