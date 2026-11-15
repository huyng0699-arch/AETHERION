import { useRequestGate } from '../hooks/useRequestGate';
import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Image, Linking, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Locale } from '../types';
import { MessageKey, t } from '../i18n';
import { ThemeColors, useThemedStyles } from '../theme';
import { ApiError, readServerUrl } from '../api/client';
import { buildScienceMediaUrl, getKnowledgeStatus, getScienceArticle, searchScienceArticles, KnowledgeStatus, ScienceArticle, ScienceArticleSummary } from '../api/science';
import { OFFLINE_CLIFF_COUNT, OFFLINE_CLIFF_STATUS, getOfflineCliffArticle, searchOfflineCliffArticles } from '../api/offlineCliff';
import { AppHeader, AppPage, Body, Panel, StatusPill, Title } from '../components/ui';
import { copy } from '../uiCopy';

export function ScienceScreen({ locale, onBack, onAskAi }: { locale: Locale; onBack: () => void; onAskAi?: (article: ScienceArticleSummary) => void }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  const [query, setQuery] = useState('');
  const [items, setItems] = useState<ScienceArticleSummary[]>([]);
  const [indexed, setIndexed] = useState(0);
  const [matched, setMatched] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [nextOffset, setNextOffset] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);
  const [serverBaseUrl, setServerBaseUrl] = useState('');
  const [status, setStatus] = useState<KnowledgeStatus | null>(null);
  const [offlineLibrary, setOfflineLibrary] = useState(false);
  const offlineLibraryRef = React.useRef(false);
  const [loading, setLoading] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [errorKey, setErrorKey] = useState<MessageKey | null>(null);
  const [detailErrorKey, setDetailErrorKey] = useState<MessageKey | null>(null);
  const [selected, setSelected] = useState<ScienceArticleSummary | null>(null);
  const [article, setArticle] = useState<ScienceArticle | null>(null);

  const beginSearch = useRequestGate(), beginDetail = useRequestGate();
  const load = useCallback(async (term: string, offset = 0, append = false) => {
    const current = beginSearch();
    if (append) setLoadingMore(true);
    else {
      setLoading(true);
      setLoadingMore(false);
      setItems([]);
      setMatched(0);
      setHasMore(false);
      setNextOffset(0);
    }
    setErrorKey(null);
    try {
      if (offlineLibraryRef.current && append) {
        const local = searchOfflineCliffArticles(term, 100, offset);
        if (!current()) return;
        setItems(previous => [...previous, ...local.items]);
        setIndexed(OFFLINE_CLIFF_COUNT);
        setMatched(local.matched);
        setNextOffset(local.next_offset ?? offset + local.items.length);
        setHasMore(local.has_more ?? false);
        return;
      }
      const result = await searchScienceArticles(term, 100, offset);
      if (!current()) return;
      const wasOffline = offlineLibraryRef.current;
      offlineLibraryRef.current = false;
      setOfflineLibrary(false);
      if (wasOffline) void getKnowledgeStatus().then(value => { if (!offlineLibraryRef.current) setStatus(value); }).catch(() => { if (!offlineLibraryRef.current) setStatus(null); });
      const page = Array.isArray(result.items) ? result.items : [];
      const total = Number.isFinite(result.matched) ? result.matched : page.length;
      const next = typeof result.next_offset === 'number' && Number.isFinite(result.next_offset) ? result.next_offset : offset + page.length;
      setItems(previous => append ? [...previous, ...page] : page);
      setIndexed(Number.isFinite(result.indexed) ? result.indexed : 0);
      setMatched(total);
      setNextOffset(next);
      setHasMore(typeof result.has_more === 'boolean' ? result.has_more : next < total);
    } catch (error) {
      if (!current()) return;
      if (canUseOfflineLibrary(error)) {
        const appendLocal = append && offlineLibraryRef.current;
        const localOffset = appendLocal ? offset : 0;
        const local = searchOfflineCliffArticles(term, 100, localOffset);
        offlineLibraryRef.current = true;
        setOfflineLibrary(true);
        setStatus(OFFLINE_CLIFF_STATUS);
        setItems(previous => appendLocal ? [...previous, ...local.items] : local.items);
        setIndexed(OFFLINE_CLIFF_COUNT);
        setMatched(local.matched);
        setNextOffset(local.next_offset ?? localOffset + local.items.length);
        setHasMore(local.has_more ?? false);
        setErrorKey(null);
      } else {
        offlineLibraryRef.current = false;
        setOfflineLibrary(false);
        if (!append) {
          setItems([]);
          setIndexed(0);
          setMatched(0);
          setHasMore(false);
          setNextOffset(0);
        }
        setErrorKey(errorMessageKey(error));
      }
    } finally {
      if (current()) {
        if (append) setLoadingMore(false);
        else setLoading(false);
      }
    }
  }, []);

  useEffect(() => { void load(''); }, [load]);
  useEffect(() => {
    let active = true;
    void getKnowledgeStatus().then(value => { if (active && !offlineLibraryRef.current) setStatus(value); }).catch(() => { if (active && !offlineLibraryRef.current) setStatus(null); });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    let active = true;
    void readServerUrl().then(value => { if (active) setServerBaseUrl(value); }).catch(() => {});
    return () => { active = false; };
  }, []);

  const openArticle = async (summary: ScienceArticleSummary) => {
    const current = beginDetail();
    setSelected(summary);
    setArticle(null);
    setDetailErrorKey(null);
    setLoadingDetail(true);
    try {
      if (offlineLibrary) {
        const local = getOfflineCliffArticle(summary.article_id);
        if (current()) {
          if (local) setArticle(local);
          else setDetailErrorKey('scienceRecordUnavailable');
        }
      } else {
        const result = await getScienceArticle(summary.article_id);
        if (current()) setArticle(result);
      }
    } catch (error) {
      const local = canUseOfflineLibrary(error) ? getOfflineCliffArticle(summary.article_id) : null;
      if (current()) {
        if (local) {
          offlineLibraryRef.current = true;
          setOfflineLibrary(true);
          setStatus(OFFLINE_CLIFF_STATUS);
          setArticle(local);
          const localPage = searchOfflineCliffArticles(query, 100, 0);
          setItems(localPage.items);
          setIndexed(OFFLINE_CLIFF_COUNT);
          setMatched(localPage.matched);
          setNextOffset(localPage.next_offset ?? localPage.items.length);
          setHasMore(localPage.has_more ?? false);
        } else setDetailErrorKey(errorMessageKey(error));
      }
    } finally {
      if (current()) setLoadingDetail(false);
    }
  };

  const submitSearch = () => { beginDetail(); setSelected(null); setArticle(null); void load(query); };
  const refresh = () => { if (selected) void openArticle(selected); else { setSelected(null); setArticle(null); void load(query); void getKnowledgeStatus().then(value => { if (!offlineLibraryRef.current) setStatus(value); }).catch(() => { if (!offlineLibraryRef.current) setStatus(null); }); } };
  const loadMore = () => { if (!loadingMore && hasMore) void load(query, nextOffset, true); };

  return (
    <AppPage>
      <AppHeader title={t(locale, 'science')} onBack={onBack} backLabel={t(locale, 'back')} trailing={
        <Pressable accessibilityRole="button" accessibilityLabel={t(locale, 'refresh')} onPress={refresh} style={styles.refreshButton}>
          <Ionicons name="refresh" size={18} color={colors.primary} />
        </Pressable>
      } />

      {selected ? (
        <>
          <Pressable accessibilityRole="button" onPress={() => { beginDetail(); setSelected(null); setArticle(null); setDetailErrorKey(null); }} style={styles.backToList}>
            <Ionicons name="chevron-back" size={17} color={colors.primary} /><Text style={styles.backText}>{t(locale, 'scienceBack')}</Text>
          </Pressable>
          {loadingDetail ? <Loading label={t(locale, 'loading')} /> : detailErrorKey ? <Panel><Body>{t(locale, detailErrorKey)}</Body></Panel> : article ? (
            <ArticleDetail article={article} status={status} locale={locale} serverBaseUrl={serverBaseUrl} onAskAi={onAskAi} />
          ) : null}
        </>
      ) : (
        <>
          <View style={styles.heading}>
            <Title>{t(locale, 'science')}</Title>
            {status ? <Text style={styles.indexed}>{copy(locale, 'nasaLibrary')}: {status.json_articles} / {status.expected_slots}</Text> : indexed > 0 ? <Text style={styles.indexed}>{t(locale, 'scienceArticleCount')}: {indexed}</Text> : null}
            {matched > 0 ? <Text style={styles.indexed}>{t(locale, 'scienceArticleCount')}: {matched}</Text> : null}
          </View>
          <Panel style={styles.searchPanel}>
            <TextInput
              accessibilityLabel={t(locale, 'scienceSearchPlaceholder')}
              value={query}
              onChangeText={setQuery}
              onSubmitEditing={submitSearch}
              returnKeyType="search"
              placeholder={t(locale, 'scienceSearchPlaceholder')}
              placeholderTextColor={colors.faint}
              selectionColor={colors.primary}
              style={styles.searchInput}
            />
            <Pressable accessibilityRole="button" onPress={submitSearch} style={styles.searchButton}>
              <Ionicons name="search" size={19} color="#FFFFFF" />
              <Text style={styles.searchButtonText}>{t(locale, 'scienceSearch')}</Text>
            </Pressable>
          </Panel>

          {status?.missing_slots?.length ? <StatusPill label={copy(locale, 'missingSources') + ': ' + status.missing_slots.join(', ')} tone="warn" /> : null}
          {status && !status.original_pdf_archive_verified ? <StatusPill label={t(locale, 'sciencePdfNotVerified')} tone="warn" /> : null}
          {status && !status.clinical_rules_validated ? <StatusPill label={t(locale, 'scienceRulesNotValidated')} tone="neutral" /> : null}
          {loading && items.length === 0 ? <Loading label={t(locale, 'loading')} /> : items.length === 0 ? (
            errorKey ? <Panel><Body>{t(locale, errorKey)}</Body></Panel> : <Panel><Text style={styles.emptyTitle}>{indexed === 0 ? t(locale, 'noData') : t(locale, 'scienceNoResults')}</Text></Panel>
          ) : <View style={styles.articleList}>
            {errorKey ? <Panel><Body>{t(locale, errorKey)}</Body></Panel> : null}
            {items.map((item) => <ArticleCard key={item.article_id} item={item} onPress={() => { void openArticle(item); }} locale={locale} />)}
            {hasMore ? <Pressable accessibilityRole="button" disabled={loadingMore} onPress={loadMore} style={({ pressed }) => [styles.loadMoreButton, pressed && styles.pressed]}>
              {loadingMore ? <ActivityIndicator color={colors.onAccent} size="small" /> : <Text style={styles.loadMoreText}>{copy(locale, 'loadMore')}</Text>}
            </Pressable> : null}
          </View>}
        </>
      )}
    </AppPage>
  );
}

