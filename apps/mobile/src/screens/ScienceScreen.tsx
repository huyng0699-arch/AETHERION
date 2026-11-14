import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Linking, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Locale } from '../types';
import { MessageKey, t } from '../i18n';
import { colors } from '../theme';
import { ApiError } from '../api/client';
import { getKnowledgeStatus, getScienceArticle, getScienceSources, searchScienceArticles, KnowledgeStatus, ScienceArticle, ScienceArticleSummary, ScienceSource } from '../api/science';
import { AppHeader, AppPage, Body, Panel, StatusPill, Title } from '../components/ui';

export function ScienceScreen({ locale, onBack }: { locale: Locale; onBack: () => void }) {
  const [query, setQuery] = useState('');
  const [items, setItems] = useState<ScienceArticleSummary[]>([]);
  const [indexed, setIndexed] = useState(0);
  const [status, setStatus] = useState<KnowledgeStatus | null>(null);
  const [sources, setSources] = useState<ScienceSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [errorKey, setErrorKey] = useState<MessageKey | null>(null);
  const [detailErrorKey, setDetailErrorKey] = useState<MessageKey | null>(null);
  const [selected, setSelected] = useState<ScienceArticleSummary | null>(null);
  const [article, setArticle] = useState<ScienceArticle | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const load = useCallback(async (term: string) => {
    setLoading(true);
    setErrorKey(null);
    try {
      const result = await searchScienceArticles(term, 30);
      setItems(Array.isArray(result.items) ? result.items : []);
      setIndexed(Number.isFinite(result.indexed) ? result.indexed : 0);
    } catch (error) {
      setItems([]);
      setIndexed(0);
      setErrorKey(errorMessageKey(error));
    }
    const [statusResult, sourcesResult] = await Promise.allSettled([getKnowledgeStatus(), getScienceSources(200)]);
    setStatus(statusResult.status === 'fulfilled' ? statusResult.value : null);
    setSources(sourcesResult.status === 'fulfilled' && Array.isArray(sourcesResult.value.items) ? sourcesResult.value.items : []);
    setLoading(false);
  }, []);

  useEffect(() => { void load(''); }, [load, refreshKey]);

  const openArticle = async (summary: ScienceArticleSummary) => {
    setSelected(summary);
    setArticle(null);
    setDetailErrorKey(null);
    setLoadingDetail(true);
    try {
      setArticle(await getScienceArticle(summary.article_id));
    } catch (error) {
      setDetailErrorKey(errorMessageKey(error));
    } finally {
      setLoadingDetail(false);
    }
  };

  const sourceByArticle = useMemo(() => new Map(sources.filter((source) => source.article_id).map((source) => [source.article_id as string, source])), [sources]);

  const submitSearch = () => { setSelected(null); setArticle(null); void load(query); };
  const refresh = () => { if (selected) void openArticle(selected); else { setSelected(null); setArticle(null); setRefreshKey((value) => value + 1); } };

  return (
    <AppPage>
      <AppHeader title={t(locale, 'science')} onBack={onBack} backLabel={t(locale, 'back')} trailing={
        <Pressable accessibilityRole="button" accessibilityLabel={t(locale, 'refresh')} onPress={refresh} style={styles.refreshButton}>
          <Ionicons name="refresh" size={18} color={colors.cyan} />
        </Pressable>
      } />

      {selected ? (
        <>
          <Pressable accessibilityRole="button" onPress={() => { setSelected(null); setArticle(null); setDetailErrorKey(null); }} style={styles.backToList}>
            <Ionicons name="chevron-back" size={17} color={colors.cyan} /><Text style={styles.backText}>{t(locale, 'scienceBack')}</Text>
          </Pressable>
          {loadingDetail ? <Loading label={t(locale, 'loading')} /> : detailErrorKey ? <Panel><Body>{t(locale, detailErrorKey)}</Body></Panel> : article ? (
            <ArticleDetail article={article} source={sourceByArticle.get(article.summary.article_id)} status={status} locale={locale} />
          ) : null}
        </>
      ) : (
        <>
          <View style={styles.heading}><Title>{t(locale, 'science')}</Title>{indexed > 0 ? <Text style={styles.indexed}>{t(locale, 'scienceArticleCount')}: {indexed}</Text> : null}</View>
          <Panel style={styles.searchPanel}>
            <TextInput
              accessibilityLabel={t(locale, 'scienceSearchPlaceholder')}
              value={query}
              onChangeText={setQuery}
              onSubmitEditing={submitSearch}
              returnKeyType="search"
              placeholder={t(locale, 'scienceSearchPlaceholder')}
              placeholderTextColor={colors.faint}
              selectionColor={colors.cyan}
              style={styles.searchInput}
            />
            <Pressable accessibilityRole="button" onPress={submitSearch} style={styles.searchButton}>
              <Ionicons name="search" size={19} color="#FFFFFF" />
              <Text style={styles.searchButtonText}>{t(locale, 'scienceSearch')}</Text>
            </Pressable>
          </Panel>

          {status && !status.original_pdf_archive_verified ? <StatusPill label={t(locale, 'sciencePdfNotVerified')} tone="warn" /> : null}
          {status && !status.clinical_rules_validated ? <StatusPill label={t(locale, 'scienceRulesNotValidated')} tone="neutral" /> : null}
          {errorKey ? <Panel><Body>{t(locale, errorKey)}</Body></Panel> : loading ? <Loading label={t(locale, 'loading')} /> : items.length === 0 ? (
            <Panel><Text style={styles.emptyTitle}>{indexed === 0 ? t(locale, 'noData') : t(locale, 'scienceNoResults')}</Text></Panel>
          ) : <View style={styles.articleList}>{items.map((item) => <ArticleCard key={item.article_id} item={item} source={sourceByArticle.get(item.article_id)} onPress={() => { void openArticle(item); }} locale={locale} />)}</View>}
        </>
      )}
    </AppPage>
  );
}

