import re
from .schemas import Claim, Context, Decision, Review, ReviewInput


def create_review(data: ReviewInput) -> Review:
    if not data.text.strip():
        raise ValueError('Paste an answer before creating a review.')
    segments = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', data.text) if s.strip()]
    if len(segments) > 12:
        raise ValueError('Use an excerpt with at most 12 sentences, or AI extraction on a shorter excerpt.')
    missing = [k for k, v in data.context.model_dump().items() if not v.strip()]
    questions = ['Which exact manufacturer and catalog identifier were used?'] if not data.context.reagent.strip() and data.intended_use == 'assay interpretation' else []
    return Review(mode='live', original_input=data, missing_fields=missing,
                  extraction_method='Editable sentence segments; not AI claim extraction',
                  claims=[Claim(original_span=s, text=s, missing_context=questions) for s in segments],
                  notices=['User-reported context and observations are not independently verified.',
                           'No automatic disk storage. Download an export to save this review.'])


def get_claim(review, claim_id):
    for claim in review.claims:
        if claim.claim_id == claim_id:
            return claim
    raise ValueError('Unknown claim.')


def edit_claim(review, claim_id, text):
    if review.mode != 'live':
        raise ValueError('Start a live review to change the curated demonstration claim.')
    if not isinstance(text, str) or not text.strip() or len(text) > 12000:
        raise ValueError('Claim text must contain 1–12000 characters.')
    claim = get_claim(review, claim_id)
    claim.text = text.strip()
    claim.type = 'unclassified'
    claim.observations = []
    claim.inferences = []
    claim.assessment = None
    claim.assessment_error = None
    claim.decision = Decision()
    # Retain retrieval history, but detach its evidence from this revised claim.
    for attempt in review.attempts:
        if attempt.claim_id == claim_id:
            attempt.claim_id = claim_id + ':prior_revision'
    review.validation_results.append('Claim edited: earlier evidence and decisions invalidated.')


def edit_context(review: Review, context: Context) -> None:
    if review.mode != 'live':
        raise ValueError('Start a live review to change curated demonstration context.')
    if context == review.original_input.context:
        return
    review.original_input.context = context
    review.missing_fields = [key for key, value in context.model_dump().items() if not value.strip()]
    question = 'Which exact manufacturer and catalog identifier were used?'
    needs_reagent = not context.reagent.strip() and review.original_input.intended_use == 'assay interpretation'
    for claim in review.claims:
        claim.assessment = None
        claim.assessment_error = None
        claim.decision = Decision()
        claim.missing_context = [item for item in claim.missing_context if item != question]
        if needs_reagent:
            claim.missing_context.append(question)
    current_claim_ids = {claim.claim_id for claim in review.claims}
    for attempt in review.attempts:
        if attempt.claim_id in current_claim_ids:
            attempt.claim_id += ':prior_context'
    review.validation_results.append('Context edited: earlier evidence and decisions invalidated.')


def decide(review, claim_id, decision):
    claim = get_claim(review, claim_id)
    if not claim.assessment:
        raise ValueError('There is no assessment to review.')
    if decision.status == 'accepted':
        decision.final_wording = claim.assessment.suggested_wording
    elif decision.status == 'edited' and not decision.final_wording.strip():
        raise ValueError('Enter your revised wording before marking it edited.')
    elif decision.status in ('pending', 'rejected'):
        decision.final_wording = ''
    claim.decision = decision
