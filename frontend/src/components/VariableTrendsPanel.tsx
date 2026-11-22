import { useMemo, useState } from 'react';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';
import type { TimeSeriesRecord } from '../api/dashboardTypes';
import { weightChartDomain } from '../utils/chartScale';

interface Props {
  records: TimeSeriesRecord[];
}

type SeriesDef = {
  sourceKey: keyof TimeSeriesRecord;
  chartKey: string;
  label: string;
  color: string;
  scale?: 'seconds_to_hours';
};

const dailySeries: SeriesDef[] = [
  { sourceKey: 'resting_hr_bpm', chartKey: 'resting_hr_bpm', label: 'Tętno spoczynkowe', color: '#D00000' },
  { sourceKey: 'sleep_seconds', chartKey: 'sleep_hours', label: 'Sen w godzinach', color: '#0066CC', scale: 'seconds_to_hours' },
  { sourceKey: 'hrv_last_night_avg_ms', chartKey: 'hrv_last_night_avg_ms', label: 'HRV', color: '#7A00CC' },
  { sourceKey: 'avg_stress', chartKey: 'avg_stress', label: 'Stres', color: '#FFB000' },
  { sourceKey: 'activity_duration_weighted_average_hr_bpm', chartKey: 'activity_duration_weighted_average_hr_bpm', label: 'Średnie tętno aktywności', color: '#008A4B' },
  { sourceKey: 'activity_maximum_hr_bpm', chartKey: 'activity_maximum_hr_bpm', label: 'Maksymalne tętno aktywności', color: '#A71930' },
  { sourceKey: 'avg_sleep_spo2', chartKey: 'avg_sleep_spo2', label: 'Sleep SpO2', color: '#00A0C6' }
];

const deterministicWeightSeries: SeriesDef[] = [
  { sourceKey: 'weight_lq', chartKey: 'weight_lq', label: 'Waga LQ - Load Quality', color: '#0066CC' },
  { sourceKey: 'weight_rec', chartKey: 'weight_rec', label: 'Waga REC - Recovery', color: '#008A4B' },
  { sourceKey: 'weight_cap', chartKey: 'weight_cap', label: 'Waga CAP - Capacity', color: '#FFB000' },
  { sourceKey: 'weight_vs', chartKey: 'weight_vs', label: 'Waga VS - Vital Stability', color: '#D00000' }
];

const localLlmWeightSeries: SeriesDef[] = [
  { sourceKey: 'local_llm_weight_lq', chartKey: 'local_llm_weight_lq', label: 'Waga LQ - Load Quality', color: '#0066CC' },
  { sourceKey: 'local_llm_weight_rec', chartKey: 'local_llm_weight_rec', label: 'Waga REC - Recovery', color: '#008A4B' },
  { sourceKey: 'local_llm_weight_cap', chartKey: 'local_llm_weight_cap', label: 'Waga CAP - Capacity', color: '#FFB000' },
  { sourceKey: 'local_llm_weight_vs', chartKey: 'local_llm_weight_vs', label: 'Waga VS - Vital Stability', color: '#D00000' }
];

const openAiWeightSeries: SeriesDef[] = [
  { sourceKey: 'openai_weight_lq', chartKey: 'openai_weight_lq', label: 'Waga LQ - Load Quality', color: '#0066CC' },
  { sourceKey: 'openai_weight_rec', chartKey: 'openai_weight_rec', label: 'Waga REC - Recovery', color: '#008A4B' },
  { sourceKey: 'openai_weight_cap', chartKey: 'openai_weight_cap', label: 'Waga CAP - Capacity', color: '#FFB000' },
  { sourceKey: 'openai_weight_vs', chartKey: 'openai_weight_vs', label: 'Waga VS - Vital Stability', color: '#D00000' }
];

function numericValue(record: TimeSeriesRecord, series: SeriesDef): number | null {
  const raw = record[series.sourceKey];
  if (typeof raw !== 'number' || Number.isNaN(raw)) return null;
  if (series.scale === 'seconds_to_hours') return Number((raw / 3600).toFixed(2));
  return raw;
}

function available(series: SeriesDef, records: TimeSeriesRecord[]) {
  return records.some((record) => numericValue(record, series) !== null);
}

function buildChartData(records: TimeSeriesRecord[], seriesList: SeriesDef[]) {
  return records.map((record) => {
    const point: Record<string, string | number | null> = { date: record.date };
    seriesList.forEach((series) => {
      point[series.chartKey] = numericValue(record, series);
    });
    return point;
  });
}

