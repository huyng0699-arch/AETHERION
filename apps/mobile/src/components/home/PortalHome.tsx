import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { ActivityIndicator, Animated, Image, Modal, PanResponder, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, useWindowDimensions, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { AppPage } from '../ui';
import { Locale, Observation } from '../../types';
import { t } from '../../i18n';
import { copy } from '../../uiCopy';
import { getObservations } from '../../api/health';
import { ApiError } from '../../api/client';
import { ThemeColors, useThemedStyles } from '../../theme';

export type MobileScreen = 'health' | 'monitor' | 'ai' | 'science' | 'mission' | 'login' | 'settings' | 'demoIntro' | 'demoData' | 'more' | 'connection' | 'settingConnection' | 'settingAccount' | 'settingLanguage' | 'notifications' | 'help' | 'privacy' | 'care' | 'appearance' | 'healthGuide';
type Icon = keyof typeof Ionicons.glyphMap;
type Destination = { route: MobileScreen; icon: Icon; label: string };

const AI_ROBOT = require('../../../assets/aetherion-ai-robot.png');
const TEAM_LOGO = require('../../../assets/truy-tinh-cosmic-orbit.png');
const HEALTH_TIP_KEY = 'aetherion.mobile.health-tip.shown.v1';
let healthTipClaim: Promise<boolean> | null = null;
let healthTipPresented = false;

function claimHealthTip(): Promise<boolean> {
  if (healthTipPresented) return Promise.resolve(false);
  if (!healthTipClaim) {
    healthTipClaim = (async () => {
      if (await AsyncStorage.getItem(HEALTH_TIP_KEY)) return false;
      await AsyncStorage.setItem(HEALTH_TIP_KEY, 'shown');
      return true;
    })().catch(() => true);
  }
  return healthTipClaim;
}

export function PortalHome({ locale, isAuthenticated, demoMode, token, subjectId, profileName, onChooseProfile, onUnauthorized, onOpen, onLogout }: {
  locale: Locale;
  isAuthenticated: boolean;
  demoMode: boolean;
  token: string;
  subjectId?: string;
  profileName?: string;
  onChooseProfile: () => void;
  onUnauthorized: () => void;
  onOpen: (screen: MobileScreen) => void;
  onLogout: () => void;
}) {
  const { colors, styles, appearance, gradient, isDark } = useThemedStyles(buildStyles);
  const insets = useSafeAreaInsets();
  const { width: viewportWidth } = useWindowDimensions();
  const frameWidth = Math.min(viewportWidth, 470);
  const frameLeft = Math.max(0, (viewportWidth - frameWidth) / 2);
  const drawerWidth = Math.min(frameWidth * 0.86, 360);
  const tipWidth = Math.min(frameWidth - 24, 420);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const drawerOpenRef = useRef(false);
  const [healthTipVisible, setHealthTipVisible] = useState(false);
  const [query, setQuery] = useState('');
  const [focusSearch, setFocusSearch] = useState(false);
  const searchInputRef = useRef<React.ElementRef<typeof TextInput>>(null);
  const drawerPosition = useRef(new Animated.Value(-drawerWidth)).current;
  const closeDragStartX = useRef(0);
  const readingsSequence = useRef(0);
  const [latestReadings, setLatestReadings] = useState<Observation[]>([]);
  const [readingsLoading, setReadingsLoading] = useState(false);
  const [readingsError, setReadingsError] = useState('');
  const isVi = locale === 'vi';
  useEffect(() => {
    let active = true;
    if (!isAuthenticated || demoMode) return;
    void claimHealthTip().then((shouldShow) => {
      if (active && shouldShow && !healthTipPresented) {
        healthTipPresented = true;
        setHealthTipVisible(true);
      }
    });
    return () => { active = false; };
  }, [demoMode, isAuthenticated]);
  useEffect(() => {
    const sequence = ++readingsSequence.current;
    let active = true;
    if (!isAuthenticated || !token || !subjectId) {
      setLatestReadings([]);
      setReadingsError('');
      setReadingsLoading(false);
      return () => { active = false; readingsSequence.current += 1; };
    }
    setReadingsLoading(true);
    setReadingsError('');
    void getObservations(subjectId, token).then(page => {
      if (active && sequence === readingsSequence.current) setLatestReadings(pickLatestReadings(page.observations || []));
    }).catch(cause => {
      if (!active || sequence !== readingsSequence.current) return;
      setLatestReadings([]);
      if (cause instanceof ApiError && cause.status === 401) onUnauthorized();
      else setReadingsError(t(locale, cause instanceof ApiError && cause.status >= 500 ? 'serverError' : 'networkError'));
    }).finally(() => {
      if (active && sequence === readingsSequence.current) setReadingsLoading(false);
    });
    return () => { active = false; readingsSequence.current += 1; };
  }, [isAuthenticated, locale, onUnauthorized, subjectId, token]);
  const quick: Destination[] = [
    { route: 'health', icon: 'medkit-outline', label: t(locale, 'personal') },
    { route: 'monitor', icon: 'radio-outline', label: t(locale, 'monitor') },
    { route: 'ai', icon: 'sparkles-outline', label: t(locale, 'ai') },
    { route: 'care', icon: 'heart-outline', label: t(locale, 'careTitle') },
    { route: 'science', icon: 'planet-outline', label: t(locale, 'science') },
  ];
  const tools: Destination[] = [
    { route: 'connection', icon: 'planet-outline', label: t(locale, 'connectionTitle') },
    { route: 'settings', icon: 'settings-outline', label: t(locale, 'settings') },
    { route: 'appearance', icon: 'color-palette-outline', label: copy(locale, 'appearance') },
    { route: 'privacy', icon: 'shield-checkmark-outline', label: t(locale, 'privacyTitle') },
    { route: 'notifications', icon: 'notifications-outline', label: t(locale, 'notifications') },
    { route: 'help', icon: 'help-circle-outline', label: t(locale, 'helpTitle') },
  ];
  const drawerItems: Destination[] = [
    { route: 'health', icon: 'medkit-outline', label: t(locale, 'personal') },
    { route: 'monitor', icon: 'pulse-outline', label: t(locale, 'monitor') },
    { route: 'ai', icon: 'sparkles-outline', label: t(locale, 'ai') },
    { route: 'science', icon: 'planet-outline', label: t(locale, 'science') },
    { route: 'care', icon: 'heart-outline', label: t(locale, 'careTitle') },
    { route: 'healthGuide', icon: 'book-outline', label: copy(locale, 'healthGuide') },
    { route: 'mission', icon: 'people-outline', label: t(locale, 'missionTitle') },
    { route: 'more', icon: 'grid-outline', label: t(locale, 'moreTitle') },
    { route: 'settingAccount', icon: 'person-circle-outline', label: t(locale, 'accountTitle') },
    { route: 'settingLanguage', icon: 'language-outline', label: t(locale, 'language') },
    ...tools,
  ];
  const matches = drawerItems.filter(item => item.label.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()));

  const settleDrawer = useCallback((open: boolean) => {
    drawerOpenRef.current = open;
    if (open) setDrawerOpen(true);
    if (appearance.reduceMotion) {
      drawerPosition.setValue(open ? 0 : -drawerWidth);
      if (!open) setDrawerOpen(false);
      return;
    }
    Animated.spring(drawerPosition, {
      toValue: open ? 0 : -drawerWidth, stiffness: open ? 220 : 220, damping: open ? 22 : 24,
      mass: 0.9, overshootClamping: true, useNativeDriver: Platform.OS !== 'web',
    }).start(({ finished }) => { if (finished && !open) setDrawerOpen(false); });
  }, [appearance.reduceMotion, drawerPosition, drawerWidth]);
  const openDrawer = useCallback(() => settleDrawer(true), [settleDrawer]);
  const closeDrawer = useCallback(() => settleDrawer(false), [settleDrawer]);
  const openSearch = useCallback(() => { setFocusSearch(true); openDrawer(); }, [openDrawer]);
  useEffect(() => {
    if (!drawerOpen || !focusSearch) return;
    const timer = setTimeout(() => { searchInputRef.current?.focus(); setFocusSearch(false); }, 120);
    return () => clearTimeout(timer);
  }, [drawerOpen, focusSearch]);
  const dismissHealthTip = useCallback(() => {
    healthTipPresented = true;
    setHealthTipVisible(false);
    void AsyncStorage.setItem(HEALTH_TIP_KEY, 'shown').catch(() => undefined);
  }, []);
  const openHealthGuide = () => {
    dismissHealthTip();
    openDestination('healthGuide');
  };
  const openDestination = (route: MobileScreen) => {
    drawerOpenRef.current = false;
    setDrawerOpen(false);
    setQuery('');
    onOpen(route);
  };
  const edgeSwipe = useMemo(() => PanResponder.create({
    onMoveShouldSetPanResponder: (_, gesture) => !drawerOpenRef.current
      && gesture.x0 <= frameLeft + Math.min(45, frameWidth / 5)
      && gesture.dx > 14 && gesture.dx > Math.abs(gesture.dy) * 1.2,
    onPanResponderGrant: () => {
      drawerPosition.stopAnimation();
      drawerPosition.setValue(-drawerWidth);
      drawerOpenRef.current = true;
      setDrawerOpen(true);
    },
    onPanResponderMove: (_, gesture) => drawerPosition.setValue(Math.min(0, Math.max(-drawerWidth, -drawerWidth + gesture.dx))),
    onPanResponderRelease: (_, gesture) => settleDrawer(gesture.vx > 0.28 || gesture.dx / drawerWidth > 0.18),
    onPanResponderTerminate: (_, gesture) => settleDrawer(gesture.vx > 0.28 || gesture.dx / drawerWidth > 0.18),
  }), [drawerOpenRef, drawerPosition, drawerWidth, frameLeft, frameWidth, settleDrawer]);
  const closeSwipe = useMemo(() => PanResponder.create({
    onMoveShouldSetPanResponder: (_, gesture) => gesture.dx < -14 && -gesture.dx > Math.abs(gesture.dy) * 1.2,
    onPanResponderGrant: () => drawerPosition.stopAnimation(value => { closeDragStartX.current = value; }),
    onPanResponderMove: (_, gesture) => drawerPosition.setValue(Math.min(0, Math.max(-drawerWidth, closeDragStartX.current + gesture.dx))),
    onPanResponderRelease: (_, gesture) => {
      const finalX = Math.min(0, Math.max(-drawerWidth, closeDragStartX.current + gesture.dx));
      settleDrawer(gesture.vx > 0.28 || (drawerWidth + finalX) / drawerWidth > 0.82);
    },
    onPanResponderTerminate: (_, gesture) => {
      const finalX = Math.min(0, Math.max(-drawerWidth, closeDragStartX.current + gesture.dx));
      settleDrawer(gesture.vx > 0.28 || (drawerWidth + finalX) / drawerWidth > 0.82);
    },
  }), [closeDragStartX, drawerPosition, drawerWidth, settleDrawer]);
  const backdropOpacity = drawerPosition.interpolate({
    inputRange: [-drawerWidth, 0], outputRange: [0, 0.38], extrapolate: 'clamp',
  });

  return (
    <View style={styles.root} {...edgeSwipe.panHandlers}>
      <AppPage contentStyle={styles.content}>
        <View style={styles.header}>
          <Pressable accessibilityRole="button" accessibilityLabel={isVi ? 'Chọn hồ sơ' : 'Choose profile'} hitSlop={5} onPress={onChooseProfile} style={styles.profileButton}>
            <View style={styles.profileAvatar}><Ionicons name="person-outline" size={21} color={colors.primary} /></View>
            <View style={styles.heading}>
              <Text numberOfLines={1} style={styles.greeting}>{profileName?.trim() ? (isVi ? `Xin chào, ${profileName}` : `Hello, ${profileName}`) : (isVi ? 'Xin chào' : 'Hello')}</Text>
              <Text numberOfLines={1} style={styles.subtitle}>{isVi ? 'Sức khỏe hôm nay' : 'Your health today'}</Text>
            </View>
            <Ionicons name="chevron-down" size={15} color={colors.muted} />
          </Pressable>
          <Pressable accessibilityRole="button" accessibilityLabel={isVi ? 'Tìm chức năng' : 'Search tools'} hitSlop={6} onPress={openSearch} style={styles.headerButton}>
            <Ionicons name="search-outline" size={19} color={colors.primary} />
          </Pressable>
          <Pressable accessibilityRole="button" accessibilityLabel={t(locale, 'notifications')} hitSlop={6} onPress={() => openDestination('notifications')} style={styles.headerButton}>
            <Ionicons name="notifications-outline" size={18} color={colors.primary} />
          </Pressable>
        </View>

        <LinearGradient colors={(isDark ? [colors.card, colors.cardSoft, colors.backgroundRaised] : gradient) as [string, string, string]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={[styles.card, styles.heroCard]}>
          <View style={styles.heroTop}>
            <View style={styles.heroCopy}>
              <Text style={styles.heroKicker}>{isVi ? 'ĐỒNG HÀNH CÙNG SỨC KHỎE' : 'YOUR HEALTH COMPANION'}</Text>
              <Text style={styles.heroTitle}>{isVi ? 'Khám phá hành trình sức khỏe.' : 'Explore your health journey.'}</Text>
              <Text style={styles.heroCaption}>{isVi ? 'Trò chuyện cùng trợ lý sức khỏe của bạn.' : 'Talk with your health assistant.'}</Text>
            </View>
            <Image source={AI_ROBOT} resizeMode="contain" style={styles.robot} />
          </View>
          <Pressable accessibilityRole="button" onPress={() => openDestination('ai')} style={({ pressed }) => [styles.heroAction, pressed && styles.pressed]}>
            <Ionicons name="sparkles-outline" size={18} color={colors.primary} />
            <Text style={styles.heroActionText}>{isVi ? 'Trò chuyện với AI' : 'Chat with AI'}</Text>
            <Ionicons name="arrow-forward" size={17} color={colors.primary} />
          </Pressable>
        </LinearGradient>

        <View style={styles.card}>
          <View style={styles.summaryHeading}>
            <Text style={[styles.sectionTitle, styles.summaryTitle]}>{isVi ? 'Chỉ số gần đây' : 'Recent readings'}</Text>
            <Pressable accessibilityRole="button" accessibilityLabel={t(locale, 'monitor')} onPress={() => openDestination('monitor')} style={styles.viewAll}>
              <Text style={styles.viewAllText}>{t(locale, 'monitor')}</Text>
              <Ionicons name="chevron-forward" size={15} color={colors.primary} />
            </Pressable>
          </View>
          {readingsError ? <Text style={styles.readingsMessage}>{readingsError}</Text> : null}
          {readingsLoading && latestReadings.length === 0 ? <View style={styles.readingsLoading}><ActivityIndicator size="small" color={colors.primary} /><Text style={styles.readingsMessage}>{t(locale, 'loading')}</Text></View> : null}
          {!readingsLoading && !readingsError && latestReadings.length === 0 ? <Text style={styles.readingsMessage}>{isVi ? 'Chưa có chỉ số cho hồ sơ này.' : 'No readings are available for this profile yet.'}</Text> : null}
          {latestReadings.length ? <View style={styles.readingGrid}>
            {latestReadings.map(item => <View key={String(item.id)} style={styles.readingCard}>
              <View style={styles.readingCardTop}>
                <Text numberOfLines={2} style={styles.readingMetric}>{metricLabel(item.metric, locale)}</Text>
              </View>
              <Text style={styles.readingValue}>{String(item.value)} <Text style={styles.readingUnit}>{item.unit}</Text></Text>
              <Text numberOfLines={1} style={styles.readingMeta}>{formatDate(item.observed_at, locale)}</Text>
            </View>)}
          </View> : null}
        </View>

        <View style={styles.card}>
          <Text style={styles.sectionTitle}>{isVi ? 'Khám phá ASTRA' : 'Explore AETHERION'}</Text>
          <View style={styles.actionGrid}>
            {quick.map(item => <Pressable accessibilityRole="button" key={item.route} onPress={() => openDestination(item.route)} style={({ pressed }) => [styles.action, pressed && styles.pressed]}>
              <View style={styles.actionIcon}><Ionicons name={item.icon} size={21} color={colors.primary} /></View>
              <Text numberOfLines={2} style={styles.actionLabel}>{item.label}</Text>
            </Pressable>)}
          </View>
        </View>
      </AppPage>

      <Modal transparent visible={drawerOpen} animationType="none" onRequestClose={closeDrawer}>
        <View style={styles.modalRoot}>
          <Animated.View pointerEvents="none" style={[StyleSheet.absoluteFill, styles.backdrop, { opacity: backdropOpacity }]} />
          <Pressable accessibilityRole="button" accessibilityLabel={isVi ? 'Đóng menu' : 'Close menu'} style={StyleSheet.absoluteFill} onPress={closeDrawer} />
          <View pointerEvents="box-none" style={styles.modalCanvas}>
            <Animated.View {...closeSwipe.panHandlers} style={[styles.drawer, { width: drawerWidth, paddingTop: Math.max(insets.top, 18) + 12, paddingBottom: Math.max(insets.bottom, 12) + 14, transform: [{ translateX: drawerPosition }] }]}>
              <View style={styles.drawerTop}>
                <Image accessibilityLabel={copy(locale, 'teamLogo')} source={TEAM_LOGO} resizeMode="cover" style={styles.drawerMark} />
                <View style={styles.heading}><Text style={styles.drawerTitle}>{isVi ? 'Menu nhanh' : 'Quick menu'}</Text><Text style={styles.subtitle}>AETHERION</Text></View>
                <Pressable accessibilityRole="button" accessibilityLabel={isVi ? 'Đóng menu' : 'Close menu'} onPress={closeDrawer} style={styles.headerButton}><Ionicons name="close" size={21} color={colors.text} /></Pressable>
              </View>
              <View style={[styles.search, styles.drawerSearch]}>
                <Ionicons name="search-outline" size={19} color={colors.muted} />
                <TextInput ref={searchInputRef} accessibilityLabel={isVi ? 'Tìm chức năng' : 'Search tools'} placeholder={isVi ? 'Tìm chức năng' : 'Search tools'} placeholderTextColor={colors.faint} value={query} onChangeText={setQuery} style={styles.searchInput} />
                {query ? <Pressable accessibilityRole="button" accessibilityLabel={isVi ? 'Xóa tìm kiếm' : 'Clear search'} onPress={() => setQuery('')}><Ionicons name="close-circle" size={19} color={colors.muted} /></Pressable> : null}
              </View>
              <ScrollView style={styles.drawerRows} contentContainerStyle={styles.drawerRowsContent} showsVerticalScrollIndicator={false}>
                {matches.length ? matches.map((item, index) => <Pressable accessibilityRole="button" key={`${item.route}-${index}`} onPress={() => openDestination(item.route)} style={({ pressed }) => [styles.drawerRow, pressed && styles.pressed]}>
                  <View style={styles.drawerIcon}><Ionicons name={item.icon} size={20} color={colors.primary} /></View>
                  <Text style={styles.drawerLabel}>{item.label}</Text>
                  <Ionicons name="chevron-forward" size={17} color={colors.faint} />
                </Pressable>) : <Text style={styles.emptySearch}>{copy(locale, 'noMatch')}</Text>}
              </ScrollView>
              <View style={styles.drawerFooter}>
                <Pressable accessibilityRole="button" onPress={() => { closeDrawer(); onLogout(); }} style={({ pressed }) => [styles.logoutRow, pressed && styles.pressed]}>
                  <View style={styles.logoutIcon}><Ionicons name="log-out-outline" size={19} color={colors.red} /></View>
                  <Text style={styles.logoutLabel}>{t(locale, 'signOut')}</Text>
                  <Ionicons name="chevron-forward" size={17} color={colors.red} />
                </Pressable>
              </View>
            </Animated.View>
          </View>
        </View>
      </Modal>
      <Modal transparent visible={healthTipVisible} animationType={appearance.reduceMotion ? 'none' : 'fade'} onRequestClose={dismissHealthTip}>
        <View style={styles.tipModalRoot}>
          <Pressable accessibilityRole="button" accessibilityLabel={copy(locale, 'healthTipClose')} style={[StyleSheet.absoluteFill, styles.tipBackdrop]} onPress={dismissHealthTip} />
          <View style={[styles.tipCard, { width: tipWidth }]}>
            <View style={styles.tipHeader}>
              <View style={styles.tipIcon}><Ionicons name="pulse-outline" size={19} color={colors.primary} /></View>
              <Text style={styles.tipTitle}>{copy(locale, 'healthTipTitle')}</Text>
              <Pressable accessibilityRole="button" accessibilityLabel={copy(locale, 'healthTipClose')} hitSlop={8} onPress={dismissHealthTip} style={styles.tipClose}>
                <Ionicons name="close" size={20} color={colors.text} />
              </Pressable>
            </View>
            <Text style={styles.tipBody}>{copy(locale, 'healthTipBody')}</Text>
            <View style={styles.tipActions}>
              <Pressable accessibilityRole="button" onPress={openHealthGuide} style={[styles.tipAction, styles.tipSecondary]}>
                <Text style={styles.tipSecondaryText}>{copy(locale, 'healthTipOpen')}</Text>
              </Pressable>
              <Pressable accessibilityRole="button" onPress={dismissHealthTip} style={[styles.tipAction, styles.tipPrimary]}>
                <Text style={styles.tipPrimaryText}>{copy(locale, 'healthTipDismiss')}</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

function pickLatestReadings(readings: Observation[]): Observation[] {
  const ordered = [...readings].sort((left, right) => {
    const leftTime = Date.parse(left.observed_at);
    const rightTime = Date.parse(right.observed_at);
    return (Number.isFinite(rightTime) ? rightTime : 0) - (Number.isFinite(leftTime) ? leftTime : 0);
  });
  const seen = new Set<string>();
  return ordered.filter(item => {
    if (seen.has(item.metric)) return false;
    seen.add(item.metric);
    return true;
  }).slice(0, 4);
}

function formatDate(value: string, locale: Locale): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString(locale === 'vi' ? 'vi-VN' : 'en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function metricLabel(metric: string, locale: Locale): string {
  const labels: Record<string, { en: string; vi: string }> = {
    heart_rate: { en: 'Heart rate', vi: 'Nhịp tim' },
    blood_pressure_systolic: { en: 'Systolic', vi: 'Tâm thu' },
    blood_pressure_diastolic: { en: 'Diastolic', vi: 'Tâm trương' },
    body_temperature: { en: 'Temperature', vi: 'Nhiệt độ' },
    oxygen_saturation: { en: 'O₂ saturation', vi: 'SpO₂' },
    respiratory_rate: { en: 'Respiratory rate', vi: 'Nhịp thở' },
    blood_glucose: { en: 'Glucose', vi: 'Đường huyết' },
    sleep_duration: { en: 'Sleep', vi: 'Giấc ngủ' },
    mood_self_report: { en: 'Mood', vi: 'Tâm trạng' },
    fatigue_self_report: { en: 'Fatigue', vi: 'Mệt mỏi' },
    steps: { en: 'Steps', vi: 'Bước chân' },
  };
  return labels[metric]?.[locale] || metric.replace(/_/g, ' ');
}

const buildStyles = (colors: ThemeColors) => StyleSheet.create({
  root: { flex: 1 },
  content: { gap: 14 },
  header: { flexDirection: 'row', alignItems: 'center', gap: 8, minHeight: 48, marginBottom: 2 },
  profileButton: { flex: 1, minWidth: 0, flexDirection: 'row', alignItems: 'center', gap: 8 },
  profileAvatar: { width: 42, height: 42, borderRadius: 21, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.cardSoft, borderWidth: 1, borderColor: colors.border },
  heading: { flex: 1, minWidth: 0 },
  subtitle: { color: colors.muted, fontSize: 10, marginTop: 2, fontWeight: '600' },
  headerButton: { width: 36, height: 36, borderRadius: 18, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.card, borderColor: colors.border, borderWidth: 1 },
  locale: { color: colors.primary, fontSize: 11, fontWeight: '900' },
  greeting: { color: colors.text, fontSize: 15, fontWeight: '900', letterSpacing: -0.2 },
  card: { width: '100%', backgroundColor: colors.card, borderRadius: 24, padding: 16, borderWidth: 1, borderColor: colors.border, shadowColor: '#27124D', shadowOpacity: 0.07, shadowRadius: 16, shadowOffset: { width: 0, height: 7 }, elevation: 2 },
  heroCard: { minHeight: 206, borderRadius: 30, padding: 18, overflow: 'hidden', shadowColor: '#4C32D7', shadowOpacity: 0.2, shadowRadius: 18, shadowOffset: { width: 0, height: 8 }, elevation: 5 },
  sectionTitle: { fontSize: 13, fontWeight: '800', color: colors.text, marginBottom: 10, letterSpacing: 0.6, textTransform: 'uppercase' },
  summaryHeading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 },
  summaryTitle: { marginBottom: 0 },
  viewAll: { minHeight: 32, flexDirection: 'row', alignItems: 'center', gap: 3, paddingLeft: 8 },
  viewAllText: { color: colors.primary, fontSize: 11, fontWeight: '800' },
  readingGrid: { flexDirection: 'row', flexWrap: 'nowrap', gap: 6 },
  readingCard: { flex: 1, minWidth: 0, minHeight: 104, borderRadius: 16, padding: 8, backgroundColor: colors.cardSoft, borderWidth: 1, borderColor: colors.border },
  readingCardTop: { minHeight: 28, flexDirection: 'row', alignItems: 'flex-start' },
  readingMetric: { flex: 1, minWidth: 0, color: colors.text, fontSize: 11, lineHeight: 15, fontWeight: '800', textTransform: 'capitalize' },
  readingValue: { color: colors.primary, fontSize: 16, lineHeight: 20, fontWeight: '900', marginTop: 5 },
  readingUnit: { color: colors.muted, fontSize: 9, fontWeight: '700' },
  readingMeta: { color: colors.muted, fontSize: 8, lineHeight: 11, marginTop: 5 },
  readingsMessage: { color: colors.muted, fontSize: 12, lineHeight: 18, paddingVertical: 7 },
  readingsLoading: { flexDirection: 'row', alignItems: 'center', gap: 9 },
  search: { minHeight: 46, borderRadius: 16, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.cardSoft, flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 12 },
  drawerSearch: { marginHorizontal: 16, marginBottom: 10 },
  searchInput: { color: colors.text, flex: 1, minWidth: 0, fontSize: 14, paddingVertical: 10 },
  searchResults: { marginTop: 8 },
  searchResult: { minHeight: 46, flexDirection: 'row', alignItems: 'center', gap: 10, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.border },
  searchResultText: { color: colors.text, flex: 1, fontSize: 13, fontWeight: '700' },
  emptySearch: { color: colors.muted, fontSize: 13, paddingVertical: 14 },
  heroTop: { flexDirection: 'row', alignItems: 'center', minHeight: 108 },
  heroCopy: { flex: 1, minWidth: 0 },
  heroKicker: { color: 'rgba(255,255,255,0.84)', fontSize: 10, fontWeight: '900', letterSpacing: 1.2, marginBottom: 8 },
  heroTitle: { color: '#FFFFFF', fontSize: 20, lineHeight: 24, fontWeight: '900', marginBottom: 6 },
  heroCaption: { color: 'rgba(255,255,255,0.82)', fontSize: 13 },
  robot: { width: 104, height: 104, marginLeft: 8 },
  heroAction: { alignSelf: 'flex-start', minHeight: 44, marginTop: 6, backgroundColor: '#FFFFFF', borderRadius: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingHorizontal: 15 },
  heroActionText: { color: colors.primary, fontWeight: '800', fontSize: 13 },
  actionGrid: { flexDirection: 'row', flexWrap: 'nowrap', justifyContent: 'space-between', columnGap: 2 },
  action: { flex: 1, minWidth: 0, minHeight: 78, borderRadius: 16, backgroundColor: 'transparent', paddingVertical: 4, paddingHorizontal: 1, flexDirection: 'column', gap: 6, alignItems: 'center', justifyContent: 'center' },
  actionIcon: { width: 44, height: 44, borderRadius: 16, backgroundColor: colors.cardSoft, alignItems: 'center', justifyContent: 'center' },
  actionLabel: { color: colors.text, fontSize: 10, fontWeight: '700', flexShrink: 1, textAlign: 'center', lineHeight: 13 },
  pressed: { opacity: 0.72 },
  tipModalRoot: { flex: 1, alignItems: 'center', justifyContent: 'flex-end', paddingBottom: 20 },
  tipBackdrop: { backgroundColor: 'rgba(3, 8, 22, 0.48)' },
  tipCard: { padding: 16, borderRadius: 18, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.card, gap: 11 },
  tipHeader: { flexDirection: 'row', alignItems: 'center', gap: 9 },
  tipIcon: { width: 34, height: 34, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.cardSoft },
  tipTitle: { flex: 1, color: colors.text, fontSize: 15, fontWeight: '800' },
  tipClose: { width: 32, height: 32, borderRadius: 16, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.cardSoft },
  tipBody: { color: colors.muted, fontSize: 13, lineHeight: 19 },
  tipActions: { flexDirection: 'row', gap: 8, marginTop: 2 },
  tipAction: { flex: 1, minHeight: 42, borderRadius: 12, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 9 },
  tipSecondary: { backgroundColor: colors.cardSoft, borderWidth: 1, borderColor: colors.border },
  tipPrimary: { backgroundColor: colors.primary },
  tipSecondaryText: { color: colors.text, fontSize: 12, fontWeight: '700', textAlign: 'center' },
  tipPrimaryText: { color: colors.onAccent, fontSize: 12, fontWeight: '800', textAlign: 'center' },
  modalRoot: { flex: 1, alignItems: 'center' },
  backdrop: { backgroundColor: '#0C081E' },
  modalCanvas: { width: '100%', maxWidth: 470, flex: 1, alignSelf: 'center', alignItems: 'flex-start' },
  drawer: { height: '100%', backgroundColor: colors.card, borderRightWidth: 1, borderRightColor: colors.border, borderTopRightRadius: 28, borderBottomRightRadius: 28, paddingHorizontal: 16 },
  drawerTop: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 22 },
  drawerMark: { width: 45, height: 45, borderRadius: 16, overflow: 'hidden', borderWidth: 1, borderColor: colors.border },
  drawerTitle: { color: colors.text, fontWeight: '900', fontSize: 19 },
  drawerRows: { flex: 1 },
  drawerRowsContent: { gap: 8, paddingBottom: 12 },
  drawerRow: { minHeight: 55, borderRadius: 17, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.card, paddingHorizontal: 10, flexDirection: 'row', alignItems: 'center', gap: 10 },
  drawerIcon: { width: 37, height: 37, borderRadius: 13, backgroundColor: colors.cardSoft, alignItems: 'center', justifyContent: 'center' },
  drawerLabel: { flex: 1, color: colors.text, fontSize: 14, fontWeight: '700' },
  drawerFooter: { borderTopWidth: 1, borderTopColor: colors.border, paddingTop: 12 },
  logoutRow: { minHeight: 54, borderRadius: 17, borderWidth: 1, borderColor: `${colors.red}44`, backgroundColor: `${colors.red}0D`, paddingHorizontal: 10, flexDirection: 'row', alignItems: 'center', gap: 10 },
  logoutIcon: { width: 37, height: 37, borderRadius: 13, backgroundColor: `${colors.red}14`, alignItems: 'center', justifyContent: 'center' },
  logoutLabel: { flex: 1, color: colors.red, fontSize: 14, fontWeight: '800' },
});

