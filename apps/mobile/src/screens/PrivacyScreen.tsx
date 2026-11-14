import React from 'react';
import { Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Locale } from '../types';
import { t } from '../i18n';
import { AppHeader, AppPage, Body, Panel } from '../components/ui';
import { useTheme } from '../theme';

export function PrivacyScreen({ locale, onBack }: { locale: Locale; onBack: () => void }) {
  const { colors } = useTheme();
  return (
    <AppPage>
      <AppHeader title={t(locale, 'privacyTitle')} onBack={onBack} backLabel={t(locale, 'back')} />
      <Panel style={{ gap: 12 }}>
        <View style={{ width: 46, height: 46, borderRadius: 16, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.cardSoft }}><Ionicons name="shield-checkmark-outline" size={24} color={colors.cyan} /></View>
        <Text style={{ color: colors.text, fontWeight: '800', fontSize: 15 }}>{t(locale, 'privacyTitle')}</Text>
        <Body>{t(locale, 'privacy')}</Body>
        <Body>{t(locale, 'privacyAi')}</Body>
        <Body>{t(locale, 'privacyDemo')}</Body>
      </Panel>
    </AppPage>
  );
}

