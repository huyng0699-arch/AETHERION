import React, { useState } from 'react';
import { Image, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { Locale } from '../types';
import { t } from '../i18n';
import { copy } from '../uiCopy';
import { ThemeColors, useThemedStyles } from '../theme';
import { ActionButton, AppPage, Field, Panel, StatusPill } from '../components/ui';
import { OrbitEarth } from '../components/home/OrbitEarth';

type Props = {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  onAppearance: () => void;
  serverUrl: string;
  setServerUrl: (url: string) => void;
  onConnect: (url: string) => void;
  onSignIn: (url: string, username: string, password: string) => void;
  onOpenDemo: () => void;
  onContinue?: () => void;
  restoredUsername?: string;
  busy: boolean;
  error?: string;
  status: 'online' | 'offline' | 'unknown';
};

export function LoginScreen({ locale, setLocale, onAppearance, serverUrl, setServerUrl, onConnect, onSignIn, onOpenDemo, onContinue, restoredUsername, busy, error, status }: Props) {
  const { colors, styles } = useThemedStyles(buildStyles);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [connectionOpen, setConnectionOpen] = useState(false);
  const submit = () => {
    if (!busy && username.trim() && password && serverUrl.trim()) onSignIn(serverUrl, username, password);
  };

  return <AppPage contentStyle={styles.page}>
    <LinearGradient colors={['#111733', '#18234E', '#344577']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
      <View style={styles.heroHeader}>
        <Image source={require('../../assets/truy-tinh-logo.png')} accessibilityLabel="Truy Tinh" resizeMode="contain" style={styles.mark} />
        <View style={styles.brandBlock}><Text style={styles.brand}>AETHERION</Text><Text style={styles.brandCaption}>BY TRUY TINH</Text></View>
        <Pressable accessibilityRole="button" accessibilityLabel={t(locale, 'language')} onPress={() => setLocale(locale === 'en' ? 'vi' : 'en')} style={styles.heroTool}>
          <Text style={styles.heroToolText}>{locale === 'en' ? 'EN' : 'VI'}</Text>
        </Pressable>
        <Pressable accessibilityRole="button" accessibilityLabel={copy(locale, 'appearance')} onPress={onAppearance} disabled={busy} style={styles.heroTool}>
          <Ionicons name="color-palette-outline" color="#DCE5FF" size={18} />
        </Pressable>
      </View>
      <View style={styles.earth}><OrbitEarth size={153} /></View>
      <View style={styles.heroCopy}>
        <Text style={styles.heroEyebrow}>MISSION HEALTH</Text>
        <Text style={styles.heroTitle}>{locale === 'vi' ? 'Sức khỏe trong tầm tay.' : 'Health, within reach.'}</Text>
        <View style={styles.heroLine} />
      </View>
    </LinearGradient>

    <View style={styles.intro}><Text style={styles.title}>{copy(locale, 'welcome')}</Text><Text style={styles.tagline}>{copy(locale, 'tagline')}</Text></View>
    <Panel style={styles.form}>
      <Field label={t(locale, 'username')} value={username} onChangeText={setUsername} editable={!busy} autoCapitalize="none" autoCorrect={false} autoComplete="username" textContentType="username" returnKeyType="next" />
      <Field label={t(locale, 'password')} value={password} onChangeText={setPassword} editable={!busy} secureTextEntry autoComplete="current-password" textContentType="password" returnKeyType="go" onSubmitEditing={submit} />
      {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
      <ActionButton title={t(locale, busy ? 'signingIn' : 'signInAction')} onPress={submit} loading={busy} disabled={!username.trim() || !password || !serverUrl.trim()} />
      {restoredUsername && onContinue ? <ActionButton title={`${copy(locale, 'continueAs')} ${restoredUsername}`} onPress={onContinue} secondary disabled={busy} /> : null}
    </Panel>

    <Pressable accessibilityRole="button" accessibilityLabel="Demo" onPress={onOpenDemo} disabled={busy} style={({ pressed }) => [styles.demo, pressed && styles.pressed]}>
      <View style={styles.demoIcon}><Ionicons name="planet-outline" color="#FFFFFF" size={21} /></View>
      <View style={styles.demoCopy}><Text style={styles.demoTitle}>Demo</Text><Text style={styles.demoHint}>{copy(locale, 'demoHint')}</Text></View>
      <View style={styles.demoArrow}><Ionicons name="arrow-forward" size={19} color={colors.cyan} /></View>
    </Pressable>

    <Pressable accessibilityRole="button" accessibilityLabel={copy(locale, 'connection')} accessibilityState={{ expanded: connectionOpen }} onPress={() => setConnectionOpen(value => !value)} style={styles.connection}>
      <Ionicons name="server-outline" color={colors.muted} size={15} /><Text style={styles.connectionText}>{copy(locale, 'connection')}</Text><Ionicons name={connectionOpen ? 'chevron-up' : 'chevron-down'} color={colors.muted} size={15} />
    </Pressable>
    {connectionOpen ? <Panel style={styles.form}>
      <Field label={t(locale, 'serverUrl')} value={serverUrl} onChangeText={setServerUrl} editable={!busy} autoCapitalize="none" autoCorrect={false} keyboardType="url" />
      <StatusPill label={t(locale, status === 'online' ? 'serverOnline' : status === 'offline' ? 'serverOffline' : 'serverUnknown')} tone={status === 'online' ? 'good' : 'neutral'} />
      <ActionButton title={t(locale, 'connectionCheck')} onPress={() => onConnect(serverUrl)} disabled={busy || !serverUrl.trim()} secondary />
    </Panel> : null}
  </AppPage>;
}

const buildStyles = (colors: ThemeColors) => StyleSheet.create({
  page: { paddingTop: 12, paddingBottom: 34, gap: 11 },
  hero: { height: 174, borderRadius: 24, overflow: 'hidden', padding: 16 },
  heroHeader: { flexDirection: 'row', alignItems: 'center', gap: 7, zIndex: 2 },
  mark: { width: 35, height: 35 },
  brandBlock: { flex: 1 },
  brand: { color: '#FFFFFF', fontSize: 12, fontWeight: '900', letterSpacing: 0.8 },
  brandCaption: { color: '#AFBDE3', fontSize: 8, fontWeight: '700', letterSpacing: 1.1, marginTop: 2 },
  heroTool: { width: 34, height: 34, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,0.09)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.16)' },
  heroToolText: { color: '#FFFFFF', fontSize: 10, fontWeight: '800' },
  earth: { position: 'absolute', right: -11, bottom: -26, opacity: 0.95 },
  heroCopy: { flex: 1, justifyContent: 'flex-end', paddingBottom: 5, maxWidth: '60%' },
  heroEyebrow: { color: '#A6D9F7', letterSpacing: 1.6, fontSize: 9, fontWeight: '800', marginBottom: 5 },
  heroTitle: { color: '#FFFFFF', fontSize: 23, lineHeight: 26, letterSpacing: -0.5, fontWeight: '800' },
  heroLine: { width: 28, height: 2, backgroundColor: '#9ACCF7', marginTop: 10, borderRadius: 2 },
  intro: { paddingHorizontal: 3, paddingTop: 2, gap: 2 },
  title: { color: colors.text, fontSize: 24, lineHeight: 30, fontWeight: '800', letterSpacing: -0.5 },
  tagline: { color: colors.muted, fontSize: 12, lineHeight: 17 },
  form: { gap: 10, padding: 14, borderRadius: 20 },
  error: { color: colors.red, fontSize: 12, lineHeight: 18 },
  demo: { minHeight: 72, borderRadius: 19, paddingHorizontal: 13, flexDirection: 'row', alignItems: 'center', gap: 11, backgroundColor: colors.card, borderColor: colors.border, borderWidth: 1 },
  demoIcon: { width: 42, height: 42, borderRadius: 14, backgroundColor: colors.cyan, alignItems: 'center', justifyContent: 'center' },
  demoCopy: { flex: 1, gap: 3 },
  demoTitle: { color: colors.text, fontSize: 15, fontWeight: '800' },
  demoHint: { color: colors.muted, fontSize: 11, lineHeight: 15 },
  demoArrow: { width: 30, height: 30, alignItems: 'center', justifyContent: 'center', borderRadius: 15, backgroundColor: colors.cardSoft },
  connection: { minHeight: 32, alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 7 },
  connectionText: { color: colors.muted, fontSize: 11, fontWeight: '600' },
  pressed: { opacity: 0.8, transform: [{ scale: 0.99 }] },
});
