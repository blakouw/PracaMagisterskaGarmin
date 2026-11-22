export function isPartialCoverage(tier: string | null | undefined): boolean {
  return tier === 'partial_eligible' || tier === 'partial';
}

export function isInsufficientCoverage(tier: string | null | undefined): boolean {
  return tier === 'insufficient';
}
