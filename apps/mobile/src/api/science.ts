import { request } from './client';

export type KnowledgeStatus = {
  json_articles: number;
  expected_slots: number;
  missing_slots: string[];
  full_text_records?: number;
  metadata_only_records?: number;
  symptom_labels: number;
  article_full_text_search: boolean;
  original_pdf_archive_verified: boolean;
  clinical_rules_validated: boolean;
  read_only: boolean;
};

export type ScienceArticleSummary = {
  article_id: string;
  title: string;
  category: string;
  slot: number | null;
  sections: number;
  text_words: number;
  tables: number;
  references: number;
  media: number;
  original_url: string | null;
  source_claim: string;
  original_sha256_claim: string | null;
  content_state: string;
};

export type ScienceArticlesResult = {
  indexed: number;
  matched: number;
  items: ScienceArticleSummary[];
  source: string;
  note: string;
};

export type NasaCondition = {
  condition_id: string;
  title: string;
  source_page: number;
  source_url: string;
  article_id: string | null;
};

export type NasaConditionsResult = {
  total: number;
  matched: number;
  items: NasaCondition[];
  source_title: string;
  source_url: string;
};

export type ScienceSection = { section_id: string; heading: string; text_content: string; source_anchor?: string | null; page_start?: number | null; page_end?: number | null };
export type ScienceReference = { reference_id: string; label: string; citation_url?: string | null; page_number?: number | null };
export type ScienceTable = { table_id: string; title: string; rows: string[][]; page_number?: number | null; source_anchor?: string | null };

export type ScienceArticle = {
  summary: ScienceArticleSummary;
  completeness_state?: string;
  source_notes?: string;
  sections: ScienceSection[];
  tables: ScienceTable[];
  references: ScienceReference[];
  media: Array<Record<string, unknown>>;
  limitations: unknown[];
  source: {
    source_id?: string;
    publisher?: string;
    title?: string;
    source_url?: string;
    final_url?: string;
    retrieved_at_utc?: string;
    content_sha256?: string;
    original_mime?: string;
    original_bytes?: number;
    license_identifier?: string;
    attribution?: string;
    verification_state?: string;
  };
  read_only: boolean;
  clinical_decision_support: boolean;
};

export function getKnowledgeStatus(): Promise<KnowledgeStatus> {
  return request('/api/v1/knowledge/status', { timeoutMs: 12000 });
}

export function searchScienceArticles(query = '', limit = 120): Promise<ScienceArticlesResult> {
  const params = [`limit=${Math.max(1, Math.min(limit, 200))}`];
  if (query.trim()) params.push(`query=${encodeURIComponent(query.trim())}`);
  return request(`/api/v1/knowledge/articles?${params.join('&')}`, { timeoutMs: 20000 });
}

export function getNasaConditions(query = ''): Promise<NasaConditionsResult> {
  const suffix = query.trim() ? `?query=${encodeURIComponent(query.trim())}` : '';
  return request(`/api/v1/knowledge/conditions${suffix}`, { timeoutMs: 20000 });
}

export function getScienceArticle(articleId: string): Promise<ScienceArticle> {
  return request(`/api/v1/knowledge/articles/${encodeURIComponent(articleId)}`, { timeoutMs: 20000 });
}


