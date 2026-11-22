import type { TimeSeriesRecord } from '../api/dashboardTypes';

type NumericSeriesKey = keyof TimeSeriesRecord;

function finiteValues(records: TimeSeriesRecord[], keys: NumericSeriesKey[]): number[] {
  return records.flatMap((record) =>
    keys.flatMap((key) => {
      const value = record[key];
      return typeof value === 'number' && Number.isFinite(value) ? [value] : [];
    })
  );
}

export function scoreChartDomain(
  records: TimeSeriesRecord[],
  keys: NumericSeriesKey[],
  minimumSpan = 12
): [number, number] {
  const values = finiteValues(records, keys);
  if (values.length === 0) return [0, 100];

  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const rawSpan = maximum - minimum;
  const requestedSpan = Math.max(minimumSpan, rawSpan * 1.2, rawSpan + 4);
  let lower = (minimum + maximum - requestedSpan) / 2;
  let upper = lower + requestedSpan;

  if (lower < 0) {
    upper -= lower;
    lower = 0;
  }
  if (upper > 100) {
    lower -= upper - 100;
    upper = 100;
  }

  return [Math.max(0, Math.floor(lower)), Math.min(100, Math.ceil(upper))];
}

export function symmetricDeltaDomain(
  records: TimeSeriesRecord[],
  keys: NumericSeriesKey[]
): [number, number] {
  const values = finiteValues(records, keys);
  const maximumAbsolute = values.length > 0 ? Math.max(...values.map(Math.abs)) : 0;
  const roundedLimit = Math.max(1, Math.ceil(maximumAbsolute * 1.2 * 2) / 2);
  return [-roundedLimit, roundedLimit];
}

export function weightChartDomain(
  records: TimeSeriesRecord[],
  keys: NumericSeriesKey[],
  minimumSpan = 0.12
): [number, number] {
  const values = finiteValues(records, keys);
  if (values.length === 0) return [0, 1];

  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const rawSpan = maximum - minimum;
  const requestedSpan = Math.max(minimumSpan, rawSpan * 1.2);
  let lower = (minimum + maximum - requestedSpan) / 2;
  let upper = lower + requestedSpan;

  if (lower < 0) {
    upper -= lower;
    lower = 0;
  }
  if (upper > 1) {
    lower -= upper - 1;
    upper = 1;
  }

  return [
    Math.max(0, Math.floor(lower * 100) / 100),
    Math.min(1, Math.ceil(upper * 100) / 100)
  ];
}
