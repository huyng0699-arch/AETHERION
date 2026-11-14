import React, { ReactNode } from 'react';
import { ActivityIndicator, Image, Pressable, ScrollView, StyleProp, StyleSheet, Text, TextInput, TextInputProps, TextStyle, View, ViewStyle } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { ThemeColors, useThemedStyles, radius } from '../theme';

const AI_ORB = require('../../assets/aetherion-ai-orb.png');

export function AppPage({ children, scroll = true, contentStyle }: { children: ReactNode; scroll?: boolean; contentStyle?: StyleProp<ViewStyle> }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  const content = scroll ? (
    <ScrollView showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled" contentContainerStyle={[styles.pageContent, styles.mobileContent, contentStyle]}>
      {children}
    </ScrollView>
  ) : <View style={[styles.pageContent, styles.mobileContent, contentStyle]}>{children}</View>;
  return <View style={styles.root}><SafeAreaView style={styles.safe} edges={['top', 'left', 'right']}>{content}</SafeAreaView></View>;
}

export function Eyebrow({ children }: { children: ReactNode }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  return <Text style={styles.eyebrow}>{children}</Text>;
}

export function Title({ children, size = 28 }: { children: ReactNode; size?: number }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  return <Text style={[styles.title, { fontSize: size }]}>{children}</Text>;
}

export function Body({ children, style }: { children: ReactNode; style?: StyleProp<TextStyle> }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  return <Text style={[styles.body, style]}>{children}</Text>;
}

export function Panel({ children, style }: { children: ReactNode; style?: StyleProp<ViewStyle> }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  return <View style={[styles.panel, style]}>{children}</View>;
}

export function ActionButton({ title, onPress, disabled, loading, secondary }: {
  title: string; onPress: () => void; disabled?: boolean; loading?: boolean; secondary?: boolean;
}) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  return (
    <Pressable accessibilityRole="button" onPress={onPress} disabled={disabled || loading}
      style={({ pressed }) => [styles.action, secondary && styles.actionSecondary, (disabled || loading) && styles.actionDisabled, pressed && !disabled && styles.actionPressed]}>
      {loading ? <ActivityIndicator color={secondary ? colors.cyan : colors.onAccent} /> : <Text style={[styles.actionText, secondary && styles.actionTextSecondary]}>{title}</Text>}
    </Pressable>
  );
}

export function Field({ label, ...props }: TextInputProps & { label: string }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  return (
    <View style={styles.fieldWrap}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput accessibilityLabel={label} {...props} placeholderTextColor={colors.faint} selectionColor={colors.cyan} style={[styles.field, props.style]} />
    </View>
  );
}

export function StatusPill({ label, tone = 'neutral' }: { label: string; tone?: 'good' | 'warn' | 'bad' | 'neutral' }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  const tint = tone === 'good' ? colors.green : tone === 'warn' ? colors.amber : tone === 'bad' ? colors.red : colors.muted;
  return <View style={[styles.pill, { borderColor: `${tint}44`, backgroundColor: `${tint}12` }]}><View style={[styles.dot, { backgroundColor: tint }]} /><Text style={[styles.pillText, { color: tint }]}>{label}</Text></View>;
}

export function AppHeader({ title, onBack, trailing, backLabel = 'Back' }: { title: string; onBack?: () => void; trailing?: ReactNode; backLabel?: string }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  return (
    <View style={styles.header}>
      {onBack
        ? <Pressable onPress={onBack} accessibilityRole="button" accessibilityLabel={backLabel} style={styles.back}><Ionicons name="chevron-back" size={21} color={colors.text} /></Pressable>
        : <Image source={AI_ORB} resizeMode="contain" style={styles.brandMark} />}
      <Text numberOfLines={1} style={styles.headerTitle}>{title}</Text>
      {trailing || <View style={styles.headerSpacer} />}
    </View>
  );
}

type NavKey = 'portal' | 'health' | 'monitor' | 'ai' | 'more';

export function BottomNav({ active, onSelect, labels }: { active: string; onSelect: (id: string) => void; labels: Record<string, string> }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  const insets = useSafeAreaInsets();
  const items: Array<{ id: NavKey; icon: keyof typeof Ionicons.glyphMap }> = [
    { id: 'portal', icon: 'planet-outline' },
    { id: 'health', icon: 'body-outline' },
    { id: 'monitor', icon: 'pulse-outline' },
    { id: 'more', icon: 'grid-outline' },
  ];
  return (
    <View style={[styles.navSafe, { paddingBottom: Math.max(insets.bottom, 10) }]}>
      <View style={styles.nav}>
        <NavItem id={items[0].id} icon={items[0].icon} active={active === items[0].id} label={labels[items[0].id]} onPress={() => onSelect(items[0].id)} />
        <NavItem id={items[1].id} icon={items[1].icon} active={active === items[1].id} label={labels[items[1].id]} onPress={() => onSelect(items[1].id)} />
        <Pressable accessibilityRole="tab" accessibilityLabel={labels.ai} accessibilityState={{ selected: active === 'ai' }} onPress={() => onSelect('ai')} style={styles.aiNavButton}>
          <Image source={AI_ORB} resizeMode="contain" style={styles.aiNavOrb} />
        </Pressable>
        <NavItem id={items[2].id} icon={items[2].icon} active={active === items[2].id} label={labels[items[2].id]} onPress={() => onSelect(items[2].id)} />
        <NavItem id={items[3].id} icon={items[3].icon} active={active === items[3].id} label={labels[items[3].id]} onPress={() => onSelect(items[3].id)} />
      </View>
    </View>
  );
}

