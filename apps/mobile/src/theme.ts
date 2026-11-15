import React, { createContext, ReactNode, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { useColorScheme } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

export const colors = {
  background: '#F7F2FF', bgWarm: '#FFF8F3', backgroundRaised: '#FFFFFF', card: '#FFFFFFE6', cardSoft: '#ECE3FF',
  border: '#EDE6FA', text: '#17132A', ink: '#17132A', muted: '#6D6882', faint: '#8B859D',
  primary: '#6F3DFF', purple: '#6F3DFF', purpleDark: '#2D1B69', violet: '#9B5CFF', cyan: '#13BFD3',
  orange: '#FF8A3D', blue: '#2D6BFF', green: '#22B07D', amber: '#E49B23', red: '#E45467', onAccent: '#FFFFFF',
};
export type ThemeColors = typeof colors;
export type ThemePreset = 'amethyst' | 'ocean' | 'sunset' | 'forest' | 'midnight' | 'sand' | 'rose' | 'gold';
export type AccentColor = 'purple' | 'teal' | 'orange' | 'black' | 'rose' | 'blue' | 'gold';
export type ThemeMode = 'system' | 'light' | 'dark';
export type TextColor = 'theme' | 'graphite' | 'navy' | 'plum' | 'warm';
export type Appearance = { preset: ThemePreset; accent: AccentColor; textColor: TextColor; mode: ThemeMode; reduceMotion: boolean };

type Palette = {
  background: string; card: string; cardElevated: string; text: string; subtext: string;
  primary: string; primarySoft: string; border: string; danger: string; success: string;
  warning: string; cyan: string; orange: string;
};
type Preset = { light: Palette; dark: Palette; gradient: [string, string, string] };
const palette = (background: string, card: string, cardElevated: string, text: string, subtext: string, primary: string,
  primarySoft: string, border: string, danger: string, success: string, warning: string, cyan: string, orange: string): Palette =>
  ({ background, card, cardElevated, text, subtext, primary, primarySoft, border, danger, success, warning, cyan, orange });

export const accents: Record<AccentColor, string> = {
  purple: '#6F3DFF', teal: '#0FA9A5', orange: '#FF8A3D', black: '#151515',
  rose: '#E83A7A', blue: '#2D6BFF', gold: '#C88A18',
};
export const textColorOptions: Record<Exclude<TextColor, 'theme'>, { light: string; dark: string }> = {
  graphite: { light: '#151515', dark: '#F7F7F7' },
  navy: { light: '#153252', dark: '#E6F0FF' },
  plum: { light: '#3B205E', dark: '#F4E9FF' },
  warm: { light: '#463122', dark: '#FFF1E4' },
};

// Palette values are ported from Solo's theme/colors.ts; all presets retain light and dark variants.
export const presets: Record<ThemePreset, Preset> = {
  amethyst: {
    light: palette('#F7F2FF', '#FFFFFFE6', '#FFFFFF', '#17132A', '#6D6882', '#6F3DFF', '#ECE3FF', '#EDE6FA', '#E45467', '#22B07D', '#E49B23', '#13BFD3', '#FF8A3D'),
    dark: palette('#0E0B18', '#1A1626', '#211C31', '#FFFFFF', '#A7A0B8', '#8C63FF', '#2C2442', 'rgba(255,255,255,0.08)', '#FF6B7A', '#3FD69A', '#F7B34A', '#44D8F0', '#FF9D56'),
    gradient: ['#6F3DFF', '#9B5CFF', '#2D1B69'],
  },
  ocean: {
    light: palette('#EEF8FF', '#FFFFFFE8', '#FFFFFF', '#11243B', '#5D7692', '#1F79FF', '#DDECFF', '#D9EAFD', '#E25E72', '#1BAA7A', '#D9962F', '#00AFCB', '#F29535'),
    dark: palette('#081A2B', '#10263A', '#163147', '#EFF7FF', '#9BB4CB', '#4C9CFF', '#1A3A5A', 'rgba(255,255,255,0.1)', '#FF7D91', '#35D49D', '#F5B65A', '#42D3F0', '#FFAB58'),
    gradient: ['#1F79FF', '#00AFCB', '#081A2B'],
  },
  sunset: {
    light: palette('#FFF4EE', '#FFFFFFE8', '#FFFFFF', '#311B18', '#896B64', '#E85C3B', '#FFE2D8', '#F6DDD6', '#D44B63', '#2DA87C', '#E8A63A', '#3CB9C7', '#ED7F30'),
    dark: palette('#1D1110', '#2B1A18', '#35201D', '#FFEFEA', '#C39F94', '#FF7A53', '#4A2A24', 'rgba(255,255,255,0.1)', '#FF6D84', '#47D09E', '#FFC067', '#57D6E2', '#FF9F4D'),
    gradient: ['#E85C3B', '#ED7F30', '#311B18'],
  },
  forest: {
    light: palette('#F1F8F4', '#FFFFFFE8', '#FFFFFF', '#163224', '#617E70', '#219268', '#DFF3EA', '#D9ECE2', '#D45F72', '#1C9E67', '#CA9734', '#2DB8B1', '#DE8A3A'),
    dark: palette('#0E1A14', '#16271F', '#1D3328', '#ECFFF4', '#9FBEAE', '#4AC696', '#234535', 'rgba(255,255,255,0.1)', '#FF758C', '#4CD8A1', '#F0B559', '#4FD9CF', '#F0A45B'),
    gradient: ['#219268', '#2DB8B1', '#163224'],
  },
  midnight: {
    light: palette('#F2F4FA', '#FFFFFFE8', '#FFFFFF', '#191E2C', '#66708A', '#445AE0', '#E0E6FF', '#DEE4F2', '#E15A71', '#2BB083', '#D39D39', '#3BBFD0', '#E38A42'),
    dark: palette('#0B1020', '#141B2E', '#1B2540', '#F2F5FF', '#9FAAD1', '#6E82FF', '#2A355D', 'rgba(255,255,255,0.09)', '#FF6C84', '#47D5A2', '#F0B45A', '#52D2E8', '#F0A45A'),
    gradient: ['#445AE0', '#6E82FF', '#0B1020'],
  },
  sand: {
    light: palette('#FBF6EF', '#FFFFFFE8', '#FFFFFF', '#2A2317', '#7D6F58', '#B07B2C', '#F2E6D3', '#EFE4D4', '#D65B6E', '#2EAA78', '#C88E26', '#2CB6B7', '#D88A2D'),
    dark: palette('#1A150E', '#271F14', '#32291B', '#FFF6E8', '#C4AE88', '#D6A255', '#473822', 'rgba(255,255,255,0.1)', '#FF748B', '#4ED3A0', '#F3BC64', '#50D4D4', '#F4AA4C'),
    gradient: ['#B07B2C', '#D88A2D', '#2A2317'],
  },
  rose: {
    light: palette('#FFF4F8', '#FFFFFFE8', '#FFFFFF', '#301721', '#865D6C', '#C94A78', '#FBE1EB', '#F2D8E2', '#D94A68', '#25A978', '#CC8B2E', '#2DB8C2', '#DD8540'),
    dark: palette('#170D12', '#24151C', '#2D1B24', '#FFF0F5', '#CDA8B7', '#F078A5', '#432433', 'rgba(255,255,255,0.09)', '#FF748D', '#46D29D', '#EFB55C', '#55D2DA', '#F4A15C'),
    gradient: ['#C94A78', '#E83A7A', '#301721'],
  },
  gold: {
    light: palette('#FFF8E8', '#FFFFFFE8', '#FFFFFF', '#2A210F', '#806D43', '#B98414', '#F4E6BE', '#EFE0B9', '#D65C6E', '#2BAA76', '#C88A18', '#28B3BD', '#D98B2E'),
    dark: palette('#161207', '#241D0D', '#302711', '#FFF7DD', '#CBB783', '#E1B552', '#463817', 'rgba(255,255,255,0.09)', '#FF768B', '#4CD49C', '#E1B552', '#53D0D5', '#F1A34A'),
    gradient: ['#B98414', '#D98B2E', '#2A210F'],
  },
};

const DEFAULT: Appearance = { preset: 'amethyst', accent: 'purple', textColor: 'theme', mode: 'light', reduceMotion: false };
const STORAGE = 'aetherion.mobile.appearance.v1';
type ThemeState = { colors: ThemeColors; appearance: Appearance; isDark: boolean; gradient: [string, string, string]; updateAppearance: (next: Partial<Appearance>) => void };
const ThemeContext = createContext<ThemeState>({ colors, appearance: DEFAULT, isDark: false, gradient: presets.amethyst.gradient, updateAppearance: () => {} });

function mix(hex: string, bg: string, ratio: number): string {
  const parse = (value: string) => {
    const cleaned = value.replace('#', '');
    return [0, 2, 4].map(index => parseInt(cleaned.slice(index, index + 2), 16));
  };
  const [red, green, blue] = parse(hex);
  const [backRed, backGreen, backBlue] = parse(bg);
  const next = [red, green, blue].map((channel, index) => Math.round(channel * ratio + [backRed, backGreen, backBlue][index] * (1 - ratio)));
  return `#${next.map(value => value.toString(16).padStart(2, '0')).join('')}`;
}

function accentForeground(hex: string): string {
  const [red, green, blue] = [1, 3, 5].map(index => parseInt(hex.slice(index, index + 2), 16) / 255);
  const luminance = [red, green, blue].map(channel => channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4);
  const relative = 0.2126 * luminance[0] + 0.7152 * luminance[1] + 0.0722 * luminance[2];
  const whiteContrast = 1.05 / (relative + 0.05);
  const darkContrast = (relative + 0.05) / 0.05;
  return whiteContrast >= darkContrast ? '#FFFFFF' : '#161329';
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [appearance, setAppearance] = useState<Appearance>(DEFAULT);
  const changed = useRef(false);
  const writes = useRef(Promise.resolve());
  const system = useColorScheme();
  useEffect(() => { let active = true; void AsyncStorage.getItem(STORAGE).then(raw => {
    if (!raw || !active || changed.current) return;
    const saved = JSON.parse(raw);
    if (!saved || typeof saved !== 'object') return;
    const preset = typeof saved.preset === 'string' && Object.prototype.hasOwnProperty.call(presets, saved.preset) ? saved.preset as ThemePreset : null;
    const mode = ['system', 'light', 'dark'].includes(saved.mode) ? saved.mode as ThemeMode : null;
    if (!preset || !mode) return;
    const accent = typeof saved.accent === 'string' && Object.prototype.hasOwnProperty.call(accents, saved.accent) ? saved.accent as AccentColor : DEFAULT.accent;
    const textColor = saved.textColor === 'theme' || (typeof saved.textColor === 'string' && Object.prototype.hasOwnProperty.call(textColorOptions, saved.textColor)) ? saved.textColor as TextColor : DEFAULT.textColor;
    setAppearance({ preset, accent, textColor, mode, reduceMotion: saved.reduceMotion === true });
  }).catch(() => {}); return () => { active = false; }; }, []);
  const updateAppearance = (next: Partial<Appearance>) => {
    changed.current = true;
    setAppearance(current => {
      const updated = { ...current, ...next };
      writes.current = writes.current.catch(() => {}).then(() => AsyncStorage.setItem(STORAGE, JSON.stringify(updated)));
      return updated;
    });
  };
  const isDark = appearance.mode === 'dark' || (appearance.mode === 'system' && system === 'dark');
  const value = useMemo(() => {
    const preset = presets[appearance.preset];
    const base = isDark ? preset.dark : preset.light;
    const accent = accents[appearance.accent];
    const text = appearance.textColor === 'theme' ? base.text : textColorOptions[appearance.textColor][isDark ? 'dark' : 'light'];
    const palette: ThemeColors = {
      ...colors,
      background: base.background, bgWarm: preset.light.background, backgroundRaised: base.cardElevated,
      card: base.card, cardSoft: mix(accent, base.cardElevated, isDark ? 0.24 : 0.13), border: base.border,
      text, ink: text, muted: base.subtext, faint: base.subtext,
      primary: accent, purple: accent, purpleDark: preset.gradient[2], violet: preset.gradient[1],
      cyan: base.cyan, orange: base.orange, blue: preset.light.primary,
      green: base.success, amber: base.warning, red: base.danger, onAccent: accentForeground(accent),
    };
    return { colors: palette, appearance, isDark, gradient: [accent, preset.gradient[1], preset.gradient[2]] as [string, string, string], updateAppearance };
  }, [appearance, isDark]);
  return React.createElement(ThemeContext.Provider, { value }, children);
}
export function useTheme() { return useContext(ThemeContext); }
export function useThemedStyles<T>(build: (palette: ThemeColors) => T) {
  const theme = useTheme();
  const styles = useMemo(() => build(theme.colors), [build, theme.colors]);
  return { ...theme, styles };
}

export const spacing = { xs: 6, sm: 10, md: 16, lg: 22, xl: 30 } as const;
export const radius = { card: 22, panel: 18, control: 14, pill: 999 } as const;

