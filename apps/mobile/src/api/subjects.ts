import { request } from './client';
export type Subject = { subject_id: string; display_name: string; scope: string; role_label: string; created_at: string };
export async function listSubjects(token: string): Promise<Subject[]> {
  const subjects: Subject[] = [];
  let offset = 0;
  for (;;) {
    const page = await request<{ subjects: Subject[]; has_more: boolean; next_offset: number }>(`/api/v1/subjects?limit=100&offset=${offset}`, { token });
    subjects.push(...page.subjects);
    if (!page.has_more || page.next_offset <= offset) break;
    offset = page.next_offset;
  }
  return subjects;
}
export async function createSubject(token: string, subject_id: string, display_name: string): Promise<Subject> {
  const response = await request<{ subject: Subject }>('/api/v1/subjects', { method: 'POST', body: { subject_id, display_name, scope: 'CREW' }, token });
  return response.subject;
}
