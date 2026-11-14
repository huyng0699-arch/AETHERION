import React from 'react';
import { StyleSheet, Text } from 'react-native';
import { Locale } from '../types';
import { t } from '../i18n';
import { ActionButton, AppHeader, AppPage, Field, Panel, StatusPill } from '../components/ui';
import { ThemeColors, useThemedStyles } from '../theme';

export function ServerConnectionScreen({ locale, serverUrl, setServerUrl, status, busy, error, onCheck, onBack }: {
  locale: Locale; serverUrl: string; setServerUrl: (value: string) => void;
  status: 'online' | 'offline' | 'unknown'; busy: boolean; error?: string;
  onCheck: () => void; onBack: () => void;
}) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  const statusText = status === 'online' ? t(locale, 'serverOnline') : status === 'offline' ? t(locale, 'serverOffline') : t(locale, 'serverUnknown');
  return (
    <AppPage>
      <AppHeader title={t(locale, 'connectionTitle')} onBack={onBack} backLabel={t(locale, 'back')} />
      <Panel style={styles.panel}>
        <StatusPill label={statusText} tone={status === 'online' ? 'good' : status === 'offline' ? 'warn' : 'neutral'} />
        <Field label={t(locale, 'serverUrl')} value={serverUrl} onChangeText={setServerUrl} autoCapitalize="none" autoCorrect={false} keyboardType="url" placeholder="https://" />
        <Text style={styles.hint}>{t(locale, 'connectionHint')}</Text>
        {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
        <ActionButton title={busy ? t(locale, 'connecting') : t(locale, 'connectionCheck')} onPress={onCheck} loading={busy} disabled={!serverUrl.trim()} />
      </Panel>
    </AppPage>
  );
}

const buildStyles = (colors: ThemeColors) => StyleSheet.create({
  panel: { gap: 16 },
  hint: { color: colors.muted, fontSize: 12, lineHeight: 18 },
  error: { color: colors.red, fontSize: 13, fontWeight: '700', lineHeight: 19 },
});

