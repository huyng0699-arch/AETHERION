import { useRequestGate } from '../hooks/useRequestGate';
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { ApiError } from '../api/client';
import {
  advanceCareEpisode,
  CareActionStatus,
  CareEpisode,
  CareOutcome,
  CarePhase,
  getCareEpisode,
  listCareEpisodes,
  startCareEpisode,
} from '../api/care';
import { AppHeader, AppPage, ActionButton, Body, Panel, StatusPill, Title } from '../components/ui';
import { MessageKey, t } from '../i18n';
import { ThemeColors, useThemedStyles } from '../theme';
import { Locale } from '../types';

type PhaseTarget = 'GATHER' | 'CLOSED';
type CopyKey = string;

function copy(locale: Locale, key: CopyKey): string {
  return t(locale, key as MessageKey);
}

export function CareScreen({ locale, token, subjectId, onBack, onUnauthorized }: {
  locale: Locale; token: string; subjectId?: string; onBack: () => void; onUnauthorized: () => void;
}) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  const [episodes, setEpisodes] = useState<CareEpisode[]>([]);
  const [episode, setEpisode] = useState<CareEpisode | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [concern, setConcern] = useState('');
  const [symptoms, setSymptoms] = useState('');
  const [consent, setConsent] = useState(false);
  const [summary, setSummary] = useState('');
  const [actionStatus, setActionStatus] = useState<CareActionStatus | null>(null);
  const [outcome, setOutcome] = useState<CareOutcome | null>(null);
  const [recheckTarget, setRecheckTarget] = useState<PhaseTarget>('GATHER');
  const [confirmed, setConfirmed] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const beginList = useRequestGate(), beginAction = useRequestGate();
  const loadEpisodes = useCallback(async () => {
    const isCurrent = beginList();
    if (!subjectId) { setEpisodes([]); return; }
    setLoading(true);
    setError(null);
    try {
      const result = await listCareEpisodes(subjectId, token);
      if (isCurrent()) setEpisodes(result.episodes);
    } catch (cause) {
      if (!isCurrent()) return;
      handleError(cause, locale, onUnauthorized, setError);
    } finally {
      if (isCurrent()) setLoading(false);
    }
  }, [locale, onUnauthorized, subjectId, token, refreshKey]);

  useEffect(() => { void loadEpisodes(); }, [loadEpisodes]);

  const openEpisode = async (episodeId: string) => {
    const isCurrent = beginAction();
    setSaving(true);
    setError(null);
    try {
      const result = await getCareEpisode(episodeId, token);
      if (isCurrent()) setEpisode(result);
      setCreating(false);
      resetTransition();
    } catch (cause) {
      if (!isCurrent()) return;
      handleError(cause, locale, onUnauthorized, setError);
    } finally {
      if (isCurrent()) setSaving(false);
    }
  };

  const resetTransition = () => {
    setSummary('');
    setActionStatus(null);
    setOutcome(null);
    setRecheckTarget('GATHER');
    setConfirmed(false);
  };

  const createEpisode = async () => {
    if (!subjectId || !consent || !concern.trim()) return;
    const symptomTerms = symptoms.split(',').map((item) => item.trim()).filter(Boolean);
    if (symptomTerms.length > 20 || symptomTerms.some((item) => item.length > 120)) {
      setError(copy(locale, 'careSymptomsInvalid'));
      return;
    }
    const isCurrent = beginAction();
    setSaving(true);
    setError(null);
    try {
      const result = await startCareEpisode({
        subject_id: subjectId,
        chief_concern: concern.trim(),
        symptom_terms: symptomTerms,
        interview_answers: {},
        explicit_consent: true,
      }, token);
      if (!isCurrent()) return;
      setEpisode(result.episode);
      setConcern('');
      setSymptoms('');
      setConsent(false);
      setCreating(false);
      resetTransition();
      setRefreshKey((key) => key + 1);
    } catch (cause) {
      if (!isCurrent()) return;
      handleError(cause, locale, onUnauthorized, setError);
    } finally {
      if (isCurrent()) setSaving(false);
    }
  };

  const advance = async () => {
    if (!episode || !confirmed || !summary.trim()) return;
    const current = episode.current_phase;
    let nextPhase: CarePhase;
    if (current === 'GATHER') nextPhase = 'EVALUATE';
    else if (current === 'EVALUATE') nextPhase = 'ACT';
    else if (current === 'ACT') nextPhase = 'RECHECK';
    else if (current === 'RECHECK') nextPhase = recheckTarget;
    else return;
    if (nextPhase === 'ACT' && !actionStatus) return;
    if (nextPhase === 'RECHECK' && !outcome) return;

    const isCurrent = beginAction();
    setSaving(true);
    setError(null);
    try {
      const result = await advanceCareEpisode(episode.episode_id, {
        next_phase: nextPhase,
        summary: summary.trim(),
        ...(nextPhase === 'ACT' && actionStatus ? { action_status: actionStatus } : {}),
        ...(nextPhase === 'RECHECK' && outcome ? { outcome } : {}),
        human_confirmed: true,
      }, token);
      if (!isCurrent()) return;
      setEpisode(result.episode);
      resetTransition();
      setRefreshKey((key) => key + 1);
    } catch (cause) {
      if (!isCurrent()) return;
      handleError(cause, locale, onUnauthorized, setError);
      if (cause instanceof ApiError && cause.status === 409) setRefreshKey((key) => key + 1);
    } finally {
      if (isCurrent()) setSaving(false);
    }
  };

  const heading = useMemo(() => episode ? episode.chief_concern : copy(locale, 'careTitle'), [episode, locale]);
  const transition = episode ? transitionCopy(episode.current_phase, recheckTarget, locale) : null;
  const transitionDisabled = !summary.trim() || !confirmed || saving
    || (episode?.current_phase === 'EVALUATE' && !actionStatus)
    || (episode?.current_phase === 'ACT' && !outcome);

  return (
    <AppPage>
      <AppHeader
        title={copy(locale, 'careTitle')}
        onBack={episode || creating ? () => { setEpisode(null); setCreating(false); setError(null); } : onBack}
        backLabel={copy(locale, 'back')}
        trailing={<Pressable accessibilityRole="button" onPress={() => setRefreshKey((key) => key + 1)} style={styles.headerAction}><Text style={styles.headerActionText}>{copy(locale, 'refresh')}</Text></Pressable>}
      />

      {!subjectId ? <Panel><Body>{copy(locale, 'noSubject')}</Body></Panel> : null}
      {error ? <Panel><Text accessibilityRole="alert" style={styles.error}>{error}</Text></Panel> : null}
      {saving && !episode && !creating ? <Loading label={copy(locale, 'loading')} /> : null}

      {episode ? <>
        <View style={styles.heading}>
          <Title size={24}>{heading}</Title>
          <View style={styles.phaseLine}>
            <StatusPill label={phaseLabel(locale, episode.current_phase)} tone={episode.current_phase === 'CLOSED' ? 'neutral' : 'good'} />
            <StatusPill label={dataStateLabel(locale, episode.events[episode.events.length - 1]?.data_state)} tone="warn" />
          </View>
        </View>
        <Panel style={styles.notice}>
          <Text style={styles.noticeTitle}>{copy(locale, 'careNotAssessed')}</Text>
          <Body>{copy(locale, 'careUserReported')}</Body>
        </Panel>

        {episode.current_phase !== 'CLOSED' && transition ? <Panel style={styles.form}>
          <Text style={styles.sectionTitle}>{transition.title}</Text>
          <Text style={styles.fieldLabel}>{transition.summaryLabel}</Text>
          <TextInput
            value={summary}
            onChangeText={setSummary}
            placeholder={copy(locale, 'careSummaryPlaceholder')}
            placeholderTextColor={colors.faint}
            maxLength={1000}
            multiline
            textAlignVertical="top"
            style={[styles.input, styles.multiline]}
          />

          {episode.current_phase === 'EVALUATE' ? <ChoiceGroup<CareActionStatus>
            label={copy(locale, 'careActionStatus')}
            value={actionStatus}
            options={[
              ['DONE', copy(locale, 'careDone')],
              ['NOT_DONE', copy(locale, 'careNotDone')],
              ['CANNOT_DO', copy(locale, 'careCannotDo')],
            ]}
            onChange={setActionStatus}
          /> : null}

          {episode.current_phase === 'ACT' ? <ChoiceGroup<CareOutcome>
            label={copy(locale, 'careOutcome')}
            value={outcome}
            options={[
              ['BETTER', copy(locale, 'careBetter')],
              ['UNCHANGED', copy(locale, 'careUnchanged')],
              ['WORSE', copy(locale, 'careWorse')],
              ['UNKNOWN', copy(locale, 'careUnknown')],
            ]}
            onChange={setOutcome}
          /> : null}

          {episode.current_phase === 'RECHECK' ? <ChoiceGroup<PhaseTarget>
            label={copy(locale, 'careAfterRecheck')}
            value={recheckTarget}
            options={[
              ['GATHER', copy(locale, 'careContinue')],
              ['CLOSED', copy(locale, 'careClose')],
            ]}
            onChange={setRecheckTarget}
          /> : null}

          <Pressable accessibilityRole="checkbox" accessibilityState={{ checked: confirmed }} onPress={() => setConfirmed((value) => !value)} style={styles.confirmRow}>
            <View style={[styles.checkbox, confirmed && styles.checkboxSelected]}>{confirmed ? <Text style={styles.checkmark}>✓</Text> : null}</View>
            <Text style={styles.confirmText}>{copy(locale, 'careConfirm')}</Text>
          </Pressable>
          <ActionButton title={transition.buttonLabel} onPress={advance} disabled={transitionDisabled} loading={saving} />
        </Panel> : null}

        <View style={styles.eventsHeading}><Text style={styles.sectionTitle}>{copy(locale, 'careHistory')}</Text></View>
        {episode.events.map((event) => <Panel key={event.event_id} style={styles.event}>
          <View style={styles.eventTop}>
            <Text style={styles.eventPhase}>{phaseLabel(locale, event.phase)}</Text>
            <Text style={styles.eventDate}>{formatDate(event.recorded_at_utc, locale)}</Text>
          </View>
          <Body style={styles.eventSummary}>{event.summary}</Body>
          <View style={styles.eventMeta}>
            <Text style={styles.metaText}>{dataStateLabel(locale, event.data_state)}</Text>
            {event.human_confirmed ? <Text style={styles.metaText}>{copy(locale, 'careHumanConfirmed')}</Text> : null}
          </View>
        </Panel>)}
      </> : null}

      {!episode && subjectId && !creating ? <>
        <View style={styles.heading}>
          <Title>{copy(locale, 'careTitle')}</Title>
          <Body>{copy(locale, 'careSubject')}: {subjectId}</Body>
        </View>
        <ActionButton title={copy(locale, 'careNew')} onPress={() => { setCreating(true); setError(null); }} />
        <Text style={styles.sectionTitle}>{copy(locale, 'careEpisodes')}</Text>
        {loading ? <Loading label={copy(locale, 'loading')} /> : episodes.length === 0 ? <Panel><Body>{copy(locale, 'careNoEpisodes')}</Body></Panel> : episodes.map((item) => (
          <Pressable key={item.episode_id} onPress={() => void openEpisode(item.episode_id)} accessibilityRole="button" style={styles.episodePressable}>
            <Panel style={styles.episodeCard}>
              <View style={styles.episodeCopy}>
                <Text numberOfLines={2} style={styles.episodeTitle}>{item.chief_concern}</Text>
                <Text style={styles.eventDate}>{formatDate(item.updated_at_utc, locale)}</Text>
              </View>
              <StatusPill label={phaseLabel(locale, item.current_phase)} tone={item.current_phase === 'CLOSED' ? 'neutral' : 'good'} />
            </Panel>
          </Pressable>
        ))}
      </> : null}

      {!episode && subjectId && creating ? <>
        <View style={styles.heading}><Title>{copy(locale, 'careNew')}</Title></View>
        <Panel style={styles.form}>
          <Text style={styles.fieldLabel}>{copy(locale, 'careConcern')}</Text>
          <TextInput value={concern} onChangeText={setConcern} maxLength={500} multiline placeholder={copy(locale, 'careConcernPlaceholder')} placeholderTextColor={colors.faint} style={[styles.input, styles.multiline]} />
          <Text style={styles.fieldLabel}>{copy(locale, 'careSymptoms')}</Text>
          <TextInput value={symptoms} onChangeText={setSymptoms} maxLength={1500} placeholder={copy(locale, 'careSymptomsPlaceholder')} placeholderTextColor={colors.faint} style={styles.input} />
          <Pressable accessibilityRole="checkbox" accessibilityState={{ checked: consent }} onPress={() => setConsent((value) => !value)} style={styles.confirmRow}>
            <View style={[styles.checkbox, consent && styles.checkboxSelected]}>{consent ? <Text style={styles.checkmark}>✓</Text> : null}</View>
            <Text style={styles.confirmText}>{copy(locale, 'careConsent')}</Text>
          </Pressable>
          <ActionButton title={copy(locale, 'careStart')} onPress={createEpisode} disabled={!concern.trim() || !consent || saving} loading={saving} />
        </Panel>
      </> : null}
    </AppPage>
  );
}