function ArticleCard({ item, source, onPress, locale }: { item: ScienceArticleSummary; source?: ScienceSource; onPress: () => void; locale: Locale }) {
  const verification = source?.verification_status || item.source_claim;
  return <Pressable accessibilityRole="button" onPress={onPress} style={({ pressed }) => [styles.cardPressable, pressed && styles.pressed]}>
    <Panel style={styles.articleCard}>
      <View style={styles.cardTop}><Ionicons name="document-text-outline" size={19} color={colors.cyan} /><Text style={styles.category}>{item.category || '—'}</Text></View>
      <Text style={styles.articleTitle}>{item.title}</Text>
      <View style={styles.cardMeta}><Text style={styles.cardMetaText}>{t(locale, 'scienceSections')}: {item.sections}</Text><Text style={styles.cardMetaText}>{t(locale, 'scienceReferences')}: {item.references}</Text></View>
      <StatusPill label={`${t(locale, 'scienceSourceStatus')}: ${verification || 'UNKNOWN'}`} tone={verification === 'VERIFIED' ? 'good' : 'warn'} />
    </Panel>
  </Pressable>;
}

function ArticleDetail({ article, source, status, locale }: { article: ScienceArticle; source?: ScienceSource; status: KnowledgeStatus | null; locale: Locale }) {
  const record = article.source || {};
  const publisher = source?.publisher || record.publisher;
  const sourceTitle = source?.title || record.title;
  const sourceUrl = record.final_url || record.source_url || source?.source_uri || article.summary.original_url || '';
  const sourceStatus = source?.verification_status || record.verification_state || article.summary.source_claim;
  const sha = source?.content_sha256 || record.content_sha256 || article.summary.original_sha256_claim;
  const sourceNote = t(locale, 'scienceSourceNote');

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
      {(source?.license || record.license_identifier) ? <MetaRow label={t(locale, 'scienceLicense')} value={source?.license || record.license_identifier || ''} /> : null}
      {(source?.attribution || record.attribution) ? <MetaRow label={t(locale, 'scienceAttribution')} value={source?.attribution || record.attribution || ''} /> : null}
      {sha ? <MetaRow label={t(locale, 'scienceSha256')} value={sha} selectable /> : null}
      {status && !status.original_pdf_archive_verified ? <Text style={styles.sourceNote}>{t(locale, 'sciencePdfNotVerified')}</Text> : null}
      {status && !status.clinical_rules_validated ? <Text style={styles.sourceNote}>{t(locale, 'scienceRulesNotValidated')}</Text> : null}
      <Text selectable style={styles.sourceNote}>{sourceNote}</Text>
    </Panel>

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
      {article.media.map((entry, index) => <MediaRecord key={String(entry.media_id || index)} entry={entry} locale={locale} />)}
    </View> : null}
  </View>;
}

