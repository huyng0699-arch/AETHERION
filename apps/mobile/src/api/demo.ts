export type LocalizedSourceLabel = { vi: string; en: string };

export type NasaMeasure = {
  value: number | string | null;
  unit: string | null;
  range: string | null;
  sample_count: number | null;
  qualifier: string;
  missing: string | null;
};

export type NasaMa7Record = {
  id: string;
  title: LocalizedSourceLabel;
  measures: Record<string, NasaMeasure>;
};

export type NasaMa7Group = {
  id: string;
  title: LocalizedSourceLabel;
  table: string;
  note: LocalizedSourceLabel;
  records: NasaMa7Record[];
};

export type NasaMa7Dataset = {
  schema_version: string;
  dataset_id: 'NASA-MA7-MERCURY-1962';
  source_publisher: string;
  source_title: string;
  source_publication: string;
  source_url: string;
  challenge_link: string;
  data_type: 'HISTORICAL_ACTUAL_REPORTED_MEASUREMENTS';
  is_live: false;
  is_synthetic: false;
  is_inspiration4: false;
  is_current_medical_record: false;
  metric_names: Record<string, LocalizedSourceLabel>;
  unavailable_metrics: string[];
  groups: NasaMa7Group[];
  [key: string]: unknown;
};

export type NasaMa7Summary = {
  group_count: number;
  timepoint_count: number;
  metric_count: number;
  reported_value_count: number;
  recorded_measure_count: number;
};

const SOURCE = require('../../assets/ma7_source.json') as NasaMa7Dataset;

function inspectSource(dataset: NasaMa7Dataset): NasaMa7Summary {
  if (dataset.dataset_id !== 'NASA-MA7-MERCURY-1962' || dataset.is_live !== false || dataset.is_synthetic !== false || dataset.is_current_medical_record !== false || dataset.is_inspiration4 !== false) {
    throw new Error('NASA demo source identity or status is invalid.');
  }
  if (!dataset.source_url.startsWith('https://www.nasa.gov/') || !Array.isArray(dataset.groups) || !dataset.metric_names || !Array.isArray(dataset.unavailable_metrics)) {
    throw new Error('NASA demo provenance is incomplete.');
  }

  let timepoint_count = 0;
  let reported_value_count = 0;
  let recorded_measure_count = 0;
  for (const group of dataset.groups) {
    if (!group.id || !group.table || !Array.isArray(group.records)) throw new Error('NASA demo source group is invalid.');
    for (const record of group.records) {
      timepoint_count += 1;
      for (const [metric, measure] of Object.entries(record.measures || {})) {
        if (!dataset.metric_names[metric]) throw new Error(`Unknown NASA source metric: ${metric}`);
        if (measure.value !== null && typeof measure.value === 'number' && !Number.isFinite(measure.value)) throw new Error('NASA source value is not finite.');
        if (measure.value !== null && typeof measure.value !== 'number' && typeof measure.value !== 'string') throw new Error('NASA source value has an unsupported type.');
        if (measure.value === null && !measure.missing) throw new Error('A missing NASA value must keep its source status.');
        recorded_measure_count += 1;
        if (measure.value !== null) reported_value_count += 1;
      }
    }
  }

  const result = {
    group_count: dataset.groups.length,
    timepoint_count,
    metric_count: Object.keys(dataset.metric_names).length,
    reported_value_count,
    recorded_measure_count,
  };
  if (result.group_count !== 4 || result.timepoint_count !== 19 || result.metric_count !== 18 || result.reported_value_count !== 83) {
    throw new Error('NASA source count audit does not match the published dataset bundle.');
  }
  return result;
}

let cached: { data: NasaMa7Dataset; summary: NasaMa7Summary } | null = null;

export function loadNasaMa7Demo(): { data: NasaMa7Dataset; summary: NasaMa7Summary } {
  if (cached) return cached;
  cached = { data: SOURCE, summary: inspectSource(SOURCE) };
  return cached;
}
