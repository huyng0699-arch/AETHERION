import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, ImageBackground, KeyboardAvoidingView, Platform, StyleSheet, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { BottomNav } from './src/components/ui';
import { checkServer, readServerUrl, saveServerUrl, ApiError } from './src/api/client';
import { signIn, signOut, validateSession } from './src/api/auth';
import { deleteSession, readSession } from './src/storage/session';
import { loadLocale, saveLocale, t } from './src/i18n';
import { colors } from './src/theme';
import { AuthSession, Locale, SessionIdentity } from './src/types';
import { PortalScreen } from './src/screens/PortalScreen';
import { LoginScreen } from './src/screens/LoginScreen';
import { PersonalHealthScreen } from './src/screens/PersonalHealthScreen';
import { MonitorScreen } from './src/screens/MonitorScreen';
import { AiScreen } from './src/screens/AiScreen';
import { ScienceScreen } from './src/screens/ScienceScreen';
import { MissionScreen } from './src/screens/MissionScreen';
import { SettingsScreen } from './src/screens/SettingsScreen';
import { SettingsDetailScreen } from './src/screens/SettingsDetailScreen';
import { MoreScreen } from './src/screens/MoreScreen';
import { ServerConnectionScreen } from './src/screens/ServerConnectionScreen';
import { NotificationScreen } from './src/screens/NotificationScreen';
import { HelpScreen } from './src/screens/HelpScreen';
import { PrivacyScreen } from './src/screens/PrivacyScreen';
import { CareScreen } from './src/screens/CareScreen';
import { HackathonDemoIntroScreen } from './src/screens/HackathonDemoIntroScreen';
import { HackathonDemoDataScreen } from './src/screens/HackathonDemoDataScreen';

type Route = 'portal' | 'login' | 'health' | 'monitor' | 'ai' | 'science' | 'mission' | 'care' | 'settings' | 'more' | 'connection' | 'notifications' | 'help' | 'privacy' | 'demoIntro' | 'demoData' | 'settingAccount' | 'settingConnection' | 'settingLanguage';
function messageFor(error: unknown, locale: Locale): string {
  if (error instanceof ApiError) {
    if (error.status === 401) return t(locale, 'loginFailed');
    if (error.status === 403) return t(locale, 'forbidden');
    if (error.status === 404) return t(locale, 'notFound');
    if (error.status === 0 || error.status === 408) return t(locale, 'networkError');
    return t(locale, 'serverError');
  }
  return t(locale, 'loginFailed');
}

