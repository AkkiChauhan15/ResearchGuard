import hashlib
import json
import re
import selectors
import shutil
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urlsplit

from .integrity import check_source_integrity, complete_pubmed_integrity, integrity_from_pubmed_article, not_applicable_result
from .ncbi import ncbi
from .schemas import Attempt, Decision, Passage, Source, uid
from .transport import FetchError, fetch, validate_url

PRODUCT = 'https://www.enzo.com/product/cyto-id-autophagy-detection-kit/'
MANUAL = 'https://www.enzo.com/wp-content/uploads/2023/01/ENZ-51031_insert.pdf'


def text(node):
    return ''.join(node.itertext()).strip() if node is not None else ''


def xml(data):
    if b'<!ENTITY' in data.upper():
        raise FetchError('XML entity declarations are not supported.', 'parse_failed')
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        raise FetchError('Source XML could not be parsed.', 'parse_failed') from None
    if root.find('.//ERROR') is not None or root.tag.lower() == 'error':
        raise FetchError('Source API reported an unavailable record.', 'partial_access')
    return root


def digest(data):
    return hashlib.sha256(data).hexdigest()


OMISSION_PREFIX = 'Omitted PubMed search record — '


def pubmed_records(data, run, expected_pmid=None):
    root = xml(data)
    sources = []
    for article in root.findall('.//PubmedArticle'):
        pmid = text(article.find('./MedlineCitation/PMID'))
        if not re.fullmatch(r'\d+', pmid):
            continue
        if expected_pmid is not None and pmid != expected_pmid:
            continue
        passages = [Passage(text=text(n), location='Abstract' + (': ' + n.attrib['Label'] if n.attrib.get('Label') else '')) for n in article.findall('./MedlineCitation/Article/Abstract/AbstractText') if text(n)]
        # PubmedArticle can contain ArticleId elements for cited references. Only the
        # record's own PubmedData/ArticleIdList supplies canonical identifiers here.
        identifiers = {n.attrib.get('IdType'): text(n) for n in article.findall('./PubmedData/ArticleIdList/ArticleId')}
        date_node = article.find('./MedlineCitation/Article/Journal/JournalIssue/PubDate')
        date = ' '.join(text(n) for n in date_node) if date_node is not None else None
        authors = [' '.join(filter(None, [text(a.find('ForeName')), text(a.find('LastName')), text(a.find('CollectiveName'))])) for a in article.findall('./MedlineCitation/Article/AuthorList/Author')]
        source = Source(retrieval_run_id=run, url=f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/', category='pubmed', title=text(article.find('./MedlineCitation/Article/ArticleTitle')) or 'Title unavailable', authors=authors, date=date, doi=identifiers.get('doi'), pmid=pmid, pmcid=identifiers.get('pmc'), access_level='abstract' if passages else 'metadata', content_sha256=digest(data), passages=passages, limitations=['Abstract only; full text and methods have not been reviewed.'] if passages else ['No accessible abstract; metadata alone cannot establish support.'])
        source.integrity = complete_pubmed_integrity(source, integrity_from_pubmed_article(article))
        sources.append(source)
    if expected_pmid is not None and not sources:
        raise FetchError(f'PubMed response did not contain requested PMID {expected_pmid}.', 'parse_failed')
    return sources


def pmc_record(data, run, pmcid):
    root = xml(data)
    article = root if root.tag == 'article' else root.find('.//article')
    if article is None:
        raise FetchError('No accessible PMC article in response.', 'partial_access')
    ids = {n.attrib.get('pub-id-type'): text(n) for n in article.findall('./front/article-meta/article-id')}
    returned_pmcid = ids.get('pmcid') or ids.get('pmc')
    if returned_pmcid and returned_pmcid.removeprefix('PMC') != pmcid.removeprefix('PMC'):
        raise FetchError('PMC returned a different article identifier.', 'parse_failed')
    passages = [Passage(text=text(n), location=f'Abstract, paragraph {i}') for i, n in enumerate(article.findall('./front/article-meta/abstract//p'), 1) if text(n)]
    body = article.find('body')
    body_passages = []
    if body is not None:
        # XPath locations are actual XML positions, not invented PDF page numbers.
        for i, n in enumerate(body.iter('p'), 1):
            if text(n):
                body_passages.append(Passage(text=text(n), location=f'XML body paragraph {i}'))
    passages.extend(body_passages)
    limitations = [] if body_passages else ['PMC supplied abstract/metadata only; no readable full-text body paragraphs were available through this endpoint.']
    # Bound model material, preserving selected paragraphs unchanged.
    selected, chars = [], 0
    for p in passages:
        if chars + len(p.text) > 45000:
            limitations.append('Evidence extract limited to the first 45,000 characters of complete paragraphs.')
            break
        selected.append(p)
        chars += len(p.text)
    date = article.find('./front/article-meta/pub-date')
    authors = [' '.join(filter(None,[text(a.find('./name/given-names')),text(a.find('./name/surname'))])) for a in article.findall('./front/article-meta/contrib-group/contrib') if a.attrib.get('contrib-type') == 'author']
    return Source(retrieval_run_id=run, url=f'https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/', category='pmc', title=text(article.find('./front/article-meta/title-group/article-title')) or 'Title unavailable', authors=authors, date=' '.join(text(n) for n in date) if date is not None else None, doi=ids.get('doi'), pmid=ids.get('pmid'), pmcid=pmcid, access_level='full text' if body_passages else ('abstract' if selected else 'metadata'), content_sha256=digest(data), passages=selected, limitations=limitations)


class ProductHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.parts = []
        self.title_parts = []
        self.in_title = False
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'nav', 'header', 'footer'):
            self.skip += 1
        if tag == 'title':
            self.in_title = True
        if tag in ('p','div','br','li','h1','h2','h3','tr') and not self.skip:
            self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'nav', 'header', 'footer'):
            self.skip = max(0, self.skip - 1)
        if tag == 'title':
            self.in_title = False
        if tag in ('p','div','li','h1','h2','h3','tr') and not self.skip:
            self.parts.append('\n')
    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data)
        elif not self.skip:
            self.parts.append(data)


