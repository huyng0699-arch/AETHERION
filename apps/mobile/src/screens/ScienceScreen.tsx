import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Image, Linking, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { getKnowledgeStatus, getNasaConditions, getScienceArticle, KnowledgeStatus, NasaCondition, NasaConditionsResult, ScienceArticle, ScienceArticleSummary, searchScienceArticles } from '../api/science';
import { AppHeader, AppPage, Body, Panel, Title } from '../components/ui';
import { useRequestGate } from '../hooks/useRequestGate';
import { t } from '../i18n';
import { ThemeColors, useThemedStyles } from '../theme';
import { Locale } from '../types';

type ViewMode = 'conditions' | 'documents';
type Selection = { kind: 'document'; id: string; title: string } | { kind: 'condition'; condition: NasaCondition };

export function ScienceScreen({ locale, onBack, onAskAi }: {
  locale: Locale;
  onBack: () => void;
  onAskAi?: (article: ScienceArticleSummary) => void;
}) {
  const { colors, styles } = useThemedStyles(buildStyles);
  const isVi = locale === 'vi';
  const [mode, setMode] = useState<ViewMode>('conditions');
  const [query, setQuery] = useState('');
  const [conditions, setConditions] = useState<NasaConditionsResult | null>(null);
  const [documents, setDocuments] = useState<ScienceArticleSummary[] | null>(null);
  const [status, setStatus] = useState<KnowledgeStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [article, setArticle] = useState<ScienceArticle | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const beginLoad = useRequestGate();
  const beginDetail = useRequestGate();

  const load = useCallback(async () => {
    const current = beginLoad();
    setLoading(true);
    const [conditionResult, articleResult, statusResult] = await Promise.allSettled([
      getNasaConditions(), searchScienceArticles('', 200), getKnowledgeStatus(),
    ]);
    if (!current()) return;
    const conditionData = conditionResult.status === 'fulfilled' && Array.isArray(conditionResult.value.items)
      ? conditionResult.value : null;
    const articleData = articleResult.status === 'fulfilled' && Array.isArray(articleResult.value.items)
      ? articleResult.value.items : null;
    setConditions(conditionData);
    setDocuments(articleData);
    setStatus(statusResult.status === 'fulfilled' ? statusResult.value : null);
    setMode(previous => previous === 'conditions' && !conditionData && articleData ? 'documents' : previous);
    setLoading(false);
  }, [beginLoad]);

  useEffect(() => { void load(); }, [load, refreshKey]);

  const openDocument = useCallback(async (id: string, title: string) => {
    const current = beginDetail();
    setSelection({ kind: 'document', id, title });
    setArticle(null);
    setDetailError(false);
    setDetailLoading(true);
    try {
      const result = await getScienceArticle(id);
      if (current()) setArticle(result);
    } catch {
      if (current()) setDetailError(true);
    } finally {
      if (current()) setDetailLoading(false);
    }
  }, [beginDetail]);

  const goToList = () => { beginDetail(); setSelection(null); setArticle(null); setDetailError(false); };
  const goBack = () => selection ? goToList() : onBack();
  const search = query.trim().toLocaleLowerCase();
  const visibleConditions = useMemo(() => (conditions?.items || []).filter(item =>
    `${item.title} ${item.condition_id}`.toLocaleLowerCase().includes(search)), [conditions, search]);
  const visibleDocuments = useMemo(() => (documents || []).filter(item =>
    `${item.title} ${item.category} ${item.article_id}`.toLocaleLowerCase().includes(search)), [documents, search]);
  const refresh = () => {
    if (selection?.kind === 'document') void openDocument(selection.id, selection.title);
    else { goToList(); setRefreshKey(value => value + 1); }
  };

  return <AppPage key={selection ? 'reader' : 'library'}>
    <AppHeader title={t(locale, 'science')} onBack={goBack} backLabel={t(locale, 'back')} trailing={
      <Pressable accessibilityRole="button" accessibilityLabel={t(locale, 'refresh')} onPress={refresh} style={styles.refreshButton}>
        <Ionicons name="refresh" size={19} color={colors.cyan} />
      </Pressable>
    } />

    {selection?.kind === 'document' ? (
      <>
        <BackToList locale={locale} onPress={goToList} />
        {detailLoading ? <Loading label={t(locale, 'loading')} /> : detailError || !article ?
          <Panel style={styles.notice}><Body>{t(locale, 'scienceRecordUnavailable')}</Body><Retry locale={locale} onPress={refresh} /></Panel> :
          <ArticleDetail key={article.summary.article_id} article={article} status={status} locale={locale} onAskAi={onAskAi} />}
      </>
    ) : selection?.kind === 'condition' ? (
      <>
        <BackToList locale={locale} onPress={goToList} />
        <ConditionDetail condition={selection.condition} locale={locale} />
      </>
    ) : (
      <>
        <LinearGradient colors={['#171D43', '#30245F', '#514085']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
          <View style={styles.heroTop}>
            <Text style={styles.heroEyebrow}>NASA / RESEARCH LIBRARY</Text>
            <Ionicons name="planet-outline" size={23} color="#DAD5FF" />
          </View>
          <Text style={styles.heroTitle}>{isVi ? 'Thư viện y học' : 'Medical library'}</Text>
          <Text style={styles.heroSub}>{isVi ? 'Dữ liệu khoa học cho chuyến bay vũ trụ' : 'Spaceflight health research'}</Text>
          <View style={styles.heroStats}>
            <View><Text style={styles.heroNumber}>{conditions?.total ?? '—'}</Text><Text style={styles.heroLabel}>{isVi ? 'ĐIỀU KIỆN' : 'CONDITIONS'}</Text></View>
            <View style={styles.heroDivider} />
            <View><Text style={styles.heroNumber}>{status?.json_articles ?? documents?.length ?? '—'}</Text><Text style={styles.heroLabel}>{isVi ? 'TÀI LIỆU' : 'DOCUMENTS'}</Text></View>
          </View>
        </LinearGradient>

        <View style={styles.search}>
          <Ionicons name="search-outline" size={19} color={colors.muted} />
          <TextInput accessibilityLabel={isVi ? 'Tìm trong thư viện' : 'Search the library'} value={query} onChangeText={setQuery}
            placeholder={isVi ? 'Tìm tình trạng hoặc tài liệu' : 'Search conditions or documents'} placeholderTextColor={colors.faint}
            selectionColor={colors.cyan} returnKeyType="search" style={styles.searchInput} />
          {query ? <Pressable accessibilityRole="button" accessibilityLabel={isVi ? 'Xóa tìm kiếm' : 'Clear search'} onPress={() => setQuery('')}><Ionicons name="close-circle" size={19} color={colors.muted} /></Pressable> : null}
        </View>

        <View accessibilityRole="tablist" style={styles.tabs}>
          <Tab label={isVi ? 'Tình trạng' : 'Conditions'} count={conditions?.total} selected={mode === 'conditions'} onPress={() => setMode('conditions')} />
          <Tab label={isVi ? 'Tài liệu' : 'Documents'} count={status?.json_articles ?? documents?.length} selected={mode === 'documents'} onPress={() => setMode('documents')} />
        </View>

        {loading ? <Loading label={t(locale, 'loading')} /> : mode === 'conditions' ? (
          !conditions ? <Unavailable locale={locale} onRetry={refresh} /> : visibleConditions.length === 0 ? <Empty locale={locale} /> :
          <Panel style={styles.list}>{visibleConditions.map((item, index) => <ListRow key={item.condition_id}
            title={item.title} subtitle={item.condition_id} detail={item.article_id ? (isVi ? 'Có tài liệu' : 'Document available') : (isVi ? 'Nguồn NASA' : 'NASA source')}
            last={index === visibleConditions.length - 1} icon="medical-outline" onPress={() => {
              if (item.article_id) void openDocument(item.article_id, item.title);
              else setSelection({ kind: 'condition', condition: item });
            }} />)}</Panel>
        ) : !documents ? <Unavailable locale={locale} onRetry={refresh} /> : visibleDocuments.length === 0 ? <Empty locale={locale} /> :
          <Panel style={styles.list}>{visibleDocuments.map((item, index) => <ListRow key={item.article_id}
            title={item.title} subtitle={item.article_id} detail={item.category} last={index === visibleDocuments.length - 1}
            icon="document-text-outline" onPress={() => { void openDocument(item.article_id, item.title); }} />)}</Panel>}

        {conditions?.source_url ? <Pressable accessibilityRole="link" onPress={() => openExternal(conditions.source_url)} style={styles.indexLink}>
          <Text style={styles.indexLinkText}>{isVi ? 'Xem danh mục gốc của NASA' : 'View NASA source index'}</Text><Ionicons name="open-outline" size={14} color={colors.cyan} />
        </Pressable> : null}
      </>
    )}
  </AppPage>;
}

function Tab({ label, count, selected, onPress }: { label: string; count?: number; selected: boolean; onPress: () => void }) {
  const { styles } = useThemedStyles(buildStyles);
  return <Pressable accessibilityRole="tab" accessibilityState={{ selected }} onPress={onPress} style={[styles.tab, selected && styles.selectedTab]}>
    <Text style={[styles.tabText, selected && styles.selectedTabText]}>{label}{typeof count === 'number' ? `  ${count}` : ''}</Text>
  </Pressable>;
}

function ListRow({ title, subtitle, detail, last, icon, onPress }: {
  title: string; subtitle: string; detail: string; last: boolean; icon: keyof typeof Ionicons.glyphMap; onPress: () => void;
}) {
  const { colors, styles } = useThemedStyles(buildStyles);
  return <Pressable accessibilityRole="button" onPress={onPress} style={({ pressed }) => [styles.listRow, !last && styles.rowBorder, pressed && styles.pressed]}>
    <View style={styles.rowIcon}><Ionicons name={icon} size={19} color={colors.cyan} /></View>
    <View style={styles.rowBody}><Text numberOfLines={2} style={styles.rowTitle}>{title}</Text><Text numberOfLines={1} style={styles.rowMeta}>{subtitle}  ·  {detail}</Text></View>
    <Ionicons name="chevron-forward" size={17} color={colors.faint} />
  </Pressable>;
}

function ConditionDetail({ condition, locale }: { condition: NasaCondition; locale: Locale }) {
  const { colors, styles } = useThemedStyles(buildStyles);
  const isVi = locale === 'vi';
  return <>
    <Text style={styles.eyebrow}>NASA / {condition.condition_id}</Text>
    <Title size={25}>{condition.title}</Title>
    <Panel style={styles.notice}>
      <Text style={styles.detailTitle}>{isVi ? 'Nguồn NASA' : 'NASA source'}</Text>
      <Body>{isVi ? 'Mục này có trong danh mục NASA. Tài liệu chi tiết chưa được liên kết trong kho.' : 'This condition is listed by NASA. A detailed document is not linked in this archive.'}</Body>
      <Text style={styles.sourceNote}>{isVi ? `Trang PDF ${condition.source_page}` : `PDF page ${condition.source_page}`}</Text>
      <Pressable accessibilityRole="link" onPress={() => openExternal(condition.source_url)} style={styles.inlineLink}>
        <Text style={styles.inlineLinkText}>{isVi ? 'Mở nguồn NASA' : 'Open NASA source'}</Text><Ionicons name="open-outline" size={16} color={colors.cyan} />
      </Pressable>
    </Panel>
  </>;
}

function ArticleDetail({ article, status, locale, onAskAi }: {
  article: ScienceArticle; status: KnowledgeStatus | null; locale: Locale; onAskAi?: (article: ScienceArticleSummary) => void;
}) {
  const { colors, styles } = useThemedStyles(buildStyles);
  const isVi = locale === 'vi';
  const sections = article.sections || [];
  const [openSection, setOpenSection] = useState<string | null>(sections[0]?.section_id || null);
  const [showSource, setShowSource] = useState(false);
  const [showReferences, setShowReferences] = useState(false);
  const [showTables, setShowTables] = useState(false);
  const [showMedia, setShowMedia] = useState(false);
  const source = article.source || {};
  const sourceUrl = source.final_url || source.source_url || article.summary.original_url || '';
  return <View style={styles.reader}>
    <Text style={styles.eyebrow}>NASA / {article.summary.article_id}</Text>
    <Title size={25}>{article.summary.title}</Title>
    <Text style={styles.readerCategory}>{article.summary.category}</Text>

    <View style={styles.sourceBar}>
      <View style={styles.sourceIcon}><Ionicons name="shield-checkmark-outline" size={19} color={colors.cyan} /></View>
      <View style={styles.rowBody}><Text style={styles.sourceBarTitle}>{source.publisher || 'NASA'}</Text><Text style={styles.rowMeta}>{isVi ? 'Nguồn tài liệu' : 'Source record'}</Text></View>
      <Pressable accessibilityRole="button" accessibilityState={{ expanded: showSource }} onPress={() => setShowSource(value => !value)} style={styles.smallButton}>
        <Text style={styles.smallButtonText}>{showSource ? (isVi ? 'Ẩn' : 'Hide') : (isVi ? 'Chi tiết' : 'Details')}</Text>
      </Pressable>
    </View>
    {showSource ? <Panel style={styles.notice}>
      {source.title ? <Meta label={isVi ? 'Nguồn' : 'Source'} value={source.title} /> : null}
      {source.retrieved_at_utc ? <Meta label={isVi ? 'Truy xuất' : 'Retrieved'} value={source.retrieved_at_utc} /> : null}
      {source.attribution ? <Meta label={isVi ? 'Ghi công' : 'Attribution'} value={source.attribution} /> : null}
      {source.license_identifier ? <Meta label={isVi ? 'Giấy phép' : 'License'} value={source.license_identifier} /> : null}
      {source.verification_state ? <Meta label={isVi ? 'Trạng thái kho' : 'Archive status'} value={source.verification_state} /> : null}
      {source.content_sha256 ? <Meta label="SHA-256" value={source.content_sha256} /> : null}
      {sourceUrl ? <Pressable accessibilityRole="link" onPress={() => openExternal(sourceUrl)} style={styles.inlineLink}><Text style={styles.inlineLinkText}>{isVi ? 'Mở tài liệu gốc' : 'Open original source'}</Text><Ionicons name="open-outline" size={16} color={colors.cyan} /></Pressable> : null}
      {status && !status.original_pdf_archive_verified ? <Text style={styles.sourceNote}>{t(locale, 'scienceSourceNote')}</Text> : null}
      {article.source_notes ? <Text style={styles.sourceNote}>{article.source_notes}</Text> : null}
    </Panel> : null}

    {onAskAi && sections.length > 0 ? <Pressable accessibilityRole="button" onPress={() => onAskAi(article.summary)} style={({ pressed }) => [styles.askAi, pressed && styles.pressed]}>
      <Ionicons name="sparkles-outline" size={18} color={colors.onAccent} /><Text style={styles.askAiText}>{t(locale, 'scienceAskAi')}</Text><Ionicons name="arrow-forward" size={17} color={colors.onAccent} />
    </Pressable> : null}

    <Text style={styles.groupHeading}>{isVi ? 'NỘI DUNG' : 'CONTENTS'}</Text>
    {sections.length ? sections.map((section, index) => <Panel key={section.section_id} style={styles.sectionCard}>
      <Pressable accessibilityRole="button" accessibilityState={{ expanded: openSection === section.section_id }} onPress={() => setOpenSection(current => current === section.section_id ? null : section.section_id)} style={styles.sectionHeader}>
        <Text style={styles.sectionIndex}>{String(index + 1).padStart(2, '0')}</Text><Text style={styles.sectionTitle}>{section.heading || (isVi ? 'Nội dung' : 'Section')}</Text>
        <Ionicons name={openSection === section.section_id ? 'remove' : 'add'} size={18} color={colors.cyan} />
      </Pressable>
      {openSection === section.section_id ? <>
        {section.source_anchor || section.page_start ? <Text style={styles.sourceNote}>{section.source_anchor || `${t(locale, 'sciencePage')} ${section.page_start}`}</Text> : null}
        <Text selectable style={styles.sectionText}>{section.text_content}</Text>
      </> : null}
    </Panel>) : <Panel><Body>{t(locale, 'scienceMetadataOnlyDetail')}</Body></Panel>}

    {(article.tables || []).length ? <Panel style={styles.sectionCard}>
      <Pressable accessibilityRole="button" accessibilityState={{ expanded: showTables }} onPress={() => setShowTables(value => !value)} style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>{t(locale, 'scienceTables')} ({article.tables.length})</Text><Ionicons name={showTables ? 'remove' : 'add'} size={18} color={colors.cyan} />
      </Pressable>
      {showTables ? article.tables.map(table => <View key={table.table_id} style={styles.expandedGroup}>
        <Text style={styles.detailTitle}>{table.title}</Text>{table.rows.map((row, index) => <Text key={`${table.table_id}-${index}`} selectable style={styles.tableText}>{row.join('  |  ')}</Text>)}
        {table.source_anchor || table.page_number ? <Text style={styles.sourceNote}>{table.source_anchor || `${t(locale, 'sciencePage')} ${table.page_number}`}</Text> : null}
      </View>) : null}
    </Panel> : null}

    {(article.references || []).length ? <Panel style={styles.sectionCard}>
      <Pressable accessibilityRole="button" accessibilityState={{ expanded: showReferences }} onPress={() => setShowReferences(value => !value)} style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>{t(locale, 'scienceReferences')} ({article.references.length})</Text><Ionicons name={showReferences ? 'remove' : 'add'} size={18} color={colors.cyan} />
      </Pressable>
      {showReferences ? article.references.map(reference => <View key={reference.reference_id} style={styles.reference}>
        <Text selectable style={styles.referenceText}>{reference.label}</Text>
        {reference.page_number ? <Text style={styles.sourceNote}>{t(locale, 'sciencePage')} {reference.page_number}</Text> : null}
        {reference.citation_url ? <Pressable accessibilityRole="link" onPress={() => openExternal(reference.citation_url || '')}><Text style={styles.inlineLinkText}>{isVi ? 'Mở nguồn' : 'Open source'}</Text></Pressable> : null}
      </View>) : null}
    </Panel> : null}
    {(article.media || []).length ? <Panel style={styles.sectionCard}>
      <Pressable accessibilityRole="button" accessibilityState={{ expanded: showMedia }} onPress={() => setShowMedia(value => !value)} style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>{isVi ? 'Hình ảnh' : 'Illustrations'} ({article.media.length})</Text><Ionicons name={showMedia ? 'remove' : 'add'} size={18} color={colors.cyan} />
      </Pressable>
      {showMedia ? article.media.map((entry, index) => <MediaItem key={String(entry.media_id || index)} entry={entry} locale={locale} />) : null}
    </Panel> : null}
    {sourceUrl ? <Pressable accessibilityRole="link" onPress={() => openExternal(sourceUrl)} style={styles.indexLink}><Text style={styles.indexLinkText}>{isVi ? 'Mở tài liệu gốc NASA' : 'Open original NASA document'}</Text><Ionicons name="open-outline" size={14} color={colors.cyan} /></Pressable> : null}
  </View>;
}

function MediaItem({ entry, locale }: { entry: Record<string, unknown>; locale: Locale }) {
  const { styles } = useThemedStyles(buildStyles);
  const [imageFailed, setImageFailed] = useState(false);
  const imageUrl = typeof entry.source_url === 'string' && /^https:\/\//i.test(entry.source_url) ? entry.source_url : '';
  const rightsUrl = typeof entry.rights_url === 'string' ? entry.rights_url : imageUrl;
  const caption = typeof entry.caption === 'string' ? entry.caption : '';
  const credit = typeof entry.attribution === 'string' ? entry.attribution : '';
  const alt = typeof entry.alt_text === 'string' ? entry.alt_text : caption;
  return <View style={styles.expandedGroup}>
    {imageUrl && !imageFailed ? <Image source={{ uri: imageUrl }} accessibilityLabel={alt} resizeMode="contain" style={styles.illustration} onError={() => setImageFailed(true)} /> : null}
    {caption ? <Text style={styles.referenceText}>{caption}</Text> : null}
    {entry.page_number ? <Text style={styles.sourceNote}>{t(locale, 'sciencePage')} {String(entry.page_number)}</Text> : null}
    {credit ? <Text selectable style={styles.sourceNote}>{credit}</Text> : null}
    {rightsUrl ? <Pressable accessibilityRole="link" onPress={() => openExternal(rightsUrl)}><Text style={styles.inlineLinkText}>{locale === 'vi' ? 'Nguồn và giấy phép' : 'Source and license'}</Text></Pressable> : null}
  </View>;
}

function BackToList({ locale, onPress }: { locale: Locale; onPress: () => void }) {
  const { colors, styles } = useThemedStyles(buildStyles);
  return <Pressable accessibilityRole="button" onPress={onPress} style={styles.backToList}><Ionicons name="chevron-back" size={16} color={colors.cyan} /><Text style={styles.backText}>{locale === 'vi' ? 'Thư viện' : 'Library'}</Text></Pressable>;
}

function Meta({ label, value }: { label: string; value: string }) {
  const { styles } = useThemedStyles(buildStyles);
  return <View style={styles.metaRow}><Text style={styles.metaLabel}>{label}</Text><Text selectable style={styles.metaValue}>{value}</Text></View>;
}

function Loading({ label }: { label: string }) {
  const { colors, styles } = useThemedStyles(buildStyles);
  return <View style={styles.loading}><ActivityIndicator color={colors.cyan} /><Text style={styles.loadingText}>{label}</Text></View>;
}

function Retry({ locale, onPress }: { locale: Locale; onPress: () => void }) {
  const { styles } = useThemedStyles(buildStyles);
  return <Pressable accessibilityRole="button" onPress={onPress} style={styles.retry}><Text style={styles.inlineLinkText}>{locale === 'vi' ? 'Thử lại' : 'Try again'}</Text></Pressable>;
}

function Unavailable({ locale, onRetry }: { locale: Locale; onRetry: () => void }) {
  return <Panel><Body>{locale === 'vi' ? 'Không tải được thư viện. Kiểm tra kết nối server.' : 'Library unavailable. Check the server connection.'}</Body><Retry locale={locale} onPress={onRetry} /></Panel>;
}

function Empty({ locale }: { locale: Locale }) {
  return <Panel><Body>{locale === 'vi' ? 'Không tìm thấy kết quả.' : 'No matching results.'}</Body></Panel>;
}

function openExternal(url: string) {
  if (/^https:\/\//i.test(url)) void Linking.openURL(url).catch(() => {});
}

const buildStyles = (colors: ThemeColors) => StyleSheet.create({
  refreshButton: { width: 38, height: 38, alignItems: 'center', justifyContent: 'center' },
  hero: { borderRadius: 20, padding: 19, gap: 5, overflow: 'hidden' },
  heroTop: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 5 },
  heroEyebrow: { color: '#C8C8ED', fontSize: 9, letterSpacing: 1.3, fontWeight: '800' },
  heroTitle: { color: '#FFFFFF', fontSize: 24, fontWeight: '800', letterSpacing: -0.5 },
  heroSub: { color: '#D7D6EB', fontSize: 12 },
  heroStats: { flexDirection: 'row', alignItems: 'center', gap: 19, marginTop: 13 },
  heroNumber: { color: '#FFFFFF', fontSize: 20, fontWeight: '800' },
  heroLabel: { color: '#CBC9E4', fontSize: 9, fontWeight: '700', letterSpacing: 0.5, marginTop: 2 },
  heroDivider: { width: 1, height: 32, backgroundColor: '#8A83AE' },
  search: { minHeight: 48, flexDirection: 'row', alignItems: 'center', gap: 9, paddingHorizontal: 13, backgroundColor: colors.card, borderWidth: 1, borderColor: colors.border, borderRadius: 13 },
  searchInput: { flex: 1, minWidth: 0, color: colors.text, fontSize: 14, paddingVertical: 10 },
  tabs: { flexDirection: 'row', padding: 4, borderRadius: 13, backgroundColor: colors.cardSoft, gap: 4 },
  tab: { flex: 1, alignItems: 'center', justifyContent: 'center', minHeight: 39, borderRadius: 10 },
  selectedTab: { backgroundColor: colors.card, shadowColor: '#211D45', shadowOpacity: 0.07, shadowRadius: 4, shadowOffset: { width: 0, height: 2 }, elevation: 1 },
  tabText: { color: colors.muted, fontSize: 12, fontWeight: '700' },
  selectedTabText: { color: colors.text },
  list: { paddingVertical: 0, paddingHorizontal: 13, overflow: 'hidden' },
  listRow: { minHeight: 72, flexDirection: 'row', alignItems: 'center', gap: 11, paddingVertical: 12 },
  rowBorder: { borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.border },
  rowIcon: { width: 38, height: 38, borderRadius: 12, backgroundColor: colors.cardSoft, alignItems: 'center', justifyContent: 'center' },
  rowBody: { flex: 1, minWidth: 0 },
  rowTitle: { color: colors.text, fontSize: 13, lineHeight: 18, fontWeight: '700' },
  rowMeta: { color: colors.muted, fontSize: 10, marginTop: 4 },
  indexLink: { alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: 6, paddingVertical: 5 },
  indexLinkText: { color: colors.cyan, fontSize: 11, fontWeight: '700' },
  pressed: { opacity: 0.68 },
  backToList: { alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: 2, paddingVertical: 3 },
  backText: { color: colors.cyan, fontSize: 12, fontWeight: '700' },
  eyebrow: { color: colors.cyan, fontSize: 10, fontWeight: '800', letterSpacing: 0.7, marginTop: 5 },
  reader: { gap: 11, paddingBottom: 16 },
  readerCategory: { color: colors.muted, fontSize: 12 },
  sourceBar: { flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: colors.card, borderWidth: 1, borderColor: colors.border, borderRadius: 14, padding: 12 },
  sourceIcon: { width: 37, height: 37, backgroundColor: colors.cardSoft, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  sourceBarTitle: { color: colors.text, fontWeight: '800', fontSize: 12 },
  smallButton: { padding: 7 },
  smallButtonText: { color: colors.cyan, fontWeight: '700', fontSize: 11 },
  notice: { gap: 10 },
  detailTitle: { color: colors.text, fontSize: 13, fontWeight: '800' },
  metaRow: { flexDirection: 'row', gap: 9 },
  metaLabel: { width: 85, color: colors.muted, fontSize: 11 },
  metaValue: { flex: 1, color: colors.text, fontSize: 11, lineHeight: 16 },
  inlineLink: { alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: 5 },
  inlineLinkText: { color: colors.cyan, fontSize: 12, fontWeight: '700' },
  sourceNote: { color: colors.muted, fontSize: 10, lineHeight: 16 },
  askAi: { minHeight: 48, backgroundColor: colors.cyan, borderRadius: 13, alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 8 },
  askAiText: { color: colors.onAccent, fontWeight: '800', fontSize: 12 },
  groupHeading: { color: colors.muted, fontSize: 10, fontWeight: '800', letterSpacing: 0.8, marginTop: 5 },
  sectionCard: { gap: 12, padding: 13 },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', gap: 9, minHeight: 24 },
  sectionIndex: { color: colors.cyan, fontSize: 10, fontWeight: '800', minWidth: 22 },
  sectionTitle: { flex: 1, color: colors.text, fontSize: 13, lineHeight: 18, fontWeight: '800' },
  sectionText: { color: colors.text, fontSize: 13, lineHeight: 21 },
  expandedGroup: { gap: 6, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border, paddingTop: 10 },
  tableText: { color: colors.text, fontSize: 11, lineHeight: 17 },
  reference: { gap: 5, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border, paddingTop: 10 },
  referenceText: { color: colors.text, fontSize: 12, lineHeight: 18 },
  illustration: { width: '100%', height: 220, borderRadius: 10, backgroundColor: colors.cardSoft },
  loading: { alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 8, padding: 22 },
  loadingText: { color: colors.muted, fontSize: 12 },
  retry: { alignSelf: 'flex-start', paddingTop: 10 },
});