function ArticleCard({ item, onPress, locale }: { item: ScienceArticleSummary; onPress: () => void; locale: Locale }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  const verification = item.source_claim;
  return <Pressable accessibilityRole="button" onPress={onPress} style={({ pressed }) => [styles.cardPressable, pressed && styles.pressed]}>
    <Panel style={styles.articleCard}>
      <View style={styles.cardTop}><Ionicons name="document-text-outline" size={19} color={colors.primary} /><Text style={styles.category}>{item.category || '—'}</Text></View>
      <Text style={styles.articleTitle}>{item.title}</Text>
      <View style={styles.cardMeta}><Text style={styles.cardMetaText}>{t(locale, 'scienceSections')}: {item.sections}</Text><Text style={styles.cardMetaText}>{t(locale, 'scienceReferences')}: {item.references}</Text></View>
      <StatusPill label={`${t(locale, 'scienceSourceStatus')}: ${verification || 'UNKNOWN'}`} tone={verification === 'VERIFIED' ? 'good' : 'warn'} />
    </Panel>
  </Pressable>;
}

function ArticleDetail({ article, status, locale, serverBaseUrl, onAskAi }: { article: ScienceArticle; status: KnowledgeStatus | null; locale: Locale; serverBaseUrl: string; onAskAi?: (article: ScienceArticleSummary) => void }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  const record = article.source || {};
  const publisher = record.publisher;
  const sourceTitle = record.title;
  const sourceUrl = record.final_url || record.source_url || article.summary.original_url || '';
  const sourceStatus = record.verification_state || article.summary.source_claim;
  const sha = record.content_sha256 || article.summary.original_sha256_claim;
  const sourceNote = t(locale, 'scienceSourceNote');
  const limitations = article.limitations.map(limitationText).filter(Boolean);

  return <View style={styles.detailContent}>
    <View style={styles.detailHeading}>
      <Title size={23}>{article.summary.title}</Title>
      <Text style={styles.category}>{article.summary.category || '—'}</Text>
    </View>

    <Panel style={styles.metadataPanel}>
      <Text style={styles.panelTitle}>{t(locale, 'scienceSourceStatus')}</Text>
      <MetaRow label={t(locale, 'verification')} value={sourceStatus || 'UNKNOWN'} />
      {sourceTitle ? <MetaRow label={t(locale, 'source')} value={sourceTitle} /> : null}
      {publisher ? <MetaRow label={t(locale, 'sciencePublisher')} value={publisher} /> : null}
      {sourceUrl ? <LinkRow label={t(locale, 'scienceOriginalLink')} url={sourceUrl} /> : null}
      {record.retrieved_at_utc ? <MetaRow label={t(locale, 'scienceRetrievedAt')} value={record.retrieved_at_utc} /> : null}
      {record.license_identifier ? <MetaRow label={t(locale, 'scienceLicense')} value={record.license_identifier} /> : null}
      {record.attribution ? <MetaRow label={t(locale, 'scienceAttribution')} value={record.attribution} /> : null}
      {sha ? <MetaRow label={t(locale, 'scienceSha256')} value={sha} selectable /> : null}
      {status && !status.original_pdf_archive_verified ? <Text style={styles.sourceNote}>{t(locale, 'sciencePdfNotVerified')}</Text> : null}
      {status && !status.clinical_rules_validated ? <Text style={styles.sourceNote}>{t(locale, 'scienceRulesNotValidated')}</Text> : null}
      <Text selectable style={styles.sourceNote}>{sourceNote}</Text>
    </Panel>

    {onAskAi && article.sections.length > 0 ? <Pressable accessibilityRole='button' onPress={() => onAskAi(article.summary)} style={styles.askAi}>
      <Ionicons name='sparkles-outline' size={18} color='#FFFFFF' /><Text style={styles.askAiText}>{t(locale, 'scienceAskAi')}</Text><Ionicons name='arrow-forward' size={17} color='#FFFFFF' />
    </Pressable> : null}

    {limitations.length > 0 ? <Panel style={styles.metadataPanel}>
      <Text style={styles.panelTitle}>{copy(locale, 'sourceLimitations')}</Text>
      {limitations.map((item, index) => <Text key={index} style={styles.sourceNote}>• {item}</Text>)}
    </Panel> : null}

    {article.sections.length > 0 ? <View style={styles.sectionList}>
      {article.sections.map((section) => <Panel key={section.section_id} style={styles.contentSection}>
        <Text style={styles.sectionTitle}>{section.heading}</Text>
        <Text selectable style={styles.sectionText}>{section.text_content}</Text>
      </Panel>)}
    </View> : null}

    {article.tables.length > 0 ? <View style={styles.sectionList}>
      <Text style={styles.panelTitle}>{t(locale, 'scienceTables')}</Text>
      {article.tables.map((table) => <Panel key={table.table_id} style={styles.contentSection}>
        <Text style={styles.sectionTitle}>{table.title}</Text>
        {table.rows.map((row, index) => <Text key={`${table.table_id}-${index}`} style={styles.tableRow}>{row.join(' · ')}</Text>)}
        {table.source_anchor ? <Text style={styles.pageAnchor}>{table.source_anchor}</Text> : table.page_number ? <Text style={styles.pageAnchor}>{t(locale, 'sciencePage')} {table.page_number}</Text> : null}
      </Panel>)}
    </View> : null}

    {article.references.length > 0 ? <View style={styles.sectionList}>
      <Text style={styles.panelTitle}>{t(locale, 'scienceReferences')}</Text>
      {article.references.map((reference) => <Panel key={reference.reference_id} style={styles.referencePanel}>
        <Text selectable style={styles.referenceText}>{reference.label}</Text>
        {reference.page_number ? <Text style={styles.pageAnchor}>{t(locale, 'sciencePage')} {reference.page_number}</Text> : null}
        {reference.citation_url ? <LinkRow label={t(locale, 'scienceOriginalLink')} url={reference.citation_url} /> : null}
      </Panel>)}
    </View> : null}

    {article.media.length > 0 ? <View style={styles.sectionList}>
      {article.media.map((entry, index) => <MediaRecord key={String(entry.media_id || index)} entry={entry} articleId={article.summary.article_id} serverBaseUrl={serverBaseUrl} locale={locale} />)}
    </View> : null}
  </View>;
}

