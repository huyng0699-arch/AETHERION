import React, { useState } from 'react';
import { Image, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { Locale } from '../types';
import { t } from '../i18n';
import { copy } from '../uiCopy';
import { ThemeColors, useThemedStyles } from '../theme';
import { ActionButton, AppPage, Field, Panel, StatusPill } from '../components/ui';
type Props = { locale: Locale; setLocale: (locale: Locale) => void; onAppearance: () => void; serverUrl: string; setServerUrl: (url: string) => void; onConnect: (url: string) => void; onSignIn: (url: string, username: string, password: string) => void; onOpenDemo: () => void; onContinue?: () => void; restoredUsername?: string; busy: boolean; error?: string; status: 'online' | 'offline' | 'unknown' };
export function LoginScreen({ locale, setLocale, onAppearance, serverUrl, setServerUrl, onConnect, onSignIn, onOpenDemo, onContinue, restoredUsername, busy, error, status }: Props) {
  const { colors, styles, gradient } = useThemedStyles(buildStyles);
  const [username, setUsername] = useState(''), [password, setPassword] = useState(''), [connectionOpen, setConnectionOpen] = useState(false);
  const submit = () => { if (!busy && username.trim() && password && serverUrl.trim()) onSignIn(serverUrl, username, password); };
  return <AppPage contentStyle={styles.page}>
    <View style={styles.intro}>
      <Image source={require('../../assets/aetherion-ai-robot.png')} resizeMode="contain" style={styles.mascot} />
      <View style={styles.heroText}>
        <Text style={styles.brand}>AETHERION</Text>
        <Text style={styles.title}>{copy(locale, 'welcome')}</Text>
        <Text style={styles.tagline}>{copy(locale, 'tagline')}</Text>
      </View>
      <View style={styles.tools}>
        <Pressable accessibilityRole="button" accessibilityLabel={t(locale, 'language')} onPress={() => setLocale(locale === 'en' ? 'vi' : 'en')} style={styles.languagePill}>
          <Text style={styles.language}>{locale === 'en' ? 'ENG' : 'VIE'}</Text>
        </Pressable>
        <Pressable accessibilityRole="button" accessibilityLabel={copy(locale, 'appearance')} onPress={onAppearance} disabled={busy} style={styles.tool}>
          <Ionicons name="color-palette-outline" color={colors.cyan} size={19} />
        </Pressable>
      </View>
    </View>
    <Panel style={styles.form}>
      <Field label={t(locale, 'username')} value={username} onChangeText={setUsername} editable={!busy} autoCapitalize="none" autoCorrect={false} autoComplete="username" textContentType="username" returnKeyType="next" />
      <Field label={t(locale, 'password')} value={password} onChangeText={setPassword} editable={!busy} secureTextEntry autoComplete="current-password" textContentType="password" returnKeyType="go" onSubmitEditing={submit} />
      {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
      <ActionButton title={t(locale, busy ? 'signingIn' : 'signInAction')} onPress={submit} loading={busy} disabled={!username.trim() || !password || !serverUrl.trim()} />
      {restoredUsername && onContinue ? <ActionButton title={`${copy(locale, 'continueAs')} ${restoredUsername}`} onPress={onContinue} secondary disabled={busy} /> : null}
    </Panel>
    <Pressable accessibilityRole="button" accessibilityLabel="Demo" onPress={onOpenDemo} disabled={busy} style={({ pressed }) => [styles.demo, pressed && styles.pressed]}><LinearGradient colors={gradient} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.demoInner}><View style={styles.demoIcon}><Ionicons name="planet-outline" color="#FFFFFF" size={25} /></View><View style={styles.demoCopy}><Text style={styles.demoTitle}>Demo</Text><Text style={styles.demoHint}>{copy(locale, 'demoHint')}</Text></View><Ionicons name="arrow-forward" size={21} color="#FFFFFF" /></LinearGradient></Pressable>
    <Pressable accessibilityRole="button" accessibilityLabel={copy(locale, 'connection')} accessibilityState={{ expanded: connectionOpen }} onPress={() => setConnectionOpen(value => !value)} style={styles.connection}><Ionicons name="server-outline" color={colors.muted} size={16} /><Text style={styles.connectionText}>{copy(locale, 'connection')}</Text><Ionicons name={connectionOpen ? 'chevron-up' : 'chevron-down'} color={colors.muted} size={15} /></Pressable>
    {connectionOpen ? <Panel style={styles.form}><Field label={t(locale, 'serverUrl')} value={serverUrl} onChangeText={setServerUrl} editable={!busy} autoCapitalize="none" autoCorrect={false} keyboardType="url" /><StatusPill label={t(locale, status === 'online' ? 'serverOnline' : status === 'offline' ? 'serverOffline' : 'serverUnknown')} tone={status === 'online' ? 'good' : 'neutral'} /><ActionButton title={t(locale, 'connectionCheck')} onPress={() => onConnect(serverUrl)} disabled={busy || !serverUrl.trim()} secondary /></Panel> : null}
    <Text style={styles.credit}>AETHERION · TRUY TINH</Text>
  </AppPage>;
}
const buildStyles = (colors: ThemeColors) => StyleSheet.create({
  page: { paddingBottom: 42, gap: 14 },
  intro: { flexDirection: 'row', alignItems: 'center', gap: 12, marginTop: 12, marginBottom: 2 },
  mascot: { width: 74, height: 74 },
  heroText: { flex: 1, minWidth: 0 },
  brand: { color: colors.cyan, fontSize: 10, letterSpacing: 1.1, fontWeight: '900', marginBottom: 3 },
  title: { color: colors.text, fontSize: 30, lineHeight: 34, fontWeight: '900', letterSpacing: -0.8 },
  tagline: { color: colors.muted, fontSize: 13, lineHeight: 20, marginTop: 5 },
  tools: { width: 52, alignItems: 'center', gap: 6 },
  languagePill: { minWidth: 52, height: 30, borderRadius: 12, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.card, alignItems: 'center', justifyContent: 'center' },
  tool: { width: 36, height: 34, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.card, borderWidth: 1, borderColor: colors.border, borderRadius: 12 },
  language: { color: colors.cyan, fontWeight: '900', fontSize: 11 },
  form: { gap: 14, padding: 16, borderRadius: 22 },
  error: { color: colors.red, fontSize: 12, lineHeight: 18 },
  demo: { borderRadius: 22, overflow: 'hidden' },
  demoInner: { minHeight: 84, flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, gap: 12 },
  demoIcon: { width: 48, height: 48, borderRadius: 18, backgroundColor: 'rgba(255,255,255,0.15)', alignItems: 'center', justifyContent: 'center' },
  demoCopy: { flex: 1, gap: 5 },
  demoTitle: { color: '#FFFFFF', fontSize: 19, fontWeight: '900' },
  demoHint: { color: '#FFFFFF', fontSize: 11, opacity: 0.88 },
  connection: { minHeight: 39, alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 8 },
  connectionText: { color: colors.muted, fontSize: 12, fontWeight: '600' },
  credit: { color: colors.faint, fontSize: 10, textAlign: 'center', letterSpacing: 1 },
  pressed: { opacity: 0.85 },
});
