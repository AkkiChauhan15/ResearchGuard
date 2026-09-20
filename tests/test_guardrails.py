import json
import os
import socket
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from google.genai import errors, types
from pydantic import ValidationError
from researchguard.assessment import assess, call_model, extract, validate_assessment
from researchguard.demo import demo_review
from researchguard.export import export_review
from researchguard.retrieval import OMISSION_PREFIX, classify_url, manual_record, pdf_text, pmc_record, product_record, pubmed_records, retrieve, search_pubmed, MANUAL, PRODUCT
from researchguard.reviews import create_review, decide, edit_claim
from researchguard.schemas import Assessment, Attempt, Decision, Passage, ReviewInput, Source
from researchguard.transport import MAX_BYTES, FetchError, fetch, public_address, validate_url


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.review = demo_review()
        self.claim = self.review.claims[0]
        self.assessment = self.claim.assessment
    def test_demo_has_valid_archived_passages_and_pending_decisions(self):
        validate_assessment(self.assessment,self.review.sources)
        self.assertEqual(self.claim.decision.status,'pending')
        self.assertFalse(self.review.model_runs)
    def test_unknown_source_rejected(self):
        self.assessment.evidence[0].source_id = 'invented'
        with self.assertRaisesRegex(ValueError,'source ID'):
            export_review(self.review,'json')
    def test_nonexistent_passage_rejected(self):
        self.assessment.evidence[0].passage = 'This experiment proved the mechanism.'
        with self.assertRaisesRegex(ValueError,'quotation'):
            export_review(self.review,'txt')
    def test_wrong_location_rejected(self):
        self.assessment.evidence[0].location = 'Figure 17'
        with self.assertRaisesRegex(ValueError,'location'):
            validate_assessment(self.assessment,self.review.sources)
    def test_only_whitespace_normalized(self):
        self.assessment.evidence[0].passage = self.assessment.evidence[0].passage.replace(' ','\n ')
        validate_assessment(self.assessment,self.review.sources)
        self.assessment.evidence[0].passage = self.assessment.evidence[0].passage.upper()
        with self.assertRaises(ValueError):
            validate_assessment(self.assessment,self.review.sources)
    def test_supported_needs_support_relationship(self):
        self.assessment.status = 'Supported within the stated context'
        with self.assertRaises(ValueError):
            validate_assessment(self.assessment,self.review.sources)
    def test_metadata_cannot_supply_passage(self):
        self.review.sources[0].access_level = 'metadata'
        with self.assertRaises(ValueError):
            validate_assessment(self.assessment,self.review.sources)
    def test_edit_preserves_suggestion_and_exports_full_provenance(self):
        original = self.assessment.suggested_wording
        decide(self.review,self.claim.claim_id,Decision(status='edited',final_wording='My qualified wording.',notes='Inspected the limits.'))
        result = json.loads(export_review(self.review,'json'))
        self.assertEqual(result['claims'][0]['assessment']['suggested_wording'],original)
        self.assertEqual(result['claims'][0]['decision']['final_wording'],'My qualified wording.')
        self.assertEqual(result['sources'],[s.model_dump() for s in self.review.sources])
        txt = export_review(self.review,'txt')
        self.assertIn('Demonstration — not a live verification',txt)
        self.assertEqual(json.loads(txt.split('Complete review record and provenance:\n')[1]),result)
    def test_accept_and_reject(self):
        decide(self.review,self.claim.claim_id,Decision(status='accepted',final_wording='Untrusted replacement'))
        self.assertEqual(self.claim.decision.final_wording,self.assessment.suggested_wording)
        decide(self.review,self.claim.claim_id,Decision(status='rejected'))
        self.assertEqual(self.claim.decision.final_wording,'')
    def test_live_does_not_recognize_demo_text(self):
        r = create_review(self.review.original_input)
        self.assertEqual(r.mode,'live')
        self.assertIsNone(r.claims[0].assessment)
        self.assertFalse(r.sources)
    def test_demo_rejects_live_operations(self):
        for operation in [lambda:retrieve(self.review,self.claim.claim_id,'flux'),lambda:assess(self.review,self.claim.claim_id),lambda:extract(self.review),lambda:edit_claim(self.review,self.claim.claim_id,'A different claim')]:
            with self.assertRaises(ValueError):operation()
    def test_edit_invalidates_assessment_and_claim_source_links(self):
        self.review.mode = 'live'  # unit fixture only; UI never exposes a mode switch.
        decide(self.review,self.claim.claim_id,Decision(status='accepted'))
        edit_claim(self.review,self.claim.claim_id,'An edited claim.')
        self.assertIsNone(self.claim.assessment)
        self.assertEqual(self.claim.decision.status,'pending')
        self.assertTrue(all(a.claim_id != self.claim.claim_id for a in self.review.attempts))
        export_review(self.review,'json')


