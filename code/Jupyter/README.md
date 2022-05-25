# Jupyter for pubmed-codeathon-team4!

## Installation

This code depends on a number of libraries. To install them from the command-line, execute:

```
pip install -r requirements.txt
```

If you are using a Jupyter nodebook, you can run a bash command using an exclamation point:

```
!pip install -r requirements.txt
```

## Why?

This code manages the Acceptable Usage Limits and makes our search client go as slow as needed.
It will sleep for microseconds if it is out of "tokens" to do an API operation.

I like that the response doesn't hide that the response is XML - you can use XPath naturally
rather than using Python specific constructions.

It also is growing to integrate with the history server, but this needs to be better
described.

## How to instantiate

I have no idea how this compares to Biopython, but it works with the E-Utilities test server.
You can import it as follows:

```python
from bmcodeathon.team4 import EUtils, print_element
```

Then, you create an instance of EUtils using the following arguments:
* `apikey` - Your API Key from your PubMed profile
* `email` - Your email address (this is currently unused, but I thought maybe put it in User-Agent.
* `rate` - A numeric, positive rate in requests/second.  This defaults to 3.
* `prefix` - The URL prefix of the server.  This defaults to https://eutils.ncbi.nlm.nih.gov/entrez,
  but you can set it to the test server by passing https://eutilspreview.ncbi.nlm.nih.gov/entrez

For instance:

```python
eutils = EUtils(my_api_key, my_email, 10, 'https://eutilspreview.ncbi.nlm.nih.gov/entrez')
```

The E-Utilities object has methods `einfo`, `esearch`, `efetch`, and `epost` that return a requests response object.
The response object is decorated with a `xml` attribute that holds the response as XML.  This has been changed
to only use XML to integrate with the history server

## Basic Usage

For example:

```python
r = eutils.esearch('pubmed', term='African Americans', retmax=200)
print_element(r.xml)
```

Since the `r.xml` above is an XML element, you can use XPath on it:

```python
pmids = [element.text for element in r.xml.xpath('//IdList/Id')]
print(pmids)
```

These PMIDs can be used with efetch, and "medline" format as well as "xml" is supported:

```python
r = eutils.efetch('pubmed', *pmids)
doc = r.xml()
returned_pmids = [element.text for element in doc.xpath('//PubmedArticle/MedlineCitation/PMID')]
returned_pmids == pmids
```

## With the History Server

See [E-Utilities and the History Server](https://dataguide.nlm.nih.gov/eutilities/history.html) for what
we are trying to do.  Do a search with history:

```python
r = eutils.esearch('pubmed', term='African Americans', sort='relevance', retmax=200)
print(r.webenv)
print(r.query_key)
```

Post those 200 results as a new saved result set:

```python
pmids = [element.text for element in r.xml.xpath('//IdList/Id')]
r2 = eutils.post('pubmed', *pmids, webenv=r.webenv)
print_element(r2.xml)
```

Compose the existing search with a new search:

```python
r3 = eutils.esearch('pubmed', term='Hedge query', webenv=r2.webenv, query_key=r2.query_key, retmax=200)
print_element(r3.xml)
```
