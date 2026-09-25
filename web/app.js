'use strict';
const session = crypto.randomUUID();
let review = null, busy = false, config = {};
const $ = (selector) => document.querySelector(selector);
function el(tag, text, cls) { const n = document.createElement(tag); if(text !== undefined) n.textContent=text; if(cls) n.className=cls; return n; }
function button(text, fn, cls) { const n=el('button',text,cls); n.type='button'; n.onclick=fn; return n; }
function message(text, error=false) { $('#status').textContent=text; $('#status').className=error?'error':''; }
async function api(path, data, method=data===undefined?'GET':'POST') {
  const res=await fetch(path,{method,headers:{'Content-Type':'application/json','X-Review-Session':session},body:data===undefined?undefined:JSON.stringify(data)});
  if(!res.ok) { const e=await res.json(); throw Error(e.error||'Request failed.'); }
  return res.json();
}
async function run(action, label) {
  if(busy)return; busy=true; message(label); document.querySelectorAll('button').forEach(n=>n.disabled=true);
  try { await action(); message('Review updated. Inspect the evidence and limitations before making a decision.'); }
  catch(e){message(e.message,true);} finally { busy=false; document.querySelectorAll('button').forEach(n=>n.disabled=false); }
}
function details(title, child) {const n=el('details'); n.append(el('summary',title),child);return n;}
function list(items) {const n=el('ul');items.forEach(t=>n.append(el('li',t)));return n;}
function field(label,value,rows=3){const wrapper=el('label',label),n=el('textarea');n.rows=rows;n.value=value;wrapper.append(n);return [wrapper,n];}
async function action(path,method='POST',data){review=await api(`/api/reviews/${review.review_id}/${path}`,data,method);render();}
function render(){
 const heading=$('#review-heading');heading.replaceChildren();
 heading.append(el('div',review.mode==='demo'?'Demonstration — not a live verification. Synthetic context; curated assessment.':'Live review · assessments use retrieved material only.',review.mode==='demo'?'banner':'banner live-banner'));
 const intro=el('div');intro.append(el('span','02 / RISK → 04 / VERIFY','section-label'),el('h2',`${review.claims.length} claim${review.claims.length===1?'':'s'} to inspect`),el('p',review.extraction_method,'muted'),el('p','Review priority: check missing context and observation-to-inference steps. This is not a clinical risk score.','fine'));
 if(review.missing_fields.length)intro.append(el('p','Context not supplied: '+review.missing_fields.join(', '),'fine'));
 if(review.mode==='live')intro.append(button('Extract claims with AI',()=>run(()=>action('extraction'),'Extracting claims with AI… Existing review decisions will be replaced.')));
 heading.append(intro);
 const container=$('#claims');container.replaceChildren();
 for(const c of review.claims){
  const card=el('article',undefined,'claim');card.append(el('span',c.type.toUpperCase(),'section-label'),el('h3',c.text));
  if(review.mode==='live'){
   const [wrap,input]=field('Edit claim text',c.text);const edit=el('div');edit.append(wrap,button('Apply claim edit',()=>run(()=>action(`claims/${c.claim_id}`,'PATCH',{text:input.value}),'Updating claim; invalidating earlier evidence and decisions…')));card.append(details('Edit this claim',edit));
  }
  if(c.observations.length||c.inferences.length){const pair=el('div',undefined,'split');for(const [title,items] of [['Reported observation',c.observations],['Inference',c.inferences]]){const col=el('div');col.append(el('h4',title),list(items));pair.append(col);}card.append(pair);}
  if(c.missing_context.length)card.append(el('h4','Missing-context questions'),list(c.missing_context));
  if(review.mode==='live'){
   const [qwrap,q]=field('PubMed search terms — include the claim and relevant context',[c.text,review.original_input.context.organism_model,review.original_input.context.assay].filter(Boolean).join(' '),2);q.maxLength=500;
   card.append(qwrap,el('p','Also searches these terms with limitation, contradiction, and replication terms. Up to three results per query; this is not an exhaustive review.','fine'));
   const actions=el('div',undefined,'actions');actions.append(button('Retrieve evidence',()=>run(()=>action(`claims/${c.claim_id}/retrievals`,'POST',{query:q.value}),'Retrieving public sources… This may take a minute.')),button('Assess retrieved evidence',()=>run(()=>action(`claims/${c.claim_id}/assessment`),'Comparing the claim with retrieved passages…'),'primary'));card.append(actions);
  }
  const attempts=review.attempts.filter(a=>a.claim_id===c.claim_id);
  if(attempts.length){const a=el('div');for(const attempt of attempts)a.append(el('p',`${attempt.adapter} · ${attempt.access_state} · ${attempt.query_or_url}\n${attempt.detail}`));card.append(details('Retrieval attempts and access',a));}
  if(c.assessment_error)card.append(el('p',c.assessment_error,'error-box'));
  const a=c.assessment;
  if(a){card.append(el('span',a.status,'badge'),el('p',a.explanation));
   for(const e of a.evidence){const s=review.sources.find(s=>s.source_id===e.source_id);const quote=el('div',undefined,'quote');quote.append(el('span',`${e.relationship} · exact source quotation`,'subtle'),el('p',e.passage),el('p',`${s?.title||'Unknown source'} · ${e.location}`,'fine'));if(s){const link=el('a','Inspect source');link.href=s.url;link.target='_blank';link.rel='noopener noreferrer';quote.append(link);}card.append(quote);}
   if(a.context_mismatches.length)card.append(el('h4','Context mismatches'),list(a.context_mismatches));
   card.append(el('h4','Limitations'),list(a.limitations),el('h4','Suggested qualified wording'),el('p',a.suggested_wording),el('h4','Next verification question'),el('p',a.next_verification_step));
   const [wordWrap,word]=field('Your final wording',c.decision.final_wording||a.suggested_wording),[notesWrap,notes]=field('Researcher notes',c.decision.notes,2);card.append(wordWrap,notesWrap,el('p',`Researcher decision: ${c.decision.status}`,'subtle'));
   const choices=el('div',undefined,'actions');for(const [title,status] of [['Accept suggestion','accepted'],['Save edited wording','edited'],['Reject','rejected'],['Reset to pending','pending']])choices.append(button(title,()=>run(()=>action(`claims/${c.claim_id}/decision`,'PUT',{decision:{status,final_wording:word.value,notes:notes.value}}),'Recording researcher decision…')));card.append(choices,el('p','Use a decision button to record wording and notes before exporting. The original suggestion remains in the record.','fine'));
  }else card.append(el('p','No assessment available. Retrieval failures and missing access do not establish whether a claim is true or false.','muted'));
  container.append(card);
 }
 const record=$('#record');record.replaceChildren();const box=el('div',undefined,'record-box');box.append(el('span','05 / RECORD','section-label'),el('h3','Keep the evidence trail'),el('p','Exports include the mode, original input, source passages, access history, model provenance, and recorded researcher decisions.'));
 const buttons=el('div',undefined,'actions');for(const [title,fmt]of[['Download JSON','json'],['Download readable review','txt']])buttons.append(button(title,()=>run(async()=>{const res=await fetch(`/api/reviews/${review.review_id}/export?format=${fmt}`,{headers:{'X-Review-Session':session}});if(!res.ok)throw Error('Export validation failed.');const url=URL.createObjectURL(await res.blob());const a=el('a');a.href=url;a.download=`research-guard-${review.mode}.${fmt}`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);},'Validating and exporting review…')));box.append(buttons);
 const sources=el('div');for(const s of review.sources){const item=el('div',undefined,'source'),link=el('a',s.title);link.href=s.url;link.target='_blank';link.rel='noopener noreferrer';const integrity=s.integrity,integrityText=!integrity?'Integrity check unavailable — older record not confirmed clean.':integrity.status==='clean'?`No retraction indicators found (${integrity.checked_via} checked ${integrity.checked_at}).`:integrity.status==='not_applicable'?'Integrity check not applicable to this source type.':integrity.status==='check_failed'?`Integrity check unavailable — ${integrity.detail}`:`Publication notice: ${integrity.status.replaceAll('_',' ')} — ${integrity.detail}`;item.append(link,el('p',`${s.category} · ${s.access_level} · retrieved ${s.retrieved_at}`,'fine'),el('p',`DOI: ${s.doi||'unavailable'} · PMID: ${s.pmid||'unavailable'} · PMCID: ${s.pmcid||'unavailable'}`,'fine'),el('p',integrityText,'fine'),list(s.limitations));for(const p of s.passages)item.append(details(p.location,el('pre',p.text)));sources.append(item);}box.append(details(`Source records (${review.sources.length})`,sources));box.append(details('Validation and model provenance',el('pre',JSON.stringify({model_runs:review.model_runs,validation:review.validation_results,notices:review.notices},null,2))));record.append(box);
}
$('#review-form').onsubmit=e=>{e.preventDefault();run(async()=>{const context={};for(const key of ['organism_model','assay','reagent','conditions'])context[key]=$('#'+key).value;review=await api('/api/reviews',{text:$('#answer').value,intended_use:$('#intended-use').value,context,source_urls:$('#source-urls').value.split('\n').map(s=>s.trim()).filter(Boolean)});render();},'Creating an editable review…');};
$('#demo-button').onclick=()=>run(async()=>{review=await api('/api/reviews/demo',{});render();},'Loading curated demonstration…');
api('/api/config').then(c=>{config=c;message(c.model_configured?`${c.model_provider} free-access configuration is present; provider access is checked when used.`:`${c.model_detail} Public retrieval and the curated demo remain available.`);}).catch(e=>message(e.message,true));
