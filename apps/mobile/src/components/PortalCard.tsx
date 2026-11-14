import React from 'react';
import { Image, Pressable, StyleSheet, Text, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { ThemeColors, useThemedStyles } from '../theme';

export type PortalDestination = 'health' | 'monitor' | 'ai' | 'science' | 'care';

const iconStyles: Record<PortalDestination, { icon: keyof typeof Ionicons.glyphMap; color: string; bg: string }> = {
  health: { icon: 'person-outline', color: '#0E9A68', bg: '#E8F8F0' },
  monitor: { icon: 'pulse-outline', color: '#2778E7', bg: '#EAF2FF' },
  ai: { icon: 'sparkles-outline', color: '#6337F1', bg: '#F0EAFF' },
  science: { icon: 'planet-outline', color: '#E48620', bg: '#FFF3E5' },
  care: { icon: 'heart-outline', color: '#DE496A', bg: '#FFF0F3' },
};
const AI_ORB = require('../../assets/aetherion-ai-orb.png');

export function PortalCard({ destination, title, onPress, wide = false }: {
  destination: PortalDestination; title: string; onPress: () => void; wide?: boolean;
}) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  const tone = iconStyles[destination];
  return (
    <Pressable accessibilityRole="button" accessibilityLabel={title} onPress={onPress} style={({ pressed }) => [styles.wrap, wide && styles.wide, pressed && styles.pressed]}>
      <LinearGradient colors={[colors.card, colors.card]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={[styles.card, wide && styles.cardWide]}>
        <View style={[styles.icon, { backgroundColor: tone.bg }]}>
          {destination === 'ai'
            ? <Image source={AI_ORB} resizeMode="contain" style={styles.orb} />
            : <Ionicons name={tone.icon} size={25} color={tone.color} />}
        </View>
        <Text numberOfLines={1} style={styles.title}>{title}</Text>
        {wide ? <Ionicons name="chevron-forward" size={18} color={colors.faint} /> : null}
      </LinearGradient>
    </Pressable>
  );
}

const buildStyles = (colors: ThemeColors) => StyleSheet.create({
  wrap: { width: '48.5%', minHeight: 126 },
  wide: { width: '100%', minHeight: 78 },
  pressed: { opacity: 0.82, transform: [{ scale: 0.985 }] },
  card: { flex: 1, alignItems: 'flex-start', justifyContent: 'space-between', borderWidth: 1, borderColor: colors.border, borderRadius: 24, padding: 14, shadowColor: '#37206E', shadowOpacity: 0.06, shadowRadius: 14, shadowOffset: { width: 0, height: 7 }, elevation: 2 },
  cardWide: { flexDirection: 'row', alignItems: 'center', justifyContent: 'flex-start', gap: 12 },
  icon: { width: 48, height: 48, borderRadius: 17, alignItems: 'center', justifyContent: 'center' },
  orb: { width: 44, height: 44 },
  title: { color: colors.text, fontSize: 13, fontWeight: '800' },
});