function ChoiceGroup<T extends string>({ label, value, options, onChange }: {
  label: string; value: T | null; options: Array<[T, string]>; onChange: (value: T) => void;
}) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  return <View style={styles.choiceGroup}>
    <Text style={styles.fieldLabel}>{label}</Text>
    <View style={styles.choices}>{options.map(([option, title]) => <Pressable
      key={option}
      accessibilityRole="radio"
      accessibilityState={{ selected: value === option }}
      onPress={() => onChange(option)}
      style={[styles.choice, value === option && styles.choiceSelected]}
    ><Text style={[styles.choiceText, value === option && styles.choiceTextSelected]}>{title}</Text></Pressable>)}</View>
  </View>;
}

function transitionCopy(phase: CarePhase, target: PhaseTarget, locale: Locale) {
  if (phase === 'GATHER') return { title: copy(locale, 'careEvaluate'), summaryLabel: copy(locale, 'careGatherSummary'), buttonLabel: copy(locale, 'careContinue') };
  if (phase === 'EVALUATE') return { title: copy(locale, 'careAct'), summaryLabel: copy(locale, 'careActionSummary'), buttonLabel: copy(locale, 'careContinue') };
  if (phase === 'ACT') return { title: copy(locale, 'careRecheck'), summaryLabel: copy(locale, 'careRecheckSummary'), buttonLabel: copy(locale, 'careContinue') };
  if (phase === 'RECHECK') return { title: target === 'CLOSED' ? copy(locale, 'careClose') : copy(locale, 'careGather'), summaryLabel: copy(locale, 'careNextSummary'), buttonLabel: target === 'CLOSED' ? copy(locale, 'careClose') : copy(locale, 'careContinue') };
  return null;
}

