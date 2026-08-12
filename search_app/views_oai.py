import base64
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone as dt_tz

from django.http import HttpResponse
from django.views.decorators.http import require_GET

from .models import XMLDocument

OAI  = 'http://www.openarchives.org/OAI/2.0/'
OADC = 'http://www.openarchives.org/OAI/2.0/oai_dc/'
DC   = 'http://purl.org/dc/elements/1.1/'
XSI  = 'http://www.w3.org/2001/XMLSchema-instance'

ET.register_namespace('',       OAI)
ET.register_namespace('oai_dc', OADC)
ET.register_namespace('dc',     DC)
ET.register_namespace('xsi',    XSI)

REPO_NAME      = 'URI Archives & Special Collections Finding Aids'
BASE_URL       = 'https://webarchives.apps.uri.edu/oai/'
ADMIN_EMAIL    = 'archives@uri.edu'
EARLIEST_STAMP = '2020-01-01T00:00:00Z'
PAGE_SIZE      = 100
OAI_PREFIX     = 'oai_dc'
SET_SPEC       = 'finding-aids'
SET_NAME       = 'URI Archival Finding Aids'
OAI_ID_PREFIX  = 'oai:webarchives.apps.uri.edu:'


@require_GET
def oai_endpoint(request):
    verb = request.GET.get('verb', '')

    root = ET.Element(f'{{{OAI}}}OAI-PMH', {
        f'{{{XSI}}}schemaLocation':
            f'{OAI} http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd',
    })

    ET.SubElement(root, f'{{{OAI}}}responseDate').text = _utc_now()
    req_elem = ET.SubElement(root, f'{{{OAI}}}request')
    req_elem.text = BASE_URL
    for k, v in request.GET.items():
        req_elem.set(k, v)

    handlers = {
        'Identify':            _identify,
        'ListMetadataFormats': _list_metadata_formats,
        'ListSets':            _list_sets,
        'ListRecords':         _list_records,
        'ListIdentifiers':     _list_identifiers,
        'GetRecord':           _get_record,
    }

    if not verb:
        _error(root, 'badVerb', 'Missing verb argument')
    elif verb not in handlers:
        _error(root, 'badVerb', f'Illegal OAI verb: {verb}')
    else:
        handlers[verb](request, root)

    xml_str = ET.tostring(root, encoding='unicode')
    return HttpResponse(
        '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str,
        content_type='text/xml; charset=utf-8',
    )


# ── verb handlers ─────────────────────────────────────────────────────────────

def _identify(request, root):
    ident = ET.SubElement(root, f'{{{OAI}}}Identify')
    ET.SubElement(ident, f'{{{OAI}}}repositoryName').text  = REPO_NAME
    ET.SubElement(ident, f'{{{OAI}}}baseURL').text         = BASE_URL
    ET.SubElement(ident, f'{{{OAI}}}protocolVersion').text = '2.0'
    ET.SubElement(ident, f'{{{OAI}}}adminEmail').text      = ADMIN_EMAIL
    ET.SubElement(ident, f'{{{OAI}}}earliestDatestamp').text = EARLIEST_STAMP
    ET.SubElement(ident, f'{{{OAI}}}deletedRecord').text   = 'persistent'
    ET.SubElement(ident, f'{{{OAI}}}granularity').text     = 'YYYY-MM-DDThh:mm:ssZ'


def _list_metadata_formats(request, root):
    identifier = request.GET.get('identifier')
    if identifier:
        try:
            _doc_by_identifier(identifier)
        except XMLDocument.DoesNotExist:
            _error(root, 'idDoesNotExist', f'No record with identifier: {identifier}')
            return

    lmf = ET.SubElement(root, f'{{{OAI}}}ListMetadataFormats')
    fmt = ET.SubElement(lmf, f'{{{OAI}}}metadataFormat')
    ET.SubElement(fmt, f'{{{OAI}}}metadataPrefix').text      = OAI_PREFIX
    ET.SubElement(fmt, f'{{{OAI}}}schema').text              = \
        'http://www.openarchives.org/OAI/2.0/oai_dc.xsd'
    ET.SubElement(fmt, f'{{{OAI}}}metadataNamespace').text   = OADC


def _list_sets(request, root):
    ls = ET.SubElement(root, f'{{{OAI}}}ListSets')
    s  = ET.SubElement(ls,   f'{{{OAI}}}set')
    ET.SubElement(s, f'{{{OAI}}}setSpec').text = SET_SPEC
    ET.SubElement(s, f'{{{OAI}}}setName').text = SET_NAME


def _list_records(request, root):
    _paginated_list(request, root, 'ListRecords', include_metadata=True)


def _list_identifiers(request, root):
    _paginated_list(request, root, 'ListIdentifiers', include_metadata=False)


def _get_record(request, root):
    identifier      = request.GET.get('identifier')
    metadata_prefix = request.GET.get('metadataPrefix')

    if not identifier:
        _error(root, 'badArgument', 'identifier is required')
        return
    if not metadata_prefix:
        _error(root, 'badArgument', 'metadataPrefix is required')
        return
    if metadata_prefix != OAI_PREFIX:
        _error(root, 'cannotDisseminateFormat', f'Unsupported format: {metadata_prefix}')
        return

    try:
        doc = _doc_by_identifier(identifier)
    except XMLDocument.DoesNotExist:
        _error(root, 'idDoesNotExist', f'No record with identifier: {identifier}')
        return

    gr = ET.SubElement(root, f'{{{OAI}}}GetRecord')
    _record_elem(gr, doc, include_metadata=True)


# ── shared pagination ─────────────────────────────────────────────────────────

