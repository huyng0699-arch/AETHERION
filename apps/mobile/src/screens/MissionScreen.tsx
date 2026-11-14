import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Locale } from '../types';
import { t } from '../i18n';
import { colors } from '../theme';
import { AppHeader, AppPage, Panel, Title } from '../components/ui';

export function MissionScreen({ locale, role, allowedSubjects, onBack }: {
  locale: Locale; role: string; allowedSubjects: string[]; onBack: () => void;
}) {
  return (
    <AppPage>
      <AppHeader title={t(locale, 'missionTitle')} onBack={onBack} backLabel={t(locale, 'back')} />
      <View style={styles.hero}>
        <View style={styles.icon}><Ionicons name="people-outline" size={26} color={colors.cyan} /></View>
        <Title>{t(locale, 'missionTitle')}</Title>
      </View>
      <Panel style={styles.details}>
        <InfoRow label={t(locale, 'role')} value={role || '—'} />
        <InfoRow label={t(locale, 'allowedSubjects')} value={String(allowedSubjects.length)} />
      </Panel>
      {allowedSubjects.length === 0 ? <Panel><Text style={styles.empty}>{t(locale, 'noSubject')}</Text></Panel> : (
        <View style={styles.list}>
          {allowedSubjects.map((subject) => <Panel key={subject} style={styles.subject}>
            <Ionicons name="person-outline" size={18} color={colors.cyan} />
            <Text style={styles.subjectName}>{subject}</Text>
            <Text style={styles.access}>{t(locale, 'authorized')}</Text>
          </Panel>)}
        </View>
      )}
    </AppPage>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return <View style={styles.infoRow}><Text style={styles.label}>{label}</Text><Text style={styles.value}>{value}</Text></View>;
}

const styles = StyleSheet.create({
  hero: { paddingTop: 18, gap: 10 },
  icon: { width: 54, height: 54, borderRadius: 18, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F0EAFF', marginBottom: 4 },
  details: { gap: 12 },
  infoRow: { flexDirection: 'row', justifyContent: 'space-between', gap: 12 },
  label: { color: colors.muted, fontSize: 12, fontWeight: '700' },
  value: { color: colors.text, fontSize: 12, fontWeight: '800' },
  list: { gap: 9 },
  subject: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 13 },
  subjectName: { flex: 1, color: colors.text, fontSize: 13, fontWeight: '800' },
  access: { color: colors.green, fontSize: 10, fontWeight: '800' },
  empty: { color: colors.muted, fontSize: 13, fontWeight: '700' },
});
