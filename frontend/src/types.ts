export type IntendedUse =
  | 'topic understanding'
  | 'assay interpretation'
  | 'presentation preparation'
  | 'experiment planning'

export type EvidenceStatus =
  | 'Supported within the stated context'
  | 'Partially supported'
  | 'Conflicting evidence'
  | 'Contradicted by retrieved evidence'
  | 'Insufficient evidence found'

export type AccessState =
  | 'ok'
  | 'no_results'
  | 'partial_access'
  | 'rate_limited'
  | 'fetch_failed'
  | 'parse_failed'

export interface ExperimentalContext {
  organism_model: string
  assay: string
  reagent: string
  conditions: string
}

export interface ReviewInput {
  text: string
  intended_use: IntendedUse
  context: ExperimentalContext
  source_urls: string[]
}

export interface Passage {
  text: string
  location: string
}

export interface Source {
  source_id: string
  retrieval_run_id: string
  url: string
  category: 'pubmed' | 'pmc' | 'manufacturer' | 'synthetic'
  title: string
  authors: string[]
  date: string | null
  doi: string | null
  pmid: string | null
  pmcid: string | null
  access_level: 'metadata' | 'abstract' | 'full text' | 'product document'
  retrieved_at: string
  document_version: string | null
  content_sha256: string
  passages: Passage[]
  limitations: string[]
}

export interface Attempt {
  retrieval_run_id: string
  claim_id: string
  query_or_url: string
  adapter: string
  access_state: AccessState
  timestamp: string
  detail: string
  source_ids: string[]
}

export interface Evidence {
  source_id: string
  passage: string
  location: string
  relationship: 'support' | 'limitation' | 'conflict'
}

export interface Assessment {
  status: EvidenceStatus
  evidence: Evidence[]
  explanation: string
  context_mismatches: string[]
  limitations: string[]
  suggested_wording: string
  next_verification_step: string
}

export interface Decision {
  status: 'pending' | 'accepted' | 'edited' | 'rejected'
  final_wording: string
  notes: string
}

export interface Claim {
  claim_id: string
  original_span: string
  text: string
  type: 'observation' | 'inference' | 'mixed' | 'unclassified'
  observations: string[]
  inferences: string[]
  missing_context: string[]
  assessment: Assessment | null
  assessment_error: string | null
  decision: Decision
}

export interface ModelRun {
  task: string
  claim_id: string | null
  source_ids: string[]
  requested_model: string
  returned_model: string
  prompt_version: string
  timestamp: string
  validation: string[]
}

export interface Review {
  review_id: string
  created_at: string
  mode: 'demo' | 'live'
  original_input: ReviewInput
  missing_fields: string[]
  extraction_method: string
  claims: Claim[]
  attempts: Attempt[]
  sources: Source[]
  model_runs: ModelRun[]
  validation_results: string[]
  notices: string[]
}

export interface ApiConfig {
  model_configured: boolean
  model_state:
    | 'configured'
    | 'unavailable_missing_credentials'
    | 'unavailable_free_tier_unconfirmed'
    | 'unavailable_model_not_free_tier'
    | 'unavailable_provider_disabled'
    | 'unavailable_invalid_configuration'
  model_provider: string
  extraction_model: string | null
  assessment_model: string | null
  model_detail: string
  retention_seconds: number
  mode: string
  auth_configured: boolean
  auth_state: 'configured' | 'unavailable_missing_configuration'
  auth_provider: 'supabase_google'
  live_auth_required: boolean
}

export interface AuthenticatedUser {
  user_id: string
  email: string | null
}