function formatWeight(value: unknown): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return 'Brak danych';
  return `${(value * 100).toFixed(1).replace('.', ',')}%`;
}

interface WeightChartProps {
  records: TimeSeriesRecord[];
  series: SeriesDef[];
  title: string;
  ariaLabel: string;
}

function WeightTrendsChart({ records, series, title, ariaLabel }: WeightChartProps) {
  const availableSeries = useMemo(() => series.filter((item) => available(item, records)), [records, series]);
  const chartData = useMemo(() => buildChartData(records, availableSeries), [records, availableSeries]);
  const domain = useMemo(
    () => weightChartDomain(records, availableSeries.map((item) => item.sourceKey)),
    [records, availableSeries]
  );

  return (
    <div className="subchart-block" aria-label={ariaLabel}>
      <div className="card-heading compact">
        <h3>{title}</h3>
      </div>
      {availableSeries.length === 0 ? (
        <p className="notice">Brak historycznych wag dla tego wariantu w aktualnym zakresie.</p>
      ) : (
        <div className="chart-wrap compact-chart">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={chartData} margin={{ top: 12, right: 16, left: 8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" minTickGap={20} />
              <YAxis
                domain={domain}
                allowDataOverflow
                tickCount={6}
                width={56}
                tickFormatter={(value) => `${Math.round(Number(value) * 100)}%`}
              />
              <Tooltip formatter={(value, name) => [formatWeight(value), String(name ?? '')]} />
              <Legend />
              {availableSeries.map((item) => (
                <Line
                  key={item.chartKey}
                  type="monotone"
                  dataKey={item.chartKey}
                  name={item.label}
                  stroke={item.color}
                  connectNulls={false}
                  dot={false}
                  strokeWidth={2.25}
                  activeDot={{ r: 4 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
      <p className="chart-scale-note">Oś pionowa dopasowuje się do widocznego zakresu wag i nie zmienia wartości źródłowych.</p>
    </div>
  );
}

export function VariableTrendsPanel({ records }: Props) {
  const [visible, setVisible] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(dailySeries.map((series) => [series.chartKey, ['resting_hr_bpm', 'sleep_hours', 'hrv_last_night_avg_ms'].includes(series.chartKey)]))
  );
  const availableDaily = useMemo(() => dailySeries.filter((series) => available(series, records)), [records]);
  const dailyData = useMemo(() => buildChartData(records, availableDaily), [records, availableDaily]);

  return (
    <section className="card wide" aria-label="Trendy sygnałów dziennych">
      <div className="card-heading">
        <div>
          <p className="eyebrow">Sygnały</p>
          <h2>Dzienne zmienne zdrowia i aktywności</h2>
        </div>
      </div>
      {availableDaily.length === 0 ? (
        <p className="notice">Brak dziennych sygnałów w aktualnym payloadzie dashboardu.</p>
      ) : (
        <>
          <div className="series-toggles">
            {availableDaily.map((series) => (
              <label key={series.chartKey}>
                <input
                  type="checkbox"
                  checked={visible[series.chartKey] !== false}
                  onChange={(event) => setVisible((current) => ({ ...current, [series.chartKey]: event.target.checked }))}
                />
                {series.label}
              </label>
            ))}
          </div>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={dailyData} margin={{ top: 12, right: 16, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" minTickGap={20} />
                <YAxis />
                <Tooltip formatter={(value, name) => [value === null ? 'Brak danych' : value, String(name ?? '')]} />
                <Legend />
                {availableDaily.map((series) =>
                  visible[series.chartKey] !== false ? (
                    <Line key={series.chartKey} type="monotone" dataKey={series.chartKey} name={series.label} stroke={series.color} connectNulls={false} dot={false} />
                  ) : null
                )}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
      <WeightTrendsChart
        records={records}
        series={deterministicWeightSeries}
        title="Wagi komponentów PWS w czasie — wariant deterministyczny"
        ariaLabel="Wagi deterministyczne PWS w czasie"
      />
      <WeightTrendsChart
        records={records}
        series={localLlmWeightSeries}
        title="Wagi komponentów PWS w czasie — lokalny LLM"
        ariaLabel="Wagi lokalnego LLM w czasie"
      />
      <WeightTrendsChart
        records={records}
        series={openAiWeightSeries}
        title="Wagi komponentów PWS w czasie — OpenAI"
        ariaLabel="Wagi OpenAI w czasie"
      />
    </section>
  );
}
