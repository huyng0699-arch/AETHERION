import React, { createContext, ReactNode, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { useColorScheme } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

export const colors = {
  background: '#F8F6FF', backgroundRaised: '#F1EDFF', card: '#FFFFFF', cardSoft: '#F4F0FF',
  border: '#EAE5F5', text: '#19152D', muted: '#66617C', faint: '#8D88A2', cyan: '#6539F5',
  blue: '#347DEB', green: '#159A61', amber: '#B97913', red: '#D83F58',
};
export type ThemeColors = typeof colors;
export type ThemePreset = 'amethyst' | 'ocean' | 'rose' | 'midnight';
export type ThemeMode = 'system' | 'light' | 'dark';
export type Appearance = { preset: ThemePreset; mode: ThemeMode; reduceMotion: boolean };
export const presets: Record<ThemePreset, { accent: string; darkAccent: string; tint: string; gradient: [string, string, string] }> = {
  amethyst: { accent: '#6539F5', darkAccent: '#B2A0FF', tint: '#F4F0FF', gradient: ['#5638D5', '#8B70F2', '#B8A6FF'] },
  ocean: { accent: '#087A96', darkAccent: '#67D4E8', tint: '#EAF8FB', gradient: ['#086B90', '#2098B0', '#8ED3DD'] },
  rose: { accent: '#B83F70', darkAccent: '#F492BD', tint: '#FFF0F5', gradient: ['#963B68', '#CF668E', '#F2A2BC'] },
  midnight: { accent: '#7163E8', darkAccent: '#A7B7FE', tint: '#F1EFFF', gradient: ['#27264F', '#505481', '#8288B1'] },
};
const DEFAULT: Appearance = { preset: 'amethyst', mode: 'light', reduceMotion: false };
const STORAGE = 'aetherion.mobile.appearance.v1';
type ThemeState = { colors: ThemeColors; appearance: Appearance; isDark: boolean; gradient: [string, string, string]; updateAppearance: (next: Partial<Appearance>) => void };
const ThemeContext = createContext<ThemeState>({ colors, appearance: DEFAULT, isDark: false, gradient: presets.amethyst.gradient, updateAppearance: () => {} });
export function ThemeProvider({ children }: { children: ReactNode }) {
  const [appearance, setAppearance] = useState<Appearance>(DEFAULT);
  const changed = useRef(false);
  const writes = useRef(Promise.resolve());
  const system = useColorScheme();
  useEffect(() => { let active = true; void AsyncStorage.getItem(STORAGE).then(raw => {
    if (!raw || !active || changed.current) return;
    const saved = JSON.parse(raw);
    if (saved.preset in presets && ['system', 'light', 'dark'].includes(saved.mode)) setAppearance({ preset: saved.preset, mode: saved.mode, reduceMotion: saved.reduceMotion === true });
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
    const palette = isDark ? { ...colors, background: '#12121F', backgroundRaised: '#1A192C', card: '#211F35', cardSoft: '#29253E', border: '#39334F', text: '#F3F0FF', muted: '#BDB6D3', faint: '#9C94B2', cyan: preset.darkAccent, green: '#5CD8A0', red: '#FF839A', amber: '#EAC279' }
      : { ...colors, cyan: preset.accent, cardSoft: preset.tint, backgroundRaised: preset.tint };
    return { colors: palette, appearance, isDark, gradient: preset.gradient, updateAppearance };
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

