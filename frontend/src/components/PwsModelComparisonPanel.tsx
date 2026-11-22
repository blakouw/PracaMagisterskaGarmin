import { useEffect, useMemo, useState, type KeyboardEvent } from 'react';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';
import type { OptionalAssistedPws, PrimaryPws, TimeSeriesRecord } from '../api/dashboardTypes';
import { scoreChartDomain, symmetricDeltaDomain } from '../utils/chartScale';
import { formatDate, formatScore } from '../utils/formatters';

type Range = 7 | 30 | 90 | 'all';

interface Props {
  records: TimeSeriesRecord[];
  primary: PrimaryPws;
  localAssisted: OptionalAssistedPws;
  externalAssisted?: OptionalAssistedPws;
  range: Range;
  onRangeChange: (range: Range) => void;
  error?: string | null;
}

const rangeOptions = [7, 30, 90, 'all'] as const;

interface DateAxisTickProps {
  x?: number;
  y?: number;
  payload?: { value?: string | number };
  selectedDate: string | null;
  onSelect: (date: string) => void;
}

function DateAxisTick({ x = 0, y = 0, payload, selectedDate, onSelect }: DateAxisTickProps) {
  const value = payload?.value;
  if (value === undefined) return null;
  const date = String(value);
  const selected = date === selectedDate;

  function handleKeyDown(event: KeyboardEvent<SVGGElement>) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onSelect(date);
    }
  }

  return (
    <g
      className={`selectable-date-tick${selected ? ' selected' : ''}`}
      transform={`translate(${x},${y})`}
      role="button"
      tabIndex={0}
      aria-label={`Pokaż wyniki PWS dla ${date}`}
      aria-pressed={selected}
      onClick={() => onSelect(date)}
      onKeyDown={handleKeyDown}
    >
      <text x={0} y={0} dy={16} textAnchor="middle">
        {date}
      </text>
    </g>
  );
}

