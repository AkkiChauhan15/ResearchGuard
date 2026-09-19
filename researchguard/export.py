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
        elif claim.decision.status != 'pending':
            raise ValueError('A decision cannot approve an absent assessment.')
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
        else:
            lines.append('Assessment unavailable: '+(c.assessment_error or 'Not assessed.'))
        lines.extend(['Final wording: '+c.decision.final_wording, 'Researcher notes: '+c.decision.notes, ''])
    # Same canonical provenance as JSON: readable summary is never a lossy substitute.
    lines.extend(['Complete review record and provenance:', encoded])
    return '\n'.join(lines)+'\n'