def product_record(data, run, url, headers):
    parser = ProductHTML()
    parser.feed(data.decode('utf-8'))
    title = ''.join(parser.title_parts).strip()
    if 'cyto-id' not in title.lower():
        raise FetchError('Product page identity could not be verified; possibly an access challenge.', 'parse_failed')
    lines = [s.strip() for s in ''.join(parser.parts).split('\n') if s.strip()]
    passages = [Passage(text=s, location=f'HTML text block {i}') for i, s in enumerate(lines, 1) if len(s) >= 40]
    if not passages:
        raise FetchError('No readable product text.', 'parse_failed')
    visible_version = next((line for line in lines if re.fullmatch(r'Last modified:\s+.+', line, re.IGNORECASE)), None)
    document_version = visible_version or (('HTTP Last-Modified: ' + headers['Last-Modified']) if headers.get('Last-Modified') else None)
    return Source(retrieval_run_id=run, url=url, category='manufacturer', title=title, access_level='product document', document_version=document_version, content_sha256=digest(data), passages=passages[:160], limitations=['Product web page, not a complete manual review; extracted HTML blocks may include site navigation.', 'HTML text-block locations refer to this hashed response and may change when the official page changes.'], integrity=not_applicable_result())


def pdf_text(data):
    executable = shutil.which('pdftotext')
    if not executable:
        raise FetchError('Manual parsing requires the pdftotext system utility.', 'parse_failed')
    if not data.startswith(b'%PDF-'):
        raise FetchError('Manual response is not a PDF.', 'parse_failed')
    # Public document only, never user input; temporary file is removed on exit.
    with tempfile.NamedTemporaryFile(suffix='.pdf') as document:
        document.write(data)
        document.flush()
        process = subprocess.Popen([executable, '-f', '1', '-l', '30', '-layout', document.name, '-'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        deadline, chunks, size = time.monotonic() + 8, [], 0
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise FetchError('Manual parser timed out.', 'parse_failed')
                    chunk = process.stdout.read1(65536)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > 250000:
                        raise FetchError('Manual text exceeds the extraction limit.', 'partial_access')
                    chunks.append(chunk)
            if process.wait(timeout=max(.01, deadline-time.monotonic())):
                raise FetchError('Manual PDF could not be parsed.', 'parse_failed')
            return b''.join(chunks).decode('utf-8')
        except subprocess.TimeoutExpired:
            raise FetchError('Manual parser timed out.', 'parse_failed') from None
        finally:
            if process.poll() is None:
                process.kill()
            process.wait()
            process.stdout.close()


def manual_record(data, run, headers):
    extracted = pdf_text(data)
    pages = extracted.split('\f')
    if 'ENZ-51031' not in pages[0] or 'CYTO-ID' not in pages[0]:
        raise FetchError('Manual product identity could not be verified.', 'parse_failed')
    passages, count = [], 0
    for i, page in enumerate(pages, 1):
        if not page.strip():
            continue
        if count + len(page) > 45000:
            break
        passages.append(Passage(text=page, location=f'PDF physical page {i}'))
        count += len(page)
    return Source(retrieval_run_id=run, url=MANUAL, category='manufacturer',
                  title='CYTO-ID Autophagy Detection Kit — ENZ-51031 Product Manual',
                  access_level='product document', document_version=('HTTP Last-Modified: '+headers['Last-Modified']) if headers.get('Last-Modified') else None,
                  content_sha256=digest(data), passages=passages,
                  limitations=['Text extraction only; diagrams and tables require visual inspection of the original PDF.',
                               'Physical PDF pages count from the cover; printed page labels may differ.',
                               'Extraction is limited to 30 physical pages and 45,000 characters of complete pages; later material may be omitted.',
                               'Product identity in a document does not establish which reagent the researcher actually used.'],
                  integrity=not_applicable_result())


def classify_url(url):
    p = validate_url(url)
    if p.query:
        raise FetchError('Source URLs must use canonical paths without query parameters.')
    if p.hostname == 'pubmed.ncbi.nlm.nih.gov' and re.fullmatch(r'/\d+/?', p.path):
        return 'pubmed', p.path.strip('/')
    if p.hostname == 'pmc.ncbi.nlm.nih.gov' and re.fullmatch(r'/articles/PMC\d+/?', p.path):
        return 'pmc', p.path.strip('/').split('/')[-1]
    if url in (PRODUCT, MANUAL):
        return 'manufacturer', url
    raise FetchError('Unsupported source URL. Use a canonical PubMed/PMC article or the exact Enzo CYTO-ID product page/manual.')


def retrieve_url(url, run):
    kind, identifier = classify_url(url)
    if kind == 'pubmed':
        data, _, _ = ncbi('efetch.fcgi', {'db':'pubmed','id':identifier,'retmode':'xml'})
        return pubmed_records(data, run, expected_pmid=identifier)
    if kind == 'pmc':
        data, _, _ = ncbi('efetch.fcgi', {'db':'pmc','id':identifier.removeprefix('PMC'),'retmode':'xml'})
        source = pmc_record(data, run, identifier)
        source.integrity = check_source_integrity(source)
        return [source]
    if url == MANUAL:
        data, final_url, headers = fetch(url, allowed_types={'application/pdf'})
        if final_url != MANUAL:
            raise FetchError('Manual redirected away from the supported exact document.', 'partial_access')
        return [manual_record(data, run, headers)]
    data, final_url, headers = fetch(url, allowed_types={'text/html'})
    if final_url != PRODUCT:
        raise FetchError('Product redirected away from the supported exact page.', 'partial_access')
    return [product_record(data, run, final_url, headers)]


def search_pubmed(query, run):
    data, _, _ = ncbi('esearch.fcgi', {'db':'pubmed','term':query,'retmode':'json','retmax':3,'sort':'relevance'})
    try:
        result = json.loads(data)['esearchresult']
        if result.get('errorlist') or result.get('ERROR'):
            raise ValueError()
        ids = result['idlist']
        if not isinstance(ids, list) or any(not isinstance(x,str) or not re.fullmatch(r'\d+',x) for x in ids):
            raise ValueError()
    except (ValueError, KeyError, TypeError):
        raise FetchError('PubMed search response could not be parsed.', 'parse_failed') from None
    if not ids:
        return []
    sources, omissions = [], []
    # Large consortium records can exceed the response budget. One oversized
    # record must not discard readable records from the same search.
    for identifier in ids:
        try:
            data, _, _ = ncbi('efetch.fcgi', {'db':'pubmed','id':identifier,'retmode':'xml'})
            sources.extend(pubmed_records(data, run, expected_pmid=identifier))
        except FetchError as exc:
            omissions.append(f'{OMISSION_PREFIX}PMID {identifier}: {exc}')
    if not sources:
        raise FetchError('Search returned identifiers but no readable records. ' + '; '.join(omissions), 'partial_access')
    for source in sources:
        source.limitations.extend(omissions)
    return sources


def retrieve(review, claim_id, query):
    from .reviews import get_claim
    if review.mode != 'live':
        raise ValueError('Demonstrations cannot perform live retrieval.')
    if not isinstance(query, str) or not query.strip() or len(query) > 500:
        raise ValueError('Enter 1–500 characters of search terms.')
    claim = get_claim(review, claim_id)
    claim.assessment, claim.assessment_error, claim.decision = None, None, Decision()
    claim.provider_assessments = []
    claim.second_opinion_attempts = []
    # Previous attempts remain inspectable but are not silently merged with a new run.
    for attempt in review.attempts:
        if attempt.claim_id == claim_id:
            attempt.claim_id = claim_id + ':prior_retrieval'
    run = uid('retrieval')
    jobs = [('pubmed', query, lambda: search_pubmed(query, run)),
            ('pubmed', f'({query}) AND (limitation OR contradictory OR replication)', lambda: search_pubmed(f'({query}) AND (limitation OR contradictory OR replication)', run))]
    for url in review.original_input.source_urls:
        jobs.append(('supplied source', url, lambda url=url: retrieve_url(url, run)))
    for adapter, value, job in jobs:
        try:
            sources = job()
            state = 'ok' if sources else 'no_results'
            if any(s.access_level in ('metadata','abstract') for s in sources):
                state = 'partial_access'
            omissions = sorted({limitation for source in sources for limitation in source.limitations if limitation.startswith(OMISSION_PREFIX)})
            if omissions:
                state = 'partial_access'
                detail = f'{len(sources)} source records retrieved; {len(omissions)} search record(s) omitted. ' + ' '.join(omissions)
            else:
                detail = f'{len(sources)} source records retrieved. Inspect access level and relevance.' if sources else 'No records returned. This does not establish that the claim is false.'
            review.sources.extend(sources)
            ids = [s.source_id for s in sources]
        except FetchError as exc:
            sources, ids, state, detail = [], [], exc.state, str(exc)
        except (ValueError, TypeError, KeyError, UnicodeError):
            sources, ids, state, detail = [], [], 'parse_failed', 'Source content could not be parsed.'
        review.attempts.append(Attempt(retrieval_run_id=run, claim_id=claim_id, query_or_url=value, adapter=adapter, access_state=state, detail=detail, source_ids=ids))
    return review