function phaseLabel(locale: Locale, phase: CarePhase) {
  const labels: Record<CarePhase, string> = {
    GATHER: copy(locale, 'careGather'),
    EVALUATE: copy(locale, 'careEvaluate'),
    ACT: copy(locale, 'careAct'),
    RECHECK: copy(locale, 'careRecheck'),
    CLOSED: copy(locale, 'careClosed'),
  };
  return labels[phase];
}

function dataStateLabel(locale: Locale, state?: string) {
  const keyByState: Record<string, string> = {
    READY: 'careDataReady', NO_DATA: 'careDataNoData', STALE: 'careDataStale',
    OFFLINE: 'careDataOffline', DENIED: 'careDataDenied', ERROR: 'careDataError',
    UNVERIFIED: 'careUnverified',
  };
  return copy(locale, keyByState[state || ''] || 'careDataOther');
}

function formatDate(value: string, locale: Locale) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString(locale === 'vi' ? 'vi-VN' : 'en-US');
}

function handleError(cause: unknown, locale: Locale, onUnauthorized: () => void, setError: (message: string) => void) {
  if (cause instanceof ApiError) {
    if (cause.status === 401) { onUnauthorized(); return; }
    if (cause.status === 403) { setError(copy(locale, 'forbidden')); return; }
    if (cause.status === 404) { setError(copy(locale, 'careUnavailable')); return; }
    if (cause.status === 409) { setError(copy(locale, 'careConflict')); return; }
    if (cause.status === 422) { setError(copy(locale, 'careInvalid')); return; }
    if (cause.status === 0 || cause.status === 408) { setError(copy(locale, 'networkError')); return; }
  }
  setError(copy(locale, 'serverError'));
}