class RuntimeTests(unittest.TestCase):
    gemini_env={
        'LLM_PROVIDER':'gemini',
        'GEMINI_API_KEY':'test-secret',
        'GEMINI_FREE_TIER_CONFIRMED':'true',
        'GEMINI_EXTRACTION_MODEL':'gemini-3.8-flash',
        'GEMINI_ASSESSMENT_MODEL':'gemini-3.8-flash',
    }

    def live(self):
        r=demo_review()
        r.mode='live'
        r.claims[0].assessment=None
        return r
    @patch.dict(os.environ,{},clear=True)
    def test_missing_credentials(self):
        r=self.live();assess(r,r.claims[0].claim_id)
        self.assertIsNone(r.claims[0].assessment)
        self.assertIn('GROQ_API_KEY',r.claims[0].assessment_error)
        self.assertEqual(r.mode,'live')

    @patch.dict(os.environ,gemini_env,clear=True)
    @patch('researchguard.providers.gemini.genai.Client')
    def test_malformed_model_output(self,client_class):
        client_class.return_value.models.generate_content.return_value=SimpleNamespace(
            candidates=[SimpleNamespace(finish_reason=types.FinishReason.STOP)],
            text='not JSON',model_version='gemini-fixture')
        with self.assertRaisesRegex(ValueError,'Malformed'):
            call_model(Assessment,'assessment',{})

    @patch.dict(os.environ,gemini_env,clear=True)
    @patch('researchguard.providers.gemini.genai.Client')
    def test_incomplete_and_oversized_model_output(self,client_class):
        response=client_class.return_value.models.generate_content.return_value
        response.candidates=[SimpleNamespace(finish_reason=types.FinishReason.MAX_TOKENS)]
        response.text='{}';response.model_version='gemini-fixture'
        with self.assertRaisesRegex(ValueError,'incomplete'):
            call_model(Assessment,'assessment',{})
        response.candidates=[SimpleNamespace(finish_reason=types.FinishReason.STOP)]
        response.text='x'*64001
        with self.assertRaisesRegex(ValueError,'response limit'):
            call_model(Assessment,'assessment',{})

    @patch.dict(os.environ,gemini_env,clear=True)
    @patch('researchguard.providers.gemini.genai.Client')
    def test_structured_output_bounds_and_provenance(self,client_class):
        payload=demo_review().claims[0].assessment.model_dump_json()
        client_class.return_value.models.generate_content.return_value=SimpleNamespace(
            candidates=[SimpleNamespace(finish_reason=types.FinishReason.STOP)],
            text=payload,model_version='gemini-3.8-flash-202609')
        parsed,run=call_model(Assessment,'assessment',{'synthetic':'input'})
        self.assertEqual(parsed.status,demo_review().claims[0].assessment.status)
        self.assertEqual(run.requested_model,'gemini-3.8-flash')
        self.assertEqual(run.returned_model,'gemini-3.8-flash-202609')
        self.assertIn('gemini',run.prompt_version)
        self.assertNotIn('test-secret',run.model_dump_json())
        call=client_class.return_value.models.generate_content.call_args
        config=call.kwargs['config']
        self.assertEqual(config.response_mime_type,'application/json')
        self.assertIsNone(config.response_schema)
        self.assertEqual(config.response_json_schema,Assessment.model_json_schema())
        self.assertEqual(config.max_output_tokens,4096)
        self.assertIsNone(config.tools)
        self.assertIsNone(config.cached_content)
        self.assertTrue(config.automatic_function_calling.disable)
        retry=client_class.call_args.kwargs['http_options'].retry_options
        self.assertEqual(retry.attempts,2)
        self.assertNotIn(429,retry.http_status_codes)
        client_class.return_value.close.assert_called_once()

    @patch.dict(os.environ,gemini_env,clear=True)
    @patch('researchguard.providers.gemini.genai.Client')
    def test_assessment_records_sources_access_and_validation(self,client_class):
        r=self.live()
        expected=demo_review().claims[0].assessment
        client_class.return_value.models.generate_content.return_value=SimpleNamespace(
            candidates=[SimpleNamespace(finish_reason=types.FinishReason.STOP)],
            text=expected.model_dump_json(),model_version='gemini-fixture')
        assess(r,r.claims[0].claim_id)
        self.assertIsNotNone(r.claims[0].assessment)
        run=r.model_runs[-1]
        self.assertEqual(run.source_ids,[s.source_id for s in r.sources])
        self.assertTrue(all(s.access_level in {'abstract','product document'} for s in r.sources))
        self.assertTrue(any('Quotation and location' in item for item in run.validation))
        exported=export_review(r,'json')
        self.assertNotIn('test-secret',exported)

    @patch.dict(os.environ,gemini_env,clear=True)
    @patch('researchguard.providers.gemini.genai.Client')
    def test_provider_output_cannot_bypass_source_and_quote_validation(self,client_class):
        for change,error in [
            (('source_id','invented_source'),'source ID'),
            (('passage','A fabricated quotation.'),'quotation'),
        ]:
            r=self.live()
            data=demo_review().claims[0].assessment.model_dump()
            data['evidence'][0][change[0]]=change[1]
            client_class.return_value.models.generate_content.return_value=SimpleNamespace(
                candidates=[SimpleNamespace(finish_reason=types.FinishReason.STOP)],
                text=json.dumps(data),model_version='gemini-fixture')
            assess(r,r.claims[0].claim_id)
            self.assertIsNone(r.claims[0].assessment)
            self.assertIn(error,r.claims[0].assessment_error)
            self.assertIn('validation failed',r.model_runs[-1].validation[-1].lower())

    @patch.dict(os.environ,gemini_env,clear=True)
    @patch('researchguard.providers.gemini.genai.Client')
    def test_invalid_key_and_quota_messages(self,client_class):
        for code,text in [(400,'configuration'),(401,'authentication'),(429,'quota')]:
            client_class.return_value.models.generate_content.side_effect=errors.APIError(code,{'error':{'message':'provider detail'}})
            with self.subTest(code=code),self.assertRaisesRegex(ValueError,text):
                call_model(Assessment,'assessment',{})

    @patch.dict(os.environ,{
        'LLM_PROVIDER':'gemini','GEMINI_API_KEY':'test-secret',
        'GEMINI_FREE_TIER_CONFIRMED':'true',
    },clear=True)
    def test_model_input_limit(self):
        with self.assertRaisesRegex(ValueError,'120000-byte'):
            call_model(Assessment,'assessment',{'passage':'x'*120001})

    @patch.dict(os.environ,{'LLM_PROVIDER':'gemini','GEMINI_API_KEY':'test-secret'},clear=True)
    def test_free_tier_confirmation_required(self):
        with self.assertRaisesRegex(ValueError,'Free Tier'):
            call_model(Assessment,'assessment',{})

    @patch.dict(os.environ,{
        'LLM_PROVIDER':'gemini','GEMINI_API_KEY':'test-secret',
        'GEMINI_FREE_TIER_CONFIRMED':'true',
        'GEMINI_ASSESSMENT_MODEL':'gemini-paid-example',
    },clear=True)
    def test_non_allowlisted_model_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'verified Free Tier allowlist'):
            call_model(Assessment,'assessment',{})

    @patch.dict(os.environ,{'LLM_PROVIDER':'openai','OPENAI_API_KEY':'test-secret'},clear=True)
    def test_legacy_openai_provider_is_disabled(self):
        with self.assertRaisesRegex(ValueError,'disabled'):
            call_model(Assessment,'assessment',{})
    @patch('researchguard.retrieval.search_pubmed',side_effect=FetchError('Unavailable.'))
    def test_failed_retrieval_has_no_verdict(self,mock):
        r=create_review(ReviewInput(text='A synthetic claim.',intended_use='topic understanding'))
        retrieve(r,r.claims[0].claim_id,'synthetic')
        self.assertEqual([a.access_state for a in r.attempts],['fetch_failed','fetch_failed'])
        assess(r,r.claims[0].claim_id)
        self.assertIsNone(r.claims[0].assessment)
    @patch('researchguard.retrieval.search_pubmed',return_value=[])
    def test_no_results_not_contradicted(self,mock):
        r=create_review(ReviewInput(text='A synthetic claim.',intended_use='topic understanding'))
        retrieve(r,r.claims[0].claim_id,'synthetic')
        self.assertTrue(all(a.access_state=='no_results' for a in r.attempts))
        self.assertIsNone(r.claims[0].assessment)
    def test_missing_product_identity_has_question(self):
        r=create_review(ReviewInput(text='The dye measures flux.',intended_use='assay interpretation'))
        self.assertIn('manufacturer',r.claims[0].missing_context[0])
    def test_schema_rejects_extra_confidence(self):
        data=demo_review().claims[0].assessment.model_dump();data['confidence']=.99
        with self.assertRaises(ValidationError):Assessment.model_validate(data)


