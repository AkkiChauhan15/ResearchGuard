import json
from .assessment import claim_sources, validate_assessment
from .schemas import Review


def validate_review(review):
    Review.model_validate_json(review.model_dump_json())
    ids = {s.source_id for s in review.sources}
    if len(ids) != len(review.sources):
        raise ValueError('Duplicate source IDs in record.')
    for attempt in review.attempts:
        if not set(attempt.source_ids) <= ids:
            raise ValueError('Retrieval record contains unknown sources.')
    if review.mode == 'live' and any(s.category == 'synthetic' for s in review.sources):
        raise ValueError('Synthetic evidence cannot appear in live reviews.')
    for claim in review.claims:
        if claim.original_span not in review.original_input.text:
            raise ValueError('Original claim span is not present in input.')
        if claim.assessment:
            validate_assessment(claim.assessment, claim_sources(review, claim.claim_id))
            if claim.provider_assessments:
                primary = [item for item in claim.provider_assessments if item.is_primary]
                if len(primary) != 1 or primary[0].assessment != claim.assessment:
                    raise ValueError('Provider assessments must contain exactly one primary matching the canonical assessment.')
                providers = [item.provider for item in claim.provider_assessments]
                if len(providers) != len(set(providers)):
                    raise ValueError('A provider can appear only once for the current claim and evidence.')
                current_sources = {source.source_id: source for source in claim_sources(review, claim.claim_id)}
                for item in claim.provider_assessments:
                    if not item.quote_check_passed:
                        raise ValueError('Provider assessment failed deterministic quotation validation.')
                    if not item.source_ids or not set(item.source_ids) <= set(current_sources):
                        raise ValueError('Provider assessment references stale or unknown evidence.')
                    validate_assessment(
                        item.assessment,
                        [current_sources[source_id] for source_id in item.source_ids],
                    )
        elif claim.decision.status != 'pending':
            raise ValueError('A decision cannot approve an absent assessment.')
        elif claim.provider_assessments:
            raise ValueError('Provider assessments cannot exist without a canonical primary assessment.')
    return review


def export_review(review, fmt):
    validate_review(review)
    record = review.model_dump()
    encoded = json.dumps(record, ensure_ascii=False, indent=2)
    if fmt == 'json':
        return encoded
    if fmt != 'txt':
        raise ValueError('Choose JSON or TXT export.')
    lines = ['Research Guard AI review', 'Demonstration — not a live verification' if review.mode == 'demo' else 'Live review', f'Review: {review.review_id}', f'Created: {review.created_at}', '', 'Original input:', review.original_input.text, '']
    for i, c in enumerate(review.claims, 1):
        lines.extend([f'Claim {i}: {c.text}', f'Researcher decision: {c.decision.status}'])
        if c.assessment:
            a = c.assessment
            lines.extend([f'Evidence status: {a.status}', a.explanation, 'Limitations:', *['- '+s for s in a.limitations], 'Suggested wording: '+a.suggested_wording,'Next verification question: '+a.next_verification_step])
            for e in a.evidence:
                s = next(s for s in review.sources if s.source_id == e.source_id)
                lines.extend([f'{e.relationship}: {s.title} ({s.url}), {e.location}', 'Exact quotation: '+e.passage])
            for provider_assessment in c.provider_assessments:
                role = 'primary' if provider_assessment.is_primary else 'second opinion'
                lines.append(
                    f'Provider assessment ({role}): {provider_assessment.provider} / '
                    f'{provider_assessment.model}; label={provider_assessment.label}; '
                    f'confidence={provider_assessment.confidence} (uncalibrated); '
                    f'quote_check_passed={str(provider_assessment.quote_check_passed).lower()}'
                )
            for attempt in c.second_opinion_attempts:
                lines.append(
                    f'Second-opinion attempt: {attempt.provider} / {attempt.requested_model}; '
                    f'{attempt.outcome}; {attempt.timestamp}; {attempt.detail}'
                )
        else:
            lines.append('Assessment unavailable: '+(c.assessment_error or 'Not assessed.'))
        lines.extend(['Final wording: '+c.decision.final_wording, 'Researcher notes: '+c.decision.notes, ''])
    # Same canonical provenance as JSON: readable summary is never a lossy substitute.
    lines.extend(['Complete review record and provenance:', encoded])
    return '\n'.join(lines)+'\n'
