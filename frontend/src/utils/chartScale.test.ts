import { describe, expect, test } from 'vitest';
import type { TimeSeriesRecord } from '../api/dashboardTypes';
import { scoreChartDomain, symmetricDeltaDomain, weightChartDomain } from './chartScale';

const records: TimeSeriesRecord[] = [
  {
    date: '2026-08-20',
    pws_deterministic: 94.6,
    optional_assisted_pws: 95.1,
    external_assisted_pws: 95.5,
    optional_assisted_delta_from_deterministic: 0.5,
    external_assisted_delta_from_deterministic: 0.9
  },
  {
    date: '2026-08-21',
    pws_deterministic: 90.2,
    optional_assisted_pws: null,
    external_assisted_pws: 91.4,
    optional_assisted_delta_from_deterministic: null,
    external_assisted_delta_from_deterministic: 1.2
  }
];

describe('chart scales', () => {
  test('zooms the score axis while retaining every visible score', () => {
    const domain = scoreChartDomain(records, ['pws_deterministic', 'optional_assisted_pws', 'external_assisted_pws']);
    expect(domain).not.toEqual([0, 100]);
    expect(domain[0]).toBeLessThanOrEqual(90.2);
    expect(domain[1]).toBeGreaterThanOrEqual(95.5);
  });

  test('builds a symmetric delta axis around zero', () => {
    const domain = symmetricDeltaDomain(records, ['optional_assisted_delta_from_deterministic', 'external_assisted_delta_from_deterministic']);
    expect(domain[0]).toBe(-domain[1]);
    expect(domain[1]).toBeGreaterThanOrEqual(1.2);
  });

  test('zooms weight axes without excluding source values', () => {
    const weightRecords: TimeSeriesRecord[] = [
      { date: '2026-08-20', pws_deterministic: 90, local_llm_weight_lq: 0.19, local_llm_weight_rec: 0.31 },
      { date: '2026-08-21', pws_deterministic: 91, local_llm_weight_lq: 0.21, local_llm_weight_rec: 0.34 }
    ];
    const domain = weightChartDomain(weightRecords, ['local_llm_weight_lq', 'local_llm_weight_rec']);
    expect(domain).not.toEqual([0, 1]);
    expect(domain[0]).toBeLessThanOrEqual(0.19);
    expect(domain[1]).toBeGreaterThanOrEqual(0.34);
  });
});