function MediaRecord({ entry, articleId, serverBaseUrl, locale }: { entry: Record<string, unknown>; articleId: string; serverBaseUrl: string; locale: Locale }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  const caption = stringValue(entry.caption) || stringValue(entry.alt_text) || stringValue(entry.media_id);
  const url = stringValue(entry.source_url) || stringValue(entry.rights_url);
  const mediaId = stringValue(entry.media_id);
  const imageUrl = serverBaseUrl && mediaId && stringValue(entry.file_path) && entry.usage_review === 'APPROVED'
    ? buildScienceMediaUrl(serverBaseUrl, articleId, mediaId) : '';
  return <Panel style={styles.referencePanel}>
    {imageUrl ? <Image accessibilityLabel={caption || articleId} source={{ uri: imageUrl }} resizeMode="contain" style={styles.medicalImage} /> : null}
    {caption ? <Text style={styles.referenceText}>{caption}</Text> : null}
    {entry.page_number ? <Text style={styles.pageAnchor}>{t(locale, 'sciencePage')} {String(entry.page_number)}</Text> : null}
    {stringValue(entry.license_identifier) ? <MetaRow label={t(locale, 'scienceLicense')} value={stringValue(entry.license_identifier)} /> : null}
    {stringValue(entry.attribution) ? <MetaRow label={t(locale, 'scienceAttribution')} value={stringValue(entry.attribution)} /> : null}
    {url ? <LinkRow label={t(locale, 'scienceOriginalLink')} url={url} /> : null}
  </Panel>;
}

