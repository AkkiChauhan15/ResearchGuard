import assert from 'node:assert/strict'
import test from 'node:test'

import { structuralDisagreementFields } from '../src/assessmentComparison.ts'

const base = {
  assessment_id: 'assessment_fixture_primary',
  provider: 'groq',
  model: 'fixture-primary',
  is_primary: true,
  label: 'supports',
  confidence: 'medium',
  quote_check_passed: true,
  source_ids: ['src_fixture'],
  created_at: '2026-09-25T00:00:00+00:00',
  assessment: {
    status: 'Supported within the stated context',
    evidence: [],
    explanation: 'Primary wording.',
    context_mismatches: [],
    limitations: [],
    suggested_wording: 'Primary suggestion.',
    next_verification_step: 'Primary question?',
  },
}

test('wording differences alone do not produce a disagreement', () => {
  const second = structuredClone(base)
  second.assessment_id = 'assessment_fixture_second'
  second.provider = 'openrouter'
  second.model = 'fixture-second'
  second.is_primary = false
  second.assessment.explanation = 'Different prose with the same structured result.'
  second.assessment.suggested_wording = 'Different wording.'
  assert.deepEqual(structuralDisagreementFields(base, second), [])
})

test('only changed structured fields are reported', () => {
  const second = structuredClone(base)
  second.label = 'uncertain'
  second.confidence = 'low'
  assert.deepEqual(structuralDisagreementFields(base, second), ['label', 'confidence'])
})
