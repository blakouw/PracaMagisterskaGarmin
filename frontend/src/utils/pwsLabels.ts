export const PWS_COMPONENT_LABELS: Record<string, string> = {
  LQ: 'Load Quality',
  REC: 'Recovery',
  CAP: 'Capacity',
  VS: 'Vital Stability'
};

export function formatPwsComponentLabel(key: string): string {
  const label = PWS_COMPONENT_LABELS[key.toUpperCase()];
  return label ? `${key.toUpperCase()} - ${label}` : key;
}