class RetrievalTests(unittest.TestCase):
    @patch('researchguard.retrieval.pdf_text',return_value='CYTO-ID Product Manual ENZ-51031\fSynthetic page two.\f')
    def test_manual_keeps_physical_page_locations(self,mock):
        s=manual_record(b'%PDF-fixture','fixture',{})
        self.assertEqual(s.passages[1].location,'PDF physical page 2')
        self.assertIsNone(s.document_version)
        self.assertEqual(classify_url(MANUAL)[0],'manufacturer')
    @patch('researchguard.retrieval.shutil.which',return_value=None)
    def test_missing_pdf_parser_explicit(self,mock):
        with self.assertRaisesRegex(FetchError,'pdftotext'):pdf_text(b'%PDF-fixture')
    @patch('researchguard.retrieval.pdf_text',return_value='Some other product')
    def test_wrong_manual_identity_rejected(self,mock):
        with self.assertRaisesRegex(FetchError,'identity'):manual_record(b'%PDF-fixture','fixture',{})
    def test_pmc_abstract_not_full_text(self):
        s=pmc_record(b'<article><front><article-meta><title-group><article-title>Synthetic</article-title></title-group><abstract><p>Only abstract.</p></abstract></article-meta></front></article>','fixture','PMC1')
        self.assertEqual(s.access_level,'abstract')
        self.assertEqual(s.passages[0].location,'Abstract, paragraph 1')
    def test_pmc_empty_body_is_not_full_text(self):
        s=pmc_record(b'<article><front><article-meta><abstract><p>Only abstract.</p></abstract></article-meta></front><body/></article>','fixture','PMC1')
        self.assertEqual(s.access_level,'abstract')
        self.assertIn('no readable full-text body paragraphs',s.limitations[0])
    def test_pmc_full_text_locations(self):
        s=pmc_record(b'<article><front><article-meta/></front><body><sec><title>Results</title><p>Synthetic observation.</p></sec></body></article>','fixture','PMC1')
        self.assertEqual(s.access_level,'full text')
        self.assertEqual(s.passages[0].text,'Synthetic observation.')
        self.assertEqual(s.passages[0].location,'XML body paragraph 1')
    def test_pubmed_no_abstract_is_metadata(self):
        data=b'<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID><Article><ArticleTitle>Synthetic fixture</ArticleTitle></Article></MedlineCitation></PubmedArticle></PubmedArticleSet>'
        s=pubmed_records(data,'fixture')[0]
        self.assertEqual(s.access_level,'metadata');self.assertFalse(s.passages)
    def test_pubmed_uses_record_identifiers_not_reference_identifiers(self):
        data=b'''<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID><Article><ArticleTitle>Requested article</ArticleTitle><Abstract><AbstractText Label="RESULTS">Exact abstract text.</AbstractText></Abstract></Article></MedlineCitation><PubmedData><ArticleIdList><ArticleId IdType="pubmed">123</ArticleId><ArticleId IdType="pmc">PMC123</ArticleId><ArticleId IdType="doi">10.1/requested</ArticleId></ArticleIdList><ReferenceList><Reference><ArticleIdList><ArticleId IdType="pmc">PMC999</ArticleId></ArticleIdList></Reference></ReferenceList></PubmedData></PubmedArticle></PubmedArticleSet>'''
        s=pubmed_records(data,'fixture',expected_pmid='123')[0]
        self.assertEqual((s.pmid,s.pmcid,s.doi),('123','PMC123','10.1/requested'))
        self.assertEqual((s.passages[0].text,s.passages[0].location),('Exact abstract text.','Abstract: RESULTS'))
        with self.assertRaisesRegex(FetchError,'requested PMID 456'):
            pubmed_records(data,'fixture',expected_pmid='456')
    def test_product_preserves_visible_version_and_exact_block_location(self):
        data=b'<html><head><title>CYTO-ID Autophagy Detection Kit - Enzo</title></head><body><p>Official product text with enough characters to become a passage.</p><p>Last modified: May 29, 2024</p></body></html>'
        s=product_record(data,'fixture',PRODUCT,{})
        self.assertEqual(s.document_version,'Last modified: May 29, 2024')
        self.assertEqual((s.passages[0].text,s.passages[0].location),('Official product text with enough characters to become a passage.','HTML text block 1'))
    def test_xml_entities_and_parse_errors_rejected(self):
        for data in [b'not XML',b'<!DOCTYPE x [<!ENTITY y "bad">]><article>&y;</article>']:
            with self.assertRaises(FetchError):pmc_record(data,'fixture','PMC1')
    def test_unsafe_or_unsupported_source_urls(self):
        for url in ['http://127.0.0.1/','https://169.254.169.254/','file:///etc/passwd','https://localhost/','https://www.enzo.com.evil.test/','https://www.enzo.com@127.0.0.1/','https://www.enzo.com:444/','https://www.enzo.com/anything','https://pubmed.ncbi.nlm.nih.gov/1/?redirect=foo','https://api.openai.com/v1/responses']:
            with self.subTest(url=url),self.assertRaises(FetchError):classify_url(url)
    @patch('researchguard.transport.socket.getaddrinfo')
    def test_private_and_mixed_dns_answers_blocked(self,mock):
        for ip in ['127.0.0.1','10.0.0.1','169.254.169.254','::1','::ffff:127.0.0.1','192.168.0.1']:
            mock.return_value=[(socket.AF_INET,socket.SOCK_STREAM,6,'',('8.8.8.8',443)),(socket.AF_INET,socket.SOCK_STREAM,6,'',(ip,443))]
            with self.subTest(ip=ip),self.assertRaises(FetchError):public_address('www.enzo.com')
    @patch('researchguard.transport.PinnedHTTPS')
    @patch('researchguard.transport.public_address',return_value='8.8.8.8')
    def test_redirect_to_private_host_blocked(self,addr,conn):
        res=conn.return_value.getresponse.return_value;res.status=302
        res.getheader.side_effect=lambda key,default=None:'https://127.0.0.1/private' if key=='Location' else default
        with self.assertRaises(FetchError):fetch('https://www.enzo.com/')
        self.assertEqual(conn.call_count,1)
    @patch('researchguard.transport.PinnedHTTPS')
    @patch('researchguard.transport.public_address',return_value='8.8.8.8')
    def test_byte_and_content_type_limits(self,addr,conn):
        res=conn.return_value.getresponse.return_value;res.status=200
        for typ,length in [('application/octet-stream','10'),('text/html','2000001')]:
            values={'Content-Type':typ,'Content-Length':length}
            res.getheader.side_effect=lambda key,default=None:values.get(key,default)
            with self.assertRaises(FetchError) as raised:fetch('https://www.enzo.com/')
            if length=='2000001':self.assertEqual(raised.exception.state,'partial_access')
    @patch('researchguard.transport.PinnedHTTPS')
    @patch('researchguard.transport.public_address',return_value='8.8.8.8')
    def test_streamed_oversized_response_is_rejected(self,addr,conn):
        res=conn.return_value.getresponse.return_value;res.status=200
        res.getheader.side_effect=lambda key,default=None:{'Content-Type':'text/html'}.get(key,default)
        res.read1.side_effect=[b'x'*(MAX_BYTES+1)]
        with self.assertRaises(FetchError) as raised:fetch('https://www.enzo.com/')
        self.assertEqual(raised.exception.state,'partial_access')
    @patch('researchguard.transport.PinnedHTTPS')
    @patch('researchguard.transport.public_address',return_value='8.8.8.8')
    def test_rate_limit_and_timeout_states(self,addr,conn):
        res=conn.return_value.getresponse.return_value
        res.status=429
        with self.assertRaises(FetchError) as raised:fetch('https://www.enzo.com/')
        self.assertEqual(raised.exception.state,'rate_limited')
        res.status=200
        res.getheader.side_effect=lambda key,default=None:{'Content-Type':'text/html'}.get(key,default)
        res.read1.side_effect=socket.timeout()
        with self.assertRaisesRegex(FetchError,'timed out'):
            fetch('https://www.enzo.com/')
    @patch('researchguard.retrieval.ncbi')
    def test_search_preserves_other_records_when_one_is_oversized(self,ncbi):
        xml=b'<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID><Article><Abstract><AbstractText>Abstract.</AbstractText></Abstract></Article></MedlineCitation></PubmedArticle></PubmedArticleSet>'
        ncbi.side_effect=[(b'{"esearchresult":{"idlist":["999","123"]}}','',{}),FetchError('Too large.','partial_access'),(xml,'',{})]
        sources=search_pubmed('synthetic','fixture')
        self.assertEqual(len(sources),1);self.assertIn('999',sources[0].limitations[-1])
        self.assertEqual([call.args[1].get('id') for call in ncbi.call_args_list[1:]],['999','123'])
    @patch('researchguard.retrieval.search_pubmed')
    def test_retrieve_preserves_success_and_reports_omission_when_another_job_fails(self,search):
        source=Source(retrieval_run_id='fixture',url='https://pubmed.ncbi.nlm.nih.gov/123/',category='pubmed',title='Readable record',pmid='123',access_level='abstract',content_sha256='0'*64,passages=[Passage(text='Exact abstract.',location='Abstract')],limitations=[OMISSION_PREFIX+'PMID 999: Source exceeds the 2 MB retrieval limit.'])
        search.side_effect=[[source],FetchError('Public source DNS lookup failed.')]
        review=create_review(ReviewInput(text='A synthetic claim.',intended_use='topic understanding'))
        retrieve(review,review.claims[0].claim_id,'synthetic query')
        self.assertEqual(len(review.sources),1)
        self.assertEqual([a.access_state for a in review.attempts],['partial_access','fetch_failed'])
        self.assertIn('1 search record(s) omitted',review.attempts[0].detail)
        self.assertIn('PMID 999',review.attempts[0].detail)


if __name__=='__main__':unittest.main()
