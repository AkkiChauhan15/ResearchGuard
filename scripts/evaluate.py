"""Inspect the case set, or run the selected free evidence provider on fixtures.

Run: python3 -m scripts.evaluate [--run-model --split dev|held_out --max-cases 2]
This never rewrites expected labels and never grades scientific entailment with a model.
"""
import argparse
import hashlib
import json
from pathlib import Path
from researchguard.assessment import Extraction, call_model, configured, validate_assessment
from researchguard.local_env import load_local_env
from researchguard.schemas import Assessment, Passage, Source


def main():
    load_local_env()
    parser=argparse.ArgumentParser()
    parser.add_argument('--run-model',action='store_true')
    parser.add_argument('--split',choices=['dev','held_out'],default='dev')
    parser.add_argument(
        '--max-cases',
        type=int,
        default=2,
        help='Maximum cases in this bounded model batch (default: 2).',
    )
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.max_cases < 1:
        parser.error('--max-cases must be at least 1')
    raw=Path('data/evaluation_cases.json').read_bytes()
    cases=json.loads(raw)
    assert len(cases)==16 and len({c['id'] for c in cases})==16
    for c in cases:
        assert c['reference']['rationale'] and c['reference']['reviewer_status']
        assert set(c['reference']['source_ids'])=={s['id'] for s in c['sources']}
        if c['access_state'] in ('fetch_failed','no_results'):
            assert c['reference']['status'] is None and not c['sources']
    selected=[c for c in cases if c['split']==args.split]
    model_batch=selected[:args.max_cases]
    report={'case_file_sha256':hashlib.sha256(raw).hexdigest(),'case_count':len(cases),
            'development_cases':10,'held_out_cases':6,'fixture_checks':'16/16 consistent',
            'selected_split':args.split,'selected_case_count':len(selected),
            'selected_case_ids':[c['id'] for c in selected],
            'reference_status':'Agent-authored drafts; knowledgeable human review pending.',
            'human_reviewed_references':'0/16',
            'mode':'model on synthetic/archived fixtures' if args.run_model else 'fixture validation only',
            'model_batch_limit':args.max_cases if args.run_model else 0,
            'model_batch_case_ids':[c['id'] for c in model_batch] if args.run_model else [],
            'model_cases_attempted':0,'model_cases_completed':0,'extraction_count_matches':0,
            'citation_valid_outputs':0,'draft_label_matches':0,'results':[],
            'scientific_support':'Unmeasured; requires human review of actual claim-to-source entailment.',
            'context_matching':'Unmeasured; human grading pending.',
            'false_alarms':'Unmeasured; human grading of supported cases pending.',
            'uncertainty_handling':'Unmeasured; human grading of failure/no-results/mismatch cases pending.'}
    if args.run_model and not configured():
        from researchguard.providers import provider_status
        report['blocked']=provider_status().detail+' No model cases were run.'
    elif args.run_model:
        for c in model_batch:
            row={'case_id':c['id'],'reference':c['reference'],'human_grades':None}
            report['model_cases_attempted']+=1
            try:
                extraction,erun=call_model(Extraction,'extraction',{'text':c['claim'],'context':c['context']})
                if any(x.original_span not in c['claim'] for x in extraction.claims):
                    raise ValueError('Extraction original-span validation failed.')
                row['extraction']=extraction.model_dump();row['extraction_run']=erun.model_dump()
                report['extraction_count_matches']+=len(extraction.claims)==c['reference']['expected_claim_count']
                sources=[Source(source_id=s['id'],retrieval_run_id='evaluation-fixture',url=s.get('url','urn:synthetic:'+s['id']),category='synthetic' if s['kind']=='synthetic' else 'pmc',title=s['kind'],access_level=s['access_level'],content_sha256=hashlib.sha256(s['text'].encode()).hexdigest(),passages=[Passage(text=s['text'],location=s['location'])]) for s in c['sources']]
                if not sources:
                    row['assessment']=None;row['access_state']=c['access_state']
                    row['note']='Deterministic no-readable-evidence gate; not a model assessment.'
                else:
                    result,run=call_model(Assessment,'assessment',{'claim':c['claim'],'user_reported_context':c['context'],'sources':[s.model_dump() for s in sources]})
                    validate_assessment(result,sources)
                    report['citation_valid_outputs']+=1
                    report['draft_label_matches']+=result.status==c['reference']['status']
                    row['assessment']=result.model_dump();row['assessment_run']=run.model_dump()
                report['model_cases_completed']+=1
            except ValueError as exc:
                row['failure']=str(exc)
            report['results'].append(row)
    encoded=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    if args.output:
        args.output.write_text(encoded)
    print(encoded)


if __name__=='__main__':main()
