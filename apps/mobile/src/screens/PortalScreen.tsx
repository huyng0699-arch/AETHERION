import React from 'react';
import { Image, Pressable, StyleSheet, Text, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { Locale } from '../types';
import { MessageKey, t } from '../i18n';
import { colors } from '../theme';
import { AppHeader, AppPage, StatusPill } from '../components/ui';
import { PortalCard, PortalDestination } from '../components/PortalCard';

export type MobileScreen = 'health' | 'monitor' | 'ai' | 'science' | 'mission' | 'login' | 'settings' | 'demoIntro' | 'demoData' | 'more' | 'connection' | 'settingConnection' | 'settingAccount' | 'settingLanguage' | 'notifications' | 'help' | 'privacy' | 'care';
const AI_ROBOT = require('../../assets/aetherion-ai-robot.png');

export function PortalScreen({
  locale, setLocale, isAuthenticated, serverStatus, onOpen,
}: {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  isAuthenticated: boolean;
  serverStatus: 'online' | 'offline' | 'unknown';
  onOpen: (screen: MobileScreen) => void;
}) {
  const statusLabel = serverStatus === 'online' ? t(locale, 'serverOnline') : t(locale, 'serverOffline');
  const statusTone = serverStatus === 'online' ? 'good' : serverStatus === 'offline' ? 'warn' : 'neutral';
  const cards: { id: PortalDestination; title: MessageKey; route: MobileScreen }[] = [
    { id: 'health', title: 'personal', route: 'health' },
    { id: 'monitor', title: 'monitor', route: 'monitor' },
    { id: 'ai', title: 'ai', route: 'ai' },
    { id: 'science', title: 'science', route: 'science' },
    { id: 'care', title: 'careTitle', route: 'care' },
  ];

  return (
    <AppPage>
      <AppHeader title={t(locale, 'brand')} trailing={
        <View style={styles.headerActions}>
          <Pressable accessibilityRole="button" accessibilityLabel={t(locale, 'language')} onPress={() => setLocale(locale === 'vi' ? 'en' : 'vi')} style={styles.localeButton}>
            <Text style={styles.localeText}>{locale === 'vi' ? 'EN' : 'VI'}</Text>
          </Pressable>
          <Pressable accessibilityRole="button" accessibilityLabel={t(locale, 'notifications')} onPress={() => onOpen('notifications')} style={styles.accountButton}>
            <Ionicons name="notifications-outline" size={20} color={colors.cyan} />
          </Pressable>
          <Pressable accessibilityRole="button" accessibilityLabel={t(locale, 'connectionTitle')} onPress={() => onOpen('connection')} style={styles.accountButton}>
            <Ionicons name="server-outline" size={20} color={colors.cyan} />
          </Pressable>
          <Pressable accessibilityRole="button" accessibilityLabel={t(locale, isAuthenticated ? 'settings' : 'signIn')} onPress={() => onOpen(isAuthenticated ? 'settings' : 'login')} style={styles.accountButton}>
            <Ionicons name={isAuthenticated ? 'settings-outline' : 'log-in-outline'} size={20} color={colors.cyan} />
          </Pressable>
        </View>
      } />

      <LinearGradient colors={['#5D43E8', '#8975F7', '#B6A9FF']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
        <View style={styles.heroCopy}>
          <Text style={styles.heroKicker}>{t(locale, 'demoKicker')}</Text>
          <Text style={styles.heroTitle}>{t(locale, 'demoBannerTitle')}</Text>
          <Pressable accessibilityRole="button" onPress={() => onOpen('demoIntro')} style={styles.heroAction}>
            <Text style={styles.heroActionText}>{t(locale, 'demoOpen')}</Text>
            <Ionicons name="chevron-forward" size={16} color="#4F31D0" />
          </Pressable>
        </View>
        <Image source={AI_ROBOT} resizeMode="contain" style={styles.robot} />
      </LinearGradient>

      <View style={styles.statusRow}>
        <StatusPill label={statusLabel} tone={statusTone} />
      </View>

      <View style={styles.grid}>
        {cards.map((card, index) => (
          <PortalCard key={card.id} destination={card.id} title={t(locale, card.title)} wide={index === cards.length - 1} onPress={() => onOpen(card.route)} />
        ))}
      </View>
    </AppPage>
  );
}

const styles = StyleSheet.create({
  headerActions: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  localeButton: { width: 38, height: 36, borderRadius: 12, borderWidth: 1, borderColor: colors.border, backgroundColor: '#FFFFFF', alignItems: 'center', justifyContent: 'center' },
  localeText: { color: colors.cyan, fontSize: 11, fontWeight: '900' },
  accountButton: { width: 38, height: 36, borderRadius: 12, borderWidth: 1, borderColor: colors.border, backgroundColor: '#FFFFFF', alignItems: 'center', justifyContent: 'center' },
  hero: { minHeight: 154, borderRadius: 27, padding: 18, overflow: 'hidden', justifyContent: 'center', shadowColor: '#4D2CCB', shadowOpacity: 0.18, shadowRadius: 14, shadowOffset: { width: 0, height: 8 }, elevation: 5 },
  heroCopy: { width: '65%', gap: 8, zIndex: 1 },
  heroKicker: { color: 'rgba(255,255,255,0.84)', fontWeight: '800', letterSpacing: 1.4, fontSize: 10 },
  heroTitle: { color: '#FFFFFF', fontSize: 24, lineHeight: 29, fontWeight: '900', letterSpacing: -0.5 },
  heroAction: { alignSelf: 'flex-start', minHeight: 34, paddingHorizontal: 12, borderRadius: 12, backgroundColor: '#FFFFFF', flexDirection: 'row', alignItems: 'center', gap: 5 },
  heroActionText: { color: '#4F31D0', fontWeight: '800', fontSize: 12 },
  robot: { position: 'absolute', width: 158, height: 158, right: 2, bottom: -9 },
  statusRow: { flexDirection: 'row', alignItems: 'center', minHeight: 35 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', rowGap: 10 },
});
