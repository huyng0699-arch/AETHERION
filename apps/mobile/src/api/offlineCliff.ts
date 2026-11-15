import { KnowledgeStatus, ScienceArticle, ScienceArticleSummary, ScienceArticlesResult } from './science';

type OfflineCliffRecord = {
  article_id: string;
  slot: number;
  display_title: string;
  category: string;
  completeness_state: string;
  sections: ScienceArticle['sections'];
  tables: ScienceArticle['tables'];
  references: ScienceArticle['references'];
  media: ScienceArticle['media'];
  limitations: unknown[];
  source: ScienceArticle['source'];
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isArrayOf<T>(value: unknown, guard: (item: unknown) => item is T): value is T[] {
  return Array.isArray(value) && value.every(guard);
}

function isSection(value: unknown): value is ScienceArticle['sections'][number] {
  return isRecord(value) && typeof value.section_id === 'string'
    && typeof value.heading === 'string' && typeof value.text_content === 'string';
}

function isTable(value: unknown): value is ScienceArticle['tables'][number] {
  return isRecord(value) && typeof value.table_id === 'string' && typeof value.title === 'string'
    && Array.isArray(value.rows)
    && value.rows.every(row => Array.isArray(row) && row.every(cell => typeof cell === 'string'))
    && (value.page_number === undefined || typeof value.page_number === 'number')
    && (value.source_anchor === undefined || typeof value.source_anchor === 'string' || value.source_anchor === null);
}

function isReference(value: unknown): value is ScienceArticle['references'][number] {
  return isRecord(value) && typeof value.reference_id === 'string' && typeof value.label === 'string'
    && (value.citation_url === undefined || typeof value.citation_url === 'string' || value.citation_url === null)
    && (value.page_number === undefined || typeof value.page_number === 'number' || value.page_number === null);
}

function isMedia(value: unknown): value is Record<string, unknown> {
  return isRecord(value);
}

function isSource(value: unknown): value is ScienceArticle['source'] {
  if (!isRecord(value)) return false;
  const stringFields = [
    'source_id', 'publisher', 'title', 'source_url', 'final_url', 'retrieved_at_utc',
    'content_sha256', 'original_mime', 'license_identifier', 'attribution', 'verification_state',
  ];
  return stringFields.every(field => value[field] === undefined || typeof value[field] === 'string')
    && (value.original_bytes === undefined || typeof value.original_bytes === 'number');
}

function adaptOfflineRecord(id: string, value: unknown): OfflineCliffRecord {
  if (!isRecord(value)) throw new Error('Offline NASA CliFF record is not an object: ' + id);
  const articleId = value.article_id;
  const slot = value.slot;
  const displayTitle = value.display_title;
  const category = value.category;
  const completenessState = value.completeness_state;
  const sections = value.sections;
  const tables = value.tables;
  const references = value.references;
  const media = value.media;
  const limitations = value.limitations;
  const source = value.source;
  if (articleId !== id || typeof slot !== 'number' || typeof displayTitle !== 'string'
    || typeof category !== 'string' || typeof completenessState !== 'string'
    || !isArrayOf(sections, isSection) || !isArrayOf(tables, isTable)
    || !isArrayOf(references, isReference) || !isArrayOf(media, isMedia)
    || !Array.isArray(limitations) || !isSource(source)) {
    throw new Error('Offline NASA CliFF record does not match the mobile science types: ' + id);
  }
  return {
    article_id: articleId,
    slot,
    display_title: displayTitle,
    category,
    completeness_state: completenessState,
    sections,
    tables,
    references,
    media,
    limitations,
    source,
  };
}

// Exact static keys keep Metro bundling limited to the verified CLIFF-001..118 allowlist.
const recordLoaders: Record<string, () => unknown> = {
  'CLIFF-001': () => require('../../assets/nasa-cliff-119/records/CLIFF-001.json'),
  'CLIFF-002': () => require('../../assets/nasa-cliff-119/records/CLIFF-002.json'),
  'CLIFF-003': () => require('../../assets/nasa-cliff-119/records/CLIFF-003.json'),
  'CLIFF-004': () => require('../../assets/nasa-cliff-119/records/CLIFF-004.json'),
  'CLIFF-005': () => require('../../assets/nasa-cliff-119/records/CLIFF-005.json'),
  'CLIFF-006': () => require('../../assets/nasa-cliff-119/records/CLIFF-006.json'),
  'CLIFF-007': () => require('../../assets/nasa-cliff-119/records/CLIFF-007.json'),
  'CLIFF-008': () => require('../../assets/nasa-cliff-119/records/CLIFF-008.json'),
  'CLIFF-009': () => require('../../assets/nasa-cliff-119/records/CLIFF-009.json'),
  'CLIFF-010': () => require('../../assets/nasa-cliff-119/records/CLIFF-010.json'),
  'CLIFF-011': () => require('../../assets/nasa-cliff-119/records/CLIFF-011.json'),
  'CLIFF-012': () => require('../../assets/nasa-cliff-119/records/CLIFF-012.json'),
  'CLIFF-013': () => require('../../assets/nasa-cliff-119/records/CLIFF-013.json'),
  'CLIFF-014': () => require('../../assets/nasa-cliff-119/records/CLIFF-014.json'),
  'CLIFF-015': () => require('../../assets/nasa-cliff-119/records/CLIFF-015.json'),
  'CLIFF-016': () => require('../../assets/nasa-cliff-119/records/CLIFF-016.json'),
  'CLIFF-017': () => require('../../assets/nasa-cliff-119/records/CLIFF-017.json'),
  'CLIFF-018': () => require('../../assets/nasa-cliff-119/records/CLIFF-018.json'),
  'CLIFF-019': () => require('../../assets/nasa-cliff-119/records/CLIFF-019.json'),
  'CLIFF-020': () => require('../../assets/nasa-cliff-119/records/CLIFF-020.json'),
  'CLIFF-021': () => require('../../assets/nasa-cliff-119/records/CLIFF-021.json'),
  'CLIFF-022': () => require('../../assets/nasa-cliff-119/records/CLIFF-022.json'),
  'CLIFF-023': () => require('../../assets/nasa-cliff-119/records/CLIFF-023.json'),
  'CLIFF-024': () => require('../../assets/nasa-cliff-119/records/CLIFF-024.json'),
  'CLIFF-025': () => require('../../assets/nasa-cliff-119/records/CLIFF-025.json'),
  'CLIFF-026': () => require('../../assets/nasa-cliff-119/records/CLIFF-026.json'),
  'CLIFF-027': () => require('../../assets/nasa-cliff-119/records/CLIFF-027.json'),
  'CLIFF-028': () => require('../../assets/nasa-cliff-119/records/CLIFF-028.json'),
  'CLIFF-029': () => require('../../assets/nasa-cliff-119/records/CLIFF-029.json'),
  'CLIFF-030': () => require('../../assets/nasa-cliff-119/records/CLIFF-030.json'),
  'CLIFF-031': () => require('../../assets/nasa-cliff-119/records/CLIFF-031.json'),
  'CLIFF-032': () => require('../../assets/nasa-cliff-119/records/CLIFF-032.json'),
  'CLIFF-033': () => require('../../assets/nasa-cliff-119/records/CLIFF-033.json'),
  'CLIFF-034': () => require('../../assets/nasa-cliff-119/records/CLIFF-034.json'),
  'CLIFF-035': () => require('../../assets/nasa-cliff-119/records/CLIFF-035.json'),
  'CLIFF-036': () => require('../../assets/nasa-cliff-119/records/CLIFF-036.json'),
  'CLIFF-037': () => require('../../assets/nasa-cliff-119/records/CLIFF-037.json'),
  'CLIFF-038': () => require('../../assets/nasa-cliff-119/records/CLIFF-038.json'),
  'CLIFF-039': () => require('../../assets/nasa-cliff-119/records/CLIFF-039.json'),
  'CLIFF-040': () => require('../../assets/nasa-cliff-119/records/CLIFF-040.json'),
  'CLIFF-041': () => require('../../assets/nasa-cliff-119/records/CLIFF-041.json'),
  'CLIFF-042': () => require('../../assets/nasa-cliff-119/records/CLIFF-042.json'),
  'CLIFF-043': () => require('../../assets/nasa-cliff-119/records/CLIFF-043.json'),
  'CLIFF-044': () => require('../../assets/nasa-cliff-119/records/CLIFF-044.json'),
  'CLIFF-045': () => require('../../assets/nasa-cliff-119/records/CLIFF-045.json'),
  'CLIFF-046': () => require('../../assets/nasa-cliff-119/records/CLIFF-046.json'),
  'CLIFF-047': () => require('../../assets/nasa-cliff-119/records/CLIFF-047.json'),
  'CLIFF-048': () => require('../../assets/nasa-cliff-119/records/CLIFF-048.json'),
  'CLIFF-049': () => require('../../assets/nasa-cliff-119/records/CLIFF-049.json'),
  'CLIFF-050': () => require('../../assets/nasa-cliff-119/records/CLIFF-050.json'),
  'CLIFF-051': () => require('../../assets/nasa-cliff-119/records/CLIFF-051.json'),
  'CLIFF-052': () => require('../../assets/nasa-cliff-119/records/CLIFF-052.json'),
  'CLIFF-053': () => require('../../assets/nasa-cliff-119/records/CLIFF-053.json'),
  'CLIFF-054': () => require('../../assets/nasa-cliff-119/records/CLIFF-054.json'),
  'CLIFF-055': () => require('../../assets/nasa-cliff-119/records/CLIFF-055.json'),
  'CLIFF-056': () => require('../../assets/nasa-cliff-119/records/CLIFF-056.json'),
  'CLIFF-057': () => require('../../assets/nasa-cliff-119/records/CLIFF-057.json'),
  'CLIFF-058': () => require('../../assets/nasa-cliff-119/records/CLIFF-058.json'),
  'CLIFF-059': () => require('../../assets/nasa-cliff-119/records/CLIFF-059.json'),
  'CLIFF-060': () => require('../../assets/nasa-cliff-119/records/CLIFF-060.json'),
  'CLIFF-061': () => require('../../assets/nasa-cliff-119/records/CLIFF-061.json'),
  'CLIFF-062': () => require('../../assets/nasa-cliff-119/records/CLIFF-062.json'),
  'CLIFF-063': () => require('../../assets/nasa-cliff-119/records/CLIFF-063.json'),
  'CLIFF-064': () => require('../../assets/nasa-cliff-119/records/CLIFF-064.json'),
  'CLIFF-065': () => require('../../assets/nasa-cliff-119/records/CLIFF-065.json'),
  'CLIFF-066': () => require('../../assets/nasa-cliff-119/records/CLIFF-066.json'),
  'CLIFF-067': () => require('../../assets/nasa-cliff-119/records/CLIFF-067.json'),
  'CLIFF-068': () => require('../../assets/nasa-cliff-119/records/CLIFF-068.json'),
  'CLIFF-069': () => require('../../assets/nasa-cliff-119/records/CLIFF-069.json'),
  'CLIFF-070': () => require('../../assets/nasa-cliff-119/records/CLIFF-070.json'),
  'CLIFF-071': () => require('../../assets/nasa-cliff-119/records/CLIFF-071.json'),
  'CLIFF-072': () => require('../../assets/nasa-cliff-119/records/CLIFF-072.json'),
  'CLIFF-073': () => require('../../assets/nasa-cliff-119/records/CLIFF-073.json'),
  'CLIFF-074': () => require('../../assets/nasa-cliff-119/records/CLIFF-074.json'),
  'CLIFF-075': () => require('../../assets/nasa-cliff-119/records/CLIFF-075.json'),
  'CLIFF-076': () => require('../../assets/nasa-cliff-119/records/CLIFF-076.json'),
  'CLIFF-077': () => require('../../assets/nasa-cliff-119/records/CLIFF-077.json'),
  'CLIFF-078': () => require('../../assets/nasa-cliff-119/records/CLIFF-078.json'),
  'CLIFF-079': () => require('../../assets/nasa-cliff-119/records/CLIFF-079.json'),
  'CLIFF-080': () => require('../../assets/nasa-cliff-119/records/CLIFF-080.json'),
  'CLIFF-081': () => require('../../assets/nasa-cliff-119/records/CLIFF-081.json'),
  'CLIFF-082': () => require('../../assets/nasa-cliff-119/records/CLIFF-082.json'),
  'CLIFF-083': () => require('../../assets/nasa-cliff-119/records/CLIFF-083.json'),
  'CLIFF-084': () => require('../../assets/nasa-cliff-119/records/CLIFF-084.json'),
  'CLIFF-085': () => require('../../assets/nasa-cliff-119/records/CLIFF-085.json'),
  'CLIFF-086': () => require('../../assets/nasa-cliff-119/records/CLIFF-086.json'),
  'CLIFF-087': () => require('../../assets/nasa-cliff-119/records/CLIFF-087.json'),
  'CLIFF-088': () => require('../../assets/nasa-cliff-119/records/CLIFF-088.json'),
  'CLIFF-089': () => require('../../assets/nasa-cliff-119/records/CLIFF-089.json'),
  'CLIFF-090': () => require('../../assets/nasa-cliff-119/records/CLIFF-090.json'),
  'CLIFF-091': () => require('../../assets/nasa-cliff-119/records/CLIFF-091.json'),
  'CLIFF-092': () => require('../../assets/nasa-cliff-119/records/CLIFF-092.json'),
  'CLIFF-093': () => require('../../assets/nasa-cliff-119/records/CLIFF-093.json'),
  'CLIFF-094': () => require('../../assets/nasa-cliff-119/records/CLIFF-094.json'),
  'CLIFF-095': () => require('../../assets/nasa-cliff-119/records/CLIFF-095.json'),
  'CLIFF-096': () => require('../../assets/nasa-cliff-119/records/CLIFF-096.json'),
  'CLIFF-097': () => require('../../assets/nasa-cliff-119/records/CLIFF-097.json'),
  'CLIFF-098': () => require('../../assets/nasa-cliff-119/records/CLIFF-098.json'),
  'CLIFF-099': () => require('../../assets/nasa-cliff-119/records/CLIFF-099.json'),
  'CLIFF-100': () => require('../../assets/nasa-cliff-119/records/CLIFF-100.json'),
  'CLIFF-101': () => require('../../assets/nasa-cliff-119/records/CLIFF-101.json'),
  'CLIFF-102': () => require('../../assets/nasa-cliff-119/records/CLIFF-102.json'),
  'CLIFF-103': () => require('../../assets/nasa-cliff-119/records/CLIFF-103.json'),
  'CLIFF-104': () => require('../../assets/nasa-cliff-119/records/CLIFF-104.json'),
  'CLIFF-105': () => require('../../assets/nasa-cliff-119/records/CLIFF-105.json'),
  'CLIFF-106': () => require('../../assets/nasa-cliff-119/records/CLIFF-106.json'),
  'CLIFF-107': () => require('../../assets/nasa-cliff-119/records/CLIFF-107.json'),
  'CLIFF-108': () => require('../../assets/nasa-cliff-119/records/CLIFF-108.json'),
  'CLIFF-109': () => require('../../assets/nasa-cliff-119/records/CLIFF-109.json'),
  'CLIFF-110': () => require('../../assets/nasa-cliff-119/records/CLIFF-110.json'),
  'CLIFF-111': () => require('../../assets/nasa-cliff-119/records/CLIFF-111.json'),
  'CLIFF-112': () => require('../../assets/nasa-cliff-119/records/CLIFF-112.json'),
  'CLIFF-113': () => require('../../assets/nasa-cliff-119/records/CLIFF-113.json'),
  'CLIFF-114': () => require('../../assets/nasa-cliff-119/records/CLIFF-114.json'),
  'CLIFF-115': () => require('../../assets/nasa-cliff-119/records/CLIFF-115.json'),
  'CLIFF-116': () => require('../../assets/nasa-cliff-119/records/CLIFF-116.json'),
  'CLIFF-117': () => require('../../assets/nasa-cliff-119/records/CLIFF-117.json'),
  'CLIFF-118': () => require('../../assets/nasa-cliff-119/records/CLIFF-118.json'),
};

export const OFFLINE_CLIFF_COUNT = 118;
export const OFFLINE_CLIFF_STATUS: KnowledgeStatus = {
  json_articles: OFFLINE_CLIFF_COUNT,
  expected_slots: 119,
  missing_slots: ['CLIFF-119'],
  symptom_labels: 0,
  article_full_text_search: true,
  original_pdf_archive_verified: false,
  clinical_rules_validated: false,
  read_only: true,
};
let cachedRecords: OfflineCliffRecord[] | null = null;

function allRecords(): OfflineCliffRecord[] {
  if (!cachedRecords) {
    cachedRecords = Object.entries(recordLoaders)
      .map(([id, load]) => adaptOfflineRecord(id, load()))
      .sort((a, b) => a.slot - b.slot);
    if (cachedRecords.length !== OFFLINE_CLIFF_COUNT) {
      throw new Error('Offline NASA CliFF bundle count mismatch');
    }
  }
  return cachedRecords;
}

function toSummary(record: OfflineCliffRecord): ScienceArticleSummary {
  const wordCount = record.sections.reduce((total, section) => {
    const words = section.text_content.trim().match(/\S+/g);
    return total + (words ? words.length : 0);
  }, 0);
  return {
    article_id: record.article_id,
    title: record.display_title,
    category: record.category,
    slot: record.slot,
    sections: record.sections.length,
    text_words: wordCount,
    tables: record.tables.length,
    references: record.references.length,
    media: record.media.length,
    original_url: record.source.final_url || record.source.source_url || null,
    source_claim: record.source.verification_state || 'UNKNOWN',
    original_sha256_claim: record.source.content_sha256 || null,
    content_state: 'STRUCTURED_JSON_LOCAL_NOT_PDF_INTEGRITY_PROOF',
  };
}

export function searchOfflineCliffArticles(query = '', limit = 100, offset = 0): ScienceArticlesResult {
  const normalized = query.trim().toLocaleLowerCase();
  const matched = allRecords().filter(record => {
    if (!normalized) return true;
    const searchable = [
      record.article_id,
      record.display_title,
      record.category,
      ...record.sections.map(section => section.heading + ' ' + section.text_content),
      ...record.tables.map(table => table.title + ' ' + table.rows.flat().join(' ')),
      ...record.references.map(reference => reference.label),
    ].join(' ').toLocaleLowerCase();
    return searchable.includes(normalized);
  });
  const start = Math.max(0, Math.floor(offset));
  const page = matched.slice(start, start + Math.max(1, Math.min(100, Math.floor(limit))));
  const nextOffset = start + page.length;
  return {
    indexed: OFFLINE_CLIFF_COUNT,
    matched: matched.length,
    items: page.map(toSummary),
    source: 'bundled-offline-nasa-cliff-json',
    note: 'Bundled source-derived NASA IMM CliFF records; read-only reference material.',
    offset: start,
    has_more: nextOffset < matched.length,
    next_offset: nextOffset,
  };
}

export function getOfflineCliffArticle(articleId: string): ScienceArticle | null {
  if (!Object.prototype.hasOwnProperty.call(recordLoaders, articleId)) return null;
  const record = adaptOfflineRecord(articleId, recordLoaders[articleId]());
  return {
    summary: toSummary(record),
    sections: record.sections,
    tables: record.tables,
    references: record.references,
    media: record.media,
    limitations: record.limitations,
    source: record.source,
    read_only: true,
    clinical_decision_support: false,
  };
}
