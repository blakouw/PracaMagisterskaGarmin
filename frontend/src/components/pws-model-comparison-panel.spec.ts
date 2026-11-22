import { TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { fireEvent, screen, within } from '@testing-library/dom';
import type { Chart } from 'chart.js';
import { afterEach, describe, expect, test } from 'vitest';
import type { OptionalAssistedPws, PrimaryPws, TimeSeriesRecord } from '../api/dashboardTypes';
import { ChartStub, stubChart } from '../test/chart-stub';
import { PwsModelComparisonPanel } from './pws-model-comparison-panel';

const records: TimeSeriesRecord[] = [
  {
    date: '2026-05-20',
    pws_deterministic: 70,
    optional_assisted_pws: 71.1,
    optional_assisted_delta_from_deterministic: 1.1,
    external_assisted_pws: 69.8,
    external_assisted_delta_from_deterministic: -0.2
  },
  {
    date: '2026-05-22',
    pws_deterministic: 78.42,
    optional_assisted_pws: 79.05,
    optional_assisted_delta_from_deterministic: 0.63,
    external_assisted_pws: 80.2,
    external_assisted_delta_from_deterministic: 1.78
  }
];

const primary: PrimaryPws = {
  score_type: 'deterministic',
  score_field: 'pws_deterministic',
  score: 78.42,
  computed: true,
  status: 'computed_full_coverage',
  label_id: 'balanced',
  label: 'stabilny',
  coverage_ratio: 1,
  coverage_tier: 'full'
};

const localAssisted: OptionalAssistedPws = {
  available: true,
  status: 'available_validated_assisted_variant',
  score: 79.05,
  delta_from_deterministic: 0.63,
  must_not_replace_primary_score: true
};

const externalAssisted: OptionalAssistedPws = {
  available: true,
  status: 'available_validated_assisted_variant',
  score: 80.2,
  delta_from_deterministic: 1.78,
  model: 'test-model',
  must_not_replace_primary_score: true
};

afterEach(() => TestBed.resetTestingModule());

describe('PwsModelComparisonPanel date selection', () => {
  test('updates all summary values after selecting a date on the PWS chart', async () => {
    TestBed.configureTestingModule({ imports: [PwsModelComparisonPanel] });
    stubChart(PwsModelComparisonPanel);
    const fixture = TestBed.createComponent(PwsModelComparisonPanel);
    fixture.componentRef.setInput('records', records);
    fixture.componentRef.setInput('primary', primary);
    fixture.componentRef.setInput('localAssisted', localAssisted);
    fixture.componentRef.setInput('externalAssisted', externalAssisted);
    fixture.componentRef.setInput('range', 30);
    fixture.autoDetectChanges();

    const chart = fixture.debugElement.query(By.directive(ChartStub)).injector.get(ChartStub);
    const layout = {
      width: 500,
      chartArea: { top: 10, bottom: 240 },
      data: chart.data(),
      scales: {
        x: {
          top: 240,
          ticks: records.map((_record, value) => ({ value })),
          getLabelForValue: (value: number) => records[value].date,
          getPixelForTick: (value: number) => 40 + value * 400,
          getPixelForValue: (value: number) => 40 + value * 400
        }
      }
    };
    chart.plugins()[0].afterLayout?.(layout as unknown as Chart<'line'>, {}, {});
    await fixture.whenStable();

    const summary = screen.getByLabelText('Wyniki wariantów PWS dla wybranego dnia');
    expect(within(summary).getByText('78,42')).toBeInTheDocument();
    expect(within(summary).getByText('79,05')).toBeInTheDocument();
    expect(within(summary).getByText('80,2')).toBeInTheDocument();

    const dateButton = await screen.findByRole('button', { name: 'Pokaż wyniki PWS dla 2026-05-20' });
    fireEvent.click(dateButton);
    await fixture.whenStable();

    expect(dateButton).toHaveAttribute('aria-pressed', 'true');
    expect(within(summary).getByText('70')).toBeInTheDocument();
    expect(within(summary).getByText('71,1')).toBeInTheDocument();
    expect(within(summary).getByText('69,8')).toBeInTheDocument();
  });
});
