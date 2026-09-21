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
  provider: string
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
  persistence_configured: boolean
  persistence_state: 'configured' | 'unavailable_missing_configuration'
  chat_persistence_configured: boolean
  chat_persistence_state: 'configured' | 'unavailable_missing_configuration'
}

export interface AuthenticatedUser {
  user_id: string
  email: string | null
}

export interface SavedReviewSummary {
  saved_id: string
  review_id: string
  schema_version: number
  revision: number
  mode: 'demo' | 'live'
  title: string
  created_at: string
  updated_at: string
}

export interface SavedReviewRecord extends SavedReviewSummary {
  review: Review
}

export interface SavedReviewList {
  items: SavedReviewSummary[]
}

export type ChatProviderId = 'groq' | 'openrouter' | 'gemini' | 'nvidia'

export interface ChatModelOption {
  id: string
  label: string
}

export interface ChatProviderOption {
  id: ChatProviderId
  display_name: string
  configured: boolean
  state: 'configured' | 'missing_api_key' | 'free_tier_unconfirmed'
  models: ChatModelOption[]
}

export interface ChatProviderStatus {
  config_version: string
  fallback_enabled: boolean
  providers: ChatProviderOption[]
}

export interface ChatMessageInput {
  role: 'user' | 'assistant'
  content: string
}

export interface SavedChatMessage extends ChatMessageInput {
  timestamp: string
  provider: string | null
  model: string | null
  fallback_used: boolean
}

export interface SavedChatSummary {
  chat_id: string
  schema_version: number
  revision: number
  title: string
  message_count: number
  last_provider: string
  last_model: string
  created_at: string
  updated_at: string
}

export interface SavedChatRecord extends SavedChatSummary {
  messages: SavedChatMessage[]
}

export interface SavedChatList {
  items: SavedChatSummary[]
}

export interface ChatAttempt {
  provider: ChatProviderId
  model: string
  status: string
}

export interface ChatResponse {
  success: true
  provider: ChatProviderId
  requested_provider: ChatProviderId
  model: string
  requested_model: string
  answer: string
  fallback_used: boolean
  attempts: ChatAttempt[]
  chat: SavedChatRecord
}