function Loading({ label }: { label: string }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  return <View style={styles.loading}><ActivityIndicator color={colors.cyan} /><Text style={styles.loadingText}>{label}</Text></View>;
}

const buildStyles = (colors: ThemeColors) => StyleSheet.create({
  heading: { gap: 7, paddingTop: 4 },
  headerAction: { padding: 8 },
  headerActionText: { color: colors.cyan, fontSize: 12, fontWeight: '800' },
  phaseLine: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  notice: { gap: 6, borderColor: '#D8CDFC', backgroundColor: colors.card },
  noticeTitle: { color: colors.text, fontSize: 14, fontWeight: '800' },
  form: { gap: 14 },
  sectionTitle: { color: colors.text, fontSize: 16, fontWeight: '800' },
  fieldLabel: { color: colors.muted, fontSize: 12, fontWeight: '700' },
  input: { minHeight: 48, borderRadius: 14, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.card, paddingHorizontal: 13, paddingVertical: 12, color: colors.text, fontSize: 15 },
  multiline: { minHeight: 92, textAlignVertical: 'top' },
  choiceGroup: { gap: 8 },
  choices: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  choice: { minHeight: 38, borderRadius: 999, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.card, paddingHorizontal: 12, justifyContent: 'center' },
  choiceSelected: { backgroundColor: '#EEE9FF', borderColor: colors.cyan },
  choiceText: { color: colors.muted, fontSize: 12, fontWeight: '700' },
  choiceTextSelected: { color: colors.cyan },
  confirmRow: { flexDirection: 'row', alignItems: 'center', gap: 10, minHeight: 42 },
  checkbox: { width: 22, height: 22, borderRadius: 7, borderWidth: 1.5, borderColor: colors.border, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.card },
  checkboxSelected: { borderColor: colors.cyan, backgroundColor: colors.cyan },
  checkmark: { color: '#FFFFFF', fontSize: 14, lineHeight: 16, fontWeight: '900' },
  confirmText: { flex: 1, color: colors.muted, fontSize: 12, lineHeight: 17 },
  eventsHeading: { paddingTop: 4 },
  event: { gap: 8 },
  eventTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 8 },
  eventPhase: { color: colors.text, fontSize: 13, fontWeight: '800' },
  eventDate: { color: colors.faint, fontSize: 10, fontWeight: '600' },
  eventSummary: { color: colors.text },
  eventMeta: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  metaText: { color: colors.muted, fontSize: 10, fontWeight: '700' },
  episodePressable: { borderRadius: 18 },
  episodeCard: { flexDirection: 'row', gap: 12, alignItems: 'center', justifyContent: 'space-between' },
  episodeCopy: { flex: 1, gap: 7 },
  episodeTitle: { color: colors.text, fontWeight: '800', fontSize: 14, lineHeight: 20 },
  loading: { flexDirection: 'row', alignItems: 'center', gap: 10, padding: 18 },
  loadingText: { color: colors.muted },
  error: { color: colors.red, lineHeight: 20, fontSize: 13 },
});

