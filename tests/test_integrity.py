import json
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

from researchguard.integrity import (
    IntegrityStatus,
    check_source_integrity,
    integrity_from_crossref_json,
    integrity_from_pubmed_article,
)
from researchguard.demo import demo_review
from researchguard.export import export_review
from researchguard.schemas import Source
from researchguard.transport import FetchError


def article(ref_type: str | None = None, notice_pmid: str = "999") -> ET.Element:
    relation = ""
    if ref_type:
        relation = (
            f"<CommentsCorrectionsList><CommentsCorrections RefType='{ref_type}'>"
            f"<RefSource>Documented notice.</RefSource><PMID>{notice_pmid}</PMID>"
            "</CommentsCorrections></CommentsCorrectionsList>"
        )
    return ET.fromstring(
        "<PubmedArticle><MedlineCitation><PMID>123</PMID>"
        f"{relation}<Article><ArticleTitle>Fixture</ArticleTitle></Article>"
        "</MedlineCitation></PubmedArticle>"
    )


def source(**changes) -> Source:
    values = {
        "retrieval_run_id": "fixture",
        "url": "https://pubmed.ncbi.nlm.nih.gov/123/",
        "category": "pubmed",
        "title": "Fixture",
        "pmid": "123",
        "access_level": "metadata",
        "content_sha256": "0" * 64,
        "passages": [],
    }
    values.update(changes)
    return Source(**values)


class IntegrityFixtureTests(unittest.TestCase):
    def test_clean_pubmed_record(self):
        result = integrity_from_pubmed_article(article())
        self.assertEqual(result.status, IntegrityStatus.CLEAN)
        self.assertEqual(result.checked_via, "pubmed")
        self.assertFalse(result.notices)

    def test_documented_retracted_pubmed_record(self):
        # Real historical case: PMID 38510612 has RetractionIn PMID 38868598.
        # https://pubmed.ncbi.nlm.nih.gov/38510612/
        result = integrity_from_pubmed_article(article("RetractionIn", "38868598"))
        self.assertEqual(result.status, IntegrityStatus.RETRACTED)
        self.assertEqual(result.notices[0].url, "https://pubmed.ncbi.nlm.nih.gov/38868598/")

    def test_correction_pubmed_record(self):
        result = integrity_from_pubmed_article(article("ErratumIn"))
        self.assertEqual(result.status, IntegrityStatus.CORRECTION)

    def test_expression_of_concern_pubmed_record(self):
        result = integrity_from_pubmed_article(article("ExpressionOfConcernIn"))
        self.assertEqual(result.status, IntegrityStatus.EXPRESSION_OF_CONCERN)

    def test_not_applicable_manufacturer_record(self):
        result = check_source_integrity(source(
            url="https://www.enzo.com/product/cyto-id-autophagy-detection-kit/",
            category="manufacturer",
            pmid=None,
            access_level="product document",
        ))
        self.assertEqual(result.status, IntegrityStatus.NOT_APPLICABLE)

    @patch("researchguard.integrity.ncbi", side_effect=FetchError("Source request timed out."))
    def test_failed_check_is_not_clean(self, _ncbi):
        result = check_source_integrity(source())
        self.assertEqual(result.status, IntegrityStatus.CHECK_FAILED)
        self.assertIn("not confirmed clean", result.detail)

    def test_crossref_update_metadata_and_malformed_response(self):
        data = json.dumps({"message": {"update-to": [
            {"type": "clarification", "DOI": "10.1000/notice", "source": "publisher", "label": "Clarification"}
        ]}}).encode()
        result = integrity_from_crossref_json(data, "10.1000/original")
        self.assertEqual(result.status, IntegrityStatus.CORRECTION)
        self.assertEqual(result.notices[0].source, "crossref:publisher")
        with self.assertRaisesRegex(ValueError, "could not be parsed"):
            integrity_from_crossref_json(b"not-json", "10.1000/original")

    @patch("researchguard.integrity._crossref", return_value=b'{"message":{"update-to":[]}}')
    def test_crossref_fallback_records_both_checks_after_clean_pubmed(self, crossref):
        record = source(doi="10.1000/original")
        with patch("researchguard.integrity.ncbi", return_value=(
            b"<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID></MedlineCitation></PubmedArticle></PubmedArticleSet>",
            "",
            {},
        )):
            result = check_source_integrity(record)
        self.assertEqual(result.status, IntegrityStatus.CLEAN)
        self.assertEqual([check.method for check in result.checks], ["pubmed", "crossref"])
        crossref.assert_called_once_with("10.1000/original")

    def test_integrity_round_trips_through_demo_exports(self):
        review = demo_review()
        self.assertEqual(
            [source.integrity.status for source in review.sources],
            [IntegrityStatus.CHECK_FAILED, IntegrityStatus.NOT_APPLICABLE],
        )
        json_record = json.loads(export_review(review, "json"))
        self.assertEqual(json_record["sources"][0]["integrity"]["status"], "check_failed")
        txt_record = export_review(review, "txt")
        self.assertIn('"status": "not_applicable"', txt_record)


if __name__ == "__main__":
    unittest.main()
