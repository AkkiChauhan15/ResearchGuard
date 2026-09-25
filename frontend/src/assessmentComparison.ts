import type { ProviderAssessment } from './types.ts'

export type ComparisonField = 'label' | 'confidence' | 'quote_check_passed'

export function structuralDisagreementFields(
  primary: ProviderAssessment,
  second: ProviderAssessment,
): ComparisonField[] {
  const fields: ComparisonField[] = ['label', 'confidence', 'quote_check_passed']
  return fields.filter((field) => primary[field] !== second[field])
}