function MediaRecord({ entry, locale }: { entry: Record<string, unknown>; locale: Locale }) {
  const caption = stringValue(entry.caption) || stringValue(entry.alt_text) || stringValue(entry.media_id);
  const url = stringValue(entry.source_url) || stringValue(entry.rights_url);
  return <Panel style={styles.referencePanel}>
    {caption ? <Text style={styles.referenceText}>{caption}</Text> : null}
    {entry.page_number ? <Text style={styles.pageAnchor}>{t(locale, 'sciencePage')} {String(entry.page_number)}</Text> : null}
    {stringValue(entry.license_identifier) ? <MetaRow label={t(locale, 'scienceLicense')} value={stringValue(entry.license_identifier)} /> : null}
    {stringValue(entry.attribution) ? <MetaRow label={t(locale, 'scienceAttribution')} value={stringValue(entry.attribution)} /> : null}
    {url ? <LinkRow label={t(locale, 'scienceOriginalLink')} url={url} /> : null}
  </Panel>;
}

function LinkRow({ label, url }: { label: string; url: string }) {
  return <View style={styles.metaRow}>
    <Text style={styles.metaLabel}>{label}</Text>
    <Pressable accessibilityRole="link" onPress={() => { void Linking.openURL(url); }} style={styles.linkArea}>
      <Text selectable style={styles.linkText}>{url}</Text>
    </Pressable>
  </View>;
}

function MetaRow({ label, value, selectable = false }: { label: string; value: string; selectable?: boolean }) {
  return <View style={styles.metaRow}><Text style={styles.metaLabel}>{label}</Text><Text selectable={selectable} style={styles.metaValue}>{value}</Text></View>;
}

function Loading({ label }: { label: string }) {
  return <View style={styles.loading}><ActivityIndicator color={colors.cyan} /><Text style={styles.loadingText}>{label}</Text></View>;
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

const styles = StyleSheet.create({
  refreshButton: { width: 38, height: 38, alignItems: 'center', justifyContent: 'center' },
  heading: { gap: 6, paddingTop: 8 },
  indexed: { color: colors.muted, fontSize: 12, fontWeight: '700' },
  searchPanel: { flexDirection: 'row', gap: 8, padding: 10 },
  searchInput: { flex: 1, minWidth: 0, minHeight: 45, paddingHorizontal: 12, color: colors.text, fontSize: 14, borderWidth: 1, borderColor: colors.border, backgroundColor: '#FFFFFF', borderRadius: 13 },
  searchButton: { minHeight: 45, borderRadius: 13, paddingHorizontal: 12, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 5, backgroundColor: colors.cyan },
  searchButtonText: { color: '#FFFFFF', fontSize: 11, fontWeight: '900' },
  articleList: { gap: 9 },
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
  backText: { color: colors.cyan, fontSize: 12, fontWeight: '800' },
  detailContent: { gap: 12, paddingBottom: 16 },
  detailHeading: { gap: 6, paddingTop: 4 },
  metadataPanel: { gap: 10 },
  panelTitle: { color: colors.text, fontSize: 15, fontWeight: '900' },
  metaRow: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10, borderTopWidth: 1, borderTopColor: colors.border, paddingTop: 9 },
  metaLabel: { width: '34%', color: colors.muted, fontSize: 10, fontWeight: '800' },
  metaValue: { flex: 1, color: colors.text, fontSize: 11, lineHeight: 16, textAlign: 'right' },
  linkArea: { flex: 1 },
  linkText: { color: colors.cyan, fontSize: 11, lineHeight: 16, textAlign: 'right', textDecorationLine: 'underline' },
  sourceNote: { color: colors.muted, fontSize: 10, lineHeight: 15 },
  sectionList: { gap: 8 },
  contentSection: { gap: 8 },
  sectionTitle: { color: colors.text, fontSize: 14, fontWeight: '900' },
  sectionText: { color: colors.text, fontSize: 13, lineHeight: 19 },
  tableRow: { color: colors.text, fontSize: 11, lineHeight: 16 },
  pageAnchor: { color: colors.muted, fontSize: 10, fontWeight: '700' },
  referencePanel: { gap: 7 },
  referenceText: { color: colors.text, fontSize: 12, lineHeight: 17 },
  pressed: { opacity: 0.82, transform: [{ scale: 0.99 }] },
});