function LinkRow({ label, url }: { label: string; url: string }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  return <View style={styles.metaRow}>
    <Text style={styles.metaLabel}>{label}</Text>
    <Pressable accessibilityRole="link" onPress={() => { void Linking.openURL(url); }} style={styles.linkArea}>
      <Text selectable style={styles.linkText}>{url}</Text>
    </Pressable>
  </View>;
}

function MetaRow({ label, value, selectable = false }: { label: string; value: string; selectable?: boolean }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  return <View style={styles.metaRow}><Text style={styles.metaLabel}>{label}</Text><Text selectable={selectable} style={styles.metaValue}>{value}</Text></View>;
}

function Loading({ label }: { label: string }) {
  const { colors, styles, isDark, appearance, gradient } = useThemedStyles(buildStyles);
  return <View style={styles.loading}><ActivityIndicator color={colors.primary} /><Text style={styles.loadingText}>{label}</Text></View>;
}

function canUseOfflineLibrary(error: unknown): boolean {
  if (error instanceof ApiError) return error.status === 0 || error.status === 408;
  return error instanceof Error && error.message === 'SERVER_URL_MISSING';
}

function errorMessageKey(error: unknown): MessageKey {
  if (!(error instanceof ApiError)) return 'networkError';
  if (error.status === 401) return 'unauthorized';
  if (error.status === 403) return 'forbidden';
  if (error.status === 404) return 'scienceRecordUnavailable';
  if (error.status === 0 || error.status === 408) return 'networkError';
  if (error.status >= 500) return 'scienceUnavailable';
  return 'scienceUnavailable';
}

