import React, { useCallback, useEffect, useMemo, useReducer, useRef, useState } from 'react';
import { ActivityIndicator, Animated, BackHandler, ImageBackground, KeyboardAvoidingView, Modal, PanResponder, Platform, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFonts } from 'expo-font';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { BottomNav } from './src/components/ui';
import { checkServer, normalizeBaseUrl, readServerUrl, saveServerUrl, ApiError } from './src/api/client';
import { signIn, signOut, validateSession } from './src/api/auth';
import { listSubjects, Subject } from './src/api/subjects';
import { deleteSession, readSession, writeSession } from './src/storage/session';
import { loadLocale, saveLocale, t } from './src/i18n';
import { copy } from './src/uiCopy';
import { ThemeColors, ThemeProvider, useThemedStyles } from './src/theme';
import { AuthSession, Locale, SessionIdentity } from './src/types';
import { initialNavigation, navigate, protectedRoutes, Route } from './src/navigation';
import { useRequestGate } from './src/hooks/useRequestGate';
import { PortalScreen } from './src/screens/PortalScreen';
import { LoginScreen } from './src/screens/LoginScreen';
import { PersonalHealthScreen } from './src/screens/PersonalHealthScreen';
import { MonitorScreen } from './src/screens/MonitorScreen';
import { AiScreen } from './src/screens/AiScreen';
import { AiServerSettingsScreen } from './src/screens/AiServerSettingsScreen';
import { ScienceScreen } from './src/screens/ScienceScreen';
import { MissionScreen } from './src/screens/MissionScreen';
import { SettingsScreen } from './src/screens/SettingsScreen';
import { SettingsDetailScreen } from './src/screens/SettingsDetailScreen';
import { AppearanceSettingsScreen } from './src/screens/AppearanceSettingsScreen';
import { MoreScreen } from './src/screens/MoreScreen';
import { ServerConnectionScreen } from './src/screens/ServerConnectionScreen';
import { NotificationScreen } from './src/screens/NotificationScreen';
import { HelpScreen } from './src/screens/HelpScreen';
import { PrivacyScreen } from './src/screens/PrivacyScreen';
import { CareScreen } from './src/screens/CareScreen';
import { HealthGuideScreen } from './src/screens/HealthGuideScreen';
import { HackathonDemoIntroScreen } from './src/screens/HackathonDemoIntroScreen';
import { HackathonDemoDataScreen } from './src/screens/HackathonDemoDataScreen';

