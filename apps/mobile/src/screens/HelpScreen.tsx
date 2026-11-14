import React from 'react';
import { Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Locale } from '../types';
import { t } from '../i18n';
import { ActionButton, AppHeader, AppPage, Body, Panel } from '../components/ui';
import { useTheme } from '../theme';
import { Route } from '../navigation';
import { copy } from '../uiCopy';

export function HelpScreen({ locale, onBack, onOpen }: { locale: Locale; onBack: () => void; onOpen: (route: Route) => void }) {
  const { colors } = useTheme();
  return (
    <AppPage>
      <AppHeader title={t(locale, 'helpTitle')} onBack={onBack} backLabel={t(locale, 'back')} />
      <Panel style={{ gap: 12 }}>
        <View style={{ width: 46, height: 46, borderRadius: 16, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.cardSoft }}><Ionicons name="help-circle-outline" size={24} color={colors.cyan} /></View>
        <Text style={{ color: colors.text, fontWeight: '800', fontSize: 15 }}>{t(locale, 'helpTitle')}</Text>
        <Body>{locale === 'en' ? 'Demo opens the NASA archive without an account. Sign in to read and manage profiles assigned by your server.' : 'Demo mở kho dữ liệu NASA không cần tài khoản. Đăng nhập để xem và quản lý hồ sơ được máy chủ cấp quyền.'}</Body>
        <ActionButton title="Demo" onPress={() => onOpen('demoIntro')} secondary />
        <ActionButton title={copy(locale, 'connection')} onPress={() => onOpen('connection')} secondary />
        <ActionButton title={t(locale, 'privacyTitle')} onPress={() => onOpen('privacy')} secondary />
        <Text style={{ color: colors.muted, fontSize: 11, lineHeight: 17 }}>AETHERION · TRUY TINH</Text>
        <Body style={{ fontSize: 11 }}>{locale === 'en' ? 'Interface and artwork adapted from Solo Business AI, supplied by the project owner. Scientific records retain their original authors and sources.' : 'Giao diện và hình ảnh được chuyển thể từ Solo Business AI do chủ dự án cung cấp. Tài liệu khoa học giữ nguyên tác giả và nguồn gốc.'}</Body>
      </Panel>
    </AppPage>
  );
}