function stringValue(value: unknown) { return typeof value === 'string' ? value : ''; }
function limitationText(value: unknown): string {
  if (typeof value === 'string') return value;
  if (!value || typeof value !== 'object') return '';
  const row = value as Record<string, unknown>;
  return stringValue(row.text) || stringValue(row.note) || stringValue(row.description);
}

const buildStyles = (colors: ThemeColors) => StyleSheet.create({
  refreshButton: { width: 38, height: 38, alignItems: 'center', justifyContent: 'center' },
  heading: { gap: 6, paddingTop: 8 },
  indexed: { color: colors.muted, fontSize: 12, fontWeight: '700' },
  searchPanel: { flexDirection: 'row', gap: 8, padding: 10 },
  searchInput: { flex: 1, minWidth: 0, minHeight: 45, paddingHorizontal: 12, color: colors.text, fontSize: 14, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.card, borderRadius: 13 },
  searchButton: { minHeight: 45, borderRadius: 13, paddingHorizontal: 12, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 5, backgroundColor: colors.primary },
  searchButtonText: { color: '#FFFFFF', fontSize: 11, fontWeight: '900' },
  articleList: { gap: 9 },
  loadMoreButton: { minHeight: 44, borderRadius: 12, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: colors.primary },
  loadMoreText: { color: '#FFFFFF', fontSize: 13, fontWeight: '800' },
  cardPressable: { borderRadius: 20 },
  articleCard: { gap: 9 },
  cardTop: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  category: { color: colors.muted, fontSize: 11, fontWeight: '800', textTransform: 'uppercase', letterSpacing: 0.4 },
  articleTitle: { color: colors.text, fontSize: 17, fontWeight: '800', lineHeight: 22 },
  cardMeta: { flexDirection: 'row', gap: 14 },
  cardMetaText: { color: colors.muted, fontSize: 11, fontWeight: '700' },
  emptyTitle: { color: colors.muted, fontSize: 14, fontWeight: '700' },
  loading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10, padding: 22 },
  loadingText: { color: colors.muted, fontSize: 13, fontWeight: '700' },
  backToList: { alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: 2, minHeight: 34, paddingRight: 8 },
  backText: { color: colors.primary, fontSize: 12, fontWeight: '800' },
  detailContent: { gap: 12, paddingBottom: 16 },
  detailHeading: { gap: 6, paddingTop: 4 },
  metadataPanel: { gap: 10 },
  panelTitle: { color: colors.text, fontSize: 15, fontWeight: '900' },
  metaRow: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10, borderTopWidth: 1, borderTopColor: colors.border, paddingTop: 9 },
  metaLabel: { width: '34%', color: colors.muted, fontSize: 10, fontWeight: '800' },
  metaValue: { flex: 1, color: colors.text, fontSize: 11, lineHeight: 16, textAlign: 'right' },
  linkArea: { flex: 1 },
  linkText: { color: colors.primary, fontSize: 11, lineHeight: 16, textAlign: 'right', textDecorationLine: 'underline' },
  sourceNote: { color: colors.muted, fontSize: 10, lineHeight: 15 },
  askAi: { minHeight: 48, backgroundColor: colors.primary, borderRadius: 13, alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 8 },
  askAiText: { color: '#FFFFFF', fontWeight: '800', fontSize: 12 },
  sectionList: { gap: 8 },
  contentSection: { gap: 8 },
  sectionTitle: { color: colors.text, fontSize: 14, fontWeight: '900' },
  sectionText: { color: colors.text, fontSize: 13, lineHeight: 19 },
  tableRow: { color: colors.text, fontSize: 11, lineHeight: 16 },
  pageAnchor: { color: colors.muted, fontSize: 10, fontWeight: '700' },
  referencePanel: { gap: 7 },
  medicalImage: { width: '100%', height: 220, borderRadius: 12, backgroundColor: colors.cardSoft },
  referenceText: { color: colors.text, fontSize: 12, lineHeight: 17 },
  pressed: { opacity: 0.82, transform: [{ scale: 0.99 }] },
});


