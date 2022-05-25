from requests.adapters import HTTPAdapter
from urllib.parse import quote
from types import MethodType
import re
from collections import OrderedDict
from lxml import etree
from io import BytesIO

from .tokenbucket import RateLimitedSession


# Hostname for eutils
EUTILS_PREFIX = 'https://eutils.ncbi.nlm.nih.gov/entrez'

# Base URL for eutils
EUTILS_URL = '{}/eutils/{}'


class EUtils(object):
    """
    An abstraction that wraps the NCBI E-Utilities
    """
    def __init__(self, apikey=None, email=None, rate=3, prefix=None, session=None):
        self.apikey = apikey
        self.email = email
        self.rate = rate
        self.prefix = prefix if prefix else EUTILS_PREFIX
        self.call_count = 0
        if not session:
            session = RateLimitedSession(rate=rate, tokens=rate, capacity=rate)
            session.mount('https://', HTTPAdapter(max_retries=3, pool_maxsize=10))
        self.session = session

    def params(self, db=None, **kwargs):
        params = dict((k,v) for k,v in kwargs.items())
        if db:
            params['db'] = db
        if self.apikey:
            params['api_key'] = self.apikey
        return '&'.join('{}={}'.format(key, quote(value)) for key, value in params.items())

    def einfo(self, db=None, **kwargs):
        params = self.params(db, retmode='xml', **kwargs)
        url = EUTILS_URL.format(self.prefix, 'einfo.fcgi') + '?' + params
        r = self.session.get(url)
        self.call_count += 1
        r.raise_for_status()
        content_type = r.headers['Content-Type']
        if content_type.startswith('text/xml'):
            r.xml = etree.parse(BytesIO(r.content))
        return r

    def esearch(self, db, history=False, webenv=None, query_key=None, retmax=20, **kwargs):
        if history or webenv:
            kwargs['usehistory'] = 'y'
            if webenv:
                kwargs['WebEnv'] = webenv
            if query_key:
                kwargs['query_key'] = query_key
        params = self.params(db, retmode='xml', retmax=str(retmax), **kwargs)
        url = EUTILS_URL.format(self.prefix, 'esearch.fcgi') + '?' + params
        r = self.session.get(url)
        self.call_count += 1
        r.raise_for_status()
        content_type = r.headers['Content-Type']
        if content_type.startswith('text/xml'):
            r.xml = etree.parse(BytesIO(r.content))
            webenv = r.xml.xpath('/eSearchResult/WebEnv')
            r.webenv = webenv[0].text if webenv else None
            query_key = r.xml.xpath('/eSearchResult/QueryKey')
            r.query_key = query_key[0].text if query_key else None
        return r

    def efetch(self, db, *args, webenv=None, query_key=None, retmax=20, **kwargs):
        if webenv:
            kwargs['usehistory'] = 'y'
            kwargs['WebEnv'] = webenv
            if query_key:
                kwargs['query_key'] = query_key
        if len(args) > 0:
            idlist = ','.join(str(arg) for arg in args)
            params = self.params(db, retmode='xml', retmax=str(retmax), id=idlist, **kwargs)
        else:
            params = self.params(db, retmode='xml', retmax=str(retmax), **kwargs)
        url = EUTILS_URL.format(self.prefix, 'efetch.fcgi') + '?' + params
        r = self.session.get(url)
        self.call_count += 1
        r.raise_for_status()
        content_type = r.headers['Content-Type']
        if content_type.startswith('text/xml'):
            setattr(r, 'xml', etree.parse(BytesIO(r.content)))
        return r

    def epost(self, db, *args, webenv=None, **kwargs):
        idlist = ','.join(str(arg) for arg in args)
        if webenv:
            kwargs['WebEnv'] = webenv
        params = self.params(db, id=idlist, retmode='xml', **kwargs)
        url = EUTILS_URL.format(self.prefix, 'epost.fcgi') + '?' + params
        r = self.session.get(url)
        self.call_count += 1
        r.raise_for_status()
        content_type = r.headers['Content-Type']
        if content_type.startswith('text/xml'):
            setattr(r, 'xml', etree.parse(BytesIO(r.content)))
            webenv = r.xml.xpath('/ePostResult/WebEnv')
            r.webenv = webenv[0].text if webenv else None
            query_key = r.xml.xpath('/ePostResult/QueryKey')
            r.query_key = query_key[0].text if query_key else None
        return r
