import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Locale } from '../types';
import { t } from '../i18n';
import { copy } from '../uiCopy';
import { ThemeColors, useThemedStyles } from '../theme';
import { AppHeader, AppPage, ActionButton, Body, Field, Panel } from '../components/ui';
import { createSubject, Subject } from '../api/subjects';
import { ApiError } from '../api/client';
export function MissionScreen({ locale, role, subjects, token, onRefresh, onSelect, onBack }: { locale: Locale; role: string; subjects: Subject[]; token: string; onRefresh: () => Promise<void>; onSelect: (id: string) => void; onBack: () => void }) {
  const { colors, styles } = useThemedStyles(buildStyles);
  const [form, setForm] = useState(false), [id, setId] = useState(''), [name, setName] = useState(''), [busy, setBusy] = useState(false), [error, setError] = useState('');
  const submit = async () => { if (busy || !id.trim() || !name.trim()) return; setBusy(true); setError(''); try { await createSubject(token, id.trim(), name.trim()); await onRefresh(); setForm(false); setId(''); setName(''); } catch (cause) { setError(t(locale, cause instanceof ApiError && cause.status === 403 ? 'forbidden' : 'serverError')); } finally { setBusy(false); } };
  return <AppPage><AppHeader title={t(locale, 'missionTitle')} onBack={onBack} backLabel={t(locale, 'back')} /><Body>{t(locale, 'role')}: {role}</Body>
    {subjects.length ? subjects.map(subject => <Pressable key={subject.subject_id} accessibilityRole="button" accessibilityLabel={subject.display_name} onPress={() => onSelect(subject.subject_id)}><Panel style={styles.profile}><View style={styles.icon}><Ionicons name="person-outline" color={colors.cyan} size={23} /></View><View style={styles.identity}><Text style={styles.name}>{subject.display_name}</Text><Text style={styles.meta}>{subject.subject_id} · {subject.scope}</Text></View><Ionicons name="chevron-forward" color={colors.muted} size={20} /></Panel></Pressable>) : <Panel><Body>{copy(locale, 'noProfiles')}</Body></Panel>}
    <ActionButton title={copy(locale, 'registerProfile')} onPress={() => setForm(value => !value)} secondary />
    {form ? <Panel style={styles.form}><Field label={copy(locale, 'profileId')} value={id} onChangeText={setId} autoCapitalize="none" autoCorrect={false} maxLength={80} /><Field label={copy(locale, 'profileName')} value={name} onChangeText={setName} maxLength={120} />{error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}<ActionButton title={copy(locale, 'registerProfile')} onPress={() => void submit()} loading={busy} disabled={!id.trim() || !name.trim()} /></Panel> : null}
  </AppPage>;
}
const buildStyles = (colors: ThemeColors) => StyleSheet.create({ profile: { flexDirection: 'row', alignItems: 'center', gap: 12 }, icon: { width: 46, height: 46, borderRadius: 16, backgroundColor: colors.cardSoft, alignItems: 'center', justifyContent: 'center' }, identity: { flex: 1, gap: 6 }, name: { color: colors.text, fontSize: 15, fontWeight: '800' }, meta: { color: colors.muted, fontSize: 11 }, form: { gap: 14 }, error: { color: colors.red, fontSize: 12, lineHeight: 18 } });