def _paginated_list(request, root, list_tag, include_metadata):
    token_str = request.GET.get('resumptionToken')
    if token_str:
        try:
            token = json.loads(base64.b64decode(token_str).decode())
        except Exception:
            _error(root, 'badResumptionToken', 'Invalid resumption token')
            return
        offset     = token.get('offset', 0)
        from_date  = token.get('from')
        until_date = token.get('until')
        set_spec   = token.get('set')
    else:
        offset          = 0
        from_date       = request.GET.get('from')
        until_date      = request.GET.get('until')
        set_spec        = request.GET.get('set')
        metadata_prefix = request.GET.get('metadataPrefix')
        if not metadata_prefix:
            _error(root, 'badArgument', 'metadataPrefix is required')
            return
        if metadata_prefix != OAI_PREFIX:
            _error(root, 'cannotDisseminateFormat', f'Unsupported format: {metadata_prefix}')
            return

    if set_spec and set_spec != SET_SPEC:
        _error(root, 'noRecordsMatch', f'Unknown set: {set_spec}')
        return

    qs = XMLDocument.objects.all()
    if from_date:
        try:
            qs = qs.filter(updated_at__gte=_parse_date(from_date))
        except ValueError:
            _error(root, 'badArgument', f'Invalid from date: {from_date}')
            return
    if until_date:
        try:
            qs = qs.filter(updated_at__lte=_parse_date(until_date))
        except ValueError:
            _error(root, 'badArgument', f'Invalid until date: {until_date}')
            return

    total = qs.count()
    if total == 0:
        _error(root, 'noRecordsMatch', 'No records match the given criteria')
        return

    container = ET.SubElement(root, f'{{{OAI}}}{list_tag}')
    for doc in qs.order_by('id')[offset:offset + PAGE_SIZE]:
        _record_elem(container, doc, include_metadata=include_metadata)

    next_offset = offset + PAGE_SIZE
    rt_attrs = {'completeListSize': str(total), 'cursor': str(offset)}
    rt = ET.SubElement(container, f'{{{OAI}}}resumptionToken', rt_attrs)
    if next_offset < total:
        token_data = {'offset': next_offset}
        if from_date:  token_data['from']  = from_date
        if until_date: token_data['until'] = until_date
        if set_spec:   token_data['set']   = set_spec
        rt.text = base64.b64encode(json.dumps(token_data).encode()).decode()


# ── record serialization ──────────────────────────────────────────────────────

def _record_elem(parent, doc, include_metadata):
    record = ET.SubElement(parent, f'{{{OAI}}}record')

    header_attrs = {'status': 'deleted'} if doc.is_deleted else {}
    header = ET.SubElement(record, f'{{{OAI}}}header', header_attrs)
    ET.SubElement(header, f'{{{OAI}}}identifier').text = doc.get_oai_identifier()
    ET.SubElement(header, f'{{{OAI}}}datestamp').text  = \
        doc.updated_at.strftime('%Y-%m-%dT%H:%M:%SZ')
    ET.SubElement(header, f'{{{OAI}}}setSpec').text    = SET_SPEC

    if doc.is_deleted or not include_metadata:
        return

    metadata = ET.SubElement(record, f'{{{OAI}}}metadata')
    dc = ET.SubElement(metadata, f'{{{OADC}}}dc', {
        f'{{{XSI}}}schemaLocation':
            f'{OADC} http://www.openarchives.org/OAI/2.0/oai_dc/oai_dc.xsd',
    })

    if doc.title:
        ET.SubElement(dc, f'{{{DC}}}title').text = doc.title

    if doc.creator:
        ET.SubElement(dc, f'{{{DC}}}creator').text = doc.creator

    if doc.abstract:
        # Primo's per-field maximum is 32,766 characters
        ET.SubElement(dc, f'{{{DC}}}description').text = doc.abstract[:32000]

    if doc.subjects:
        for subj in doc.subjects.split('; '):
            subj = subj.strip()
            if subj:
                ET.SubElement(dc, f'{{{DC}}}subject').text = subj

    if doc.dates:
        ET.SubElement(dc, f'{{{DC}}}date').text = doc.dates

    ET.SubElement(dc, f'{{{DC}}}type').text = 'Archival finding aid'

    if doc.eadid:
        ET.SubElement(dc, f'{{{DC}}}identifier').text = doc.eadid

    delivery_url = doc.public_url or doc.url or ''
    if delivery_url:
        ET.SubElement(dc, f'{{{DC}}}identifier').text = delivery_url

    ET.SubElement(dc, f'{{{DC}}}publisher').text = \
        'University of Rhode Island Libraries'
    ET.SubElement(dc, f'{{{DC}}}rights').text = \
        'Contact the repository regarding access and reuse.'


# ── utilities ─────────────────────────────────────────────────────────────────

def _error(root, code, message):
    ET.SubElement(root, f'{{{OAI}}}error', {'code': code}).text = message


def _utc_now():
    return datetime.now(dt_tz.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def _parse_date(date_str):
    for fmt in ('%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d'):
        try:
            return datetime.strptime(date_str, fmt).replace(tzinfo=dt_tz.utc)
        except ValueError:
            continue
    raise ValueError(f'Cannot parse date: {date_str}')


def _doc_by_identifier(identifier):
    """Resolve oai:webarchives.apps.uri.edu:{key} to an XMLDocument."""
    if not identifier.startswith(OAI_ID_PREFIX):
        raise XMLDocument.DoesNotExist
    key = identifier[len(OAI_ID_PREFIX):]
    try:
        return XMLDocument.objects.get(eadid=key)
    except XMLDocument.DoesNotExist:
        return XMLDocument.objects.get(filename=key + '.xml')
