import { ScienceArticle, ScienceArticleSummary, ScienceArticlesResult } from './science';

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

// Static require paths let Metro embed each source JSON in the offline app bundle.
const recordLoaders: Record<string, () => OfflineCliffRecord> = {
  'CLIFF-001': () => require('../../assets/nasa-cliff-119/records/CLIFF-001.json') as OfflineCliffRecord,
  'CLIFF-002': () => require('../../assets/nasa-cliff-119/records/CLIFF-002.json') as OfflineCliffRecord,
  'CLIFF-003': () => require('../../assets/nasa-cliff-119/records/CLIFF-003.json') as OfflineCliffRecord,
  'CLIFF-004': () => require('../../assets/nasa-cliff-119/records/CLIFF-004.json') as OfflineCliffRecord,
  'CLIFF-005': () => require('../../assets/nasa-cliff-119/records/CLIFF-005.json') as OfflineCliffRecord,
  'CLIFF-006': () => require('../../assets/nasa-cliff-119/records/CLIFF-006.json') as OfflineCliffRecord,
  'CLIFF-007': () => require('../../assets/nasa-cliff-119/records/CLIFF-007.json') as OfflineCliffRecord,
  'CLIFF-008': () => require('../../assets/nasa-cliff-119/records/CLIFF-008.json') as OfflineCliffRecord,
  'CLIFF-009': () => require('../../assets/nasa-cliff-119/records/CLIFF-009.json') as OfflineCliffRecord,
  'CLIFF-010': () => require('../../assets/nasa-cliff-119/records/CLIFF-010.json') as OfflineCliffRecord,
  'CLIFF-011': () => require('../../assets/nasa-cliff-119/records/CLIFF-011.json') as OfflineCliffRecord,
  'CLIFF-012': () => require('../../assets/nasa-cliff-119/records/CLIFF-012.json') as OfflineCliffRecord,
  'CLIFF-013': () => require('../../assets/nasa-cliff-119/records/CLIFF-013.json') as OfflineCliffRecord,
  'CLIFF-014': () => require('../../assets/nasa-cliff-119/records/CLIFF-014.json') as OfflineCliffRecord,
  'CLIFF-015': () => require('../../assets/nasa-cliff-119/records/CLIFF-015.json') as OfflineCliffRecord,
  'CLIFF-016': () => require('../../assets/nasa-cliff-119/records/CLIFF-016.json') as OfflineCliffRecord,
  'CLIFF-017': () => require('../../assets/nasa-cliff-119/records/CLIFF-017.json') as OfflineCliffRecord,
  'CLIFF-018': () => require('../../assets/nasa-cliff-119/records/CLIFF-018.json') as OfflineCliffRecord,
  'CLIFF-019': () => require('../../assets/nasa-cliff-119/records/CLIFF-019.json') as OfflineCliffRecord,
  'CLIFF-020': () => require('../../assets/nasa-cliff-119/records/CLIFF-020.json') as OfflineCliffRecord,
  'CLIFF-021': () => require('../../assets/nasa-cliff-119/records/CLIFF-021.json') as OfflineCliffRecord,
  'CLIFF-022': () => require('../../assets/nasa-cliff-119/records/CLIFF-022.json') as OfflineCliffRecord,
  'CLIFF-023': () => require('../../assets/nasa-cliff-119/records/CLIFF-023.json') as OfflineCliffRecord,
  'CLIFF-024': () => require('../../assets/nasa-cliff-119/records/CLIFF-024.json') as OfflineCliffRecord,
  'CLIFF-025': () => require('../../assets/nasa-cliff-119/records/CLIFF-025.json') as OfflineCliffRecord,
  'CLIFF-026': () => require('../../assets/nasa-cliff-119/records/CLIFF-026.json') as OfflineCliffRecord,
  'CLIFF-027': () => require('../../assets/nasa-cliff-119/records/CLIFF-027.json') as OfflineCliffRecord,
  'CLIFF-028': () => require('../../assets/nasa-cliff-119/records/CLIFF-028.json') as OfflineCliffRecord,
  'CLIFF-029': () => require('../../assets/nasa-cliff-119/records/CLIFF-029.json') as OfflineCliffRecord,
  'CLIFF-030': () => require('../../assets/nasa-cliff-119/records/CLIFF-030.json') as OfflineCliffRecord,
  'CLIFF-031': () => require('../../assets/nasa-cliff-119/records/CLIFF-031.json') as OfflineCliffRecord,
  'CLIFF-032': () => require('../../assets/nasa-cliff-119/records/CLIFF-032.json') as OfflineCliffRecord,
  'CLIFF-033': () => require('../../assets/nasa-cliff-119/records/CLIFF-033.json') as OfflineCliffRecord,
  'CLIFF-034': () => require('../../assets/nasa-cliff-119/records/CLIFF-034.json') as OfflineCliffRecord,
  'CLIFF-035': () => require('../../assets/nasa-cliff-119/records/CLIFF-035.json') as OfflineCliffRecord,
  'CLIFF-036': () => require('../../assets/nasa-cliff-119/records/CLIFF-036.json') as OfflineCliffRecord,
  'CLIFF-037': () => require('../../assets/nasa-cliff-119/records/CLIFF-037.json') as OfflineCliffRecord,
  'CLIFF-038': () => require('../../assets/nasa-cliff-119/records/CLIFF-038.json') as OfflineCliffRecord,
  'CLIFF-039': () => require('../../assets/nasa-cliff-119/records/CLIFF-039.json') as OfflineCliffRecord,
  'CLIFF-040': () => require('../../assets/nasa-cliff-119/records/CLIFF-040.json') as OfflineCliffRecord,
  'CLIFF-041': () => require('../../assets/nasa-cliff-119/records/CLIFF-041.json') as OfflineCliffRecord,
  'CLIFF-042': () => require('../../assets/nasa-cliff-119/records/CLIFF-042.json') as OfflineCliffRecord,
  'CLIFF-043': () => require('../../assets/nasa-cliff-119/records/CLIFF-043.json') as OfflineCliffRecord,
  'CLIFF-044': () => require('../../assets/nasa-cliff-119/records/CLIFF-044.json') as OfflineCliffRecord,
  'CLIFF-045': () => require('../../assets/nasa-cliff-119/records/CLIFF-045.json') as OfflineCliffRecord,
  'CLIFF-046': () => require('../../assets/nasa-cliff-119/records/CLIFF-046.json') as OfflineCliffRecord,
  'CLIFF-047': () => require('../../assets/nasa-cliff-119/records/CLIFF-047.json') as OfflineCliffRecord,
  'CLIFF-048': () => require('../../assets/nasa-cliff-119/records/CLIFF-048.json') as OfflineCliffRecord,
  'CLIFF-049': () => require('../../assets/nasa-cliff-119/records/CLIFF-049.json') as OfflineCliffRecord,
  'CLIFF-050': () => require('../../assets/nasa-cliff-119/records/CLIFF-050.json') as OfflineCliffRecord,
  'CLIFF-051': () => require('../../assets/nasa-cliff-119/records/CLIFF-051.json') as OfflineCliffRecord,
  'CLIFF-052': () => require('../../assets/nasa-cliff-119/records/CLIFF-052.json') as OfflineCliffRecord,
  'CLIFF-053': () => require('../../assets/nasa-cliff-119/records/CLIFF-053.json') as OfflineCliffRecord,
  'CLIFF-054': () => require('../../assets/nasa-cliff-119/records/CLIFF-054.json') as OfflineCliffRecord,
  'CLIFF-055': () => require('../../assets/nasa-cliff-119/records/CLIFF-055.json') as OfflineCliffRecord,
  'CLIFF-056': () => require('../../assets/nasa-cliff-119/records/CLIFF-056.json') as OfflineCliffRecord,
  'CLIFF-057': () => require('../../assets/nasa-cliff-119/records/CLIFF-057.json') as OfflineCliffRecord,
  'CLIFF-058': () => require('../../assets/nasa-cliff-119/records/CLIFF-058.json') as OfflineCliffRecord,
  'CLIFF-059': () => require('../../assets/nasa-cliff-119/records/CLIFF-059.json') as OfflineCliffRecord,
  'CLIFF-060': () => require('../../assets/nasa-cliff-119/records/CLIFF-060.json') as OfflineCliffRecord,
  'CLIFF-061': () => require('../../assets/nasa-cliff-119/records/CLIFF-061.json') as OfflineCliffRecord,
  'CLIFF-062': () => require('../../assets/nasa-cliff-119/records/CLIFF-062.json') as OfflineCliffRecord,
  'CLIFF-063': () => require('../../assets/nasa-cliff-119/records/CLIFF-063.json') as OfflineCliffRecord,
  'CLIFF-064': () => require('../../assets/nasa-cliff-119/records/CLIFF-064.json') as OfflineCliffRecord,
  'CLIFF-065': () => require('../../assets/nasa-cliff-119/records/CLIFF-065.json') as OfflineCliffRecord,
  'CLIFF-066': () => require('../../assets/nasa-cliff-119/records/CLIFF-066.json') as OfflineCliffRecord,
  'CLIFF-067': () => require('../../assets/nasa-cliff-119/records/CLIFF-067.json') as OfflineCliffRecord,
  'CLIFF-068': () => require('../../assets/nasa-cliff-119/records/CLIFF-068.json') as OfflineCliffRecord,
  'CLIFF-069': () => require('../../assets/nasa-cliff-119/records/CLIFF-069.json') as OfflineCliffRecord,
  'CLIFF-070': () => require('../../assets/nasa-cliff-119/records/CLIFF-070.json') as OfflineCliffRecord,
  'CLIFF-071': () => require('../../assets/nasa-cliff-119/records/CLIFF-071.json') as OfflineCliffRecord,
  'CLIFF-072': () => require('../../assets/nasa-cliff-119/records/CLIFF-072.json') as OfflineCliffRecord,
  'CLIFF-073': () => require('../../assets/nasa-cliff-119/records/CLIFF-073.json') as OfflineCliffRecord,
  'CLIFF-074': () => require('../../assets/nasa-cliff-119/records/CLIFF-074.json') as OfflineCliffRecord,
  'CLIFF-075': () => require('../../assets/nasa-cliff-119/records/CLIFF-075.json') as OfflineCliffRecord,
  'CLIFF-076': () => require('../../assets/nasa-cliff-119/records/CLIFF-076.json') as OfflineCliffRecord,
  'CLIFF-077': () => require('../../assets/nasa-cliff-119/records/CLIFF-077.json') as OfflineCliffRecord,
  'CLIFF-078': () => require('../../assets/nasa-cliff-119/records/CLIFF-078.json') as OfflineCliffRecord,
  'CLIFF-079': () => require('../../assets/nasa-cliff-119/records/CLIFF-079.json') as OfflineCliffRecord,
  'CLIFF-080': () => require('../../assets/nasa-cliff-119/records/CLIFF-080.json') as OfflineCliffRecord,
  'CLIFF-081': () => require('../../assets/nasa-cliff-119/records/CLIFF-081.json') as OfflineCliffRecord,
  'CLIFF-082': () => require('../../assets/nasa-cliff-119/records/CLIFF-082.json') as OfflineCliffRecord,
  'CLIFF-083': () => require('../../assets/nasa-cliff-119/records/CLIFF-083.json') as OfflineCliffRecord,
  'CLIFF-084': () => require('../../assets/nasa-cliff-119/records/CLIFF-084.json') as OfflineCliffRecord,
  'CLIFF-085': () => require('../../assets/nasa-cliff-119/records/CLIFF-085.json') as OfflineCliffRecord,
  'CLIFF-086': () => require('../../assets/nasa-cliff-119/records/CLIFF-086.json') as OfflineCliffRecord,
  'CLIFF-087': () => require('../../assets/nasa-cliff-119/records/CLIFF-087.json') as OfflineCliffRecord,
  'CLIFF-088': () => require('../../assets/nasa-cliff-119/records/CLIFF-088.json') as OfflineCliffRecord,
  'CLIFF-089': () => require('../../assets/nasa-cliff-119/records/CLIFF-089.json') as OfflineCliffRecord,
  'CLIFF-090': () => require('../../assets/nasa-cliff-119/records/CLIFF-090.json') as OfflineCliffRecord,
  'CLIFF-091': () => require('../../assets/nasa-cliff-119/records/CLIFF-091.json') as OfflineCliffRecord,
  'CLIFF-092': () => require('../../assets/nasa-cliff-119/records/CLIFF-092.json') as OfflineCliffRecord,
  'CLIFF-093': () => require('../../assets/nasa-cliff-119/records/CLIFF-093.json') as OfflineCliffRecord,
  'CLIFF-094': () => require('../../assets/nasa-cliff-119/records/CLIFF-094.json') as OfflineCliffRecord,
  'CLIFF-095': () => require('../../assets/nasa-cliff-119/records/CLIFF-095.json') as OfflineCliffRecord,
  'CLIFF-096': () => require('../../assets/nasa-cliff-119/records/CLIFF-096.json') as OfflineCliffRecord,
  'CLIFF-097': () => require('../../assets/nasa-cliff-119/records/CLIFF-097.json') as OfflineCliffRecord,
  'CLIFF-098': () => require('../../assets/nasa-cliff-119/records/CLIFF-098.json') as OfflineCliffRecord,
  'CLIFF-099': () => require('../../assets/nasa-cliff-119/records/CLIFF-099.json') as OfflineCliffRecord,
  'CLIFF-100': () => require('../../assets/nasa-cliff-119/records/CLIFF-100.json') as OfflineCliffRecord,
  'CLIFF-101': () => require('../../assets/nasa-cliff-119/records/CLIFF-101.json') as OfflineCliffRecord,
  'CLIFF-102': () => require('../../assets/nasa-cliff-119/records/CLIFF-102.json') as OfflineCliffRecord,
  'CLIFF-103': () => require('../../assets/nasa-cliff-119/records/CLIFF-103.json') as OfflineCliffRecord,
  'CLIFF-104': () => require('../../assets/nasa-cliff-119/records/CLIFF-104.json') as OfflineCliffRecord,
  'CLIFF-105': () => require('../../assets/nasa-cliff-119/records/CLIFF-105.json') as OfflineCliffRecord,
  'CLIFF-106': () => require('../../assets/nasa-cliff-119/records/CLIFF-106.json') as OfflineCliffRecord,
  'CLIFF-107': () => require('../../assets/nasa-cliff-119/records/CLIFF-107.json') as OfflineCliffRecord,
  'CLIFF-108': () => require('../../assets/nasa-cliff-119/records/CLIFF-108.json') as OfflineCliffRecord,
  'CLIFF-109': () => require('../../assets/nasa-cliff-119/records/CLIFF-109.json') as OfflineCliffRecord,
  'CLIFF-110': () => require('../../assets/nasa-cliff-119/records/CLIFF-110.json') as OfflineCliffRecord,
  'CLIFF-111': () => require('../../assets/nasa-cliff-119/records/CLIFF-111.json') as OfflineCliffRecord,
  'CLIFF-112': () => require('../../assets/nasa-cliff-119/records/CLIFF-112.json') as OfflineCliffRecord,
  'CLIFF-113': () => require('../../assets/nasa-cliff-119/records/CLIFF-113.json') as OfflineCliffRecord,
  'CLIFF-114': () => require('../../assets/nasa-cliff-119/records/CLIFF-114.json') as OfflineCliffRecord,
  'CLIFF-115': () => require('../../assets/nasa-cliff-119/records/CLIFF-115.json') as OfflineCliffRecord,
  'CLIFF-116': () => require('../../assets/nasa-cliff-119/records/CLIFF-116.json') as OfflineCliffRecord,
  'CLIFF-117': () => require('../../assets/nasa-cliff-119/records/CLIFF-117.json') as OfflineCliffRecord,
  'CLIFF-118': () => require('../../assets/nasa-cliff-119/records/CLIFF-118.json') as OfflineCliffRecord,
};

export const OFFLINE_CLIFF_COUNT = 118;
let cachedRecords: OfflineCliffRecord[] | null = null;

function allRecords(): OfflineCliffRecord[] {
  if (!cachedRecords) {
    cachedRecords = Object.entries(recordLoaders)
      .map(([id, load]) => {
        const record = load();
        if (record.article_id !== id) throw new Error('Offline NASA CliFF record identity mismatch: ' + id);
        return record;
      })
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
    content_state: record.completeness_state,
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
  const record = recordLoaders[articleId]?.();
  if (!record || record.article_id !== articleId) return null;
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