function NavItem({ id, icon, active, label, onPress }: { id: NavKey; icon: keyof typeof Ionicons.glyphMap; active: boolean; label: string; onPress: () => void }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  return (
    <Pressable key={id} onPress={onPress} accessibilityRole="tab" accessibilityState={{ selected: active }} style={styles.navItem}>
      <Ionicons name={icon} size={20} color={active ? colors.cyan : colors.muted} />
      <Text numberOfLines={1} style={[styles.navLabel, active && styles.navSelected]}>{label}</Text>
    </Pressable>
  );
}

const buildStyles = (colors: ThemeColors) => StyleSheet.create({
  root: { flex: 1, backgroundColor: 'transparent' },
  safe: { flex: 1 },
  pageContent: { flexGrow: 1, paddingHorizontal: 16, paddingTop: 8, paddingBottom: 120, gap: 12 },
  mobileContent: { width: '100%', maxWidth: 470, alignSelf: 'center' },
  eyebrow: { color: colors.cyan, fontWeight: '800', letterSpacing: 1.2, fontSize: 10, marginBottom: 7 },
  title: { color: colors.text, fontWeight: '800', letterSpacing: -0.4, lineHeight: 34 },
  body: { color: colors.muted, fontSize: 14, lineHeight: 21 },
  panel: { backgroundColor: colors.card, borderWidth: 1, borderColor: colors.border, borderRadius: 14, padding: 14, shadowColor: '#392073', shadowOpacity: 0.05, shadowRadius: 12, shadowOffset: { width: 0, height: 7 }, elevation: 2 },
  action: { minHeight: 50, borderRadius: 12, backgroundColor: colors.cyan, paddingHorizontal: 16, alignItems: 'center', justifyContent: 'center' },
  actionSecondary: { backgroundColor: colors.card, borderWidth: 1, borderColor: colors.border },
  actionDisabled: { opacity: 0.56 },
  actionPressed: { transform: [{ scale: 0.985 }], opacity: 0.86 },
  actionText: { color: colors.onAccent, fontWeight: '800', fontSize: 15 },
  actionTextSecondary: { color: colors.text },
  fieldWrap: { gap: 7 },
  fieldLabel: { color: colors.muted, fontSize: 12, fontWeight: '700', letterSpacing: 0.2 },
  field: { minHeight: 50, borderRadius: radius.control, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.card, paddingHorizontal: 14, color: colors.text, fontSize: 15 },
  pill: { alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: 7, borderWidth: 1, borderRadius: radius.pill, paddingHorizontal: 11, paddingVertical: 7 },
  dot: { width: 6, height: 6, borderRadius: 3 },
  pillText: { fontSize: 11, fontWeight: '800' },
  header: { minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 4 },
  brandMark: { width: 38, height: 38 },
  headerSpacer: { width: 38 },
  headerTitle: { flex: 1, color: colors.text, fontSize: 16, fontWeight: '800' },
  back: { width: 38, height: 38, borderRadius: 14, backgroundColor: colors.card, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: colors.border },
  navSafe: { position: 'absolute', left: 0, right: 0, bottom: 0, paddingHorizontal: 16, paddingTop: 10, alignItems: 'center', backgroundColor: 'transparent' },
  nav: { width: '100%', maxWidth: 470, height: 80, borderRadius: 28, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.card, paddingHorizontal: 4, flexDirection: 'row', alignItems: 'center', shadowColor: '#311C6F', shadowOpacity: 0.12, shadowRadius: 18, shadowOffset: { width: 0, height: 6 }, elevation: 9 },
  navItem: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 3, minHeight: 54 },
  navLabel: { color: colors.muted, fontSize: 11, fontWeight: '700' },
  navSelected: { color: colors.cyan },
  aiNavButton: { width: 62, height: 62, borderRadius: 31, alignItems: 'center', justifyContent: 'center', marginTop: -24, backgroundColor: colors.card, borderWidth: 5, borderColor: '#E9E1FF', shadowColor: '#5528E9', shadowOpacity: 0.35, shadowRadius: 15, shadowOffset: { width: 0, height: 5 }, elevation: 10 },
  aiNavOrb: { width: 51, height: 51 },
});

