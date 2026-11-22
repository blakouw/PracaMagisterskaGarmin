import { expect, test } from 'vitest';
import { lineData } from './lineChart';

test('preserves missing chart values and converts sleep seconds for display', () => {
  const data = lineData([
    { date: '2026-05-20', pws_deterministic: null, sleep_seconds: 23400 },
    { date: '2026-05-21', pws_deterministic: null, sleep_seconds: null },
    { date: '2026-05-22', pws_deterministic: null, sleep_seconds: 0 }
  ], [{ sourceKey: 'sleep_seconds', label: 'Sen', color: '#0066CC', scale: 'seconds_to_hours' }]);

  expect(data.labels).toEqual(['2026-05-20', '2026-05-21', '2026-05-22']);
  expect(data.datasets[0].data).toEqual([6.5, null, 0]);
  expect(data.datasets[0].spanGaps).toBe(false);
});
