import React from 'react';
import { Text } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Locale } from '../types';
import { t } from '../i18n';
import { AppHeader, AppPage, Panel } from '../components/ui';
import { useTheme } from '../theme';

export function NotificationScreen({ locale, onBack }: { locale: Locale; onBack: () => void }) {
  const { colors } = useTheme();
  return (
    <AppPage>
      <AppHeader title={t(locale, 'notifications')} onBack={onBack} backLabel={t(locale, 'back')} />
      <Panel style={{ alignItems: 'center', gap: 10, paddingVertical: 28 }}>
        <Ionicons name="notifications-off-outline" size={28} color={colors.muted} />
        <Text style={{ color: colors.text, fontWeight: '800', textAlign: 'center' }}>{t(locale, 'notificationsUnavailable')}</Text>
      </Panel>
    </AppPage>
  );
}