export function PwsModelComparisonPanel({ records, primary, localAssisted, externalAssisted, range, onRangeChange, error }: Props) {
  const chartData = useMemo(() => records.map((record) => ({ ...record })), [records]);
  const [selectedDate, setSelectedDate] = useState<string | null>(() => records[records.length - 1]?.date ?? null);
  useEffect(() => {
    setSelectedDate((current) => (
      current && records.some((record) => record.date === current)
        ? current
        : records[records.length - 1]?.date ?? null
    ));
  }, [records]);
  const selectedRecord = useMemo(
    () => records.find((record) => record.date === selectedDate) ?? records[records.length - 1] ?? null,
    [records, selectedDate]
  );
  const scoreDomain = useMemo(
    () => scoreChartDomain(records, ['pws_deterministic', 'optional_assisted_pws', 'external_assisted_pws']),
    [records]
  );
  const deltaDomain = useMemo(
    () => symmetricDeltaDomain(records, ['optional_assisted_delta_from_deterministic', 'external_assisted_delta_from_deterministic']),
    [records]
  );
  const localCount = records.filter((record) => record.optional_assisted_pws !== null && record.optional_assisted_pws !== undefined).length;
  const externalCount = records.filter((record) => record.external_assisted_pws !== null && record.external_assisted_pws !== undefined).length;
  const externalName = externalAssisted?.model ? `OpenAI · ${externalAssisted.model}` : 'Model zewnętrzny · OpenAI';
  const selectedPrimaryScore = selectedRecord ? selectedRecord.pws_deterministic : primary.score;
  const selectedLocalScore = selectedRecord
    ? selectedRecord.optional_assisted_pws
    : localAssisted.available ? localAssisted.score : null;
  const selectedExternalScore = selectedRecord
    ? selectedRecord.external_assisted_pws
    : externalAssisted?.available ? externalAssisted.score : null;
  const selectedLocalDelta = selectedRecord
    ? selectedRecord.optional_assisted_delta_from_deterministic
    : localAssisted.delta_from_deterministic;
  const selectedExternalDelta = selectedRecord
    ? selectedRecord.external_assisted_delta_from_deterministic
    : externalAssisted?.delta_from_deterministic;
  const formatDelta = (value: number | null | undefined) => {
    if (value === null || value === undefined) return 'Brak różnicy';
    const prefix = value > 0 ? '+' : '';
    return `${prefix}${value.toLocaleString('pl-PL', { maximumFractionDigits: 2 })} pkt`;
  };

  return (
    <section className="card wide model-comparison" aria-label="Porównanie wariantów PWS w czasie">
      <div className="card-heading">
        <div>
          <p className="eyebrow">Porównanie modeli</p>
          <h2>Deterministyczny, lokalny LLM i model zewnętrzny</h2>
        </div>
        <div className="model-comparison-heading-actions">
          <div className="segmented" role="group" aria-label="Zakres porównania modeli">
            {rangeOptions.map((option) => (
              <button
                key={option}
                type="button"
                className={range === option ? 'active' : ''}
                onClick={() => onRangeChange(option)}
              >
                {option === 'all' ? 'Całość' : `${option} dni`}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error ? <p className="notice error-text">{error}</p> : null}

      <p className="comparison-selected-date">Wyniki PWS: <strong>{formatDate(selectedRecord?.date)}</strong></p>
      <div className="comparison-summary" aria-label="Wyniki wariantów PWS dla wybranego dnia">
        <div>
          <span>Deterministyczny PWS</span>
          <strong>{formatScore(selectedPrimaryScore)}</strong>
          <small className="comparison-reference">Punkt odniesienia · 0 pkt</small>
        </div>
        <div>
          <span>Lokalny LLM</span>
          <strong>{formatScore(selectedLocalScore)}</strong>
          <small>{localCount} dni z analizą</small>
          <small className="comparison-delta local">Różnica: {formatDelta(selectedLocalDelta)}</small>
        </div>
        <div>
          <span>{externalName}</span>
          <strong>{formatScore(selectedExternalScore)}</strong>
          <small>{externalCount} dni z analizą</small>
          <small className="comparison-delta external">Różnica: {formatDelta(selectedExternalDelta)}</small>
        </div>
      </div>

      {selectedExternalScore === null || selectedExternalScore === undefined ? (
        <p className="notice">Wariant OpenAI nie jest dostępny dla wybranego dnia. Wykres zachowuje istniejące wartości historyczne i nie zastępuje ich zerami.</p>
      ) : null}

      <div className="chart-section-heading">
        <span>Wyniki PWS</span>
      </div>
      <div className="chart-wrap model-score-chart">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart
            data={chartData}
            margin={{ top: 12, right: 16, left: 0, bottom: 0 }}
            onClick={({ activeLabel }) => {
              if (activeLabel !== undefined && records.some((record) => record.date === String(activeLabel))) {
                setSelectedDate(String(activeLabel));
              }
            }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              minTickGap={20}
              height={38}
              tick={<DateAxisTick selectedDate={selectedRecord?.date ?? null} onSelect={setSelectedDate} />}
            />
            <YAxis domain={scoreDomain} allowDataOverflow tickCount={7} width={48} />
            <Tooltip formatter={(value, name) => [value === null ? 'Brak danych' : Number(value).toLocaleString('pl-PL', { maximumFractionDigits: 2 }), String(name ?? '')]} />
            <Legend />
            {selectedRecord ? <ReferenceLine x={selectedRecord.date} stroke="#FFFFFF" strokeOpacity={0.6} /> : null}
            <Line type="monotone" dataKey="pws_deterministic" name="Deterministyczny PWS" stroke="#FFFFFF" connectNulls={false} dot={false} strokeWidth={3} activeDot={{ r: 4 }} />
            <Line type="monotone" dataKey="optional_assisted_pws" name="Lokalny LLM" stroke="#00693C" connectNulls={false} dot={false} strokeWidth={3} strokeDasharray="8 4" activeDot={{ r: 4 }} />
            <Line type="monotone" dataKey="external_assisted_pws" name="OpenAI" stroke="#A71930" connectNulls={false} dot={false} strokeWidth={3} strokeDasharray="3 3" activeDot={{ r: 4 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="chart-scale-note">Skala pionowa jest zawężona do widocznych wyników, dzięki czemu niewielkie różnice pozostają czytelne.</p>

      <div className="comparison-delta-section">
        <div className="chart-section-heading">
          <span>Odchylenie od wyniku deterministycznego</span>
        </div>
        <div className="chart-wrap delta-chart-wrap">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={chartData} margin={{ top: 12, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" minTickGap={20} />
              <YAxis
                domain={deltaDomain}
                allowDataOverflow
                width={52}
                tickFormatter={(value) => `${value > 0 ? '+' : ''}${value}`}
              />
              <ReferenceLine y={0} stroke="#9eacb7" strokeWidth={1.5} />
              <Tooltip formatter={(value, name) => [formatDelta(Number(value)), String(name ?? '')]} />
              <Legend />
              <Line type="linear" dataKey="optional_assisted_delta_from_deterministic" name="Lokalny LLM vs PWS" stroke="#00693C" connectNulls={false} dot={false} strokeWidth={3} />
              <Line type="linear" dataKey="external_assisted_delta_from_deterministic" name="OpenAI vs PWS" stroke="#A71930" connectNulls={false} dot={false} strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <p className="chart-scale-note">Wartość dodatnia oznacza wynik modelu powyżej PWS deterministycznego, a ujemna – poniżej.</p>
      </div>
    </section>
  );
}
