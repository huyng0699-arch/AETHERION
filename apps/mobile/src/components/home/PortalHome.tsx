import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Animated, Image, Modal, PanResponder, Platform, Pressable, StyleSheet, Text, TextInput, useWindowDimensions, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AppPage, StatusPill } from '../ui';
import { Locale } from '../../types';
import { MessageKey, t } from '../../i18n';
import { copy } from '../../uiCopy';
import { ThemeColors, useThemedStyles } from '../../theme';

export type MobileScreen = 'health' | 'monitor' | 'ai' | 'science' | 'mission' | 'login' | 'settings' | 'demoIntro' | 'demoData' | 'more' | 'connection' | 'settingConnection' | 'settingAccount' | 'settingLanguage' | 'notifications' | 'help' | 'privacy' | 'care' | 'appearance';
type Icon = keyof typeof Ionicons.glyphMap;
type Destination = { route: MobileScreen; icon: Icon; label: string };

const AI_ROBOT = require('../../../assets/aetherion-ai-robot.png');

export function PortalHome({ locale, setLocale, isAuthenticated, serverStatus, onOpen }: {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  isAuthenticated: boolean;
  serverStatus: 'online' | 'offline' | 'unknown';
  onOpen: (screen: MobileScreen) => void;
}) {
  const { colors, styles, appearance } = useThemedStyles(buildStyles);
  const { width: viewportWidth } = useWindowDimensions();
  const frameWidth = Math.min(viewportWidth, 470);
  const frameLeft = Math.max(0, (viewportWidth - frameWidth) / 2);
  const drawerWidth = Math.min(frameWidth * 0.86, 360);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [query, setQuery] = useState('');
  const drawerPosition = useRef(new Animated.Value(-drawerWidth)).current;
  const isVi = locale === 'vi';
  const statusKey: MessageKey = serverStatus === 'online' ? 'serverOnline' : serverStatus === 'offline' ? 'serverOffline' : 'serverUnknown';
  const statusTone = serverStatus === 'online' ? 'good' : serverStatus === 'offline' ? 'warn' : 'neutral';
  const quick: Destination[] = [
    { route: 'health', icon: 'medkit-outline', label: t(locale, 'personal') },
    { route: 'monitor', icon: 'radio-outline', label: t(locale, 'monitor') },
    { route: 'ai', icon: 'sparkles-outline', label: t(locale, 'ai') },
    { route: 'science', icon: 'planet-outline', label: t(locale, 'science') },
    { route: 'care', icon: 'heart-outline', label: t(locale, 'careTitle') },
    { route: 'mission', icon: 'people-outline', label: t(locale, 'missionTitle') },
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
    { route: isAuthenticated ? 'settingAccount' : 'login', icon: 'person-circle-outline', label: t(locale, isAuthenticated ? 'accountTitle' : 'signIn') },
    { route: 'mission', icon: 'people-outline', label: t(locale, 'missionTitle') },
    { route: 'connection', icon: 'planet-outline', label: t(locale, 'connectionTitle') },
    { route: 'settings', icon: 'settings-outline', label: t(locale, 'settings') },
    { route: 'appearance', icon: 'color-palette-outline', label: copy(locale, 'appearance') },
    { route: 'help', icon: 'help-circle-outline', label: t(locale, 'helpTitle') },
  ];
  const matches = [...quick, ...tools].filter(item => item.label.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()));

  useEffect(() => {
    if (!drawerOpen) {
      drawerPosition.setValue(-drawerWidth);
      return;
    }
    if (appearance.reduceMotion) {
      drawerPosition.setValue(0);
      return;
    }
    const animation = Animated.spring(drawerPosition, {
      toValue: 0, stiffness: 220, damping: 22, mass: 0.9,
      overshootClamping: true, useNativeDriver: Platform.OS !== 'web',
    });
    animation.start();
    return () => animation.stop();
  }, [drawerOpen, drawerWidth, drawerPosition, appearance.reduceMotion]);

  const closeDrawer = useCallback(() => {
    if (appearance.reduceMotion) {
      setDrawerOpen(false);
      return;
    }
    Animated.timing(drawerPosition, {
      toValue: -drawerWidth, duration: 160, useNativeDriver: Platform.OS !== 'web',
    }).start(({ finished }) => { if (finished) setDrawerOpen(false); });
  }, [appearance.reduceMotion, drawerPosition, drawerWidth]);
  const openDestination = (route: MobileScreen) => {
    setDrawerOpen(false);
    setQuery('');
    onOpen(route);
  };
  const edgeSwipe = useMemo(() => PanResponder.create({
    onMoveShouldSetPanResponder: (_, gesture) => !drawerOpen
      && gesture.x0 <= frameLeft + Math.min(45, frameWidth / 5)
      && gesture.dx > 14 && gesture.dx > Math.abs(gesture.dy) * 1.2,
    onPanResponderRelease: (_, gesture) => {
      if (gesture.dx > 55 || gesture.vx > 0.35) setDrawerOpen(true);
    },
  }), [drawerOpen, frameLeft, frameWidth]);
  const closeSwipe = useMemo(() => PanResponder.create({
    onMoveShouldSetPanResponder: (_, gesture) => gesture.dx < -14 && -gesture.dx > Math.abs(gesture.dy) * 1.2,
    onPanResponderRelease: (_, gesture) => { if (gesture.dx < -45 || gesture.vx < -0.35) closeDrawer(); },
  }), [closeDrawer]);
  const backdropOpacity = drawerPosition.interpolate({
    inputRange: [-drawerWidth, 0], outputRange: [0, 0.38], extrapolate: 'clamp',
  });

  return (
    <View style={styles.root} {...edgeSwipe.panHandlers}>
      <AppPage contentStyle={styles.content}>
        <View style={styles.header}>
          <View style={styles.logo}><Ionicons name="planet-outline" size={21} color={colors.onAccent} /></View>
          <View style={styles.heading}>
            <Text numberOfLines={1} style={styles.brand}>{t(locale, 'brand')}</Text>
            <Text numberOfLines={1} style={styles.subtitle}>{isVi ? 'Sức khỏe phi hành đoàn' : 'Mission health'}</Text>
          </View>
          <Pressable accessibilityRole="button" accessibilityLabel={t(locale, 'language')} hitSlop={6} onPress={() => setLocale(isVi ? 'en' : 'vi')} style={styles.headerButton}>
            <Text style={styles.locale}>{isVi ? 'EN' : 'VI'}</Text>
          </Pressable>
          <Pressable accessibilityRole="button" accessibilityLabel={t(locale, 'notifications')} hitSlop={6} onPress={() => openDestination('notifications')} style={styles.headerButton}>
            <Ionicons name="notifications-outline" size={18} color={colors.cyan} />
          </Pressable>
          <Pressable accessibilityRole="button" accessibilityLabel={isVi ? 'Mở menu' : 'Open menu'} hitSlop={6} onPress={() => setDrawerOpen(true)} style={styles.headerButton}>
            <Ionicons name="menu-outline" size={21} color={colors.text} />
          </Pressable>
        </View>

        <View style={styles.greetingRow}>
          <Text numberOfLines={1} style={styles.greeting}>{isVi ? 'Trung tâm nhiệm vụ' : 'Mission control'}</Text>
          <Pressable accessibilityRole="button" accessibilityLabel={t(locale, 'connectionTitle')} onPress={() => openDestination('connection')}>
            <StatusPill label={t(locale, statusKey)} tone={statusTone} />
          </Pressable>
        </View>

        <View style={styles.card}>
          <Text style={styles.sectionTitle}>{isVi ? 'Tìm kiếm' : 'Search'}</Text>
          <View style={styles.search}>
            <Ionicons name="search-outline" size={19} color={colors.muted} />
            <TextInput accessibilityLabel={isVi ? 'Tìm chức năng' : 'Search tools'} placeholder={isVi ? 'Tìm chức năng' : 'Search tools'} placeholderTextColor={colors.faint} value={query} onChangeText={setQuery} style={styles.searchInput} />
            {query ? <Pressable accessibilityRole="button" accessibilityLabel={isVi ? 'Xóa tìm kiếm' : 'Clear search'} onPress={() => setQuery('')}><Ionicons name="close-circle" size={19} color={colors.muted} /></Pressable> : null}
          </View>
          {query.trim() ? <View style={styles.searchResults}>
            {matches.length ? matches.map(item => <Pressable accessibilityRole="button" key={item.route} onPress={() => openDestination(item.route)} style={styles.searchResult}>
              <Ionicons name={item.icon} size={19} color={colors.cyan} />
              <Text style={styles.searchResultText}>{item.label}</Text>
              <Ionicons name="chevron-forward" size={17} color={colors.faint} />
            </Pressable>) : <Text style={styles.emptySearch}>{isVi ? 'Không tìm thấy chức năng' : 'No matching tools'}</Text>}
          </View> : null}
        </View>

        <View style={styles.card}>
          <View style={styles.heroTop}>
            <View style={styles.heroCopy}>
              <Text style={styles.sectionTitle}>{t(locale, 'demoKicker')}</Text>
              <Text style={styles.heroTitle}>{t(locale, 'demoBannerTitle')}</Text>
              <Text style={styles.heroCaption}>{t(locale, 'demoHistorical')}</Text>
            </View>
            <Image source={AI_ROBOT} resizeMode="contain" style={styles.robot} />
          </View>
          <Pressable accessibilityRole="button" onPress={() => openDestination('demoIntro')} style={({ pressed }) => [styles.heroAction, pressed && styles.pressed]}>
            <Ionicons name="planet-outline" size={18} color={colors.onAccent} />
            <Text style={styles.heroActionText}>{t(locale, 'demoForHackathon')}</Text>
            <Ionicons name="arrow-forward" size={17} color={colors.onAccent} />
          </Pressable>
        </View>

        <View style={styles.card}>
          <Text style={styles.sectionTitle}>{isVi ? 'Thao tác nhanh' : 'Quick actions'}</Text>
          <View style={styles.actionGrid}>
            {quick.map(item => <Pressable accessibilityRole="button" key={item.route} onPress={() => openDestination(item.route)} style={({ pressed }) => [styles.action, pressed && styles.pressed]}>
              <Ionicons name={item.icon} size={19} color={colors.cyan} />
              <Text numberOfLines={2} style={styles.actionLabel}>{item.label}</Text>
            </Pressable>)}
          </View>
        </View>

        <View style={styles.card}>
          <Text style={styles.sectionTitle}>{isVi ? 'Công cụ' : 'Mission tools'}</Text>
          <View style={styles.actionGrid}>
            {tools.map(item => <Pressable accessibilityRole="button" key={item.route} onPress={() => openDestination(item.route)} style={({ pressed }) => [styles.action, pressed && styles.pressed]}>
              <Ionicons name={item.icon} size={19} color={colors.cyan} />
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
            <Animated.View {...closeSwipe.panHandlers} style={[styles.drawer, { width: drawerWidth, transform: [{ translateX: drawerPosition }] }]}>
              <View style={styles.drawerTop}>
                <View style={styles.drawerMark}><Ionicons name="planet-outline" size={24} color={colors.cyan} /></View>
                <View style={styles.heading}><Text style={styles.drawerTitle}>{isVi ? 'Menu nhanh' : 'Quick menu'}</Text><Text style={styles.subtitle}>AETHERION</Text></View>
                <Pressable accessibilityRole="button" accessibilityLabel={isVi ? 'Đóng menu' : 'Close menu'} onPress={closeDrawer} style={styles.headerButton}><Ionicons name="close" size={21} color={colors.text} /></Pressable>
              </View>
              <View style={styles.drawerRows}>
                {drawerItems.map(item => <Pressable accessibilityRole="button" key={item.route} onPress={() => openDestination(item.route)} style={({ pressed }) => [styles.drawerRow, pressed && styles.pressed]}>
                  <View style={styles.drawerIcon}><Ionicons name={item.icon} size={20} color={colors.cyan} /></View>
                  <Text style={styles.drawerLabel}>{item.label}</Text>
                  <Ionicons name="chevron-forward" size={17} color={colors.faint} />
                </Pressable>)}
              </View>
            </Animated.View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const buildStyles = (colors: ThemeColors) => StyleSheet.create({
  root: { flex: 1 },
  content: { gap: 12 },
  header: { flexDirection: 'row', alignItems: 'center', gap: 8, minHeight: 36 },
  logo: { width: 36, height: 36, borderRadius: 10, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.cyan },
  heading: { flex: 1, minWidth: 0 },
  brand: { color: colors.text, fontWeight: '700', fontSize: 15 },
  subtitle: { color: colors.muted, fontSize: 12, marginTop: 2 },
  headerButton: { width: 32, height: 32, borderRadius: 16, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.card, borderColor: colors.border, borderWidth: 1 },
  locale: { color: colors.cyan, fontSize: 11, fontWeight: '900' },
  greetingRow: { gap: 6, alignItems: 'flex-start' },
  greeting: { color: colors.text, fontSize: 24, fontWeight: '700' },
  card: { width: '100%', backgroundColor: colors.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: colors.border },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: colors.text, marginBottom: 10 },
  search: { minHeight: 46, borderRadius: 12, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.cardSoft, flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 12 },
  searchInput: { color: colors.text, flex: 1, minWidth: 0, fontSize: 14, paddingVertical: 10 },
  searchResults: { marginTop: 8 },
  searchResult: { minHeight: 46, flexDirection: 'row', alignItems: 'center', gap: 10, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.border },
  searchResultText: { color: colors.text, flex: 1, fontSize: 13, fontWeight: '700' },
  emptySearch: { color: colors.muted, fontSize: 13, paddingVertical: 14 },
  heroTop: { flexDirection: 'row', alignItems: 'center', minHeight: 76 },
  heroCopy: { flex: 1, minWidth: 0 },
  heroTitle: { color: colors.text, fontSize: 18, fontWeight: '700', marginBottom: 6 },
  heroCaption: { color: colors.muted, fontSize: 13 },
  robot: { width: 88, height: 88, marginLeft: 8 },
  heroAction: { minHeight: 44, marginTop: 6, backgroundColor: colors.cyan, borderRadius: 12, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingHorizontal: 12 },
  heroActionText: { color: colors.onAccent, fontWeight: '700', fontSize: 14 },
  actionGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  action: { flexBasis: '48%', flexGrow: 1, minHeight: 42, borderRadius: 10, backgroundColor: colors.cardSoft, borderWidth: 1, borderColor: colors.border, paddingVertical: 9, paddingHorizontal: 8, flexDirection: 'row', gap: 7, alignItems: 'center', justifyContent: 'center' },
  actionLabel: { color: colors.text, fontSize: 13, fontWeight: '600', flexShrink: 1, textAlign: 'center' },
  pressed: { opacity: 0.72 },
  modalRoot: { flex: 1, alignItems: 'center' },
  backdrop: { backgroundColor: '#0C081E' },
  modalCanvas: { width: '100%', maxWidth: 470, flex: 1, alignSelf: 'center', alignItems: 'flex-start' },
  drawer: { height: '100%', backgroundColor: colors.card, borderRightWidth: 1, borderRightColor: colors.border, paddingTop: 28, paddingHorizontal: 16 },
  drawerTop: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 22 },
  drawerMark: { width: 45, height: 45, borderRadius: 16, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.cardSoft },
  drawerTitle: { color: colors.text, fontWeight: '900', fontSize: 19 },
  drawerRows: { gap: 8 },
  drawerRow: { minHeight: 55, borderRadius: 17, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.card, paddingHorizontal: 10, flexDirection: 'row', alignItems: 'center', gap: 10 },
  drawerIcon: { width: 37, height: 37, borderRadius: 13, backgroundColor: colors.cardSoft, alignItems: 'center', justifyContent: 'center' },
  drawerLabel: { flex: 1, color: colors.text, fontSize: 14, fontWeight: '700' },
});