export default function App() { return <ThemeProvider><AppShell /></ThemeProvider>; }
function messageFor(error: unknown, locale: Locale): string {
  if (error instanceof ApiError) return t(locale, error.status === 401 ? 'loginFailed' : error.status === 403 ? 'forbidden' : error.status === 404 ? 'notFound' : error.status === 0 || error.status === 408 ? 'networkError' : 'serverError');
  return t(locale, error instanceof Error && ['INVALID_SERVER_URL', 'HTTPS_REQUIRED'].includes(error.message) ? 'urlInvalid' : 'loginFailed');
}
function AppShell() {
  const { styles, colors, isDark, appearance } = useThemedStyles(buildStyles);
  const [fontLoaded, fontError] = useFonts(Ionicons.font);
  const [navigation, dispatch] = useReducer(navigate, initialNavigation);
  const { route, history } = navigation;
  const [locale, setLocale] = useState<Locale>('en');
  const [session, setSession] = useState<AuthSession | null>(null);
  const [identity, setIdentity] = useState<SessionIdentity | null>(null);
  const [unlocked, setUnlocked] = useState(false);
  const [serverUrl, setServerUrl] = useState('');
  const [serverStatus, setServerStatus] = useState<'online' | 'offline' | 'unknown'>('unknown');
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [ready, setReady] = useState(false);
  const [subjects, setSubjects] = useState<Subject[]>([]), [subjectId, setSubjectId] = useState<string>(), [chooseSubject, setChooseSubject] = useState(false);
  const [assistantContext, setAssistantContext] = useState<{ articleId: string; title: string } | null>(null);
  const busyFlag = useRef(false);
  const operation = useRef(0), mounted = useRef(true), localeWrites = useRef(Promise.resolve());
  const fade = useRef(new Animated.Value(1)).current;
  const beginSubjects = useRequestGate();
  const clearIdentity = useCallback(() => { beginSubjects(); setSession(null); setIdentity(null); setUnlocked(false); setSubjects([]); setSubjectId(undefined); setChooseSubject(false); setAssistantContext(null); }, [beginSubjects]);
  useEffect(() => { mounted.current = true; let active = true; const restoreOperation = operation.current; void (async () => {
    const [saved, language, url] = await Promise.all([readSession(), loadLocale().catch(() => 'en' as Locale), readServerUrl().catch(() => '')]);
    if (!active) return;
    setLocale(language); setServerUrl(url); setReady(true);
    if (saved && saved.server_url === url && Date.parse(saved.expires_at) > Date.now()) {
      try { const me = await validateSession(saved.access_token); if (active && operation.current === restoreOperation) { setSession(saved); setIdentity(me); } }
      catch (cause) { if (active && operation.current === restoreOperation && cause instanceof ApiError && cause.status === 401) await deleteSession(); }
    } else if (saved) await deleteSession();
  })().catch(() => { if (active) setReady(true); }); return () => { active = false; mounted.current = false; operation.current += 1; }; }, []);
  useEffect(() => {
    if (appearance.reduceMotion) { fade.setValue(1); return; }
    fade.setValue(0.3); const animation = Animated.timing(fade, { toValue: 1, duration: 160, useNativeDriver: Platform.OS !== 'web' }); animation.start(); return () => animation.stop();
  }, [route, appearance.reduceMotion, fade]);
  const handleUnauthorized = useCallback(() => { operation.current += 1; busyFlag.current = false; setBusy(false); void deleteSession(); clearIdentity(); dispatch({ type: 'signedOut', pending: route }); setError(t(locale, 'unauthorized')); }, [clearIdentity, locale, route]);
  const refreshSubjects = useCallback(async () => { const current = beginSubjects(); if (!session?.access_token || !unlocked) return; const rows = await listSubjects(session.access_token); if (current()) { setSubjects(rows); setSubjectId(selected => rows.some(row => row.subject_id === selected) ? selected : rows[0]?.subject_id); } }, [session?.access_token, unlocked, beginSubjects]);
  useEffect(() => { let active = true; const current = beginSubjects(); if (!session?.access_token || !unlocked) return; void listSubjects(session.access_token).then(rows => { if (active && current()) { setSubjects(rows); setSubjectId(selected => rows.some(row => row.subject_id === selected) ? selected : rows[0]?.subject_id); } }).catch(cause => { if (active && current() && cause instanceof ApiError && cause.status === 401) handleUnauthorized(); }); return () => { active = false; }; }, [session?.access_token, unlocked, beginSubjects]);
  const changeLocale = (next: Locale) => { setLocale(next); localeWrites.current = localeWrites.current.catch(() => {}).then(() => saveLocale(next)); };
  const openRoute = (next: Route, tab = false) => { if (busyFlag.current) return; operation.current += 1; setError(''); dispatch({ type: 'open', route: next, unlocked, tab }); };
  const goBack = useCallback(() => { if (busyFlag.current) return; operation.current += 1; setError(''); dispatch({ type: 'back' }); }, []);
  useEffect(() => { const event = BackHandler.addEventListener('hardwareBackPress', () => { if (busyFlag.current) return true; if (!history.length) return false; goBack(); return true; }); return () => event.remove(); }, [history.length, goBack]);
  const swipe = useMemo(() => PanResponder.create({ onMoveShouldSetPanResponder: (_, state) => !busyFlag.current && history.length > 0 && state.x0 < 36 && state.dx > 55 && Math.abs(state.dy) < 24, onPanResponderRelease: (_, state) => { if (state.dx > 85) goBack(); } }), [history.length, goBack]);
  const saveUrl = async (value: string) => { const normalized = normalizeBaseUrl(value); const old = await readServerUrl().catch(() => ''); if (old !== normalized) { await deleteSession(); clearIdentity(); dispatch({ type: 'signedOut' }); setServerStatus('unknown'); } await saveServerUrl(normalized); setServerUrl(normalized); return normalized; };
  const connect = async (value: string) => { if (busyFlag.current) return; busyFlag.current = true; const id = ++operation.current; setBusy(true); setError(''); try { await saveUrl(value); await checkServer(); if (mounted.current && operation.current === id) setServerStatus('online'); } catch (cause) { if (mounted.current && operation.current === id) { setServerStatus('offline'); setError(messageFor(cause, locale)); } } finally { if (mounted.current && operation.current === id) { busyFlag.current = false; setBusy(false); } } };
  const submitLogin = async (value: string, username: string, password: string) => { if (busyFlag.current) return; busyFlag.current = true; const id = ++operation.current; setBusy(true); setError(''); try { const capturedServer = await saveUrl(value); if (!mounted.current || operation.current !== id) return; const next = await signIn(username, password, capturedServer); if (!mounted.current || operation.current !== id) return; await writeSession(next); if (operation.current !== id) return; setSession(next); setIdentity({ ...next.user, expires_at: next.expires_at }); setUnlocked(true); setServerStatus('online'); dispatch({ type: 'signedIn' }); } catch (cause) { if (mounted.current && operation.current === id) setError(messageFor(cause, locale)); } finally { if (mounted.current && operation.current === id) { busyFlag.current = false; setBusy(false); } } };
  const continueSession = async () => { if (!session || busyFlag.current) return; busyFlag.current = true; const id = ++operation.current; setBusy(true); try { const me = await validateSession(session.access_token); if (operation.current === id) { setIdentity(me); setUnlocked(true); dispatch({ type: 'signedIn' }); } } catch (cause) { if (operation.current === id) { if (cause instanceof ApiError && cause.status === 401) handleUnauthorized(); else setError(messageFor(cause, locale)); } } finally { if (operation.current === id) { busyFlag.current = false; setBusy(false); } } };
  const handleSignOut = async () => { const id = ++operation.current; busyFlag.current = true; setBusy(true); clearIdentity(); dispatch({ type: 'signedOut' }); try { await signOut(); } finally { if (operation.current === id) { busyFlag.current = false; setBusy(false); } } };
  const navSelect = (id: string) => openRoute(id === 'portal' ? 'portal' : id === 'health' ? 'health' : id === 'monitor' ? 'monitor' : id === 'more' ? 'more' : 'ai', true);
  const showNav = unlocked && !['login', 'demoIntro', 'demoData', 'appearance'].includes(route);
  const activeTab = ['health', 'monitor', 'ai', 'portal'].includes(route) ? route : 'more';
  const profileRoute = ['health', 'monitor', 'care'].includes(route);
  if (!ready || (!fontLoaded && !fontError)) return <SafeAreaProvider><View style={styles.loading}><ActivityIndicator color={colors.cyan} size="large" /></View></SafeAreaProvider>;
  return <SafeAreaProvider><StatusBar style={isDark ? 'light' : 'dark'} /><KeyboardAvoidingView style={styles.fill} behavior={Platform.OS === 'ios' ? 'padding' : undefined}><ImageBackground source={require('./assets/aetherion-app-background.png')} imageStyle={{ opacity: isDark ? 0.05 : 0.5 }} resizeMode="cover" style={styles.fill}><View style={styles.mobileShell}>
    {profileRoute && unlocked ? <Pressable accessibilityRole="button" accessibilityLabel={copy(locale, 'chooseProfile')} onPress={() => setChooseSubject(true)} style={styles.profile}><Ionicons name="person-circle-outline" size={22} color={colors.cyan} /><Text style={styles.profileText}>{subjects.find(row => row.subject_id === subjectId)?.display_name || copy(locale, 'noProfiles')}</Text><Ionicons name="chevron-down" size={17} color={colors.muted} /></Pressable> : null}
    <Animated.View key={`${route}:${subjectId || ''}`} style={[styles.fill, { backgroundColor: 'transparent', opacity: fade }]} {...swipe.panHandlers}>
      {route === 'login' && <LoginScreen locale={locale} setLocale={changeLocale} onAppearance={() => openRoute('appearance')} serverUrl={serverUrl} setServerUrl={setServerUrl} onConnect={connect} onSignIn={submitLogin} onOpenDemo={() => openRoute('demoIntro')} onContinue={continueSession} restoredUsername={session?.user.username} busy={busy} error={error} status={serverStatus} />}
      {route === 'portal' && unlocked && <PortalScreen locale={locale} setLocale={changeLocale} isAuthenticated={true} token={session?.access_token || ''} serverStatus={serverStatus} onUnauthorized={handleUnauthorized} onOpen={openRoute} />}
      {route === 'health' && unlocked && <PersonalHealthScreen locale={locale} token={session?.access_token || ''} subjectId={subjectId} onBack={goBack} onUnauthorized={handleUnauthorized} />}
      {route === 'monitor' && unlocked && <MonitorScreen locale={locale} token={session?.access_token || ''} subjectId={subjectId} onBack={goBack} onUnauthorized={handleUnauthorized} />}
      {route === 'care' && unlocked && <CareScreen locale={locale} token={session?.access_token || ''} subjectId={subjectId} onBack={goBack} onUnauthorized={handleUnauthorized} />}
      {route === 'healthGuide' && <HealthGuideScreen locale={locale} onBack={goBack} />}
      {route === 'ai' && unlocked && <AiScreen locale={locale} token={session?.access_token || ''} context={assistantContext} onClearContext={() => setAssistantContext(null)} onBack={goBack} onUnauthorized={handleUnauthorized} />}
      {route === 'science' && <ScienceScreen locale={locale} onBack={goBack} onAskAi={article => { setAssistantContext({ articleId: article.article_id, title: article.title }); openRoute('ai'); }} />}
      {route === 'mission' && unlocked && <MissionScreen locale={locale} role={identity?.role || ''} subjects={subjects} token={session?.access_token || ''} onRefresh={refreshSubjects} onSelect={id => { setSubjectId(id); openRoute('health'); }} onBack={goBack} />}
      {route === 'demoIntro' && <HackathonDemoIntroScreen locale={locale} onBack={goBack} onLoad={() => openRoute('demoData')} onLibrary={() => openRoute('science')} onHealthGuide={() => openRoute('healthGuide')} />}
      {route === 'demoData' && <HackathonDemoDataScreen locale={locale} onBack={goBack} />}
      {route === 'more' && <MoreScreen locale={locale} onBack={goBack} onOpen={openRoute} />}
      {route === 'appearance' && <AppearanceSettingsScreen locale={locale} onBack={goBack} />}
      {route === 'connection' && <ServerConnectionScreen locale={locale} serverUrl={serverUrl} setServerUrl={setServerUrl} status={serverStatus} busy={busy} error={error} onCheck={() => void connect(serverUrl)} onBack={goBack} />}
      {route === 'notifications' && <NotificationScreen locale={locale} onBack={goBack} />}
      {route === 'help' && <HelpScreen locale={locale} onBack={goBack} onOpen={openRoute} />}
      {route === 'privacy' && <PrivacyScreen locale={locale} onBack={goBack} />}
      {route === 'settings' && <SettingsScreen locale={locale} role={identity?.role} onBack={goBack} onOpen={section => openRoute(section === 'account' ? 'settingAccount' : section === 'connection' ? 'settingConnection' : section === 'language' ? 'settingLanguage' : section)} />}
      {route === 'aiSettings' && unlocked && identity?.role === 'admin' && <AiServerSettingsScreen locale={locale} token={session?.access_token || ''} onBack={goBack} onUnauthorized={handleUnauthorized} />}
      {['settingAccount', 'settingConnection', 'settingLanguage'].includes(route) && <SettingsDetailScreen section={route === 'settingAccount' ? 'account' : route === 'settingConnection' ? 'connection' : 'language'} locale={locale} onChangeLocale={changeLocale} onBack={goBack} serverUrl={serverUrl} onChangeServerUrl={setServerUrl} onSaveServerUrl={async () => { await saveUrl(serverUrl); }} onSignOut={handleSignOut} onSignIn={() => openRoute('login')} username={identity?.username || ''} role={identity?.role || ''} />}
    </Animated.View>
    {showNav && <BottomNav active={activeTab} onSelect={navSelect} labels={{ portal: t(locale, 'home'), health: t(locale, 'personal'), monitor: t(locale, 'monitor'), ai: 'AI', more: t(locale, 'moreTitle') }} />}
    <Modal transparent visible={chooseSubject} onRequestClose={() => setChooseSubject(false)} animationType={appearance.reduceMotion ? 'none' : 'fade'}><View style={styles.modal}><View style={styles.sheet}><View style={styles.sheetHeading}><Text style={styles.profileText}>{copy(locale, 'chooseProfile')}</Text><Pressable accessibilityRole="button" accessibilityLabel={t(locale, 'back')} onPress={() => setChooseSubject(false)}><Ionicons name="close" color={colors.text} size={24} /></Pressable></View><ScrollView>{subjects.map(row => <Pressable accessibilityRole="button" key={row.subject_id} style={styles.profile} onPress={() => { setSubjectId(row.subject_id); setChooseSubject(false); }}><Text style={styles.profileText}>{row.display_name}</Text>{subjectId === row.subject_id && <Ionicons name="checkmark" color={colors.cyan} size={20} />}</Pressable>)}</ScrollView><Pressable accessibilityRole="button" style={styles.profile} onPress={() => { setChooseSubject(false); openRoute('mission'); }}><Text style={styles.profileText}>{copy(locale, 'registerProfile')}</Text><Ionicons name="add" color={colors.cyan} size={22} /></Pressable></View></View></Modal>
  </View></ImageBackground></KeyboardAvoidingView></SafeAreaProvider>;
}
const buildStyles = (colors: ThemeColors) => StyleSheet.create({ fill: { flex: 1, backgroundColor: colors.background }, mobileShell: { flex: 1, width: '100%', maxWidth: 470, alignSelf: 'center' }, loading: { flex: 1, backgroundColor: colors.background, alignItems: 'center', justifyContent: 'center' }, profile: { minHeight: 48, flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 18, borderBottomWidth: 1, borderBottomColor: colors.border, backgroundColor: colors.card }, profileText: { flex: 1, color: colors.text, fontSize: 13, fontWeight: '700' }, modal: { flex: 1, justifyContent: 'flex-end', alignItems: 'center', backgroundColor: 'rgba(12,8,30,0.45)' }, sheet: { width: '100%', maxWidth: 470, maxHeight: '65%', padding: 18, paddingBottom: 30, borderTopLeftRadius: 28, borderTopRightRadius: 28, backgroundColor: colors.card }, sheetHeading: { flexDirection: 'row', alignItems: 'center', paddingBottom: 14 } });

