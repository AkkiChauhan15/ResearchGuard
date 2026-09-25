import unittest
from unittest.mock import patch

from researchguard.assessment import (
    AssessmentWithConfidence,
    assess,
    assess_second_opinion,
    structural_disagreement_fields,
)
from researchguard.demo import demo_review
from researchguard.export import export_review
from researchguard.providers.base import ProviderStatus
from researchguard.schemas import ModelRun


def model_result(provider, assessment, confidence="medium", *, wording=None):
    data = assessment.model_dump()
    if wording is not None:
        data["suggested_wording"] = wording
    result = AssessmentWithConfidence(**data, confidence=confidence)
    run = ModelRun(
        provider=provider,
        task="assessment",
        requested_model=f"{provider}-fixture",
        returned_model=f"{provider}-fixture-version",
        prompt_version="phase-three-fixture",
        validation=["Fixture structured output validated."],
    )
    return result, run


class SecondOpinionTests(unittest.TestCase):
    def live_review_with_primary(self):
        review = demo_review()
        review.mode = "live"
        expected = review.claims[0].assessment.model_copy(deep=True)
        review.claims[0].assessment = None
        with patch(
            "researchguard.assessment.call_model",
            return_value=model_result("groq", expected, "medium"),
        ):
            assess(review, review.claims[0].claim_id)
        return review, expected

    @staticmethod
    def available(provider):
        return ProviderStatus(
            provider=provider,
            state="configured",
            detail="Fixture free-access configuration is present.",
            extraction_model=f"{provider}-fixture",
            assessment_model=f"{provider}-fixture",
        )

    def test_matching_structured_results_ignore_wording_differences(self):
        review, expected = self.live_review_with_primary()
        with (
            patch("researchguard.assessment.provider_status_for", side_effect=self.available),
            patch(
                "researchguard.assessment.call_model",
                return_value=model_result(
                    "openrouter",
                    expected,
                    "medium",
                    wording="Different provider prose with the same structured comparison fields.",
                ),
            ),
        ):
            assess_second_opinion(review, review.claims[0].claim_id, "openrouter")
        primary, second = review.claims[0].provider_assessments
        self.assertEqual(structural_disagreement_fields(primary, second), [])
        self.assertNotEqual(primary.assessment.suggested_wording, second.assessment.suggested_wording)
        self.assertEqual(review.claims[0].second_opinion_attempts[-1].outcome, "succeeded")
        self.assertIn("second_opinion_assessment", review.model_runs[-1].task)
        export_review(review, "json")

    def test_mismatched_structured_fields_are_reported_directly(self):
        review, expected = self.live_review_with_primary()
        changed = expected.model_copy(deep=True)
        changed.status = "Partially supported"
        with (
            patch("researchguard.assessment.provider_status_for", side_effect=self.available),
            patch(
                "researchguard.assessment.call_model",
                return_value=model_result("nvidia", changed, "low"),
            ),
        ):
            assess_second_opinion(review, review.claims[0].claim_id, "nvidia")
        primary, second = review.claims[0].provider_assessments
        self.assertEqual(
            structural_disagreement_fields(primary, second),
            ["label", "confidence"],
        )

    def test_second_opinion_reuses_quote_validation_and_records_failure(self):
        review, expected = self.live_review_with_primary()
        invalid = expected.model_copy(deep=True)
        invalid.evidence[0].passage = "Fabricated quotation that is absent from the source."
        with (
            patch("researchguard.assessment.provider_status_for", side_effect=self.available),
            patch(
                "researchguard.assessment.call_model",
                return_value=model_result("gemini", invalid, "high"),
            ),
        ):
            assess_second_opinion(review, review.claims[0].claim_id, "gemini")
        self.assertEqual(len(review.claims[0].provider_assessments), 1)
        attempt = review.claims[0].second_opinion_attempts[-1]
        self.assertEqual(attempt.outcome, "failed")
        self.assertIn("quotation", attempt.detail)
        self.assertIn("rejected", review.model_runs[-1].validation[-1])

    def test_quota_failure_is_visible_and_preserves_primary(self):
        review, _expected = self.live_review_with_primary()
        primary = review.claims[0].assessment.model_copy(deep=True)
        with (
            patch("researchguard.assessment.provider_status_for", side_effect=self.available),
            patch(
                "researchguard.assessment.call_model",
                side_effect=ValueError(
                    "OpenRouter free quota or rate limit is exhausted. Retry later; no fallback was used."
                ),
            ),
        ):
            assess_second_opinion(review, review.claims[0].claim_id, "openrouter")
        claim = review.claims[0]
        self.assertEqual(claim.assessment, primary)
        self.assertEqual(len(claim.provider_assessments), 1)
        self.assertEqual(claim.second_opinion_attempts[-1].outcome, "failed")
        self.assertIn("quota", claim.second_opinion_attempts[-1].detail)
        self.assertIn("no fallback", claim.second_opinion_attempts[-1].detail)

    def test_unavailable_and_same_provider_do_not_call_model(self):
        review, _expected = self.live_review_with_primary()
        with self.assertRaisesRegex(ValueError, "different configured provider"):
            assess_second_opinion(review, review.claims[0].claim_id, "groq")
        unavailable = ProviderStatus(
            provider="openrouter",
            state="unavailable_missing_credentials",
            detail="Configure OPENROUTER_API_KEY; no fallback was used.",
            assessment_model="openrouter/free",
        )
        with (
            patch("researchguard.assessment.provider_status_for", return_value=unavailable),
            patch("researchguard.assessment.call_model") as call_model,
        ):
            assess_second_opinion(review, review.claims[0].claim_id, "openrouter")
        call_model.assert_not_called()
        self.assertEqual(review.claims[0].second_opinion_attempts[-1].outcome, "failed")
        self.assertIn("OPENROUTER_API_KEY", review.claims[0].second_opinion_attempts[-1].detail)


if __name__ == "__main__":
    unittest.main()
