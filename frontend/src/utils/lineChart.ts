import type { ChartData, ChartOptions } from 'chart.js';
import type { TimeSeriesRecord } from '../api/dashboardTypes';

const axisColor = '#bdbdbd';
const gridColor = '#505050';

export type LineData = ChartData<'line', (number | null)[], string>;

export interface LineSeries {
  sourceKey: keyof TimeSeriesRecord;
  label: string;
  color: string;
  scale?: 'seconds_to_hours';
  dash?: number[];
  width?: number;
  linear?: boolean;
}

interface LineOptions {
  domain?: [number, number];
  tickCount?: number;
  tickFormat?: (value: number) => string;
  valueFormat?: (value: number) => string;
  legend?: boolean;
  zeroLine?: boolean;
  beginAtZero?: boolean;
  dateTickButtons?: boolean;
  datePrefix?: boolean;
  onDateSelect?: (date: string) => void;
}

export function seriesValue(record: TimeSeriesRecord, series: LineSeries): number | null {
  const value = record[series.sourceKey];
  if (typeof value !== 'number' || !Number.isFinite(value)) return null;
  return series.scale === 'seconds_to_hours' ? Number((value / 3600).toFixed(2)) : value;
}

export function hasSeries(records: TimeSeriesRecord[], series: LineSeries): boolean {
  return records.some(record => seriesValue(record, series) !== null);
}

export function lineData(records: TimeSeriesRecord[], series: readonly LineSeries[]): LineData {
  return {
    labels: records.map(record => record.date),
    datasets: series.map(item => ({
      label: item.label,
      data: records.map(record => seriesValue(record, item)),
      borderColor: item.color,
      backgroundColor: item.color,
      borderWidth: item.width ?? 2.25,
      borderDash: item.dash,
      cubicInterpolationMode: item.linear ? 'default' : 'monotone',
      spanGaps: false,
      pointRadius: 0,
      pointHoverRadius: 4
    }))
  };
}

export function lineOptions(options: LineOptions = {}): ChartOptions<'line'> {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 12, right: 14, left: 8 } },
    interaction: { mode: 'index', intersect: false, axis: 'x' },
    onClick: options.onDateSelect
      ? (event, _items, chart) => {
          if (event.x === null) return;
          const index = chart.scales['x'].getValueForPixel(event.x);
          const date = index === undefined ? undefined : chart.data.labels?.[index];
          if (typeof date === 'string') options.onDateSelect?.(date);
        }
      : undefined,
    scales: {
      x: {
        type: 'category',
        grid: { color: gridColor },
        border: { color: gridColor, dash: [3, 3] },
        ticks: {
          color: options.dateTickButtons ? 'transparent' : axisColor,
          maxRotation: 0,
          autoSkipPadding: 20,
          font: { size: 12 }
        }
      },
      y: {
        type: 'linear',
        beginAtZero: options.beginAtZero,
        min: options.domain?.[0],
        max: options.domain?.[1],
        grid: {
          color: context => options.zeroLine && context.tick?.value === 0 ? '#9eacb7' : gridColor,
          lineWidth: context => options.zeroLine && context.tick?.value === 0 ? 1.5 : 1
        },
        border: { color: gridColor, dash: [3, 3] },
        ticks: {
          color: axisColor,
          count: options.tickCount,
          maxTicksLimit: 7,
          callback: options.tickFormat ? value => options.tickFormat!(Number(value)) : undefined
        }
      }
    },
    plugins: {
      legend: {
        display: options.legend ?? true,
        position: 'bottom',
        labels: { color: '#ffffff', usePointStyle: true, pointStyle: 'line', boxWidth: 16, padding: 14 }
      },
      tooltip: {
        backgroundColor: '#171717',
        borderColor: '#4a4a4a',
        borderWidth: 1,
        callbacks: {
          title: items => {
            const date = items[0]?.label ?? '';
            return options.datePrefix ? 'Data: ' + date : date;
          },
          label: item => {
            const value = item.parsed.y;
            const formatted = value === null
              ? 'Brak danych'
              : (options.valueFormat?.(value) ?? value.toLocaleString('pl-PL', { maximumFractionDigits: 2 }));
            return (item.dataset.label ?? '') + ': ' + formatted;
          }
        }
      }
    }
  };
}
