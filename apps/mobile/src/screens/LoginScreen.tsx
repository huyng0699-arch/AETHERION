import React, { useState } from 'react';
import { Image, KeyboardAvoidingView, Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Locale } from '../types';
import { t } from '../i18n';
import { colors } from '../theme';
import { ActionButton, AppHeader, AppPage, Field, Panel, Title } from '../components/ui';

const AI_ORB = require('../../assets/aetherion-ai-orb.png');

export function LoginScreen({
  locale, serverUrl, setServerUrl, onConnect, onSignIn, onOpenDemo, onBack, busy, error,
}: {
  locale: Locale;
  serverUrl: string;
  setServerUrl: (value: string) => void;
  onConnect: (serverUrl: string) => void | Promise<void>;
  onSignIn: (serverUrl: string, username: string, password: string) => void | Promise<void>;
  onOpenDemo: () => void;
  onBack?: () => void;
  busy: boolean;
  error?: string | null;
}) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const canSubmit = serverUrl.trim().length > 0 && username.trim().length > 0 && password.length > 0;

  return (
    <AppPage contentStyle={styles.page}>
      <AppHeader title={t(locale, 'signIn')} onBack={onBack} backLabel={t(locale, 'back')} />
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.wrap}>
        <View style={styles.intro}>
          <Image source={AI_ORB} resizeMode="contain" style={styles.orb} />
          <Title size={27}>{t(locale, 'signInTitle')}</Title>
        </View>
        <Pressable accessibilityRole="button" onPress={onOpenDemo} style={({ pressed }) => [styles.demoButton, pressed && styles.dimmed]}>
          <Image source={AI_ORB} resizeMode="contain" style={styles.demoIcon} />
          <Text style={styles.demoText}>{t(locale, 'demoForHackathon')}</Text>
          <Ionicons name="chevron-forward" size={20} color="#FFFFFF" />
        </Pressable>
        <Panel style={styles.panel}>
          <Field label={t(locale, 'serverUrl')} value={serverUrl} onChangeText={setServerUrl} autoCapitalize="none" autoCorrect={false} keyboardType="url" placeholder="https://" />
          <Pressable accessibilityRole="button" onPress={() => void onConnect(serverUrl)} disabled={!serverUrl.trim() || busy} style={({ pressed }) => [styles.connect, (pressed || busy) && styles.dimmed]}>
            <Ionicons name="radio-outline" size={18} color={colors.cyan} />
            <Text style={styles.connectText}>{t(locale, 'connect')}</Text>
          </Pressable>
          <View style={styles.separator} />
          <Field label={t(locale, 'username')} value={username} onChangeText={setUsername} autoCapitalize="none" autoCorrect={false} textContentType="username" autoComplete="username" />
          <Field label={t(locale, 'password')} value={password} onChangeText={setPassword} secureTextEntry textContentType="password" autoComplete="current-password" />
          {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
          <ActionButton title={busy ? t(locale, 'signingIn') : t(locale, 'signInAction')} onPress={() => void onSignIn(serverUrl, username, password)} disabled={!canSubmit || busy} loading={busy} />
        </Panel>
      </KeyboardAvoidingView>
    </AppPage>
  );
}

const styles = StyleSheet.create({
  page: { paddingTop: 8 },
  wrap: { flex: 1, gap: 18 },
  intro: { alignItems: 'center', gap: 7, paddingTop: 25, paddingBottom: 8 },
  orb: { width: 84, height: 84, marginBottom: 5 },
  panel: { gap: 15, padding: 18 },
  demoButton: { minHeight: 58, borderRadius: 18, backgroundColor: colors.cyan, flexDirection: 'row', alignItems: 'center', gap: 12, paddingHorizontal: 16, marginHorizontal: 2, shadowColor: '#5528E9', shadowOpacity: 0.2, shadowRadius: 12, shadowOffset: { width: 0, height: 6 }, elevation: 4 },
  demoIcon: { width: 34, height: 34 },
  demoText: { flex: 1, color: '#FFFFFF', fontSize: 15, fontWeight: '900' },
  connect: { minHeight: 42, borderRadius: 13, borderWidth: 1, borderColor: colors.border, backgroundColor: '#F6F3FF', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  connectText: { color: colors.cyan, fontWeight: '800', fontSize: 13 },
  dimmed: { opacity: 0.7 },
  separator: { height: 1, backgroundColor: colors.border, marginVertical: 1 },
  error: { color: colors.red, fontSize: 13, fontWeight: '700', lineHeight: 19 },
});
