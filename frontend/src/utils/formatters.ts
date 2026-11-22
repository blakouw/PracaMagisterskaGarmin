export function formatNumber(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return 'Brak danych';
  return value.toLocaleString('pl-PL', { maximumFractionDigits: digits, minimumFractionDigits: digits });
}

export function formatScore(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return 'Brak wyniku';
  return value.toLocaleString('pl-PL', { maximumFractionDigits: 2, minimumFractionDigits: 0 });
}

export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return 'Brak danych';
  return `${Math.round(value * 100)}%`;
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return 'Brak danych';
  return value;
}

export function shortId(value: string | undefined): string {
  if (!value) return 'Brak snapshotu';
  if (value.length <= 22) return value;
  return `${value.slice(0, 14)}...${value.slice(-6)}`;
}

export function titleCase(value: string | null | undefined): string {
  if (!value) return 'Brak danych';
  const normalized = value.replace(/_/g, ' ');
  return normalized.charAt(0).toLocaleUpperCase('pl-PL') + normalized.slice(1);
}