export default function App() {
  const [route, setRoute] = useState<Route>('portal');
  const [history, setHistory] = useState<Route[]>([]);
  const [pendingRoute, setPendingRoute] = useState<Route>('portal');
  const [locale, setLocale] = useState<Locale>('en');
  const [session, setSession] = useState<AuthSession | null>(null);
  const [identity, setIdentity] = useState<SessionIdentity | null>(null);
  const [serverUrl, setServerUrl] = useState('');
  const [serverStatus, setServerStatus] = useState<'online' | 'offline' | 'unknown'>('unknown');
  const [busy, setBusy] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (Platform.OS === 'web' && typeof window !== 'undefined') window.scrollTo(0, 0);
  }, [route]);

  useEffect(() => {
    let active = true;
    void (async () => {
      const [savedSession, savedLocale, savedUrl] = await Promise.all([
        readSession(),
        loadLocale(),
        readServerUrl().catch(() => ''),
      ]);
      if (!active) return;
      setLocale(savedLocale);
      setServerUrl(savedUrl);
      if (savedSession) {
        const expires = Date.parse(savedSession.expires_at);
        if (Number.isFinite(expires) && expires <= Date.now()) {
          void deleteSession();
        } else {
          setSession(savedSession);
          setIdentity({ ...savedSession.user, expires_at: savedSession.expires_at });
          void validateSession(savedSession.access_token).then((current) => {
            if (active) setIdentity(current);
          }).catch((error) => {
            if (error instanceof ApiError && error.status === 401) {
              void deleteSession();
              if (active) { setSession(null); setIdentity(null); }
            }
          });
        }
      }
      if (savedUrl) {
        void checkServer().then(() => { if (active) setServerStatus('online'); })
          .catch(() => { if (active) setServerStatus('offline'); });
      }
      if (active) { setRoute('portal'); setReady(true); }
    })();
    return () => { active = false; };
  }, []);

  const changeLocale = async (next: Locale) => {
    setLocale(next);
    await saveLocale(next);
  };

  const openRoute = (next: Route) => {
    if (next === route) return;
    if (next === 'login') {
      setPendingRoute(route);
      setHistory((stack) => [...stack, route]);
      setRoute('login');
      return;
    }
    const requiresAuth = next === 'health' || next === 'monitor' || next === 'ai' || next === 'care' || next === 'mission';
    if (requiresAuth && !session?.access_token) {
      setPendingRoute(next);
      setLoginError(t(locale, 'loginRequired'));
      setHistory((stack) => [...stack, route]);
      setRoute('login');
      return;
    }
    setHistory((stack) => [...stack, route]);
    setRoute(next);
  };

  const goBack = () => {
    const previous = history[history.length - 1] || 'portal';
    setHistory((stack) => stack.slice(0, -1));
    setRoute(previous);
  };

  const saveUrl = async (value: string) => {
    const normalized = await saveServerUrl(value);
    setServerUrl(normalized);
  };

  const connect = async (value: string) => {
    setBusy(true); setLoginError('');
    try {
      await saveUrl(value);
      await checkServer();
      setServerStatus('online');
    } catch (error) {
      setServerStatus('offline');
      setLoginError(error instanceof Error && error.message === 'INVALID_SERVER_URL' ? t(locale, 'urlInvalid') : t(locale, 'networkError'));
    } finally { setBusy(false); }
  };

  const submitLogin = async (value: string, username: string, password: string) => {
    setBusy(true); setLoginError('');
    try {
      await saveUrl(value);
      const next = await signIn(username, password);
      setSession(next);
      setIdentity({ ...next.user, expires_at: next.expires_at });
      setServerStatus('online');
      setRoute(pendingRoute);
    } catch (error) {
      setLoginError(messageFor(error, locale));
    } finally { setBusy(false); }
  };

  const handleSignOut = async () => {
    await signOut();
    setSession(null); setIdentity(null); setHistory([]); setRoute('portal');
  };

  const handleUnauthorized = useCallback(async () => {
    await deleteSession();
    setSession(null); setIdentity(null); setPendingRoute(route); setRoute('login');
    setLoginError(t(locale, 'unauthorized'));
  }, [locale, route]);

  const navSelect = (id: string) => {
    const next: Route = id === 'portal' ? 'portal' : id === 'health' ? 'health' : id === 'monitor' ? 'monitor' : id === 'more' ? 'more' : 'ai';
    if ((next === 'health' || next === 'monitor' || next === 'ai') && !session?.access_token) {
      setPendingRoute(next); setLoginError(t(locale, 'loginRequired')); setHistory((stack) => [...stack, route]); setRoute('login'); return;
    }
    setHistory([]); setRoute(next);
  };
  const showNav = route !== 'login';
  const activeTab = route === 'health' ? 'health' : route === 'monitor' ? 'monitor' : route === 'ai' ? 'ai' : route === 'portal' || route === 'login' || route === 'demoIntro' || route === 'demoData' ? 'portal' : 'more';

  if (!ready) {
    return <SafeAreaProvider><View style={styles.loading}><ActivityIndicator color={colors.cyan} size="large" /></View></SafeAreaProvider>;
  }

  return (
    <SafeAreaProvider>
      <StatusBar style="dark" />
      <KeyboardAvoidingView style={styles.fill} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ImageBackground source={require('./assets/aetherion-app-background.png')} resizeMode="cover" style={styles.fill}>
          {route === 'portal' && <PortalScreen locale={locale} setLocale={changeLocale} isAuthenticated={!!session} serverStatus={serverStatus} onOpen={openRoute} />}
          {route === 'login' && <LoginScreen locale={locale} serverUrl={serverUrl} setServerUrl={setServerUrl} onConnect={connect} onSignIn={submitLogin} onBack={goBack} busy={busy} error={loginError} />}
          {route === 'health' && <PersonalHealthScreen locale={locale} token={session?.access_token || ''} subjectId={identity?.allowed_subjects?.[0]} onBack={goBack} onUnauthorized={handleUnauthorized} />}
          {route === 'monitor' && <MonitorScreen locale={locale} token={session?.access_token || ''} subjectId={identity?.allowed_subjects?.[0]} onBack={goBack} onUnauthorized={handleUnauthorized} />}
          {route === 'ai' && <AiScreen locale={locale} token={session?.access_token || ''} onBack={goBack} onUnauthorized={handleUnauthorized} />}
          {route === 'science' && <ScienceScreen locale={locale} onBack={goBack} />}
          {route === 'mission' && <MissionScreen locale={locale} role={identity?.role || ''} allowedSubjects={identity?.allowed_subjects || []} onBack={goBack} />}
          {route === 'care' && <CareScreen locale={locale} token={session?.access_token || ''} subjectId={identity?.allowed_subjects?.[0]} onBack={goBack} onUnauthorized={handleUnauthorized} />}
          {route === 'demoIntro' && <HackathonDemoIntroScreen locale={locale} onBack={goBack} onLoad={() => openRoute('demoData')} />}
          {route === 'demoData' && <HackathonDemoDataScreen locale={locale} onBack={goBack} />}
          {route === 'more' && <MoreScreen locale={locale} onBack={goBack} onOpen={openRoute} />}
          {route === 'connection' && <ServerConnectionScreen locale={locale} serverUrl={serverUrl} setServerUrl={setServerUrl} status={serverStatus} busy={busy} error={loginError} onCheck={() => void connect(serverUrl)} onBack={goBack} />}
          {route === 'notifications' && <NotificationScreen locale={locale} onBack={goBack} />}
          {route === 'help' && <HelpScreen locale={locale} onBack={goBack} />}
          {route === 'privacy' && <PrivacyScreen locale={locale} onBack={goBack} />}
          {route === 'settings' && <SettingsScreen locale={locale} onBack={goBack} onOpen={(section) => {
            if (section === 'account') openRoute('settingAccount');
            else if (section === 'connection') openRoute('settingConnection');
            else if (section === 'language') openRoute('settingLanguage');
            else openRoute(section);
          }} />}
          {(route === 'settingAccount' || route === 'settingConnection' || route === 'settingLanguage') && <SettingsDetailScreen
            section={route === 'settingAccount' ? 'account' : route === 'settingConnection' ? 'connection' : 'language'}
            locale={locale} onChangeLocale={changeLocale} onBack={goBack} serverUrl={serverUrl} onChangeServerUrl={setServerUrl}
            onSaveServerUrl={async () => { await saveUrl(serverUrl); }} onSignOut={handleSignOut} onSignIn={() => openRoute('login')}
            username={identity?.username || ''} role={identity?.role || ''}
          />}
          {showNav && <BottomNav active={activeTab} onSelect={navSelect} labels={{ portal: t(locale, 'home'), health: t(locale, 'personal'), monitor: t(locale, 'monitor'), ai: 'AI', more: t(locale, 'moreTitle') }} />}
        </ImageBackground>
      </KeyboardAvoidingView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({ fill: { flex: 1, backgroundColor: colors.background }, loading: { flex: 1, backgroundColor: colors.background, alignItems: 'center', justifyContent: 'center' } });
